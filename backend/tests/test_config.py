"""Unit tests for Pydantic application settings configuration."""

from backend.app.core.config import Settings, get_settings


def test_settings_load_defaults():
    settings = get_settings()
    assert settings.PROJECT_NAME == "Autonomous BI Multi-Agent System"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.POSTGRES_PORT == 5432
    assert settings.POSTGRES_DB == "olist_db"
    assert settings.READONLY_USER == "olist_readonly"


def test_settings_connection_strings():
    settings = get_settings()
    duckdb_str = settings.duckdb_postgres_connection_string
    assert "host=" in duckdb_str
    assert "port=5432" in duckdb_str
    assert "dbname=olist_db" in duckdb_str
    assert f"user={settings.READONLY_USER}" in duckdb_str

    pg_uri = settings.readonly_postgres_uri
    assert pg_uri.startswith("postgresql://")
    assert settings.READONLY_USER in pg_uri
    assert "olist_db" in pg_uri
