"""Unit tests for DuckDB OLAP connection manager and queries."""

from backend.app.db.duckdb_client import DuckDBManager


def test_duckdb_manager_singleton():
    m1 = DuckDBManager.get_instance()
    m2 = DuckDBManager.get_instance()
    assert m1 is m2


def test_duckdb_health():
    manager = DuckDBManager.get_instance()
    health = manager.health_check()
    assert health["status"] == "healthy"
    assert health["orders_count"] == 99441
    assert health["latency_ms"] >= 0


def test_duckdb_analytical_aggregation():
    manager = DuckDBManager.get_instance()
    sql = """
    SELECT 
        order_status,
        COUNT(*) AS total_orders
    FROM orders
    GROUP BY order_status
    ORDER BY total_orders DESC;
    """
    res = manager.execute_query(sql)
    assert res["row_count"] > 0
    assert "order_status" in res["columns"]
    assert "total_orders" in res["columns"]
    # Check that 'delivered' is the top status
    assert res["rows"][0]["order_status"] == "delivered"
