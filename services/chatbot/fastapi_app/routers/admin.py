"""
FastAPI Admin Router
Mirrors Flask routes/admin.py endpoints for the FastAPI mode.
Auth guard: session must have authenticated=True and user_role='admin'.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("chatbot.admin")

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ── Auth helper ──────────────────────────────────────────────────────────────

def _require_admin(request: Request):
    """Returns JSONResponse(403) if not admin, else None."""
    sess = request.session
    if not sess.get("authenticated"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    if sess.get("user_role") != "admin":
        return JSONResponse({"error": "Forbidden"}, status_code=403)
    return None


def _get_db():
    try:
        from core.extensions import get_db
        return get_db()
    except Exception:
        try:
            from config.mongodb_config import mongodb_client
            return mongodb_client.db
        except Exception:
            return None


# ── Stats ────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(request: Request):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    db = _get_db()
    if db is None:
        return JSONResponse({"error": "Database not available"}, status_code=503)
    try:
        stats = {
            "users": db.users.count_documents({}),
            "conversations": db.conversations.count_documents({}),
            "messages": db.messages.count_documents({}),
            "images": _count_images(db),
            "memories": db.chatbot_memory.count_documents({}),
        }
        recent = list(
            db.conversations.find(
                {}, {"title": 1, "user_id": 1, "model": 1, "created_at": 1, "updated_at": 1}
            ).sort("updated_at", -1).limit(10)
        )
        for c in recent:
            c["_id"] = str(c["_id"])
        stats["recent_conversations"] = recent
        return stats
    except Exception as e:
        logger.error(f"[Admin] Stats error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


def _count_images(db) -> int:
    try:
        pipeline = [
            {"$match": {"images": {"$exists": True, "$ne": []}}},
            {"$project": {"count": {"$size": "$images"}}},
            {"$group": {"_id": None, "total": {"$sum": "$count"}}},
        ]
        result = list(db.messages.aggregate(pipeline))
        msg_count = result[0]["total"] if result else 0
        file_count = (
            db.uploaded_files.count_documents(
                {"mime_type": {"$regex": "^image/", "$options": "i"}}
            )
            if "uploaded_files" in db.list_collection_names()
            else 0
        )
        return msg_count + file_count
    except Exception:
        return 0


# ── Users ────────────────────────────────────────────────────────────────────

@router.get("/users")
async def get_users(request: Request):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    db = _get_db()
    from core.user_auth import list_users
    users = list_users(db)
    return {"users": users}


@router.post("/users")
async def create_new_user(request: Request):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    try:
        data = await request.json()
    except Exception:
        data = {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = data.get("role", "user")
    display_name = (data.get("display_name") or "").strip()

    if not username or not password:
        return JSONResponse({"success": False, "message": "Username và password là bắt buộc"}, status_code=400)
    if len(username) < 3:
        return JSONResponse({"success": False, "message": "Username phải >= 3 ký tự"}, status_code=400)
    if len(password) < 4:
        return JSONResponse({"success": False, "message": "Password phải >= 4 ký tự"}, status_code=400)

    db = _get_db()
    from core.user_auth import create_user
    result = create_user(db, username, password, role, display_name or username)
    if result:
        logger.info(f"[Admin] Created user: {username} (role={role})")
        return {"success": True, "user": result}
    return JSONResponse({"success": False, "message": "Username đã tồn tại"}, status_code=409)


@router.post("/users/{username}/toggle")
async def toggle_user(username: str, request: Request):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    try:
        data = await request.json()
    except Exception:
        data = {}
    active = data.get("active", True)
    db = _get_db()
    from core.user_auth import toggle_user_active
    success = toggle_user_active(db, username, active)
    if success:
        return {"success": True}
    return JSONResponse({"success": False, "message": "Không thể thay đổi trạng thái admin"}, status_code=400)


@router.post("/users/{username}/password")
async def reset_password(username: str, request: Request):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    try:
        data = await request.json()
    except Exception:
        data = {}
    new_password = data.get("password") or ""
    if len(new_password) < 4:
        return JSONResponse({"success": False, "message": "Password phải >= 4 ký tự"}, status_code=400)
    db = _get_db()
    from core.user_auth import change_password
    success = change_password(db, username, new_password)
    if success:
        return {"success": True}
    return JSONResponse({"success": False, "message": "User không tồn tại"}, status_code=404)


@router.post("/users/{username}/quota/reset")
async def reset_user_quota(username: str, request: Request):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    db = _get_db()
    from core.user_auth import reset_image_quota
    ok = reset_image_quota(db, username)
    return {"success": ok}


@router.post("/users/{username}/video/unlock")
async def unlock_video(username: str, request: Request):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    db = _get_db()
    result = db["users"].update_one({"username": username}, {"$set": {"video_unlocked": True}})
    return {"success": result.modified_count > 0}


@router.post("/users/{username}/video/lock")
async def lock_video(username: str, request: Request):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    db = _get_db()
    result = db["users"].update_one({"username": username}, {"$set": {"video_unlocked": False}})
    return {"success": result.modified_count > 0}


# ── Sessions (Conversations) ─────────────────────────────────────────────────

@router.get("/sessions")
async def get_sessions(
    request: Request,
    page: int = 1,
    per_page: int = 20,
    search: str = "",
    user_id: str = "",
    model: str = "",
):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    db = _get_db()
    if db is None:
        return JSONResponse({"error": "Database not available"}, status_code=503)
    try:
        query = {}
        if user_id:
            query["user_id"] = user_id
        if model:
            query["model"] = {"$regex": model, "$options": "i"}
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"user_id": {"$regex": search, "$options": "i"}},
            ]
        total = db.conversations.count_documents(query)
        conversations = list(
            db.conversations.find(query)
            .sort("updated_at", -1)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        for c in conversations:
            c["_id"] = str(c["_id"])
        return {"conversations": conversations, "total": total, "page": page}
    except Exception as e:
        logger.error(f"[Admin] Sessions error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/sessions/{conversation_id}")
async def get_session_detail(conversation_id: str, request: Request):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    db = _get_db()
    if db is None:
        return JSONResponse({"error": "Database not available"}, status_code=503)
    try:
        from bson import ObjectId
        conv = db.conversations.find_one({"_id": conversation_id})
        if not conv:
            try:
                conv = db.conversations.find_one({"_id": ObjectId(conversation_id)})
            except Exception:
                pass
        if not conv:
            return JSONResponse({"error": "Session not found"}, status_code=404)
        conv["_id"] = str(conv["_id"])
        conv_id_str = str(conv["_id"])
        messages = list(
            db.messages.find(
                {"$or": [{"conversation_id": conv_id_str}, {"conversation_id": conversation_id}]}
            ).sort("created_at", 1)
        )
        for m in messages:
            m["_id"] = str(m["_id"])
            m["conversation_id"] = str(m.get("conversation_id", ""))
        conv["messages"] = messages
        return conv
    except Exception as e:
        logger.error(f"[Admin] Session detail error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Images ───────────────────────────────────────────────────────────────────

@router.get("/images")
async def get_images(
    request: Request,
    page: int = 1,
    per_page: int = 24,
    user_id: str = "",
    search: str = "",
):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    db = _get_db()
    if db is None:
        return JSONResponse({"error": "Database not available"}, status_code=503)
    try:
        images = []
        msg_query = {"images": {"$exists": True, "$ne": []}}
        if user_id:
            conv_ids = [str(c["_id"]) for c in db.conversations.find({"user_id": user_id}, {"_id": 1})]
            msg_query["conversation_id"] = {"$in": conv_ids}

        for msg in db.messages.find(msg_query).sort("created_at", -1):
            conv_id = str(msg.get("conversation_id", ""))
            msg_user = "unknown"
            try:
                from bson import ObjectId
                conv = db.conversations.find_one(
                    {"$or": [{"_id": conv_id}, {"_id": ObjectId(conv_id)}]}, {"user_id": 1}
                )
                if conv:
                    msg_user = conv.get("user_id", "unknown")
            except Exception:
                pass

            for img in msg.get("images", []):
                entry = {
                    "url": img.get("url", ""),
                    "cloud_url": img.get("cloud_url", ""),
                    "caption": img.get("caption", ""),
                    "name": img.get("caption") or f"Image from {msg.get('role', 'unknown')}",
                    "user_id": msg_user,
                    "created_at": msg.get("created_at"),
                    "source": "message",
                    "conversation_id": conv_id,
                }
                if search and search.lower() not in (entry["caption"] + entry["name"]).lower():
                    continue
                images.append(entry)

        file_query = {"mime_type": {"$regex": "^image/", "$options": "i"}}
        if user_id:
            file_query["user_id"] = user_id
        if search:
            file_query["name"] = {"$regex": search, "$options": "i"}
        try:
            for f in db.uploaded_files.find(file_query).sort("created_at", -1):
                images.append({
                    "url": f.get("path", ""),
                    "cloud_url": f.get("cloud_url", ""),
                    "caption": f.get("name", ""),
                    "name": f.get("name", "Uploaded Image"),
                    "user_id": f.get("user_id", "unknown"),
                    "created_at": f.get("created_at"),
                    "source": "upload",
                })
        except Exception:
            pass

        total = len(images)
        start = (page - 1) * per_page
        return {"images": images[start : start + per_page], "total": total, "page": page}
    except Exception as e:
        logger.error(f"[Admin] Images error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Memory ───────────────────────────────────────────────────────────────────

@router.get("/memory")
async def get_memory(
    request: Request,
    page: int = 1,
    per_page: int = 20,
    user_id: str = "",
    search: str = "",
):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    db = _get_db()
    if db is None:
        return JSONResponse({"error": "Database not available"}, status_code=503)
    try:
        query = {}
        if user_id:
            query["user_id"] = user_id
        if search:
            query["$or"] = [
                {"content": {"$regex": search, "$options": "i"}},
                {"question": {"$regex": search, "$options": "i"}},
                {"tags": {"$regex": search, "$options": "i"}},
            ]
        total = db.chatbot_memory.count_documents(query)
        memories = list(
            db.chatbot_memory.find(query)
            .sort("created_at", -1)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        for m in memories:
            m["_id"] = str(m["_id"])
        return {"memories": memories, "total": total, "page": page}
    except Exception as e:
        logger.error(f"[Admin] Memory error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Logs ─────────────────────────────────────────────────────────────────────

@router.get("/logs")
async def get_logs(
    request: Request,
    page: int = 1,
    per_page: int = 20,
    user_id: str = "",
    event: str = "",
    search: str = "",
):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    db = _get_db()
    if db is None:
        return JSONResponse({"error": "Database not available"}, status_code=503)
    try:
        query = {}
        if user_id:
            query["$or"] = [{"session_id": user_id}, {"user_id": user_id}]
        if event:
            query["event"] = event
        if search:
            search_conditions = [
                {"message": {"$regex": search, "$options": "i"}},
                {"response": {"$regex": search, "$options": "i"}},
            ]
            if "$or" in query:
                query["$and"] = [{"$or": query.pop("$or")}, {"$or": search_conditions}]
            else:
                query["$or"] = search_conditions

        col_name = "chat_logs"
        if col_name not in db.list_collection_names():
            return {"logs": [], "total": 0, "page": page}

        total = db[col_name].count_documents(query)
        logs = list(
            db[col_name].find(query)
            .sort("timestamp", -1)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        for l in logs:
            l["_id"] = str(l["_id"])
        return {"logs": logs, "total": total, "page": page}
    except Exception as e:
        logger.error(f"[Admin] Logs error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Payments ─────────────────────────────────────────────────────────────────

@router.get("/payments")
async def get_payment_requests(request: Request, status: Optional[str] = None):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    db = _get_db()
    from core.user_auth import list_payment_requests
    items = list_payment_requests(db, status if status and status != "all" else None)
    return {"payments": items, "total": len(items)}


@router.post("/payments/{req_id}/approve")
async def approve_payment(req_id: str, request: Request):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    db = _get_db()
    from core.user_auth import approve_payment_request
    ok = approve_payment_request(db, req_id, request.session.get("username", "admin"))
    if ok:
        return {"success": True}
    return JSONResponse({"success": False, "error": "Not found or already processed"}, status_code=404)


@router.post("/payments/{req_id}/reject")
async def reject_payment(req_id: str, request: Request):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    db = _get_db()
    from core.user_auth import reject_payment_request
    ok = reject_payment_request(db, req_id, request.session.get("username", "admin"))
    if ok:
        return {"success": True}
    return JSONResponse({"success": False, "error": "Not found or already processed"}, status_code=404)


# ── Quota limit ───────────────────────────────────────────────────────────────

@router.post("/users/{username}/quota/limit")
async def set_quota_limit(username: str, request: Request):
    guard = _require_admin(request)
    if guard is not None:
        return guard
    try:
        data = await request.json()
    except Exception:
        data = {}
    limit = data.get("limit")
    if limit is None:
        return JSONResponse({"success": False, "message": "limit is required"}, status_code=400)
    db = _get_db()
    from core.user_auth import set_image_quota_limit
    ok = set_image_quota_limit(db, username, int(limit))
    return {"success": ok}
