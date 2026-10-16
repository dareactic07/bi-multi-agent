"""Chief Orchestrator Agent Node.

Classifies analytical intent and prunes schema context down to only relevant tables and metrics.
"""

from functools import lru_cache
import json
import logging
from pathlib import Path
from typing import Any, Dict, List
import yaml
from langchain_core.messages import HumanMessage, SystemMessage
from backend.app.agent.llm_factory import LLMFactory
from backend.app.agent.prompts import ORCHESTRATOR_SYSTEM_PROMPT
from backend.app.agent.state import AgentState

logger = logging.getLogger(__name__)

SEMANTIC_LAYER_PATH = Path(__file__).resolve().parent.parent.parent / "core" / "semantic_layer.yaml"


@lru_cache
def get_semantic_layer_raw() -> Dict[str, Any]:
    with open(SEMANTIC_LAYER_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_pruned_context(
    relevant_tables: List[str],
    relevant_metrics: List[str],
    full_dict: Dict[str, Any],
) -> str:
    """Format a clean markdown text block of pruned table schemas and metric formulas."""
    sections: List[str] = []

    # Tables
    sections.append("### RELEVANT TABLES & COLUMNS:")
    all_tables = full_dict.get("tables", {})
    for tbl in relevant_tables:
        tbl_info = all_tables.get(tbl)
        if tbl_info:
            sections.append(f"\nTable '{tbl}': {tbl_info.get('description', '')}")
            sections.append(f"Primary Key: {tbl_info.get('primary_key', [])}")
            cols = tbl_info.get("columns", {})
            for col_name, col_desc in cols.items():
                sections.append(f"  - {col_name}: {col_desc}")

    # Relationships
    sections.append("\n### RELEVANT TABLE RELATIONSHIPS:")
    rel_list = full_dict.get("relationships", [])
    relevant_set = set(relevant_tables)
    for rel in rel_list:
        if rel.get("from_table") in relevant_set and rel.get("to_table") in relevant_set:
            sections.append(
                f"- {rel.get('from_table')}.{rel.get('from_column')} = "
                f"{rel.get('to_table')}.{rel.get('to_column')} ({rel.get('join_type')})"
            )

    # Metrics
    if relevant_metrics:
        sections.append("\n### METRIC DEFINITIONS & FORMULAS:")
        all_metrics = full_dict.get("metrics", {})
        for metric_key in relevant_metrics:
            m_info = all_metrics.get(metric_key)
            if m_info:
                sections.append(f"- **{m_info.get('name', metric_key)}**: `{m_info.get('sql_expression')}`")
                sections.append(f"  Description: {m_info.get('description')}")
                if m_info.get("default_filters"):
                    sections.append(f"  Default Filters: {', '.join(m_info.get('default_filters'))}")

    return "\n".join(sections)


def orchestrator_node(state: AgentState) -> Dict[str, Any]:
    """Execute Orchestrator: classify question and prune schema context."""
    user_query = state.get("user_query", "")
    logger.info(f"[Orchestrator] Processing query: {user_query}")

    semantic_dict = get_semantic_layer_raw()
    system_prompt = ORCHESTRATOR_SYSTEM_PROMPT.format(
        semantic_dictionary=yaml.dump(semantic_dict, sort_keys=False)
    )

    llm = LLMFactory.get_chat_model()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Analyze this business question:\n{user_query}"),
    ]

    try:
        response = llm.invoke(messages)
        content = response.content if isinstance(response.content, str) else str(response.content)
        # Extract json object if surrounded by markdown code blocks
        clean_json = content.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json.removeprefix("```json").removesuffix("```").strip()
        elif clean_json.startswith("```"):
            clean_json = clean_json.removeprefix("```").removesuffix("```").strip()

        parsed = json.loads(clean_json)
        relevant_tables = parsed.get("relevant_tables", ["orders"])
        relevant_metrics = parsed.get("relevant_metrics", [])
    except Exception as exc:
        logger.warning(f"[Orchestrator] Parsing failed: {exc}. Defaulting to core tables.")
        relevant_tables = ["orders", "order_items", "products", "customers"]
        relevant_metrics = ["gmv"]

    pruned_context = build_pruned_context(relevant_tables, relevant_metrics, semantic_dict)

    return {
        "relevant_tables": relevant_tables,
        "relevant_metrics": relevant_metrics,
        "pruned_schema_context": pruned_context,
        "current_step": "orchestrator",
        "status_message": f"🔍 Pruned schema to {len(relevant_tables)} relevant tables: {', '.join(relevant_tables)}.",
    }
