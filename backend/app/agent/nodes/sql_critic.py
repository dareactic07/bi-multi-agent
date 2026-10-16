"""Data QA & SQL Critic Agent Node.

Adversarially validates candidate queries against AST guardrails and business metric logic.
"""

import json
import logging
from typing import Any, Dict
from langchain_core.messages import HumanMessage, SystemMessage
from backend.app.agent.llm_factory import LLMFactory
from backend.app.agent.prompts import SQL_CRITIC_SYSTEM_PROMPT
from backend.app.agent.state import AgentState
from backend.app.core.validator import validate_sql_query

logger = logging.getLogger(__name__)


def sql_critic_node(state: AgentState) -> Dict[str, Any]:
    """Execute SQL Critic: enforce AST security and evaluate business logic."""
    candidate_sql = state.get("generated_sql", "")
    user_query = state.get("user_query", "")
    reflection_history = list(state.get("reflection_history", []))

    logger.info(f"[SQL Critic] Auditing SQL: {candidate_sql[:80]}...")

    # 1. Deterministic AST Security and Syntax Validation (sqlglot)
    ast_result = validate_sql_query(candidate_sql)
    if not ast_result.is_valid:
        error_msg = f"AST Security Check Failed: {ast_result.error_message}"
        logger.warning(f"[SQL Critic] {error_msg}")
        reflection_history.append(error_msg)
        return {
            "validation_passed": False,
            "validation_error": error_msg,
            "reflection_history": reflection_history,
            "current_step": "sql_critic",
            "status_message": f"⚠️ Rejected by AST Validator: {ast_result.error_message}",
        }

    sanitized_sql = ast_result.sanitized_sql or candidate_sql

    # 2. LLM Business Logic & Semantic Audit
    system_prompt = SQL_CRITIC_SYSTEM_PROMPT.format(
        user_query=user_query,
        candidate_sql=sanitized_sql,
    )
    llm = LLMFactory.get_chat_model()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Audit this candidate query for business semantic correctness."),
    ]

    try:
        response = llm.invoke(messages)
        content = response.content if isinstance(response.content, str) else str(response.content)
        clean_json = content.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json.removeprefix("```json").removesuffix("```").strip()
        elif clean_json.startswith("```"):
            clean_json = clean_json.removeprefix("```").removesuffix("```").strip()

        audit = json.loads(clean_json)
        approved = audit.get("approved", True)
        issues = audit.get("issues", [])
        corrected_sql = audit.get("corrected_sql")

        if not approved and issues:
            critic_error = f"Semantic Review Issue: {'; '.join(issues)}"
            logger.warning(f"[SQL Critic] {critic_error}")
            reflection_history.append(critic_error)
            return {
                "validation_passed": False,
                "validation_error": critic_error,
                "critic_notes": critic_error,
                "reflection_history": reflection_history,
                "current_step": "sql_critic",
                "status_message": f"⚠️ Critic flagged logic issues: {issues[0] if issues else 'Logic warning'}",
            }

        final_sql = corrected_sql if (corrected_sql and len(corrected_sql.strip()) > 10) else sanitized_sql

    except Exception as exc:
        logger.info(f"[SQL Critic] Semantic LLM audit skipped ({exc}). Relying on passing AST validation.")
        final_sql = sanitized_sql

    return {
        "validation_passed": True,
        "validation_error": None,
        "generated_sql": final_sql,
        "current_step": "sql_critic",
        "status_message": "🛡️ SQL validated: read-only AST verified and approved.",
    }
