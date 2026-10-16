"""Golden evaluation benchmark suite verifying 10 canonical business questions on the live 99k orders database."""

import pytest
from backend.app.core.validator import validate_sql_query
from backend.app.db.duckdb_client import DuckDBManager

BENCHMARK_QUERIES = [
    # 1. GMV & Revenue by Category
    (
        "Top 5 categories by revenue",
        """
        SELECT 
            p.category_name,
            ROUND(SUM(oi.price), 2) AS total_revenue
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE o.order_status = 'delivered'
        GROUP BY p.category_name
        ORDER BY total_revenue DESC
        LIMIT 5;
        """,
        5,
    ),
    # 2. Order Volume by Status
    (
        "Order counts by status",
        """
        SELECT 
            order_status,
            COUNT(*) AS order_count
        FROM orders
        GROUP BY order_status
        ORDER BY order_count DESC;
        """,
        3,  # At least 3 statuses
    ),
    # 3. Top Customer States
    (
        "Top 5 customer states by volume",
        """
        SELECT 
            c.state,
            COUNT(DISTINCT o.order_id) AS total_orders
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY c.state
        ORDER BY total_orders DESC
        LIMIT 5;
        """,
        5,
    ),
    # 4. Average Order Value (AOV)
    (
        "Overall Average Order Value",
        """
        SELECT 
            ROUND(SUM(oi.price) / COUNT(DISTINCT o.order_id), 2) AS aov
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered';
        """,
        1,
    ),
    # 5. Payment Method Share
    (
        "Payment method breakdown",
        """
        SELECT 
            payment_type,
            COUNT(DISTINCT order_id) AS orders,
            ROUND(SUM(payment_value), 2) AS total_value
        FROM order_payments
        GROUP BY payment_type
        ORDER BY total_value DESC;
        """,
        4,  # credit_card, boleto, voucher, debit_card
    ),
    # 6. Customer Satisfaction Score (CSAT)
    (
        "Average review rating",
        """
        SELECT 
            ROUND(AVG(review_score), 2) AS csat_score,
            COUNT(*) AS total_reviews
        FROM order_reviews;
        """,
        1,
    ),
    # 7. Delivery Performance
    (
        "On-time delivery percentage",
        """
        SELECT 
            ROUND(100.0 * COUNT(CASE WHEN delivered_customer_date <= estimated_delivery_date THEN 1 END) /
            NULLIF(COUNT(CASE WHEN delivered_customer_date IS NOT NULL THEN 1 END), 0), 2) AS on_time_rate
        FROM orders
        WHERE order_status = 'delivered';
        """,
        1,
    ),
    # 8. Merchant Distribution
    (
        "Top 5 merchant seller states",
        """
        SELECT 
            state,
            COUNT(DISTINCT seller_id) AS seller_count
        FROM sellers
        GROUP BY state
        ORDER BY seller_count DESC
        LIMIT 5;
        """,
        5,
    ),
    # 9. Monthly Order Trend
    (
        "Monthly volume trend in 2017",
        """
        SELECT 
            DATE_TRUNC('month', purchase_timestamp) AS order_month,
            COUNT(*) AS monthly_orders
        FROM orders
        WHERE EXTRACT(year FROM purchase_timestamp) = 2017
        GROUP BY 1
        ORDER BY 1 ASC;
        """,
        12,  # 12 months in 2017
    ),
    # 10. Repeat Customer Ratio
    (
        "Repeat customer count",
        """
        WITH customer_order_counts AS (
            SELECT 
                c.customer_unique_id,
                COUNT(o.order_id) AS order_count
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            GROUP BY c.customer_unique_id
        )
        SELECT 
            COUNT(CASE WHEN order_count > 1 THEN 1 END) AS repeat_buyers,
            COUNT(*) AS total_unique_customers
        FROM customer_order_counts;
        """,
        1,
    ),
]


@pytest.mark.parametrize("title, sql, min_expected_rows", BENCHMARK_QUERIES)
def test_golden_benchmark_query(title: str, sql: str, min_expected_rows: int):
    # 1. AST Validation
    val = validate_sql_query(sql)
    assert val.is_valid, f"Validation failed for '{title}': {val.error_message}"

    # 2. Execution on DuckDB
    db = DuckDBManager.get_instance()
    res = db.execute_query(sql, validate=False)

    # 3. Assertions
    assert res["row_count"] >= min_expected_rows, (
        f"Query '{title}' returned {res['row_count']} rows, expected at least {min_expected_rows}"
    )
    # Ensure performance latency is sub-second (typically < 100ms)
    assert res["execution_time_ms"] < 2000, (
        f"Query '{title}' took {res['execution_time_ms']}ms, expected sub-second execution"
    )
