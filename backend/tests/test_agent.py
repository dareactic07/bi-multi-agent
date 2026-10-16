"""Unit and integration tests for the LangGraph 4-Agent Pod and reflection loop."""

import pytest
from backend.app.agent.graph import bi_agent_app, route_after_critic, route_after_executor
from backend.app.agent.nodes.executor import executor_node
from backend.app.agent.nodes.orchestrator import orchestrator_node
from backend.app.agent.nodes.sql_critic import sql_critic_node
from backend.app.agent.nodes.sql_engineer import sql_engineer_node
from backend.app.agent.nodes.storyteller import storyteller_node
from backend.app.agent.state import AgentState


def test_orchestrator_node():
    state: AgentState = {
        "user_query": "What are our top 5 product categories by total sales revenue?",
    }
    result = orchestrator_node(state)
    assert "orders" in result["relevant_tables"]
    assert "order_items" in result["relevant_tables"]
    assert "products" in result["relevant_tables"]
    assert len(result["pruned_schema_context"]) > 0
    assert result["current_step"] == "orchestrator"


def test_sql_engineer_node():
    state: AgentState = {
        "user_query": "Show me total orders by order status",
        "pruned_schema_context": "Table orders: columns order_id, order_status",
        "reflection_history": [],
        "reflection_count": 0,
    }
    result = sql_engineer_node(state)
    assert "generated_sql" in result
    assert "orders" in result["generated_sql"].lower()
    assert result["current_step"] == "sql_engineer"


def test_sql_critic_approves_valid():
    state: AgentState = {
        "user_query": "Show delivered orders",
        "generated_sql": "SELECT order_id, order_status FROM orders WHERE order_status = 'delivered' LIMIT 10;",
        "reflection_history": [],
    }
    result = sql_critic_node(state)
    assert result["validation_passed"] is True
    assert result["validation_error"] is None


def test_sql_critic_rejects_destructive():
    state: AgentState = {
        "user_query": "Delete all customers",
        "generated_sql": "DROP TABLE customers;",
        "reflection_history": [],
    }
    result = sql_critic_node(state)
    assert result["validation_passed"] is False
    assert "AST Security Check Failed" in result["validation_error"]
    assert len(result["reflection_history"]) == 1


def test_executor_node_success():
    state: AgentState = {
        "generated_sql": "SELECT order_status, COUNT(*) AS count FROM orders GROUP BY order_status LIMIT 3;",
        "reflection_history": [],
        "reflection_count": 0,
    }
    result = executor_node(state)
    assert result["execution_error"] is None
    assert result["query_result"] is not None
    assert result["query_result"]["row_count"] > 0
    assert "order_status" in result["query_result"]["columns"]


def test_executor_node_healing_trigger():
    state: AgentState = {
        "generated_sql": "SELECT non_existent_column FROM orders;",
        "reflection_history": [],
        "reflection_count": 0,
    }
    result = executor_node(state)
    assert result["execution_error"] is not None
    assert result["query_result"] is None
    assert result["reflection_count"] == 1
    assert len(result["reflection_history"]) == 1


def test_graph_conditional_routing():
    # Critic pass -> executor
    pass_state: AgentState = {"validation_passed": True}
    assert route_after_critic(pass_state) == "executor"

    # Critic fail under retry limit -> sql_engineer
    fail_retry_state: AgentState = {"validation_passed": False, "reflection_count": 1}
    assert route_after_critic(fail_retry_state) == "sql_engineer"

    # Critic fail at max retries -> storyteller
    fail_max_state: AgentState = {"validation_passed": False, "reflection_count": 3}
    assert route_after_critic(fail_max_state) == "storyteller"


def test_storyteller_node_success():
    state: AgentState = {
        "user_query": "Top 5 categories by revenue",
        "generated_sql": "SELECT category_name, SUM(price) FROM products GROUP BY 1;",
        "query_result": {
            "columns": ["category_name", "total_revenue"],
            "rows": [
                {"category_name": "bed_bath_table", "total_revenue": 1037490.0},
                {"category_name": "health_beauty", "total_revenue": 974550.0},
            ],
            "row_count": 2,
            "execution_time_ms": 5.2,
        },
    }
    result = storyteller_node(state)
    assert "insights" in result
    assert result["chart_spec"] is not None
    assert result["chart_spec"]["chart_type"] in ("bar", "line", "area", "pie", "metric_card")
    assert result["is_terminal_error"] is False


def test_full_agent_workflow_end_to_end():
    """Run full multi-agent state graph pipeline on the live 99k orders database."""
    initial_state: AgentState = {
        "user_query": "What are our top 5 product categories by revenue in 2017?",
        "reflection_count": 0,
        "reflection_history": [],
        "is_terminal_error": False,
    }
    final_state = bi_agent_app.invoke(initial_state)

    assert final_state["current_step"] == "storyteller"
    assert "generated_sql" in final_state
    assert final_state["validation_passed"] is True
    assert final_state["query_result"] is not None
    assert final_state["query_result"]["row_count"] > 0
    assert final_state["chart_spec"] is not None
    assert len(final_state["insights"]) > 0
    assert final_state["is_terminal_error"] is False


def test_self_healing_recovery_cycle():
    """Verify that a database runtime failure successfully triggers reflection and re-generation."""
    state: AgentState = {
        "user_query": "Count orders by status",
        "pruned_schema_context": "Table orders: columns order_id, order_status",
        "generated_sql": "SELECT invalid_col_name FROM orders;",
        "reflection_count": 0,
        "reflection_history": [],
    }

    # Step 1: Executor fails and logs error
    exec_res = executor_node(state)
    assert exec_res["execution_error"] is not None
    assert exec_res["reflection_count"] == 1
    assert len(exec_res["reflection_history"]) == 1

    # Step 2: Router routes back to sql_engineer
    state.update(exec_res)
    assert route_after_executor(state) == "sql_engineer"

    # Step 3: SQL engineer reflects on error and produces valid SQL
    engineer_res = sql_engineer_node(state)
    assert "generated_sql" in engineer_res
    state.update(engineer_res)

    # Step 4: Critic approves corrected SQL
    critic_res = sql_critic_node(state)
    assert critic_res["validation_passed"] is True

