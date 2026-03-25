"""
Image Storage Service
Upload images to ImgBB and save metadata to MongoDB/Firebase
"""
import os
import base64
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ImgBB API
IMGBB_API_KEY = os.getenv('IMGBB_API_KEY', '')
IMGBB_UPLOAD_URL = 'https://api.imgbb.com/1/upload'
GOOGLE_DRIVE_UPLOAD_URL = os.getenv('GOOGLE_DRIVE_UPLOAD_URL', '')
GOOGLE_DRIVE_FOLDER_URL = os.getenv(
    'GOOGLE_DRIVE_FOLDER_URL',
    'https://drive.google.com/drive/folders/11MN5m72gl84LsP1NMfBjeX9YAzsIlRxz?usp=sharing'
)

# MongoDB (optional)
try:
    from pymongo import MongoClient
    MONGO_URI = os.getenv('MONGODB_URI', '')
    if MONGO_URI:
        mongo_client = MongoClient(
            MONGO_URI, 
            serverSelectionTimeoutMS=5000,
            tls=True,
            tlsAllowInvalidCertificates=True
        )
        mongo_db = mongo_client.get_default_database() or mongo_client['ai_assistant']
        images_collection = mongo_db['generated_images']
        logger.info("[ImageStorage] MongoDB connected")
    else:
        mongo_client = None
        images_collection = None
except Exception as e:
    logger.warning(f"[ImageStorage] MongoDB not available: {e}")
    mongo_client = None
    images_collection = None

# Firebase Admin (optional)
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    FIREBASE_CREDS_PATH = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', '')
    if FIREBASE_CREDS_PATH and os.path.exists(FIREBASE_CREDS_PATH):
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CREDS_PATH)
            firebase_admin.initialize_app(cred)
        firebase_db = firestore.client()
        logger.info("[ImageStorage] Firebase connected")
    else:
        firebase_db = None
except Exception as e:
    logger.warning(f"[ImageStorage] Firebase not available: {e}")
    firebase_db = None

# Firebase Realtime Database (REST API — no Admin SDK required)
FIREBASE_RTDB_URL = os.getenv('FIREBASE_RTDB_URL', '').rstrip('/')
FIREBASE_DB_SECRET = os.getenv('FIREBASE_DB_SECRET', '')


def rtdb_push(path: str, data: dict) -> Optional[str]:
    """Push data to Firebase RTDB under the given path (POST → auto key).

    Returns the auto-generated key string, or None on failure.
    Works without a service account — uses DB Secret if set, otherwise
    relies on the RTDB security rules allowing writes.
    """
    if not FIREBASE_RTDB_URL:
        return None
    try:
        url = f"{FIREBASE_RTDB_URL}/{path.strip('/')}.json"
        params = {'auth': FIREBASE_DB_SECRET} if FIREBASE_DB_SECRET else {}
        resp = requests.post(url, json=data, params=params, timeout=10)
        if resp.status_code == 200:
            key = (resp.json() or {}).get('name')
            logger.info(f"[RTDB] Push /{path} → key={key}")
            return key
        logger.warning(f"[RTDB] Push failed {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"[RTDB] Push error: {e}")
    return None


def rtdb_set(path: str, data: dict) -> bool:
    """Set data at a specific RTDB path (PUT).  Returns True on success."""
    if not FIREBASE_RTDB_URL:
        return False
    try:
        url = f"{FIREBASE_RTDB_URL}/{path.strip('/')}.json"
        params = {'auth': FIREBASE_DB_SECRET} if FIREBASE_DB_SECRET else {}
        resp = requests.put(url, json=data, params=params, timeout=10)
        if resp.status_code == 200:
            logger.info(f"[RTDB] Set /{path}: OK")
            return True
        logger.warning(f"[RTDB] Set failed {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"[RTDB] Set error: {e}")
    return False


def rtdb_health() -> dict:
    """Ping Firebase RTDB. Returns {ok: bool, url: str, error: str|None}."""
    if not FIREBASE_RTDB_URL:
        return {'ok': False, 'url': '', 'error': 'FIREBASE_RTDB_URL not configured'}
    try:
        params = {'auth': FIREBASE_DB_SECRET, 'shallow': 'true'} if FIREBASE_DB_SECRET else {'shallow': 'true'}
        resp = requests.get(f"{FIREBASE_RTDB_URL}/.json", params=params, timeout=8)
        return {'ok': resp.status_code == 200, 'url': FIREBASE_RTDB_URL,
                'error': None if resp.status_code == 200 else f"HTTP {resp.status_code}"}
    except Exception as e:
        return {'ok': False, 'url': FIREBASE_RTDB_URL, 'error': str(e)}
    try:
        # Remove data URL prefix if present
        if 'base64,' in image_base64:
            image_base64 = image_base64.split('base64,')[1]
        
        payload = {
            'key': IMGBB_API_KEY,
            'image': image_base64,
            'name': name or f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        response = requests.post(IMGBB_UPLOAD_URL, data=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                url = result['data']['url']
                logger.info(f"[ImgBB] Image uploaded: {url}")
                return url
            else:
                logger.error(f"[ImgBB] Upload failed: {result}")
        else:
            logger.error(f"[ImgBB] HTTP error: {response.status_code}")
            
    except Exception as e:
        logger.error(f"[ImgBB] Exception: {e}")
    
    return None


def upload_to_drive(image_base64: str, name: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Upload image to Google Drive through configured webhook endpoint.

    Expected request body:
      { image: <base64>, name: <filename>, metadata: {...} }

    The endpoint can return fields like:
      url, webViewLink, webContentLink, file_id
    """
    result = {
        'success': False,
        'url': None,
        'file_id': None,
        'folder_url': GOOGLE_DRIVE_FOLDER_URL,
        'message': ''
    }

    if not GOOGLE_DRIVE_UPLOAD_URL:
        result['message'] = 'GOOGLE_DRIVE_UPLOAD_URL not configured'
        return result

    try:
        if 'base64,' in image_base64:
            image_base64 = image_base64.split('base64,')[1]

        payload = {
            'image': image_base64,
            'name': name or f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            'metadata': metadata or {}
        }

        response = requests.post(GOOGLE_DRIVE_UPLOAD_URL, json=payload, timeout=45)
        if response.status_code != 200:
            result['message'] = f'HTTP {response.status_code}'
            return result

        data = response.json() if response.content else {}
        drive_url = data.get('url') or data.get('webViewLink') or data.get('webContentLink')

        result.update({
            'success': bool(data.get('success', False) or drive_url),
            'url': drive_url,
            'file_id': data.get('file_id') or data.get('id') or data.get('fileId'),
            'folder_url': data.get('folder_url') or GOOGLE_DRIVE_FOLDER_URL,
            'message': data.get('message', '')
        })

        if result['success']:
            logger.info(f"[Drive] Image uploaded: {result['url']}")
        else:
            logger.warning(f"[Drive] Upload response without success/url: {data}")
    except Exception as e:
        result['message'] = str(e)
        logger.warning(f"[Drive] Upload failed: {e}")

    return result


def save_to_mongodb(image_data: Dict[str, Any]) -> Optional[str]:
    """
    Save image metadata to MongoDB
    
    Args:
        image_data: Dictionary with image metadata
        
    Returns:
        Document ID or None if failed
    """
    if not images_collection:
        logger.warning("[MongoDB] Not connected")
        return None
    
    try:
        image_data['created_at'] = datetime.utcnow()
        result = images_collection.insert_one(image_data)
        logger.info(f"[MongoDB] Image saved: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"[MongoDB] Save error: {e}")
        return None


def save_to_firebase(image_data: Dict[str, Any]) -> Optional[str]:
    """
    Save image metadata to Firebase Firestore
    
    Args:
        image_data: Dictionary with image metadata
        
    Returns:
        Document ID or None if failed
    """
    if not firebase_db:
        logger.warning("[Firebase] Not connected")
        return None
    
    try:
        image_data['created_at'] = datetime.utcnow()
        doc_ref = firebase_db.collection('generated_images').add(image_data)
        doc_id = doc_ref[1].id
        logger.info(f"[Firebase] Image saved: {doc_id}")
        return doc_id
    except Exception as e:
        logger.error(f"[Firebase] Save error: {e}")
        return None


def store_generated_image(
    image_base64: str,
    prompt: str,
    negative_prompt: str = "",
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Store generated image to ImgBB and save metadata to databases
    
    Args:
        image_base64: Base64 encoded image
        prompt: Generation prompt
        negative_prompt: Negative prompt
        metadata: Additional metadata
        
    Returns:
        Dictionary with storage results
    """
    result = {
        'success': False,
        'imgbb_url': None,
        'drive_url': None,
        'drive_file_id': None,
        'drive_folder_url': GOOGLE_DRIVE_FOLDER_URL,
        'mongodb_id': None,
        'firebase_id': None,
        'saved_to_mongodb': False,
        'saved_to_firebase': False
    }
    
    # Upload to ImgBB
    imgbb_url = upload_to_imgbb(image_base64)
    if imgbb_url:
        result['imgbb_url'] = imgbb_url
        result['success'] = True

    drive_result = upload_to_drive(
        image_base64=image_base64,
        name=(metadata or {}).get('filename'),
        metadata=metadata or {}
    )
    if drive_result.get('success'):
        result['drive_url'] = drive_result.get('url')
        result['drive_file_id'] = drive_result.get('file_id')
        result['drive_folder_url'] = drive_result.get('folder_url') or GOOGLE_DRIVE_FOLDER_URL
        result['success'] = True
    
    # Prepare metadata
    image_metadata = {
        'url': imgbb_url,
        'cloud_url': imgbb_url,
        'drive_url': result['drive_url'],
        'drive_file_id': result['drive_file_id'],
        'drive_folder_url': result['drive_folder_url'],
        'prompt': prompt,
        'negative_prompt': negative_prompt,
        'source': 'comfyui',
        **(metadata or {})
    }
    
    # Save to MongoDB
    mongo_id = save_to_mongodb(image_metadata.copy())
    if mongo_id:
        result['mongodb_id'] = mongo_id
        result['saved_to_mongodb'] = True
    
    # Save to Firebase
    firebase_id = save_to_firebase(image_metadata.copy())
    if firebase_id:
        result['firebase_id'] = firebase_id
        result['saved_to_firebase'] = True
    
    logger.info(f"[ImageStorage] Storage result: {result}")
    return result


def get_images_from_cloud(limit: int = 50) -> list:
    """
    Get images from cloud storage (MongoDB or Firebase)
    
    Args:
        limit: Maximum number of images to return
        
    Returns:
        List of image metadata
    """
    images = []
    
    # Try MongoDB first
    if images_collection:
        try:
            cursor = images_collection.find().sort('created_at', -1).limit(limit)
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                images.append(doc)
            if images:
                return images
        except Exception as e:
            logger.error(f"[MongoDB] Query error: {e}")
    
    # Fallback to Firebase
    if firebase_db:
        try:
            docs = firebase_db.collection('generated_images')\
                .order_by('created_at', direction='DESCENDING')\
                .limit(limit)\
                .stream()
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                images.append(data)
        except Exception as e:
            logger.error(f"[Firebase] Query error: {e}")
    
    return images
