"""
last30days social media research router — FastAPI parity.

Provides:
  POST /api/tools/last30days — run a last30days research query (JSON response)
"""
import logging
import time
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger("chatbot.fastapi.last30days")


class Last30daysRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    depth: str = Field(default="default", pattern=r"^(quick|default|deep)$")
    days: int = Field(default=30, ge=1, le=90)
    sources: Optional[str] = Field(default=None, max_length=200)


class Last30daysMetadata(BaseModel):
    topic: str
    depth: str
    days: int
    elapsed_s: float


class Last30daysResponse(BaseModel):
    success: bool
    result: str
    metadata: Last30daysMetadata
    error: Optional[str] = None


@router.post(
    "/api/tools/last30days",
    response_model=Last30daysResponse,
    tags=["Tools"],
    summary="Run last30days social media research",
)
async def last30days_research(body: Last30daysRequest):
    """Run a multi-platform social media research query via the last30days engine."""
    topic = body.topic.strip()
    logger.info(
        "[LAST30DAYS-ROUTE] Request: topic=%r depth=%s days=%d sources=%s",
        topic, body.depth, body.days, body.sources,
    )

    start = time.time()
    try:
        from core.last30days_tool import run_last30days_research
        result = run_last30days_research(
            topic,
            depth=body.depth,
            days=body.days,
            sources=body.sources,
        )
    except Exception as e:
        logger.error("[LAST30DAYS-ROUTE] Unhandled error: %s", e)
        return Last30daysResponse(
            success=False,
            result="",
            metadata=Last30daysMetadata(
                topic=topic,
                depth=body.depth,
                days=body.days,
                elapsed_s=round(time.time() - start, 2),
            ),
            error=f"Internal error: {e}",
        )

    elapsed = round(time.time() - start, 2)
    is_error = result.startswith("❌") if result else True

    logger.info(
        "[LAST30DAYS-ROUTE] Completed: success=%s elapsed=%.2fs len=%d",
        not is_error, elapsed, len(result or ""),
    )

    return Last30daysResponse(
        success=not is_error,
        result=result or "",
        metadata=Last30daysMetadata(
            topic=topic,
            depth=body.depth,
            days=body.days,
            elapsed_s=elapsed,
        ),
        error=result if is_error else None,
    )
