"""
Tests for Hermes Agent integration — adapter + Flask route.

All tests use mocks. No real HTTP calls to Hermes sidecar.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

# Ensure chatbot root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def _enable_hermes(monkeypatch):
    """Enable Hermes feature flag."""
    monkeypatch.setattr("core.hermes_adapter.HERMES_ENABLED", True)
    monkeypatch.setattr("core.hermes_adapter.HERMES_API_URL", "http://fake-hermes:8080")
    monkeypatch.setattr("core.hermes_adapter.HERMES_API_KEY", "test-key")
    monkeypatch.setattr("core.hermes_adapter.HERMES_TIMEOUT", 30)


@pytest.fixture
def mock_hermes_success(monkeypatch):
    """Mock requests.post to return a successful Hermes response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": "Hermes says hello!"}
    mock_resp.text = '{"response": "Hermes says hello!"}'
    monkeypatch.setattr("core.hermes_adapter.requests.post", lambda *a, **kw: mock_resp)
    return mock_resp


# ---------------------------------------------------------------------------
# Adapter tests
# ---------------------------------------------------------------------------

class TestHermesChat:
    """Tests for core.hermes_adapter.hermes_chat."""

    def test_disabled_returns_error(self, monkeypatch):
        monkeypatch.setattr("core.hermes_adapter.HERMES_ENABLED", False)
        from core.hermes_adapter import hermes_chat
        result = hermes_chat("hello")
        assert result["success"] is False
        assert "HERMES_ENABLED" in result["error"]

    def test_empty_message_returns_error(self, _enable_hermes):
        from core.hermes_adapter import hermes_chat
        result = hermes_chat("")
        assert result["success"] is False
        assert "message" in result["error"].lower()

    def test_message_too_long(self, _enable_hermes):
        from core.hermes_adapter import hermes_chat
        result = hermes_chat("x" * 11_000)
        assert result["success"] is False
        assert "dài" in result["error"]

    def test_successful_chat(self, _enable_hermes, mock_hermes_success):
        from core.hermes_adapter import hermes_chat
        result = hermes_chat("hello world")
        assert result["success"] is True
        assert "Hermes says hello" in result["result"]
        assert result["elapsed_s"] >= 0

    def test_connection_error(self, _enable_hermes, monkeypatch):
        def raise_conn(*a, **kw):
            raise requests.ConnectionError("refused")
        monkeypatch.setattr("core.hermes_adapter.requests.post", raise_conn)
        from core.hermes_adapter import hermes_chat
        result = hermes_chat("hello")
        assert result["success"] is False
        assert "kết nối" in result["error"]

    def test_timeout_error(self, _enable_hermes, monkeypatch):
        def raise_timeout(*a, **kw):
            raise requests.Timeout("timed out")
        monkeypatch.setattr("core.hermes_adapter.requests.post", raise_timeout)
        from core.hermes_adapter import hermes_chat
        result = hermes_chat("hello")
        assert result["success"] is False
        assert "timeout" in result["error"].lower()

    def test_non_200_response(self, _enable_hermes, monkeypatch):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        monkeypatch.setattr("core.hermes_adapter.requests.post", lambda *a, **kw: mock_resp)
        from core.hermes_adapter import hermes_chat
        result = hermes_chat("hello")
        assert result["success"] is False
        assert "500" in result["error"]

    def test_non_json_response(self, _enable_hermes, monkeypatch):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("not json")
        mock_resp.text = "plain text response"
        monkeypatch.setattr("core.hermes_adapter.requests.post", lambda *a, **kw: mock_resp)
        from core.hermes_adapter import hermes_chat
        result = hermes_chat("hello")
        assert result["success"] is True
        assert "plain text response" in result["result"]

    def test_auth_header_sent(self, _enable_hermes, monkeypatch):
        """Verify Authorization header is included when API key is set."""
        captured = {}
        def capture_post(url, json=None, headers=None, timeout=None):
            captured['headers'] = headers
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"response": "ok"}
            return mock_resp
        monkeypatch.setattr("core.hermes_adapter.requests.post", capture_post)
        from core.hermes_adapter import hermes_chat
        hermes_chat("test")
        assert "Authorization" in captured["headers"]
        assert "Bearer test-key" == captured["headers"]["Authorization"]

    def test_conversation_history_forwarded(self, _enable_hermes, monkeypatch):
        captured = {}
        def capture_post(url, json=None, headers=None, timeout=None):
            captured['payload'] = json
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"response": "ok"}
            return mock_resp
        monkeypatch.setattr("core.hermes_adapter.requests.post", capture_post)
        from core.hermes_adapter import hermes_chat
        history = [{"role": "user", "content": "hi"}]
        hermes_chat("follow up", conversation_history=history)
        assert captured['payload']['conversation_history'] == history


# ---------------------------------------------------------------------------
# Flask route tests
# ---------------------------------------------------------------------------

class TestHermesRoute:
    """Tests for routes/hermes.py Flask blueprint."""

    @pytest.fixture
    def client(self):
        from flask import Flask
        app = Flask(__name__)
        app.config['TESTING'] = True
        from routes.hermes import hermes_bp
        app.register_blueprint(hermes_bp)
        return app.test_client()

    def test_missing_message_returns_400(self, client):
        resp = client.post(
            '/api/hermes/chat',
            json={},
            content_type='application/json',
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['success'] is False

    def test_successful_request(self, client, monkeypatch):
        monkeypatch.setattr(
            "core.hermes_adapter.hermes_chat",
            lambda msg, **kw: {"success": True, "result": "answer", "error": None, "elapsed_s": 1.0},
        )
        resp = client.post(
            '/api/hermes/chat',
            json={'message': 'hello'},
            content_type='application/json',
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['result'] == 'answer'

    def test_adapter_error_returns_422(self, client, monkeypatch):
        monkeypatch.setattr(
            "core.hermes_adapter.hermes_chat",
            lambda msg, **kw: {
                "success": False, "result": "", "error": "sidecar down", "elapsed_s": 0,
            },
        )
        resp = client.post(
            '/api/hermes/chat',
            json={'message': 'test'},
            content_type='application/json',
        )
        assert resp.status_code == 422

    def test_internal_exception_returns_500(self, client, monkeypatch):
        def boom(*a, **kw):
            raise RuntimeError("unexpected")
        monkeypatch.setattr("core.hermes_adapter.hermes_chat", boom)
        resp = client.post(
            '/api/hermes/chat',
            json={'message': 'test'},
            content_type='application/json',
        )
        assert resp.status_code == 500
