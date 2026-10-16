"""Integration tests for FastAPI endpoints using TestClient."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Autonomous BI Multi-Agent System"
    assert data["docs_url"] == "/docs"


def test_semantic_layer():
    response = client.get("/api/v1/semantic-layer")
    assert response.status_code == 200
    data = response.json()
    assert "tables" in data
    assert "metrics" in data
    assert "relationships" in data
    assert "orders" in data["tables"]


def test_metrics():
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert "gmv" in metrics
    assert "aov" in metrics
    assert "csat" in metrics


def test_schema():
    response = client.get("/api/v1/schema")
    assert response.status_code == 200
    data = response.json()
    assert "tables" in data
    assert "relationships" in data


def test_validate_valid_sql():
    response = client.post(
        "/api/v1/validate",
        json={"query": "SELECT order_id, order_status FROM orders LIMIT 5;"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["tables_referenced"] == ["orders"]


def test_validate_destructive_sql():
    response = client.post(
        "/api/v1/validate",
        json={"query": "DELETE FROM customers;"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "database" in data


def test_execute_analytical_query():
    query = """
    SELECT 
        order_status,
        COUNT(*) AS count
    FROM orders
    GROUP BY order_status
    ORDER BY count DESC
    LIMIT 3;
    """
    response = client.post(
        "/api/v1/query",
        json={"query": query, "validate": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["row_count"] > 0
    assert "order_status" in data["columns"]
    assert "count" in data["columns"]
    assert data["execution_time_ms"] >= 0
