"""Executive BI Storyteller Agent Node.

Synthesizes executive business takeaways and constructs typed Recharts JSON specifications.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from backend.app.agent.llm_factory import LLMFactory
from backend.app.agent.prompts import STORYTELLER_SYSTEM_PROMPT
from backend.app.agent.state import AgentState, ChartSpec

logger = logging.getLogger(__name__)


def build_fallback_chart_spec(
    user_query: str,
    columns: List[str],
    rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Dynamically infer an appropriate Recharts chart specification from column names and types."""
    if not rows or not columns:
        return {
            "chart_type": "metric_card",
            "title": "Query Result",
            "x_axis_key": "",
            "y_axis_keys": [],
            "data": [],
            "summary": "No data returned for this query.",
        }

    # If single row / KPI
    if len(rows) == 1:
        metric_col = columns[-1]
        return {
            "chart_type": "metric_card",
            "title": f"Summary: {metric_col.replace('_', ' ').title()}",
            "x_axis_key": columns[0],
            "y_axis_keys": [metric_col],
            "data": rows,
            "summary": f"Calculated value: {rows[0].get(metric_col)}",
        }

    # Determine X-axis and Y-axis keys
    x_key = columns[0]
    numeric_keys = [
        col for col in columns[1:]
        if any(isinstance(rows[0].get(col), (int, float)) for _ in [0])
    ]
    if not numeric_keys:
        numeric_keys = [columns[-1]]

    # Choose chart type based on dimension
    lower_x = x_key.lower()
    if any(k in lower_x for k in ["date", "month", "year", "time", "day"]):
        chart_type = "line"
    elif "share" in user_query.lower() or "distribution" in user_query.lower() or "type" in lower_x:
        chart_type = "pie"
    else:
        chart_type = "bar"

    return {
        "chart_type": chart_type,
        "title": user_query[:60].title(),
        "x_axis_key": x_key,
        "y_axis_keys": numeric_keys,
        "data": rows[:25],
        "summary": f"Visual breakdown across {len(rows)} data points.",
    }


def storyteller_node(state: AgentState) -> Dict[str, Any]:
    """Execute Storyteller: produce executive insight summary and Recharts config."""
    user_query = state.get("user_query", "")
    query_result = state.get("query_result")
    execution_error = state.get("execution_error")
    validation_error = state.get("validation_error")

    # 1. Handle persistent failure after max retries
    if execution_error or validation_error or not query_result:
        err = execution_error or validation_error or "Unknown query failure"
        logger.warning(f"[Storyteller] Formulating error recovery narrative for: {err}")
        explanation = (
            "### ⚠️ Query Could Not Be Completed\n"
            f"The autonomous agent was unable to execute this query after multiple reflection cycles.\n\n"
            f"**Error Encountered:**\n`{err}`\n\n"
            "**Suggested Adjustments:**\n"
            "- Check that the requested metrics exist in the Olist schema (e.g. orders, products, sellers, customers).\n"
            "- Clarify date parameters or state/category names."
        )
        return {
            "insights": explanation,
            "chart_spec": None,
            "is_terminal_error": True,
            "current_step": "storyteller",
            "status_message": "Analysis concluded with error recovery explanation.",
        }

    # 2. Query succeeded: formulate narrative and chart spec
    rows = query_result.get("rows", [])
    columns = query_result.get("columns", [])
    sql = state.get("generated_sql", "")

    logger.info(f"[Storyteller] Formulating insights for {len(rows)} records...")

    sample_rows = rows[:12]
    context_str = (
        f"USER QUESTION: {user_query}\n"
        f"EXECUTED SQL: {sql}\n"
        f"COLUMNS: {columns}\n"
        f"SAMPLE DATA ({len(sample_rows)} rows):\n"
        f"{json.dumps(sample_rows, default=str, indent=2)}"
    )

    llm = LLMFactory.get_chat_model()
    messages = [
        SystemMessage(content=STORYTELLER_SYSTEM_PROMPT),
        HumanMessage(content=context_str),
    ]

    try:
        response = llm.invoke(messages)
        content = response.content if isinstance(response.content, str) else str(response.content)
        clean_json = content.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json.removeprefix("```json").removesuffix("```").strip()
        elif clean_json.startswith("```"):
            clean_json = clean_json.removeprefix("```").removesuffix("```").strip()

        parsed = json.loads(clean_json)
        insights = parsed.get("insights", "### Key Findings\n- Query executed successfully.")
        raw_chart = parsed.get("chart_spec", {})
        raw_chart["data"] = rows[:30]  # bind actual dataset rows
        chart_spec = raw_chart
    except Exception as exc:
        logger.info(f"[Storyteller] LLM parsing fallback ({exc}). Utilizing rule-based spec.")
        insights = (
            "### Executive Summary\n"
            f"- Analytical query returned **{len(rows)} records** across `{', '.join(columns)}`.\n"
            f"- Columnar processing completed in **{query_result.get('execution_time_ms', 0)} ms** via DuckDB.\n"
            "- Distribution visualized in the interactive chart below."
        )
        chart_spec = build_fallback_chart_spec(user_query, columns, rows)

    return {
        "insights": insights,
        "chart_spec": chart_spec,
        "is_terminal_error": False,
        "current_step": "storyteller",
        "status_message": "📊 Generated business insights and interactive chart specification.",
    }
