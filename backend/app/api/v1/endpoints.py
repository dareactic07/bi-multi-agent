"""FastAPI v1 API routes for database querying, SQL validation, and semantic layer discovery."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
import yaml
from backend.app.core.config import Settings, get_settings
from backend.app.core.validator import validate_sql_query
from backend.app.db.duckdb_client import DuckDBManager, get_duckdb_manager

router = APIRouter()

SEMANTIC_LAYER_PATH = Path(__file__).resolve().parent.parent.parent / "core" / "semantic_layer.yaml"


class QueryRequest(BaseModel):
    """Payload for analytical SQL query execution."""

    model_config = ConfigDict(populate_by_name=True)

    query: str = Field(..., description="SQL SELECT query to execute against the analytical engine.")
    validate_ast: bool = Field(True, alias="validate", description="Enforce strict AST read-only validation.")


class QueryResponse(BaseModel):
    """Response payload containing query results and performance metrics."""

    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    sanitized_sql: str


class ValidationRequest(BaseModel):
    """Payload for SQL AST validation."""

    query: str = Field(..., description="SQL string to check for safety and read-only compliance.")


class ValidationResponse(BaseModel):
    """Response payload for AST validation."""

    is_valid: bool
    error_message: Optional[str] = None
    sanitized_sql: Optional[str] = None
    tables_referenced: List[str] = Field(default_factory=list)


def load_semantic_layer_data() -> Dict[str, Any]:
    """Helper to parse semantic_layer.yaml."""
    if not SEMANTIC_LAYER_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Semantic layer configuration file not found.",
        )
    with open(SEMANTIC_LAYER_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@router.post("/query", response_model=QueryResponse, summary="Execute Analytical SQL Query")
def execute_query(
    request: QueryRequest,
    db: DuckDBManager = Depends(get_duckdb_manager),
) -> QueryResponse:
    """Execute a sanitized, read-only SQL analytical query against DuckDB."""
    try:
        result = db.execute_query(sql=request.query, validate=request.validate_ast)
        return QueryResponse(**result)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution error: {str(exc)}",
        )


@router.post("/validate", response_model=ValidationResponse, summary="Validate SQL AST")
def validate_sql(request: ValidationRequest) -> ValidationResponse:
    """Validate that a query is 100% read-only and conforms to the Olist schema."""
    res = validate_sql_query(request.query)
    return ValidationResponse(
        is_valid=res.is_valid,
        error_message=res.error_message,
        sanitized_sql=res.sanitized_sql,
        tables_referenced=res.tables_referenced,
    )


@router.get("/semantic-layer", summary="Get Full Semantic Layer")
def get_semantic_layer() -> Dict[str, Any]:
    """Retrieve full semantic layer definitions including tables, metrics, and relationships."""
    return load_semantic_layer_data()


@router.get("/metrics", summary="Get Business Metrics")
def get_metrics() -> Dict[str, Any]:
    """Retrieve standardized business metrics and calculation formulas."""
    data = load_semantic_layer_data()
    return data.get("metrics", {})


@router.get("/schema", summary="Get Schema Tables and Relationships")
def get_schema() -> Dict[str, Any]:
    """Retrieve schema tables, column definitions, and canonical entity relationships."""
    data = load_semantic_layer_data()
    return {
        "tables": data.get("tables", {}),
        "relationships": data.get("relationships", []),
    }
