"""
Video Generation Routes (Flask) — /api/video/*
Wraps the Sora 2 module for the Flask new-structure mode.
Supports text-to-video and image-to-video (multipart upload).
"""
import logging
import os
import tempfile
import uuid

from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)
video_bp = Blueprint("video", __name__)

_ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
_MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20 MB


def _save_upload(file_storage) -> str | None:
    """Save an uploaded image to a temp file and return its path."""
    if not file_storage or not file_storage.filename:
        return None
    fname = secure_filename(file_storage.filename)
    ext = os.path.splitext(fname)[1].lower()
    if ext not in _ALLOWED_IMAGE_EXT:
        raise ValueError(f"Unsupported image type: {ext}")
    data = file_storage.read()
    if len(data) > _MAX_IMAGE_SIZE:
        raise ValueError("Image too large (max 20 MB)")
    dest = os.path.join(tempfile.gettempdir(), f"sora2_{uuid.uuid4().hex}{ext}")
    with open(dest, "wb") as f:
        f.write(data)
    return dest


@video_bp.route("/generate", methods=["POST"])
def generate_video():
    """Submit a video generation job.

    Accepts either JSON body or multipart/form-data (when an image is attached).
    """
    from src.video_generation import generate_video as _gen

    image_path = None
    try:
        # Multipart form (image upload)
        if request.content_type and "multipart" in request.content_type:
            prompt = (request.form.get("prompt") or "").strip()
            size = request.form.get("size", "1280x720")
            seconds = request.form.get("seconds", "8")
            model = request.form.get("model", "sora-2")
            image_path = _save_upload(request.files.get("image"))
        else:
            data = request.get_json(silent=True) or {}
            prompt = (data.get("prompt") or "").strip()
            size = data.get("size", "1280x720")
            seconds = data.get("seconds", "8")
            model = data.get("model", "sora-2")

        if not prompt:
            return jsonify({"error": "prompt is required"}), 400

        result = _gen(
            prompt=prompt,
            size=size,
            seconds=seconds,
            model=model,
            image_path=image_path,
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error("[Video] Generation error: %s", e)
        return jsonify({"error": str(e)}), 500
    finally:
        if image_path and os.path.exists(image_path):
            try:
                os.unlink(image_path)
            except OSError:
                pass


@video_bp.route("/status/<video_id>", methods=["GET"])
def video_status(video_id: str):
    """Poll OpenAI for current status of a video job."""
    from src.video_generation import poll_video

    try:
        job = poll_video(video_id)
        return jsonify(job)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error("[Video] Status poll error: %s", e)
        return jsonify({"error": str(e)}), 500


@video_bp.route("/cancel/<video_id>", methods=["POST"])
def cancel_video(video_id: str):
    """Cancel a running video generation job."""
    from src.video_generation import cancel_video as _cancel

    try:
        job = _cancel(video_id)
        return jsonify(job)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error("[Video] Cancel error: %s", e)
        return jsonify({"error": str(e)}), 500


@video_bp.route("/download/<video_id>", methods=["GET"])
def download_video(video_id: str):
    """Download the generated video file (mp4)."""
    from src.video_generation import VIDEO_STORAGE_DIR, download_video as _dl

    local_path = VIDEO_STORAGE_DIR / f"{video_id}.mp4"
    if not local_path.exists():
        try:
            local_path = _dl(video_id)
        except RuntimeError as e:
            return jsonify({"error": str(e)}), 503
        except Exception as e:
            logger.error("[Video] Download error: %s", e)
            return jsonify({"error": str(e)}), 500

    return send_file(str(local_path), mimetype="video/mp4", download_name=f"{video_id}.mp4")


@video_bp.route("/list", methods=["GET"])
def list_videos():
    """List recent video generation jobs from local metadata."""
    from src.video_generation import list_jobs

    limit = min(int(request.args.get("limit", 20)), 100)
    return jsonify({"videos": list_jobs(limit=limit)})
