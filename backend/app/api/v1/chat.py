"""Chat and Server-Sent Events (SSE) streaming endpoints for the BI Multi-Agent Pod."""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from backend.app.agent.graph import bi_agent_app
from backend.app.agent.state import AgentState

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    """Payload for conversational business queries."""

    query: str = Field(..., description="Natural language business question (e.g., 'What were top 5 product categories by revenue in 2017?')")
    thread_id: Optional[str] = Field(None, description="Optional conversation session ID")


class ChatResponse(BaseModel):
    """Full consolidated analytical answer and dynamic chart spec."""

    query: str
    generated_sql: Optional[str] = None
    relevant_tables: List[str] = Field(default_factory=list)
    query_result: Optional[Dict[str, Any]] = None
    insights: str
    chart_spec: Optional[Dict[str, Any]] = None
    reflection_count: int = 0
    is_terminal_error: bool = False


@router.post("", response_model=ChatResponse, summary="Synchronous Conversational BI Query")
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Execute the multi-agent pod synchronously and return complete insights and chart."""
    initial_state: AgentState = {
        "user_query": request.query,
        "reflection_count": 0,
        "reflection_history": [],
        "is_terminal_error": False,
    }

    try:
        final_state = await asyncio.to_thread(bi_agent_app.invoke, initial_state)
        return ChatResponse(
            query=request.query,
            generated_sql=final_state.get("generated_sql"),
            relevant_tables=final_state.get("relevant_tables", []),
            query_result=final_state.get("query_result"),
            insights=final_state.get("insights", "Analysis complete."),
            chart_spec=final_state.get("chart_spec"),
            reflection_count=final_state.get("reflection_count", 0),
            is_terminal_error=final_state.get("is_terminal_error", False),
        )
    except Exception as exc:
        logger.error(f"Error in chat endpoint: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow execution error: {str(exc)}",
        )


async def sse_event_generator(query: str, request: Request) -> AsyncGenerator[Dict[str, str], None]:
    """Stream real-time agent node updates via Server-Sent Events (SSE)."""
    initial_state: AgentState = {
        "user_query": query,
        "reflection_count": 0,
        "reflection_history": [],
        "is_terminal_error": False,
    }

    try:
        # Initial greeting event
        yield {
            "event": "status",
            "data": json.dumps({"step": "init", "message": "🚀 Starting Autonomous Multi-Agent Pod..."}),
        }

        # Stream node-by-node updates from LangGraph
        for chunk in bi_agent_app.stream(initial_state):
            # chunk is a dict of {node_name: updated_state_fields}
            for node_name, updates in chunk.items():
                if await request.is_disconnected():
                    logger.info("Client disconnected from SSE stream.")
                    return

                status_msg = updates.get("status_message", f"Completed step: {node_name}")
                yield {
                    "event": "step",
                    "data": json.dumps({
                        "node": node_name,
                        "status_message": status_msg,
                        "generated_sql": updates.get("generated_sql"),
                        "execution_time_ms": updates.get("query_result", {}).get("execution_time_ms") if updates.get("query_result") else None,
                    }),
                }

                # If storyteller node finished, stream the final payload
                if node_name == "storyteller":
                    yield {
                        "event": "final_result",
                        "data": json.dumps({
                            "insights": updates.get("insights"),
                            "chart_spec": updates.get("chart_spec"),
                            "is_terminal_error": updates.get("is_terminal_error", False),
                        }),
                    }

        yield {
            "event": "done",
            "data": json.dumps({"status": "complete"}),
        }

    except Exception as exc:
        logger.error(f"Error during SSE streaming: {exc}")
        yield {
            "event": "error",
            "data": json.dumps({"error": str(exc)}),
        }


@router.post("/stream", summary="Stream Multi-Agent Execution via SSE")
async def chat_stream_endpoint(request: ChatRequest, req: Request) -> EventSourceResponse:
    """Stream real-time node thoughts, generated SQL, and final charts using Server-Sent Events."""
    return EventSourceResponse(sse_event_generator(request.query, req))
