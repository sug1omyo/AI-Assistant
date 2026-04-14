"""
Miscellaneous chat/file utility routes — mirrors Flask routes/main.py extras.

Routes:
    POST /api/extract-file-text   — Extract text from a base64-encoded file
    POST /api/chat/suggestions    — AI follow-up suggestion chips
"""
import base64

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core.extensions import logger

router = APIRouter(tags=["Utilities"])


# ---------------------------------------------------------------------------
# Extract file text
# ---------------------------------------------------------------------------

class ExtractFileBody(BaseModel):
    file_b64: str
    filename: str


@router.post("/api/extract-file-text")
async def extract_file_text(body: ExtractFileBody):
    """Extract readable text from a base64-encoded file (PDF, DOCX, XLSX, image, etc.)."""
    file_b64 = body.file_b64
    filename = body.filename.strip()

    if not file_b64 or not filename:
        raise HTTPException(400, "file_b64 and filename required")

    # Strip data URL prefix (e.g. "data:application/pdf;base64,...")
    if "," in file_b64:
        file_b64 = file_b64.split(",", 1)[1]

    try:
        file_bytes = base64.b64decode(file_b64)
    except Exception as e:
        raise HTTPException(400, f"Invalid base64: {e}")

    try:
        from src.ocr_integration import extract_file_content
        success, text = extract_file_content(file_bytes, filename)
    except Exception as e:
        logger.error(f"[extract-file-text] OCR error: {e}")
        raise HTTPException(500, str(e))

    if success and text and text.strip():
        return {"success": True, "text": text.strip(), "filename": filename}
    return {"success": False, "text": "", "error": "Could not extract text from file"}


# ---------------------------------------------------------------------------
# Chat suggestions
# ---------------------------------------------------------------------------

class SuggestionsBody(BaseModel):
    message: str
    response: str
    model: str | None = None
    language: str = "vi"


@router.post("/api/chat/suggestions")
async def chat_suggestions(body: SuggestionsBody, request: Request):
    """Generate 3 context-aware follow-up suggestions based on the conversation."""
    user_msg = body.message.strip()[:500]
    bot_resp = body.response.strip()[:1000]
    language = body.language.strip()
    model = body.model.strip() if body.model else None

    if not user_msg or not bot_resp:
        raise HTTPException(400, "message and response are required")

    vi = language != "en"
    if vi:
        prompt = (
            "Dựa trên cuộc trò chuyện dưới đây, hãy tạo ra ĐÚNG 3 câu hỏi tiếp theo "
            "mà người dùng có thể muốn hỏi. Mỗi câu hỏi phải:\n"
            "- Cụ thể, liên quan trực tiếp đến nội dung vừa trả lời\n"
            "- Ngắn gọn (tối đa 12 từ)\n"
            "- Khác nhau về góc nhìn (ví dụ: chi tiết hơn / ứng dụng thực tế / so sánh)\n"
            "Chỉ trả về 3 câu, mỗi câu 1 dòng, không đánh số, không giải thích.\n\n"
            f"Người dùng hỏi: {user_msg}\n"
            f"AI trả lời: {bot_resp}"
        )
    else:
        prompt = (
            "Based on the conversation below, generate EXACTLY 3 follow-up questions "
            "the user might want to ask. Each question must be:\n"
            "- Specific and directly related to the answer\n"
            "- Concise (max 12 words)\n"
            "- Different angles (e.g. deeper detail / practical use / comparison)\n"
            "Return only 3 questions, one per line, no numbering, no explanation.\n\n"
            f"User asked: {user_msg}\n"
            f"AI replied: {bot_resp}"
        )

    try:
        from fastapi_app.dependencies import get_chatbot_for_session
        chatbot = get_chatbot_for_session(request)
        response = chatbot.chat(
            message=prompt,
            model=model,
            context="casual",
            deep_thinking=False,
        )
        raw = response.get("text", "") if isinstance(response, dict) else str(response)
        lines = [ln.strip().lstrip("•-–—").strip() for ln in raw.strip().splitlines() if ln.strip()]
        suggestions = [ln for ln in lines if 5 < len(ln) < 150][:3]
        if suggestions:
            return {"suggestions": suggestions}
    except Exception as e:
        logger.warning(f"[chat/suggestions] AI call failed: {e}")

    return {"suggestions": []}
