"""DuckDB OLAP Connection Manager with PostgreSQL postgres_scanner integration.

Provides thread-safe in-memory columnar query execution against PostgreSQL
with zero data duplication and microsecond analytical performance.
"""

import logging
import threading
import time
from typing import Any, Dict, List, Optional
import duckdb
from backend.app.core.config import Settings, get_settings
from backend.app.core.validator import ALLOWED_TABLES, validate_sql_query

logger = logging.getLogger(__name__)


class DuckDBManager:
    """Singleton manager for DuckDB in-memory engine attached to PostgreSQL."""

    _instance: Optional["DuckDBManager"] = None
    _lock = threading.Lock()

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._connection: Optional[duckdb.DuckDBPyConnection] = None
        self._initialized = False

    @classmethod
    def get_instance(cls, settings: Optional[Settings] = None) -> "DuckDBManager":
        """Get or initialize the singleton DuckDBManager."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(settings=settings)
            return cls._instance

    def initialize(self) -> None:
        """Initialize DuckDB connection, load postgres extension, attach DB, and register views."""
        if self._initialized and self._connection is not None:
            return

        with self._lock:
            if self._initialized and self._connection is not None:
                return

            logger.info("Initializing DuckDB in-memory OLAP engine...")
            self._connection = duckdb.connect(
                database=self.settings.DUCKDB_DATABASE_PATH,
                read_only=False,
            )

            try:
                # 1. Install and load PostgreSQL scanner extension
                logger.info("Loading DuckDB postgres extension...")
                self._connection.execute("INSTALL postgres;")
                self._connection.execute("LOAD postgres;")

                # 2. Attach PostgreSQL database in READ_ONLY mode
                attach_sql = (
                    f"ATTACH '{self.settings.duckdb_postgres_connection_string}' "
                    f"AS olist_pg (TYPE POSTGRES, READ_ONLY);"
                )
                logger.info("Attaching PostgreSQL to DuckDB (READ_ONLY mode)...")
                self._connection.execute(attach_sql)

                # 3. Create views in default memory.main for every table
                logger.info("Registering logical views in DuckDB memory engine...")
                for table_name in ALLOWED_TABLES:
                    self._connection.execute(
                        f"CREATE OR REPLACE VIEW memory.main.{table_name} "
                        f"AS SELECT * FROM olist_pg.public.{table_name};"
                    )

                self._connection.execute("USE memory.main;")
                self._initialized = True
                logger.info("DuckDB successfully attached to PostgreSQL with all views registered.")

            except Exception as exc:
                logger.error(f"Failed to initialize DuckDB postgres attachment: {exc}")
                raise

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Return the active DuckDB connection, initializing if necessary."""
        if not self._initialized or self._connection is None:
            self.initialize()
        return self._connection

    def execute_query(
        self,
        sql: str,
        validate: bool = True,
    ) -> Dict[str, Any]:
        """Validate and execute an analytical SQL query against the DuckDB-PostgreSQL engine.

        Args:
            sql: The SQL SELECT statement to run.
            validate: Whether to perform AST validation via sqlglot.

        Returns:
            Dict containing:
                - columns: list of column names
                - rows: list of row dicts
                - row_count: number of records returned
                - execution_time_ms: query execution latency in milliseconds
                - sanitized_sql: formatted and validated SQL
        """
        if validate:
            validation = validate_sql_query(sql)
            if not validation.is_valid:
                raise ValueError(f"SQL validation failed: {validation.error_message}")
            executable_sql = validation.sanitized_sql or sql
        else:
            executable_sql = sql

        cursor = self.connection.cursor()
        start_time = time.perf_counter()

        try:
            cursor.execute(executable_sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            raw_rows = cursor.fetchall()
            execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

            rows: List[Dict[str, Any]] = [
                dict(zip(columns, row)) for row in raw_rows
            ]

            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "execution_time_ms": execution_time_ms,
                "sanitized_sql": executable_sql,
            }
        finally:
            cursor.close()

    def health_check(self) -> Dict[str, Any]:
        """Perform a quick ping query to verify DuckDB and PostgreSQL health."""
        try:
            result = self.execute_query(
                "SELECT count(*) AS count FROM orders;",
                validate=True,
            )
            orders_count = result["rows"][0]["count"] if result["rows"] else 0
            return {
                "status": "healthy",
                "engine": "DuckDB + postgres_scanner",
                "orders_count": orders_count,
                "latency_ms": result["execution_time_ms"],
            }
        except Exception as exc:
            return {
                "status": "unhealthy",
                "error": str(exc),
            }


def get_duckdb_manager() -> DuckDBManager:
    """Dependency helper for FastAPI endpoints."""
    return DuckDBManager.get_instance()
