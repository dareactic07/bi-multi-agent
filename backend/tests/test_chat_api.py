"""Integration tests for Chat and SSE Streaming endpoints."""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_chat_endpoint_sync():
    payload = {
        "query": "What are the top 5 product categories by total sales revenue?",
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == payload["query"]
    assert data["generated_sql"] is not None
    assert "orders" in data["generated_sql"].lower()
    assert data["query_result"] is not None
    assert data["query_result"]["row_count"] > 0
    assert data["chart_spec"] is not None
    assert "insights" in data
    assert data["is_terminal_error"] is False


def test_chat_stream_endpoint():
    payload = {
        "query": "Show monthly order volume trend",
    }
    with client.stream("POST", "/api/v1/chat/stream", json=payload) as response:
        assert response.status_code == 200
        content = ""
        for chunk in response.iter_text():
            content += chunk

        assert "event: status" in content or "event: step" in content
        assert "event: final_result" in content
        assert "event: done" in content
