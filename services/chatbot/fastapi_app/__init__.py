"""
FastAPI Application - Chatbot Service
Migrated from Flask monolith for native async support and better performance.
"""
import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware

# Ensure paths
CHATBOT_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = CHATBOT_DIR.parent.parent

if str(CHATBOT_DIR) not in sys.path:
    sys.path.insert(0, str(CHATBOT_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(1, str(ROOT_DIR))

from core.config import IMAGE_STORAGE_DIR, MEMORY_DIR
from core.extensions import MONGODB_ENABLED, logger

# Import routers
from fastapi_app.routers import (
    chat,
    council_stream,
    xai_native_stream,
    stream,
    conversations,
    memory,
    images,
    video,
    rag,
    skills,
    last30days,
    hermes,
)

logger = logging.getLogger("chatbot.fastapi")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 FastAPI Chatbot starting up...")

    # Ensure storage directories
    IMAGE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    if MONGODB_ENABLED:
        logger.info("✅ MongoDB connection available")
    else:
        logger.warning("⚠️ MongoDB not available — some features disabled")

    yield

    logger.info("🛑 FastAPI Chatbot shutting down...")


def create_app() -> FastAPI:
    """Application factory"""
    app = FastAPI(
        title="AI Assistant Chatbot",
        description="Multi-model AI chatbot with streaming, video generation, and more",
        version="2.0.0",
        lifespan=lifespan,
    )

    # --- Middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    secret = os.getenv("SESSION_SECRET", os.urandom(32).hex())
    app.add_middleware(SessionMiddleware, secret_key=secret)

    # --- Static files ---
    static_dir = CHATBOT_DIR / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    storage_dir = IMAGE_STORAGE_DIR
    if storage_dir.exists():
        app.mount(
            "/storage/images",
            StaticFiles(directory=str(storage_dir)),
            name="image_storage",
        )

    # --- Templates ---
    templates_dir = CHATBOT_DIR / "templates"
    templates = Jinja2Templates(directory=str(templates_dir)) if templates_dir.exists() else None

    # Inject a Flask-compatible url_for into Jinja2 globals so that
    # {{ url_for('static', filename='css/app.css') }} works unchanged.
    if templates:
        def _url_for(name: str, **kwargs) -> str:
            if name == 'static':
                path = kwargs.get('filename', kwargs.get('path', ''))
                return f"/static/{path}"
            # Other named routes: best-effort path construction
            path = kwargs.get('filename', kwargs.get('path', ''))
            return f"/{name}/{path}" if path else f"/{name}"
        templates.env.globals['url_for'] = _url_for

    # --- Page routes ---
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        if templates:
            return templates.TemplateResponse("index.html", {"request": request})
        return HTMLResponse("<h1>AI Chatbot (FastAPI)</h1><p>Templates directory not found.</p>")

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        ico = CHATBOT_DIR / "static" / "favicon.ico"
        if ico.exists():
            return FileResponse(str(ico))
        return HTMLResponse("", status_code=204)

    # --- Auth endpoints ---
    @app.get("/api/auth/me")
    async def auth_me(request: Request):
        """Return current session user info (FastAPI/session-middleware path)."""
        sess = request.session
        if not sess.get("authenticated"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"authenticated": False}, status_code=401)
        return {
            "authenticated": True,
            "user": {
                "user_id": sess.get("user_id"),
                "username": sess.get("username"),
                "role": sess.get("user_role"),
                "display_name": sess.get("display_name"),
            },
        }

    # --- Misc API stubs (non-critical, polled by frontend on load) ---
    @app.get("/api/local-models-status")
    async def local_models_status():
        """Report whether local transformer models are available."""
        try:
            from core.model_loader import model_loader  # type: ignore
            return {"available": True, "models": model_loader.get_available_models()}
        except ImportError:
            return {
                "available": False,
                "error": "Local models not available. Install: pip install torch transformers accelerate",
            }

    _NEGATIVE_PRESETS_DATA = [
        {"id": "quality", "label": "Quality Fix", "prompt": "worst quality, low quality, normal quality, lowres, blurry, jpeg artifacts, watermark, text, signature, cropped, out of frame, duplicate, mutation, deformed"},
        {"id": "anatomy", "label": "Anatomy Fix", "prompt": "bad anatomy, bad hands, missing fingers, extra fingers, fused fingers, too many fingers, missing limbs, extra limbs, malformed limbs, floating limbs, disconnected limbs"},
        {"id": "face", "label": "Face Fix", "prompt": "bad face, disfigured face, mutated face, blurry face, extra face, cloned face, deformed eyes, crossed eyes, asymmetrical eyes"},
        {"id": "nsfw", "label": "SFW Filter", "prompt": "nsfw, nude, naked, sexual, explicit, pornographic, lewd, erotic, suggestive, revealing clothing, underwear, bikini, lingerie"},
    ]

    @app.get("/api/sd-negative-presets")
    async def sd_negative_presets():
        """Return stable diffusion negative prompt presets."""
        return {"success": True, "presets": _NEGATIVE_PRESETS_DATA}

    # --- Routers ---
    app.include_router(chat.router, tags=["Chat"])
    app.include_router(council_stream.router, tags=["Council Streaming"])
    app.include_router(xai_native_stream.router, tags=["xAI Native Streaming"])
    app.include_router(stream.router, tags=["Streaming"])
    app.include_router(conversations.router, prefix="/api", tags=["Conversations"])
    app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
    app.include_router(images.router, tags=["Images"])
    app.include_router(video.router, prefix="/api/video", tags=["Video Generation"])
    app.include_router(rag.router, prefix="/api/rag", tags=["RAG"])
    app.include_router(skills.router, tags=["Skills"])
    app.include_router(last30days.router, tags=["Tools"])
    app.include_router(hermes.router, tags=["Tools"])

    # --- Root health check ---
    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "service": "chatbot",
            "framework": "fastapi",
            "mongodb": MONGODB_ENABLED,
        }

    return app
