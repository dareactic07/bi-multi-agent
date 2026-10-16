"""Agent state representation for the LangGraph 4-Agent Pod."""

from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field


class ChartSpec(BaseModel):
    """Structured Recharts visualization specification."""

    chart_type: str = Field(
        ...,
        description="Optimal visualization type: 'bar', 'line', 'area', 'pie', or 'metric_card'",
    )
    title: str = Field(..., description="Title for the chart card")
    x_axis_key: str = Field(..., description="Column name mapped to X-axis / category")
    y_axis_keys: List[str] = Field(..., description="List of numeric metric column names")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Chart series data rows")
    summary: Optional[str] = Field(None, description="Brief interpretation of the visualization")


class AgentState(TypedDict, total=False):
    """Shared state dictionary passed across LangGraph nodes."""

    # Input
    user_query: str

    # Orchestrator outputs
    relevant_tables: List[str]
    relevant_metrics: List[str]
    pruned_schema_context: str

    # SQL Engineer outputs
    generated_sql: str

    # Critic outputs
    validation_passed: bool
    validation_error: Optional[str]
    critic_notes: Optional[str]

    # Executor outputs
    execution_error: Optional[str]
    query_result: Optional[Dict[str, Any]]

    # Reflection / Healing tracking
    reflection_count: int
    reflection_history: List[str]

    # Storyteller outputs
    insights: str
    chart_spec: Optional[Dict[str, Any]]

    # Progress and status for SSE streaming
    current_step: str
    status_message: str
    is_terminal_error: bool
