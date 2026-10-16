"""Query Execution Node.

Executes sanitized SQL against the in-memory DuckDB OLAP engine attached to PostgreSQL.
Captures runtime errors for the self-healing loop.
"""

import logging
from typing import Any, Dict
from backend.app.agent.state import AgentState
from backend.app.db.duckdb_client import get_duckdb_manager

logger = logging.getLogger(__name__)


def executor_node(state: AgentState) -> Dict[str, Any]:
    """Execute SQL against DuckDB and record query results or execution traceback."""
    sql = state.get("generated_sql", "")
    reflection_history = list(state.get("reflection_history", []))
    reflection_count = state.get("reflection_count", 0)

    logger.info(f"[Executor] Executing SQL against DuckDB:\n{sql}")
    db = get_duckdb_manager()

    try:
        result = db.execute_query(sql=sql, validate=False)
        return {
            "query_result": result,
            "execution_error": None,
            "current_step": "executor",
            "status_message": (
                f"⚡ Executed in {result['execution_time_ms']}ms. Returned {result['row_count']} rows."
            ),
        }
    except Exception as exc:
        error_msg = f"DuckDB Execution Error: {str(exc)}"
        logger.warning(f"[Executor] {error_msg}")
        reflection_history.append(error_msg)
        return {
            "query_result": None,
            "execution_error": error_msg,
            "reflection_count": reflection_count + 1,
            "reflection_history": reflection_history,
            "current_step": "executor",
            "status_message": f"⚠️ Query execution failed: {str(exc)[:100]}...",
        }
