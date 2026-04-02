"""
Streaming routes: /chat/stream - SSE endpoint for real-time chat responses

Supports live thinking display (like ChatGPT) with real-time reasoning steps
streamed before the actual response.
"""
import json
import os
import uuid
import time
from datetime import datetime
from pathlib import Path
import sys
from flask import Blueprint, request, session, Response
import logging

# Setup path
CHATBOT_DIR = Path(__file__).parent.parent.resolve()
if str(CHATBOT_DIR) not in sys.path:
    sys.path.insert(0, str(CHATBOT_DIR))

from core.config import MEMORY_DIR
from core.extensions import MONGODB_ENABLED, logger
from core.chatbot_v2 import get_chatbot
from core.streaming import StreamingChatHandler, StreamEvent
from core.thinking_generator import (
    ThinkTagParser, detect_category,
    generate_thinking_summary, REASONING_PREFIX
)

# Check MCP availability
MCP_AVAILABLE = False
try:
    from src.handlers.mcp_handler import inject_code_context, get_mcp_client
    MCP_AVAILABLE = True
except ImportError:
    pass

stream_bp = Blueprint('stream', __name__)


# ── Auto web-search detection ────────────────────────────────────────

_REALTIME_PATTERNS_VI = [
    "giá", "tỷ giá", "thời tiết", "tin tức", "mới nhất", "hiện tại",
    "hôm nay", "bây giờ", "mấy giờ", "ngày bao nhiêu",
    "lịch", "kết quả", "tỉ số", "xổ số", "chứng khoán",
    "cổ phiếu", "bitcoin", "crypto", "coin", "vàng", "USD",
    "bao nhiêu tiền", "review", "đánh giá", "so sánh",
    "nên mua", "mua ở đâu", "ở đâu", "địa chỉ", "số điện thoại",
    "sự kiện", "lịch trình", "cập nhật", "phiên bản mới",
    "ra mắt", "release", "công bố", "thông báo",
]
_REALTIME_PATTERNS_EN = [
    "price", "weather", "news", "latest", "current", "today",
    "right now", "stock", "bitcoin", "crypto", "gold price",
    "exchange rate", "how much", "review", "compare",
    "where to buy", "address", "phone number", "schedule",
    "update", "new version", "release", "announcement",
    "score", "result", "ranking", "trending",
]
_SEARCH_KEYWORDS = [
    "tìm", "search", "tra cứu", "look up", "google",
    "tìm kiếm", "find", "tìm giúp", "check",
]


def _needs_web_search(message: str, tools: list) -> bool:
    """Detect if the message needs web search for accurate real-time data."""
    if "google-search" in tools or "deep-research" in tools:
        return True
    msg_lower = message.lower()
    if any(kw in msg_lower for kw in _SEARCH_KEYWORDS):
        return True
    if any(p in msg_lower for p in _REALTIME_PATTERNS_VI + _REALTIME_PATTERNS_EN):
        return True
    return False


def _run_web_search(query: str, engine: str = "google") -> str:
    """
    Web search. Uses SerpAPI when SERPAPI_API_KEY is set; falls back to Google CSE.
    engine: 'google' (default), 'bing', 'baidu'
    """
    import requests as _req
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    serpapi_key = os.getenv("SERPAPI_API_KEY", "")

    # ── SerpAPI (primary) ──────────────────────────────────────────────
    if serpapi_key:
        try:
            resp = _req.get("https://serpapi.com/search.json", params={
                "engine": engine,
                "q": query,
                "api_key": serpapi_key,
                "num": 5,
            }, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("organic_results", [])
                if items:
                    label = {"google": "Google", "bing": "Bing", "baidu": "Baidu"}.get(engine, engine.title())
                    parts = []
                    for item in items[:5]:
                        title = item.get("title", "")
                        snippet = item.get("snippet", item.get("description", ""))
                        link = item.get("link", "")
                        parts.append(f"**{title}**\n{snippet}\n🔗 {link}")
                    return f"🔍 **{label} Search — Kết quả thực tế:**\n\n" + "\n\n---\n\n".join(parts)
        except Exception as e:
            logger.warning(f"[WebSearch:SerpAPI] Error: {e}")

    # ── Google Custom Search (fallback) ────────────────────────────────
    api_key_1 = os.getenv("GOOGLE_SEARCH_API_KEY_1", "")
    api_key_2 = os.getenv("GOOGLE_SEARCH_API_KEY_2", "")
    cse_id = os.getenv("GOOGLE_CSE_ID", "")

    if not api_key_1 or not cse_id:
        logger.warning("[WebSearch] Missing all search credentials")
        return ""

    url = "https://www.googleapis.com/customsearch/v1"
    s = _req.Session()
    retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[500, 502, 503])
    s.mount("https://", HTTPAdapter(max_retries=retry))

    for api_key in [api_key_1, api_key_2]:
        if not api_key:
            continue
        try:
            resp = s.get(url, params={
                "key": api_key, "cx": cse_id, "q": query, "num": 5,
            }, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                if items:
                    parts = []
                    for item in items[:5]:
                        title = item.get("title", "")
                        snippet = item.get("snippet", "")
                        link = item.get("link", "")
                        parts.append(f"**{title}**\n{snippet}\n🔗 {link}")
                    return "🔍 **Kết quả tìm kiếm web (real-time):**\n\n" + "\n\n---\n\n".join(parts)
            elif resp.status_code in (429, 403):
                continue
            else:
                logger.warning(f"[WebSearch] HTTP {resp.status_code}")
                return ""
        except Exception as e:
            logger.warning(f"[WebSearch] Error: {e}")
            continue

    return ""


@stream_bp.route('/chat/stream', methods=['POST', 'GET'])
def chat_stream():
    """
    Streaming chat endpoint using Server-Sent Events (SSE)
    
    Supports both POST (preferred) and GET (for simple testing)
    
    Request Body (POST) or Query Params (GET):
        - message: User message (required)
        - model: AI model to use (default: 'grok')
        - context: Conversation context (default: 'casual')
        - deep_thinking: Enable detailed reasoning (default: false)
        - language: Response language (default: 'vi')
        - custom_prompt: Custom system prompt (optional)
        - memory_ids: List of memory IDs to include (optional)
    
    Returns:
        SSE stream with events:
        - metadata: Initial metadata about the request
        - chunk: Response chunks as they arrive
        - complete: Final event with full response
        - error: Error event if something fails
    """
    try:
        # Parse request
        if request.method == 'POST':
            if request.content_type and 'application/json' in request.content_type:
                data = request.json or {}
            else:
                data = request.form.to_dict()
                # Parse JSON fields
                for key in ['memory_ids', 'history', 'mcp_selected_files']:
                    if key in data:
                        try:
                            data[key] = json.loads(data[key])
                        except:
                            data[key] = []
        else:
            # GET request
            data = request.args.to_dict()
        
        message = data.get('message', '')
        model = data.get('model', 'grok')
        context = data.get('context', 'casual')
        deep_thinking = str(data.get('deep_thinking', 'false')).lower() == 'true'
        language = data.get('language', 'vi')
        custom_prompt = data.get('custom_prompt', '')
        memory_ids = data.get('memory_ids', [])
        mcp_selected_files = data.get('mcp_selected_files', [])
        history = data.get('history')

        # Map thinking_mode (from frontend) to backend behavior
        thinking_mode = data.get('thinking_mode', 'auto')
        if thinking_mode in ('thinking', 'deep', 'multi-thinking'):
            deep_thinking = True
        elif thinking_mode in ('instant', 'auto'):
            # auto: parse <think> tags if model produces them, but don't force
            # instant: no thinking at all
            deep_thinking = False
        
        # Extract images for vision models (base64 data URLs from frontend)
        images = data.get('images', [])
        if images and not isinstance(images, list):
            images = []
        # Validate and cap images (max 5 images, each max ~10MB base64)
        MAX_IMAGES = 5
        MAX_IMAGE_LEN = 15 * 1024 * 1024  # ~10MB raw ≈ 14MB base64
        validated_images = []
        for img in (images or [])[:MAX_IMAGES]:
            if isinstance(img, str) and img.startswith('data:image/') and len(img) <= MAX_IMAGE_LEN:
                validated_images.append(img)
        images = validated_images if validated_images else None
        
        if images:
            logger.info(f"[STREAM] {len(images)} image(s) attached for vision")
        
        if not message:
            return Response(
                StreamEvent(event="error", data=json.dumps({"error": "Empty message"})).format(),
                mimetype='text/event-stream',
                status=400
            )
        
        # Ensure session
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        # MCP Integration
        if MCP_AVAILABLE:
            try:
                mcp_client = get_mcp_client()
                if mcp_client and mcp_client.enabled:
                    message = inject_code_context(message, mcp_client, mcp_selected_files)
            except Exception as e:
                logger.warning(f"[MCP] Error injecting context: {e}")
        
        session_id = session.get('session_id')
        chatbot = get_chatbot(session_id)
        
        # Load memories
        memories = []
        if memory_ids:
            for mem_id in memory_ids:
                memory_file = MEMORY_DIR / f"{mem_id}.json"
                if memory_file.exists():
                    try:
                        with open(memory_file, 'r', encoding='utf-8') as f:
                            memories.append(json.load(f))
                    except Exception as e:
                        logger.error(f"Error loading memory {mem_id}: {e}")
        
        # ── Tool execution (auto web search) ──────────────────────────
        tools = data.get('tools', [])
        if isinstance(tools, str):
            try:
                tools = json.loads(tools)
            except Exception:
                tools = []
        _search_performed = False

        if _needs_web_search(data.get('message', message), tools):
            try:
                search_results = _run_web_search(data.get('message', message))
                if search_results:
                    _search_performed = True
                    message = (
                        f"{message}\n\n"
                        f"---\n"
                        f"📋 DỮ LIỆU THỰC TẾ TỪ WEB (sử dụng thông tin này để trả lời chính xác):\n"
                        f"{search_results}\n"
                        f"---\n"
                        f"Hãy trả lời dựa trên dữ liệu web ở trên. Nếu dữ liệu có ngày/giờ cụ thể, hãy trích dẫn."
                    )
                    logger.info(f"[Stream] Auto web search triggered for: {data.get('message', '')[:60]}")
            except Exception as e:
                logger.warning(f"[Stream] Web search failed: {e}")

        # ── SauceNAO reverse image search ──
        if 'saucenao' in tools:
            import re as _re
            _img_urls = _re.findall(r'https?://\S+\.(?:jpg|jpeg|png|gif|webp)\S*', data.get('message', ''), _re.IGNORECASE)
            try:
                from core.tools import saucenao_search_tool
                if _img_urls:
                    _sauce = saucenao_search_tool(image_url=_img_urls[0])
                elif images:
                    import base64 as _b64
                    _first = images[0]
                    if ',' in _first:
                        _first = _first.split(',', 1)[1]
                    _sauce = saucenao_search_tool(image_data=_b64.b64decode(_first))
                else:
                    _sauce = ""
                if _sauce:
                    message = f"{message}\n\n---\n{_sauce}\n---\nHãy tổng hợp kết quả tìm kiếm ảnh ở trên để trả lời."
                    logger.info("[Stream] SauceNAO search completed")
            except Exception as e:
                logger.warning(f"[Stream] SauceNAO failed: {e}")

        # ── SerpAPI — Google Lens / Reverse Image ──
        if 'serpapi-reverse-image' in tools:
            import re as _re
            _img_urls = _re.findall(r'https?://\S+\.(?:jpg|jpeg|png|gif|webp)\S*', data.get('message', ''), _re.IGNORECASE)
            try:
                from core.tools import serpapi_reverse_image
                if _img_urls:
                    _lens_result = serpapi_reverse_image(_img_urls[0])
                elif images:
                    _lens_result = "❌ Google Lens cần URL ảnh (http/https). Vui lòng paste URL ảnh vào tin nhắn."
                else:
                    _lens_result = ""
                if _lens_result:
                    message = f"{message}\n\n---\n{_lens_result}\n---\nHãy phân tích và tổng hợp kết quả tìm kiếm ảnh trên."
                    logger.info("[Stream] Google Lens search completed")
            except Exception as e:
                logger.warning(f"[Stream] SerpAPI reverse image failed: {e}")

        # ── SerpAPI — Bing Search ──
        if 'serpapi-bing' in tools:
            try:
                _bing_results = _run_web_search(data.get('message', message), engine='bing')
                if _bing_results:
                    _search_performed = True
                    message = (
                        f"{message}\n\n---\n"
                        f"📋 KẾT QUẢ BING SEARCH:\n{_bing_results}\n---\n"
                        f"Hãy trả lời dựa trên dữ liệu Bing ở trên."
                    )
                    logger.info("[Stream] Bing search completed")
            except Exception as e:
                logger.warning(f"[Stream] Bing search failed: {e}")

        # ── SerpAPI — Baidu Search ──
        if 'serpapi-baidu' in tools:
            try:
                _baidu_results = _run_web_search(data.get('message', message), engine='baidu')
                if _baidu_results:
                    _search_performed = True
                    message = (
                        f"{message}\n\n---\n"
                        f"📋 KẾT QUẢ BAIDU SEARCH:\n{_baidu_results}\n---\n"
                        f"Hãy trả lời dựa trên dữ liệu Baidu ở trên."
                    )
                    logger.info("[Stream] Baidu search completed")
            except Exception as e:
                logger.warning(f"[Stream] Baidu search failed: {e}")

        # ── SerpAPI — Image Search ──
        if 'serpapi-images' in tools:
            try:
                from core.tools import serpapi_image_search
                _img_search_result = serpapi_image_search(data.get('message', message))
                if _img_search_result:
                    message = (
                        f"{message}\n\n---\n"
                        f"📋 KẾT QUẢ IMAGE SEARCH:\n{_img_search_result}\n---\n"
                        f"Hãy liệt kê và mô tả các ảnh tìm được."
                    )
                    logger.info("[Stream] SerpAPI image search completed")
            except Exception as e:
                logger.warning(f"[Stream] SerpAPI image search failed: {e}")

        # Create streaming generator
        def generate_stream():
            try:
                thinking_start = time.time()
                
                # Send metadata
                yield StreamEvent(
                    event="metadata",
                    data=json.dumps({
                        "model": model,
                        "context": context,
                        "deep_thinking": deep_thinking,
                        "thinking_mode": thinking_mode,
                        "web_search": _search_performed,
                        "streaming": True,
                        "timestamp": datetime.now().isoformat()
                    })
                ).format()
                
                # ── Thinking Phase ──
                # Real AI reasoning via <think> tags or native reasoning_content
                category = detect_category(message)
                thinking_steps_text = []
                thinking_summary = ""
                thinking_duration = 0
                thinking_started = False
                thinking_ended = False

                # For instant mode, skip thinking entirely
                use_thinking = thinking_mode != 'instant'
                is_multi_thinking = thinking_mode == 'multi-thinking'
                
                # ── Response Phase (with integrated thinking) ──
                full_response = ""
                chunk_count = 0
                has_model_reasoning = False

                # ── 4-Agents Coordinated Reasoning ──
                if is_multi_thinking:
                    yield StreamEvent(
                        event="thinking_start",
                        data=json.dumps({
                            "mode": "multi-thinking",
                            "label": "4-Agents Reasoning",
                            "category": category,
                            "timestamp": datetime.now().isoformat()
                        })
                    ).format()

                    try:
                        from app.services.reasoning_service import get_reasoning_service
                        from app.services.ai_service import AIService
                        reasoning_svc = get_reasoning_service(ai_service=AIService())

                        result = reasoning_svc.coordinate_reasoning_sync(
                            message=message,
                            context=context,
                            max_rounds=3,
                        )

                        # Stream thinking process as steps
                        if result.thinking_process:
                            for i, part in enumerate(result.thinking_process.split("\n\n")):
                                part = part.strip()
                                if part:
                                    thinking_steps_text.append(part)
                                    yield StreamEvent(
                                        event="thinking",
                                        data=json.dumps({
                                            "step": part,
                                            "step_index": i,
                                            "is_reasoning_chunk": True,
                                        })
                                    ).format()

                        thinking_duration = round(result.reasoning_time * 1000)
                        yield StreamEvent(
                            event="thinking_end",
                            data=json.dumps({
                                "summary": f"{result.total_rounds} rounds · {result.total_trajectories} trajectories · {result.reasoning_time:.1f}s",
                                "duration_ms": thinking_duration,
                                "rounds": result.total_rounds,
                                "trajectories": result.total_trajectories,
                                "steps": thinking_steps_text,
                                "category": category,
                            })
                        ).format()

                        full_response = result.final_answer
                        _est_tokens = result.total_tokens or max(1, int(len(full_response) * 0.75))

                        # Stream the final answer in chunks for progressive rendering
                        chunk_size = 80
                        for i in range(0, len(full_response), chunk_size):
                            text = full_response[i:i + chunk_size]
                            chunk_count += 1
                            yield StreamEvent(
                                event="chunk",
                                data=json.dumps({"content": text, "chunk_index": chunk_count})
                            ).format()

                    except Exception as e:
                        logger.error(f"[4-Agents] Coordinated reasoning failed, fallback: {e}")
                        yield StreamEvent(
                            event="thinking_end",
                            data=json.dumps({
                                "summary": "Fallback to standard",
                                "duration_ms": 0,
                                "steps": [],
                                "category": category,
                            })
                        ).format()
                        # Fallback to standard deep-thinking stream below
                        is_multi_thinking = False

                if not is_multi_thinking:
                    # ── Standard streaming (instant or thinking) ──
                    think_parser = ThinkTagParser() if use_thinking else None

                    # Get streaming response from chatbot
                    for chunk in chatbot.chat_stream(
                        message=message,
                        model=model,
                        context=context,
                        deep_thinking=deep_thinking,
                        history=history,
                        memories=memories if memories else None,
                        language=language,
                        custom_prompt=custom_prompt,
                        images=images
                    ):
                        if not chunk:
                            continue
                        
                        # Handle native reasoning_content (DeepSeek R1, etc.)
                        if chunk.startswith(REASONING_PREFIX):
                            reasoning_text = chunk[len(REASONING_PREFIX):]
                            if reasoning_text and use_thinking:
                                if not thinking_started:
                                    thinking_started = True
                                    has_model_reasoning = True
                                    yield StreamEvent(
                                        event="thinking_start",
                                        data=json.dumps({
                                            "category": category,
                                            "timestamp": datetime.now().isoformat()
                                        })
                                    ).format()
                                thinking_steps_text.append(reasoning_text)
                                yield StreamEvent(
                                    event="thinking",
                                    data=json.dumps({
                                        "step": reasoning_text,
                                        "category": "model_reasoning",
                                        "is_reasoning_chunk": True,
                                    })
                                ).format()
                            continue
                        
                        # Parse <think> tags from model output
                        if think_parser:
                            segments = think_parser.feed(chunk)
                            for is_thinking, text in segments:
                                if is_thinking:
                                    # This is reasoning content inside <think>
                                    if not thinking_started:
                                        thinking_started = True
                                        yield StreamEvent(
                                            event="thinking_start",
                                            data=json.dumps({
                                                "category": category,
                                                "timestamp": datetime.now().isoformat()
                                            })
                                        ).format()
                                    thinking_steps_text.append(text)
                                    yield StreamEvent(
                                        event="thinking",
                                        data=json.dumps({
                                            "step": text,
                                            "category": category,
                                            "is_reasoning_chunk": True,
                                        })
                                    ).format()
                                else:
                                    # Regular response content — end thinking if active
                                    if thinking_started and not thinking_ended:
                                        thinking_ended = True
                                        thinking_duration = round((time.time() - thinking_start) * 1000)
                                        thinking_summary = generate_thinking_summary(message, category, language)
                                        yield StreamEvent(
                                            event="thinking_end",
                                            data=json.dumps({
                                                "summary": thinking_summary,
                                                "steps": thinking_steps_text,
                                                "category": category,
                                                "duration_ms": thinking_duration,
                                            })
                                        ).format()
                                    
                                    full_response += text
                                    chunk_count += 1
                                    yield StreamEvent(
                                        event="chunk",
                                        data=json.dumps({
                                            "content": text,
                                            "chunk_index": chunk_count
                                        })
                                    ).format()
                        else:
                            # No thinking parser (instant mode) — pass through
                            full_response += chunk
                            chunk_count += 1
                            yield StreamEvent(
                                event="chunk",
                                data=json.dumps({
                                    "content": chunk,
                                    "chunk_index": chunk_count
                                })
                            ).format()
                    
                    # Flush remaining buffer from think parser
                    if think_parser:
                        for is_thinking, text in think_parser.flush():
                            if is_thinking:
                                thinking_steps_text.append(text)
                                yield StreamEvent(
                                    event="thinking",
                                    data=json.dumps({
                                        "step": text,
                                        "category": category,
                                        "is_reasoning_chunk": True,
                                    })
                                ).format()
                            else:
                                full_response += text
                                chunk_count += 1
                                yield StreamEvent(
                                    event="chunk",
                                    data=json.dumps({
                                        "content": text,
                                        "chunk_index": chunk_count
                                    })
                                ).format()
                    
                    # Close thinking if still open (model didn't close </think>)
                    if thinking_started and not thinking_ended:
                        thinking_duration = round((time.time() - thinking_start) * 1000)
                        thinking_summary = generate_thinking_summary(message, category, language)
                        yield StreamEvent(
                            event="thinking_end",
                            data=json.dumps({
                                "summary": thinking_summary,
                                "steps": thinking_steps_text,
                                "category": category,
                                "duration_ms": thinking_duration,
                            })
                        ).format()
                
                # Send complete event
                yield StreamEvent(
                    event="complete",
                    data=json.dumps({
                        "response": full_response,
                        "model": model,
                        "context": context,
                        "deep_thinking": deep_thinking,
                        "total_chunks": chunk_count,
                        "thinking_summary": thinking_summary,
                        "thinking_steps": thinking_steps_text,
                        "thinking_duration_ms": thinking_duration,
                        "timestamp": datetime.now().isoformat()
                    })
                ).format()
                
            except GeneratorExit:
                logger.info("[SSE] Client disconnected")
            except Exception as e:
                logger.error(f"[SSE] Streaming error: {e}")
                yield StreamEvent(
                    event="error",
                    data=json.dumps({"error": str(e)})
                ).format()
        
        return Response(
            generate_stream(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',
                'Access-Control-Allow-Origin': '*',
            }
        )
        
    except Exception as e:
        logger.error(f"[Stream] Error: {e}")
        return Response(
            StreamEvent(event="error", data=json.dumps({"error": str(e)})).format(),
            mimetype='text/event-stream',
            status=500
        )


@stream_bp.route('/chat/stream/models', methods=['GET'])
def list_streaming_models():
    """List models that support streaming"""
    from core.chatbot_v2 import get_model_registry
    
    registry = get_model_registry()
    models = []
    
    for name in registry.list_available():
        config = registry.get_config(name)
        if config:
            models.append({
                'name': name,
                'supports_streaming': config.supports_streaming,
                'provider': config.provider.value
            })
    
    return {
        'models': models,
        'streaming_supported': [m['name'] for m in models if m['supports_streaming']]
    }
