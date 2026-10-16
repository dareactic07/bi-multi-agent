"""LangGraph Multi-Agent Pod Orchestration with Self-Healing Reflection Loop."""

import logging
from typing import Literal
from langgraph.graph import END, START, StateGraph
from backend.app.agent.nodes.executor import executor_node
from backend.app.agent.nodes.orchestrator import orchestrator_node
from backend.app.agent.nodes.sql_critic import sql_critic_node
from backend.app.agent.nodes.sql_engineer import sql_engineer_node
from backend.app.agent.nodes.storyteller import storyteller_node
from backend.app.agent.state import AgentState
from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


def route_after_critic(state: AgentState) -> Literal["executor", "sql_engineer", "storyteller"]:
    """Determine whether to proceed to execution, retry via reflection, or abort to storyteller."""
    if state.get("validation_passed", False):
        return "executor"

    reflection_count = state.get("reflection_count", 0)
    max_retries = get_settings().MAX_REFLECTION_ATTEMPTS

    if reflection_count < max_retries:
        logger.info(f"[Graph Router] Critic validation failed. Retrying (reflection {reflection_count + 1}/{max_retries})...")
        return "sql_engineer"

    logger.warning(f"[Graph Router] Max reflections ({max_retries}) exceeded at critic. Routing to error narrative.")
    return "storyteller"


def route_after_executor(state: AgentState) -> Literal["storyteller", "sql_engineer"]:
    """Determine whether to conclude with insights or loop back to correct runtime error."""
    execution_error = state.get("execution_error")
    if not execution_error and state.get("query_result"):
        return "storyteller"

    reflection_count = state.get("reflection_count", 0)
    max_retries = get_settings().MAX_REFLECTION_ATTEMPTS

    if reflection_count < max_retries:
        logger.info(f"[Graph Router] Execution failed: {execution_error}. Healing (reflection {reflection_count}/{max_retries})...")
        return "sql_engineer"

    logger.warning(f"[Graph Router] Max reflections ({max_retries}) exceeded at executor. Routing to error narrative.")
    return "storyteller"


def build_bi_agent_graph() -> StateGraph:
    """Construct and configure the 4-agent LangGraph state machine."""
    workflow = StateGraph(AgentState)

    # 1. Register agent nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("sql_engineer", sql_engineer_node)
    workflow.add_node("sql_critic", sql_critic_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("storyteller", storyteller_node)

    # 2. Add edges and conditional branches
    workflow.add_edge(START, "orchestrator")
    workflow.add_edge("orchestrator", "sql_engineer")
    workflow.add_edge("sql_engineer", "sql_critic")

    workflow.add_conditional_edges(
        "sql_critic",
        route_after_critic,
        {
            "executor": "executor",
            "sql_engineer": "sql_engineer",
            "storyteller": "storyteller",
        },
    )

    workflow.add_conditional_edges(
        "executor",
        route_after_executor,
        {
            "storyteller": "storyteller",
            "sql_engineer": "sql_engineer",
        },
    )

    workflow.add_edge("storyteller", END)

    return workflow


# Compile executable agent application
bi_agent_app = build_bi_agent_graph().compile()
