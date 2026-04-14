"""
Image storage router — save / serve / list / delete generated images
"""
import base64
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from fastapi_app.dependencies import get_gallery_session_id
from fastapi_app.models import SaveImageRequest
from core.config import IMAGE_STORAGE_DIR
from core.extensions import logger

router = APIRouter()


@router.post("/api/save-image")
async def save_image(body: SaveImageRequest, request: Request):
    try:
        session_id = get_gallery_session_id(request)
        image_b64 = body.image
        if "base64," in image_b64:
            image_b64 = image_b64.split("base64,")[1]

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_{ts}.png"
        filepath = IMAGE_STORAGE_DIR / filename
        filepath.write_bytes(base64.b64decode(image_b64))

        metadata = {**body.metadata, "session_id": session_id}

        cloud_url = None
        try:
            from core.image_storage import store_generated_image
            res = store_generated_image(
                image_base64=image_b64,
                prompt=metadata.get("prompt", ""),
                negative_prompt=metadata.get("negative_prompt", ""),
                metadata=metadata,
            )
            if res.get("success"):
                cloud_url = res.get("imgbb_url")
        except Exception as e:
            logger.warning(f"[SaveImage] Cloud upload failed: {e}")

        return {
            "success": True,
            "filename": filename,
            "url": f"/storage/images/{filename}",
            "cloud_url": cloud_url,
            "session_id": session_id,
        }
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        raise HTTPException(500, str(e))


@router.get("/storage/images/{filename}")
async def serve_image(filename: str):
    path = IMAGE_STORAGE_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(404, "Image not found")
    # Ensure the resolved path is under IMAGE_STORAGE_DIR to prevent path traversal
    if not path.resolve().is_relative_to(IMAGE_STORAGE_DIR.resolve()):
        raise HTTPException(403, "Access denied")
    return FileResponse(path)


@router.get("/api/images")
async def list_images(request: Request):
    try:
        session_id = get_gallery_session_id(request)
        images = []
        for f in sorted(IMAGE_STORAGE_DIR.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True):
            meta_path = f.with_suffix(".json")
            meta = {}
            if meta_path.exists():
                import json
                try:
                    meta = json.loads(meta_path.read_text("utf-8"))
                except Exception:
                    pass
            # Only return images from this session (privacy)
            if meta.get("session_id") and meta["session_id"] != session_id:
                continue
            images.append({
                "filename": f.name,
                "url": f"/storage/images/{f.name}",
                "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "metadata": meta,
            })
        return {"images": images, "count": len(images)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.delete("/api/images/{filename}")
async def delete_image(filename: str):
    path = IMAGE_STORAGE_DIR / filename
    if not path.resolve().is_relative_to(IMAGE_STORAGE_DIR.resolve()):
        raise HTTPException(403, "Access denied")
    if not path.exists():
        raise HTTPException(404, "Image not found")
    path.unlink()
    meta = path.with_suffix(".json")
    if meta.exists():
        meta.unlink()
    return {"success": True, "message": "Image deleted"}


# ---------------------------------------------------------------------------
# Gallery upload to DB / cloud
# ---------------------------------------------------------------------------

class GalleryUploadBody(BaseModel):
    filename: str


@router.post("/api/gallery/upload-db")
async def upload_image_to_db(body: GalleryUploadBody, request: Request):
    """Upload a locally stored image + metadata to MongoDB/Firebase/ImgBB."""
    import json as _json
    import re as _re

    filename = body.filename.strip()
    if not filename or not _re.match(r"^[a-zA-Z0-9_\-\.]+$", filename):
        raise HTTPException(400, "Invalid filename")

    filepath = IMAGE_STORAGE_DIR / filename
    if not filepath.exists() or not filepath.resolve().is_relative_to(IMAGE_STORAGE_DIR.resolve()):
        raise HTTPException(404, "Image not found locally")

    raw_bytes = filepath.read_bytes()
    image_b64 = base64.b64encode(raw_bytes).decode()

    meta_path = filepath.with_suffix(".json")
    local_payload: dict = {}
    if meta_path.exists():
        try:
            local_payload = _json.loads(meta_path.read_text("utf-8"))
        except Exception:
            pass

    session_id = get_gallery_session_id(request)
    metadata = local_payload.get("metadata", local_payload if isinstance(local_payload, dict) else {})
    metadata["filename"] = filename
    metadata.setdefault("session_id", session_id)

    try:
        from core.image_storage import store_generated_image
        result = store_generated_image(
            image_base64=image_b64,
            prompt=metadata.get("prompt", ""),
            negative_prompt=metadata.get("negative_prompt", ""),
            metadata=metadata,
            raw_legacy_payload=local_payload if isinstance(local_payload, dict) else {},
        )
    except Exception as e:
        logger.error(f"[UploadDB] store_generated_image error: {e}")
        raise HTTPException(500, "Failed to upload to database")

    db_status = {
        "mongodb": bool(result.get("saved_to_mongodb")),
        "firebase": bool(result.get("saved_to_firebase")),
    }

    merged = {
        **(local_payload if isinstance(local_payload, dict) else {}),
        "filename": filename,
        "created_at": local_payload.get("created_at", datetime.now().isoformat()),
        "cloud_url": result.get("imgbb_url") or local_payload.get("cloud_url"),
        "drive_url": result.get("drive_url") or local_payload.get("drive_url"),
        "drive_file_id": result.get("drive_file_id") or local_payload.get("drive_file_id"),
        "db_status": db_status,
        "metadata": metadata,
    }
    try:
        meta_path.write_text(_json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    return {
        "success": True,
        "filename": filename,
        "imageURL": result.get("drive_url") or result.get("imgbb_url") or f"/storage/images/{filename}",
        "cloud_url": result.get("imgbb_url"),
        "drive_url": result.get("drive_url"),
        "db_status": db_status,
        "storage_result": result,
    }


# ---------------------------------------------------------------------------
# Upload to ImgBB
# ---------------------------------------------------------------------------

class ImgBBUploadBody(BaseModel):
    image: str  # base64-encoded image data
    name: str | None = None


@router.post("/api/upload-imgbb")
async def upload_to_imgbb(body: ImgBBUploadBody):
    """Upload a base64 image to ImgBB and return the URL."""
    if not body.image:
        raise HTTPException(400, "No image data provided")
    try:
        from core.image_storage import upload_to_imgbb as _imgbb_upload
        url = _imgbb_upload(body.image, body.name)
        if url:
            return {"success": True, "url": url}
        return JSONResponse(status_code=500, content={"success": False, "error": "Upload failed"})
    except Exception as e:
        logger.error(f"[UploadImgBB] Error: {e}")
        raise HTTPException(500, "Failed to upload image")
