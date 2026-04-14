"""
Flask blueprint — Hermes Agent proxy route.

Provides:
  POST /api/hermes/chat — proxy to Hermes sidecar (JSON response)
"""
import logging

from flask import Blueprint, jsonify, request

hermes_bp = Blueprint('hermes', __name__)
logger = logging.getLogger(__name__)


@hermes_bp.route('/api/hermes/chat', methods=['POST'])
def hermes_chat_route():
    """Forward a chat request to the Hermes Agent sidecar."""
    data = request.get_json(silent=True) or {}

    message = (data.get('message') or '').strip()
    if not message:
        return jsonify({
            'success': False, 'result': '', 'error': 'Missing required field: message',
        }), 400

    conversation_history = data.get('conversation_history')
    if conversation_history is not None and not isinstance(conversation_history, list):
        conversation_history = None

    model = data.get('model') or None

    logger.info(
        "[HERMES-ROUTE] Request: msg_len=%d model=%s history_len=%d",
        len(message), model, len(conversation_history or []),
    )

    try:
        from core.hermes_adapter import hermes_chat
        result = hermes_chat(
            message,
            conversation_history=conversation_history,
            model=model,
        )
    except Exception as e:
        logger.error("[HERMES-ROUTE] Unhandled error: %s", e)
        return jsonify({
            'success': False, 'result': '',
            'error': f'Internal error: {e}',
        }), 500

    status_code = 200 if result.get('success') else 422
    return jsonify(result), status_code
