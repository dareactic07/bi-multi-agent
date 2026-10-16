"""SQL Abstract Syntax Tree (AST) validation using sqlglot.

Enforces zero-hallucination and security constraints:
- Queries must be strictly read-only SELECT (or UNION of SELECTs)
- Disallows multi-statement queries, DDL, DML, or injection patterns
- Validates referenced tables against allowed database entities and CTEs
"""

from typing import List, Optional, Set
from pydantic import BaseModel, Field
import sqlglot
from sqlglot import exp

ALLOWED_TABLES: Set[str] = {
    "customers",
    "sellers",
    "products",
    "orders",
    "order_items",
    "order_payments",
    "order_reviews",
}

DISALLOWED_EXPRESSION_TYPES = (
    exp.Drop,
    exp.Delete,
    exp.Insert,
    exp.Update,
    exp.Alter,
    exp.Create,
    exp.Command,
    exp.Pragma,
    exp.Transaction,
    exp.Commit,
    exp.Rollback,
)


class ValidationResult(BaseModel):
    """Result of SQL AST security and structure validation."""

    is_valid: bool
    error_message: Optional[str] = None
    sanitized_sql: Optional[str] = None
    tables_referenced: List[str] = Field(default_factory=list)


def validate_sql_query(
    sql_text: str,
    dialect: str = "duckdb",
    allowed_tables: Optional[Set[str]] = None,
) -> ValidationResult:
    """Validate that the SQL query is strictly read-only and references valid schema tables.

    Args:
        sql_text: Raw SQL string to validate.
        dialect: SQL dialect for parser (defaults to 'duckdb').
        allowed_tables: Set of allowed table names (defaults to Olist tables).

    Returns:
        ValidationResult with validation status, error message, and extracted tables.
    """
    if not sql_text or not sql_text.strip():
        return ValidationResult(
            is_valid=False,
            error_message="Query cannot be empty.",
        )

    clean_sql = sql_text.strip().rstrip(";")
    valid_tables = allowed_tables or ALLOWED_TABLES

    # 1. Parse into AST statements
    try:
        statements = sqlglot.parse(clean_sql, read=dialect)
    except Exception as exc:
        return ValidationResult(
            is_valid=False,
            error_message=f"SQL syntax error: {str(exc)}",
        )

    if not statements:
        return ValidationResult(
            is_valid=False,
            error_message="No valid SQL statements found.",
        )

    # 2. Reject multi-statement queries
    if len(statements) > 1:
        return ValidationResult(
            is_valid=False,
            error_message="Multi-statement queries are strictly prohibited.",
        )

    expression = statements[0]
    if expression is None:
        return ValidationResult(
            is_valid=False,
            error_message="Could not parse expression.",
        )

    # 3. Ensure root statement is read-only (SELECT or UNION)
    if not isinstance(expression, (exp.Select, exp.Union)):
        return ValidationResult(
            is_valid=False,
            error_message=f"Prohibited statement type: only SELECT queries are permitted (got {type(expression).__name__}).",
        )

    # 4. Check for any nested destructive expressions
    for disallowed_type in DISALLOWED_EXPRESSION_TYPES:
        if expression.find(disallowed_type):
            return ValidationResult(
                is_valid=False,
                error_message=f"Destructive or mutating operation detected: {disallowed_type.__name__}.",
            )

    # 5. Extract CTE names defined inside query
    cte_names: Set[str] = set()
    for cte in expression.find_all(exp.CTE):
        alias = cte.alias
        if alias:
            cte_names.add(alias.lower())

    # 6. Extract and validate physical table references
    tables_found: Set[str] = set()
    for table_node in expression.find_all(exp.Table):
        table_name = table_node.name.lower() if table_node.name else ""
        if not table_name:
            continue

        # If it's a CTE alias, it's valid
        if table_name in cte_names:
            continue

        # Check against database schema
        if table_name not in valid_tables:
            return ValidationResult(
                is_valid=False,
                error_message=f"Unauthorized or unknown table referenced: '{table_name}'. Allowed tables are: {sorted(list(valid_tables))}",
            )

        tables_found.add(table_name)

    # 7. Normalize SQL using dialect
    try:
        sanitized = expression.sql(dialect=dialect, pretty=True)
    except Exception:
        sanitized = clean_sql

    return ValidationResult(
        is_valid=True,
        sanitized_sql=sanitized,
        tables_referenced=sorted(list(tables_found)),
    )
