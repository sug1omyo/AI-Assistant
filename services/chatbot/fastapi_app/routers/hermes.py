"""
Hermes Agent proxy router — FastAPI parity.

Provides:
  POST /api/hermes/chat — proxy to Hermes sidecar (JSON response)
"""
import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger("chatbot.fastapi.hermes")


class HermesRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10_000)
    conversation_history: Optional[list] = None
    model: Optional[str] = None


class HermesResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None
    elapsed_s: float = 0


@router.post(
    "/api/hermes/chat",
    response_model=HermesResponse,
    tags=["Tools"],
    summary="Proxy chat to Hermes Agent sidecar",
)
async def hermes_chat_route(body: HermesRequest):
    """Forward a chat request to the Hermes Agent sidecar."""
    message = body.message.strip()
    logger.info(
        "[HERMES-ROUTE] Request: msg_len=%d model=%s history_len=%d",
        len(message), body.model, len(body.conversation_history or []),
    )

    try:
        from core.hermes_adapter import hermes_chat
        result = hermes_chat(
            message,
            conversation_history=body.conversation_history,
            model=body.model,
        )
    except Exception as e:
        logger.error("[HERMES-ROUTE] Unhandled error: %s", e)
        return HermesResponse(
            success=False, result="",
            error=f"Internal error: {e}",
        )

    return HermesResponse(**result)
