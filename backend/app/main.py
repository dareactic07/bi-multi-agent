"""FastAPI Application Entry Point for Olist Autonomous BI Agent."""

from contextlib import asynccontextmanager
import logging
from typing import Any, Dict
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.endpoints import router as api_v1_router
from backend.app.core.config import get_settings
from backend.app.db.duckdb_client import get_duckdb_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown hooks."""
    logger.info("Starting up Autonomous BI Multi-Agent Backend...")
    try:
        duckdb_manager = get_duckdb_manager()
        duckdb_manager.initialize()
        logger.info("DuckDB-PostgreSQL OLAP engine successfully initialized.")
    except Exception as exc:
        logger.warning(f"DuckDB automatic initialization deferred: {exc}")

    yield

    logger.info("Shutting down Autonomous BI Multi-Agent Backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="High-performance analytical API and AI Agent backend for Olist E-Commerce BI.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
app.include_router(chat_router, prefix=f"{settings.API_V1_PREFIX}/chat", tags=["Chat & Agent Pod"])


@app.get("/", tags=["Root"])
def root() -> Dict[str, Any]:
    """Root endpoint returning API service metadata."""
    return {
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": "/health",
        "api_v1": settings.API_V1_PREFIX,
    }


@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
def health_check() -> Dict[str, Any]:
    """Health check endpoint evaluating both API and DuckDB/PostgreSQL connectivity."""
    db_manager = get_duckdb_manager()
    db_health = db_manager.health_check()

    is_healthy = db_health.get("status") == "healthy"
    return {
        "status": "healthy" if is_healthy else "degraded",
        "environment": settings.APP_ENV,
        "database": db_health,
    }
