#!/usr/bin/env python3
"""
Google Drive Connectivity Diagnostic Script
Tests the Google Drive service account configuration and connectivity
"""

import os
import sys
import json
import base64
from pathlib import Path
from io import BytesIO
from PIL import Image
from datetime import datetime
from dotenv import load_dotenv

def get_project_root():
    """Get chatbot project root"""
    return Path(__file__).parent

# Load .env file first
env_file = get_project_root() / '.env'
if env_file.exists():
    load_dotenv(env_file)
else:
    print(f"⚠️  .env file not found at {env_file}")

def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_step(step_num, text):
    """Print step info"""
    print(f"[Step {step_num}] {text}")

def print_success(text):
    """Print success message"""
    print(f"  ✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"  ❌ {text}")

def print_warning(text):
    """Print warning message"""
    print(f"  ⚠️  {text}")

def check_env_vars():
    """Check if required environment variables are set"""
    print_step(1, "Checking environment variables...")
    
    sa_json_path = os.getenv('GOOGLE_DRIVE_SA_JSON_PATH', '')
    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')
    
    if not sa_json_path:
        print_error("GOOGLE_DRIVE_SA_JSON_PATH not configured in .env")
        return False, sa_json_path, folder_id
    
    if not folder_id:
        print_warning("GOOGLE_DRIVE_FOLDER_ID not configured (optional)")
    else:
        print_success(f"Google Drive folder ID: {folder_id}")
    
    print_success(f"Service account JSON path: {sa_json_path}")
    return True, sa_json_path, folder_id

def check_service_account_file(sa_path):
    """Check if service account JSON file exists and is valid"""
    print_step(2, "Validating service account JSON file...")
    
    # Resolve path
    resolved_path = Path(sa_path)
    if not resolved_path.is_absolute():
        chatbot_dir = get_project_root()
        resolved_path = (chatbot_dir / sa_path).resolve()
    
    if not resolved_path.exists():
        print_error(f"Service account file not found: {resolved_path}")
        return False, None
    
    print_success(f"File found: {resolved_path}")
    
    # Try to load and validate JSON
    try:
        with open(resolved_path, 'r', encoding='utf-8') as f:
            sa_data = json.load(f)
        
        # Check required fields
        required_fields = ['type', 'project_id', 'private_key_id', 'client_email']
        missing_fields = [f for f in required_fields if f not in sa_data]
        
        if missing_fields:
            print_error(f"Service account JSON missing fields: {missing_fields}")
            return False, sa_data
        
        print_success(f"Service account type: {sa_data.get('type')}")
        print_success(f"Project ID: {sa_data.get('project_id')}")
        print_success(f"Service account email: {sa_data.get('client_email')}")
        
        return True, sa_data
    
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in service account file: {e}")
        return False, None
    
    except Exception as e:
        print_error(f"Failed to read service account file: {e}")
        return False, None

def check_google_libraries():
    """Check if required Google libraries are installed"""
    print_step(3, "Checking Google libraries...")
    
    libraries = {
        'google.oauth2.service_account': 'google-auth',
        'google.oauth2': 'google-auth',
        'googleapiclient.discovery': 'google-api-python-client',
        'googleapiclient.http': 'google-api-python-client',
    }
    
    all_ok = True
    for import_path, package_name in libraries.items():
        try:
            parts = import_path.split('.')
            for i in range(len(parts), 0, -1):
                try:
                    __import__('.'.join(parts[:i]))
                    break
                except ImportError:
                    continue
            print_success(f"Library available: {package_name}")
        except ImportError:
            print_error(f"Library NOT installed: {package_name}")
            print(f"      Install with: pip install {package_name}")
            all_ok = False
    
    return all_ok

def test_google_drive_service(sa_data, folder_id):
    """Test Google Drive service initialization"""
    print_step(4, "Testing Google Drive service initialization...")
    
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload
        
        # Create credentials
        credentials = service_account.Credentials.from_service_account_info(
            sa_data,
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        print_success("Service account credentials created successfully")
        
        # Build Drive service
        service = build('drive', 'v3', credentials=credentials)
        print_success("Google Drive API service built successfully")
        
        # Try to list files in target folder (if available)
        if folder_id:
            try:
                results = service.files().list(
                    q=f"'{folder_id}' in parents",
                    spaces='drive',
                    pageSize=5,
                    fields='files(id, name, mimeType, createdTime)'
                ).execute()
                
                files = results.get('files', [])
                print_success(f"Can access Google Drive folder: {folder_id}")
                print(f"      Files in folder: {len(files)}")
                
                if files:
                    print("\n      Recent files:")
                    for file in files[:5]:
                        print(f"        - {file['name']} (ID: {file['id'][:20]}...)")
                else:
                    print_warning("      Folder is empty or newly created")
                
                return True, service
            
            except Exception as e:
                print_error(f"Failed to access folder {folder_id}: {e}")
                print_warning("  Possible causes:")
                print_warning("    - Folder ID is incorrect")
                print_warning("    - Service account doesn't have access to folder")
                print_warning("    - Folder was deleted/shared")
                return False, service
        
        return True, service
    
    except Exception as e:
        print_error(f"Failed to initialize Google Drive service: {e}")
        return False, None

def test_file_upload(service, folder_id):
    """Test uploading a small test file"""
    print_step(5, "Testing file upload (supportsAllDrives=True for Shared Drive)...")
    
    if not service:
        print_warning("Skipping upload test - no valid service")
        return False
    
    try:
        from googleapiclient.http import MediaIoBaseUpload
        import base64
        
        # Create a tiny PNG (1x1 transparent)
        png_bytes = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        )
        
        file_metadata = {
            'name': f'test_upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png',
            'mimeType': 'image/png'
        }
        
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        media = MediaIoBaseUpload(
            BytesIO(png_bytes),
            mimetype='image/png',
            resumable=True
        )
        
        # supportsAllDrives=True is required for Shared Drive uploads
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink',
            supportsAllDrives=True
        ).execute()
        
        file_id = file.get('id')
        web_link = file.get('webViewLink')
        
        print_success(f"Test file uploaded successfully!")
        print(f"      File ID: {file_id}")
        print(f"      Link: {web_link}")
        
        # Delete the test file
        try:
            service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
            print_success("Test file deleted successfully")
        except Exception:
            print_warning("Could not delete test file (manual cleanup may be needed)")
        
        return True
    
    except Exception as e:
        error_str = str(e)
        if 'storageQuotaExceeded' in error_str:
            print_error("Upload failed: This is a personal Drive folder (not Shared Drive)")
            print_warning("  FIX: Create a Shared Drive and use its folder ID")
            print_warning("  → drive.google.com → 'Shared drives' → '+ New'")
            print_warning(f"  → Add member: drive-761@ai-assistant-7dbb8.iam.gserviceaccount.com as Manager")
        else:
            print_error(f"File upload test failed: {e}")
        return False

def test_google_drive_service_class():
    """Test the GoogleDriveService class from the app"""
    print_step(6, "Testing GoogleDriveService class...")
    
    try:
        sys.path.insert(0, str(get_project_root()))
        from core.google_drive_service import GoogleDriveService
        
        service = GoogleDriveService()
        
        if service._service is None:
            print_error("GoogleDriveService._service is None")
            print_warning("  Possible causes:")
            print_warning("    - Service account file not found")
            print_warning("    - Google libraries not installed")
            return False
        
        print_success("GoogleDriveService instance created successfully")
        
        folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')
        if folder_id:
            service.set_folder_id(folder_id)
            print_success(f"Folder ID set: {folder_id}")
        
        return True
    
    except Exception as e:
        print_error(f"GoogleDriveService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_summary(results):
    """Create a summary of all test results"""
    print_header("DIAGNOSTIC SUMMARY")
    
    checks = [
        ("Environment Variables", results.get('env_vars', False)),
        ("Service Account File", results.get('sa_file', False)),
        ("Google Libraries", results.get('libraries', False)),
        ("Drive Service Test", results.get('service_test', False)),
        ("File Upload Test", results.get('upload_test', False)),
        ("GoogleDriveService Class", results.get('class_test', False)),
    ]
    
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status:10} | {check_name}")
    
    print(f"\n  Result: {passed}/{total} checks passed")
    
    if passed == total:
        print_success("All checks passed! Google Drive is ready to use.")
        return True
    elif passed >= 4:
        print_warning("Most checks passed. Some features may work but check errors above.")
        return True
    else:
        print_error("Multiple issues found. See error messages above.")
        return False

def main():
    """Main diagnostic flow"""
    print_header("GOOGLE DRIVE CONNECTIVITY DIAGNOSTIC")
    print("This script checks if Google Drive upload is properly configured.\n")
    
    results = {}
    
    # Step 1: Check environment variables
    env_ok, sa_path, folder_id = check_env_vars()
    results['env_vars'] = env_ok
    
    if not env_ok:
        print("\n❌ Critical: Environment variables not configured properly")
        create_summary(results)
        return False
    
    # Step 2: Check service account file
    sa_ok, sa_data = check_service_account_file(sa_path)
    results['sa_file'] = sa_ok
    
    if not sa_ok:
        print("\n❌ Critical: Service account file invalid")
        create_summary(results)
        return False
    
    # Step 3: Check Google libraries
    lib_ok = check_google_libraries()
    results['libraries'] = lib_ok
    
    if not lib_ok:
        print("\n❌ Critical: Required Google libraries not installed")
        print("   Install them with: pip install google-auth google-api-python-client")
        create_summary(results)
        return False
    
    # Step 4: Test Drive service
    service_ok, service = test_google_drive_service(sa_data, folder_id)
    results['service_test'] = service_ok
    
    # Step 5: Test file upload (only if service works)
    if service_ok:
        upload_ok = test_file_upload(service, folder_id)
        results['upload_test'] = upload_ok
    else:
        results['upload_test'] = False
    
    # Step 6: Test GoogleDriveService class
    class_ok = test_google_drive_service_class()
    results['class_test'] = class_ok
    
    # Summary
    success = create_summary(results)
    
    # Recommendations
    if not success:
        print_header("NEXT STEPS")
        if not results.get('env_vars'):
            print("1. Configure environment variables in .env:")
            print("   GOOGLE_DRIVE_SA_JSON_PATH=config/google-drive-sa.json")
            print("   GOOGLE_DRIVE_FOLDER_ID=<your-folder-id>")
        
        if not results.get('libraries'):
            print("2. Install Google libraries:")
            print("   pip install google-auth google-api-python-client")
        
        if results.get('env_vars') and results.get('sa_file') and not results.get('service_test'):
            print("3. Check service account permissions:")
            print("   - Ensure service account has access to Google Drive folder")
            print("   - Verify folder ID is correct")
            print("   - Check Drive API is enabled in Google Cloud Console")
    
    return success

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnostic cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
