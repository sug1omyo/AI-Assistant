"""
Streaming routes: /chat/stream - SSE endpoint for real-time chat responses

Supports live thinking display (like ChatGPT) with real-time reasoning steps
streamed before the actual response.
"""
import json
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
                
                # ── Response Phase (with integrated thinking) ──
                full_response = ""
                chunk_count = 0
                has_model_reasoning = False
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
                        if reasoning_text:
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
