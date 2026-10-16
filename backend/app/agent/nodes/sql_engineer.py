"""SQL Engineer Agent Node.

Crafts optimized DuckDB analytical queries grounded in the pruned semantic layer.
Incorporates self-healing reflection context upon retries.
"""

import logging
import re
from typing import Any, Dict
from langchain_core.messages import HumanMessage, SystemMessage
from backend.app.agent.llm_factory import LLMFactory
from backend.app.agent.prompts import SQL_ENGINEER_SYSTEM_PROMPT
from backend.app.agent.state import AgentState

logger = logging.getLogger(__name__)


def extract_sql_from_response(raw_text: str) -> str:
    """Extract raw SQL statement from an LLM markdown response."""
    text = raw_text.strip()
    match = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip().rstrip(";") + ";"


def sql_engineer_node(state: AgentState) -> Dict[str, Any]:
    """Execute SQL Engineer: synthesize or correct analytical SQL query."""
    user_query = state.get("user_query", "")
    pruned_context = state.get("pruned_schema_context", "")
    reflection_history = state.get("reflection_history", [])
    reflection_count = state.get("reflection_count", 0)

    logger.info(f"[SQL Engineer] Attempt {reflection_count + 1} for query: {user_query}")

    reflection_context = ""
    if reflection_history:
        latest_error = reflection_history[-1]
        reflection_context = (
            f"\n### ⚠️ CRITICAL SELF-HEALING REFLECTION (Attempt {reflection_count + 1}):\n"
            f"Your previous query was rejected or failed with this database/validation error:\n"
            f"> {latest_error}\n\n"
            f"Carefully analyze this exact failure and provide a corrected, safe SQL query."
        )

    system_prompt = SQL_ENGINEER_SYSTEM_PROMPT.format(
        pruned_context=pruned_context,
        reflection_context=reflection_context,
    )

    llm = LLMFactory.get_chat_model()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Generate the optimal DuckDB SQL query for:\n{user_query}"),
    ]

    response = llm.invoke(messages)
    content = response.content if isinstance(response.content, str) else str(response.content)
    sql = extract_sql_from_response(content)

    return {
        "generated_sql": sql,
        "current_step": "sql_engineer",
        "status_message": f"📝 Synthesized candidate SQL (Attempt {reflection_count + 1}).",
    }
