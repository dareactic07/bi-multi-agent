"""Unit tests for sqlglot AST query validation and safety guardrails."""

import pytest
from backend.app.core.validator import validate_sql_query


def test_valid_select_query():
    sql = "SELECT order_id, order_status FROM orders WHERE order_status = 'delivered' LIMIT 10;"
    result = validate_sql_query(sql)
    assert result.is_valid is True
    assert result.error_message is None
    assert result.tables_referenced == ["orders"]
    assert "LIMIT 10" in result.sanitized_sql


def test_valid_multi_table_join():
    sql = """
    SELECT 
        p.category_name,
        SUM(oi.price) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE o.order_status = 'delivered'
    GROUP BY p.category_name
    ORDER BY revenue DESC
    LIMIT 5;
    """
    result = validate_sql_query(sql)
    assert result.is_valid is True
    assert sorted(result.tables_referenced) == ["order_items", "orders", "products"]


def test_valid_cte_query():
    sql = """
    WITH monthly_revenue AS (
        SELECT 
            DATE_TRUNC('month', o.purchase_timestamp) AS order_month,
            SUM(oi.price) AS total_rev
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        GROUP BY 1
    )
    SELECT order_month, total_rev FROM monthly_revenue ORDER BY order_month;
    """
    result = validate_sql_query(sql)
    assert result.is_valid is True
    assert sorted(result.tables_referenced) == ["order_items", "orders"]


def test_reject_drop_table():
    sql = "DROP TABLE orders;"
    result = validate_sql_query(sql)
    assert result.is_valid is False
    assert "Prohibited statement type" in result.error_message or "Destructive" in result.error_message


def test_reject_delete_statement():
    sql = "DELETE FROM customers WHERE customer_id = '123';"
    result = validate_sql_query(sql)
    assert result.is_valid is False
    assert "Prohibited statement type" in result.error_message or "Destructive" in result.error_message


def test_reject_update_statement():
    sql = "UPDATE orders SET order_status = 'canceled';"
    result = validate_sql_query(sql)
    assert result.is_valid is False


def test_reject_insert_statement():
    sql = "INSERT INTO customers (customer_id) VALUES ('fake');"
    result = validate_sql_query(sql)
    assert result.is_valid is False


def test_reject_multi_statement_injection():
    sql = "SELECT * FROM orders; DROP TABLE customers;"
    result = validate_sql_query(sql)
    assert result.is_valid is False
    assert "Multi-statement queries are strictly prohibited" in result.error_message


def test_reject_unauthorized_table():
    sql = "SELECT * FROM users_passwords_secret;"
    result = validate_sql_query(sql)
    assert result.is_valid is False
    assert "Unauthorized or unknown table" in result.error_message


def test_empty_query():
    result = validate_sql_query("   ")
    assert result.is_valid is False
    assert "Query cannot be empty" in result.error_message
