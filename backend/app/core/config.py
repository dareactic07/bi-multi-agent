"""Application configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for the Autonomous BI application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project metadata
    PROJECT_NAME: str = "Autonomous BI Multi-Agent System"
    API_V1_PREFIX: str = "/api/v1"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # PostgreSQL Admin Configuration
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "olist_db"
    POSTGRES_USER: str = "olist_admin"
    POSTGRES_PASSWORD: str = "olist_secure_password_123"

    # PostgreSQL Read-Only Analytical User (used by DuckDB and Agent)
    READONLY_USER: str = "olist_readonly"
    READONLY_PASSWORD: str = "readonly_secure_password_123"

    # DuckDB In-Memory OLAP Configuration
    DUCKDB_DATABASE_PATH: str = ":memory:"
    DUCKDB_ATTACH_SCHEMA: str = "public"

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @property
    def duckdb_postgres_connection_string(self) -> str:
        """Connection string formatted for DuckDB postgres_scanner ATTACH command."""
        return (
            f"host={self.POSTGRES_HOST} "
            f"port={self.POSTGRES_PORT} "
            f"dbname={self.POSTGRES_DB} "
            f"user={self.READONLY_USER} "
            f"password={self.READONLY_PASSWORD}"
        )

    @property
    def readonly_postgres_uri(self) -> str:
        """Standard PostgreSQL URI for the read-only user."""
        return (
            f"postgresql://{self.READONLY_USER}:{self.READONLY_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of application settings."""
    return Settings()
