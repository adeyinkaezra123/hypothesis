"""Database connection management with pooling and validation."""

from typing import Literal

from sqlalchemy import Column, MetaData, Table, create_engine, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import Select


def _split_table_identifier(table: str) -> tuple[str | None, str]:
    """Split an optional ``schema.table`` identifier for SQLAlchemy Core."""
    parts = table.split(".")
    if len(parts) == 1:
        schema = None
        table_name = parts[0]
    elif len(parts) == 2:
        schema, table_name = parts
    else:
        raise ValueError(f"Invalid table identifier: {table!r}")

    if not table_name or any(part == "" or "\x00" in part for part in parts):
        raise ValueError(f"Invalid table identifier: {table!r}")
    return schema, table_name


def _max_pk_statement(table: str, pk_column: str) -> Select[tuple[int | None]]:
    """Build a dialect-quoted ``SELECT max(pk)`` statement."""
    if not pk_column or "\x00" in pk_column:
        raise ValueError(f"Invalid primary-key column identifier: {pk_column!r}")

    schema, table_name = _split_table_identifier(table)
    table_ref = Table(
        table_name,
        MetaData(),
        Column(pk_column, quote=True),
        schema=schema,
        quote=True,
        quote_schema=True,
    )
    return select(func.max(table_ref.c[pk_column]))


class DatabaseConnection:
    """Manages database connections with pooling and validation."""

    def __init__(
        self,
        connection_string: str,
        pool_size: int = 5,
        max_overflow: int = 10,
    ):
        """Initialize database connection.

        Args:
            connection_string: Database connection URL
            pool_size: Number of connections to maintain in pool
            max_overflow: Maximum overflow connections
        """
        self.connection_string = connection_string
        self.engine = create_engine(
            connection_string,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Verify connection health
            echo=False,  # Disable SQL logging
        )

    def validate(self) -> bool:
        """Check connection and basic permissions.

        Returns:
            True if connection is valid and accessible
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    def get_dialect(self) -> Literal["postgresql", "mysql"]:
        """Return database dialect using SQLAlchemy's type system.

        Returns:
            Database dialect ('postgresql' or 'mysql')

        Raises:
            ValueError: If database dialect is not supported
        """
        from sqlalchemy.dialects import mysql, postgresql

        dialect = self.engine.dialect

        # Type-safe detection using isinstance
        if isinstance(dialect, postgresql.dialect):
            return "postgresql"
        elif isinstance(dialect, mysql.dialect):
            return "mysql"
        else:
            raise ValueError(
                f"Unsupported database: {dialect.name}. "
                "Hypothesis supports PostgreSQL and MySQL only."
            )

    def test_write_permissions(self) -> bool:
        """Verify write access to database.

        Returns:
            True if write permissions are available
        """
        try:
            with self.engine.begin() as conn:
                # Try to create and drop a temporary table
                conn.execute(text("CREATE TEMPORARY TABLE _hypothesis_test (id INT)"))
                conn.execute(text("DROP TABLE _hypothesis_test"))
            return True
        except SQLAlchemyError:
            return False

    def get_next_sequence_value(self, table: str, pk_column: str) -> int:
        """Get next available PK value for append mode.

        Args:
            table: Table name
            pk_column: Primary key column name

        Returns:
            Next available sequence value
        """
        dialect = self.get_dialect()
        statement = _max_pk_statement(table, pk_column)

        with self.engine.connect() as conn:
            if dialect in ("postgresql", "mysql"):
                result = conn.execute(statement).scalar()
                return (result or 0) + 1

        raise ValueError(f"Unsupported database dialect: {dialect}")

    def close(self) -> None:
        """Close database connection and cleanup resources."""
        self.engine.dispose()
