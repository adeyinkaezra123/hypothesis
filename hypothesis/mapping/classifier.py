"""ColumnClassifier — orchestrates the classification pipeline."""

from __future__ import annotations

from typing import Any

from hypothesis.core.models import ColumnSchema, TableSchema
from hypothesis.mapping.pipeline import base_sql_type, run_pipeline
from hypothesis.mapping.types import (
    SEMANTIC_TO_FAKER,
    SQL_TYPE_FALLBACK,
    ClassificationResult,
    SemanticType,
)


class ColumnClassifier:
    """Classifies columns using the layered pipeline and resolves Faker providers."""

    def __init__(
        self,
        custom_patterns: dict[str, str] | None = None,
        confidence_threshold: float = 0.6,
    ) -> None:
        # custom_patterns is reserved for user-defined name -> provider overrides
        # (FR-017/FR-019); stored now, applied in a later task.
        self.custom_patterns = custom_patterns or {}
        self.confidence_threshold = confidence_threshold

    def classify_column(
        self, column: ColumnSchema, table_context: str | None = None
    ) -> ClassificationResult:
        """Classify a single column."""
        layer = run_pipeline(column, table_context)
        provider, kwargs = self._resolve_provider(layer.semantic_type, column)
        return ClassificationResult(
            column=column,
            semantic_type=layer.semantic_type,
            confidence=layer.confidence,
            faker_provider=provider,
            faker_kwargs=kwargs,
            matched_layer=layer.layer,
            matched_pattern=layer.matched_pattern,
            reasoning=layer.reasoning,
            needs_review=layer.confidence < self.confidence_threshold,
            is_auto_increment=column.is_auto_increment,
            is_foreign_key=column.is_foreign_key,
        )

    def classify_table(self, table: TableSchema) -> dict[str, ClassificationResult]:
        """Classify every column in a table, keyed by column name."""
        return {
            column.name: self.classify_column(column, table_context=table.name)
            for column in table.columns
        }

    def classify_schema(
        self, tables: list[TableSchema]
    ) -> dict[str, dict[str, ClassificationResult]]:
        """Classify every column in every table, keyed by table then column name."""
        return {table.name: self.classify_table(table) for table in tables}

    def get_low_confidence_columns(
        self, results: dict[str, dict[str, ClassificationResult]]
    ) -> list[tuple[str, str, ClassificationResult]]:
        """Return ``(table, column, result)`` for every column flagged for review."""
        return [
            (table_name, column_name, result)
            for table_name, columns in results.items()
            for column_name, result in columns.items()
            if result.needs_review
        ]

    def _resolve_provider(
        self, semantic_type: SemanticType, column: ColumnSchema
    ) -> tuple[str, dict[str, Any]]:
        if semantic_type is SemanticType.TYPE_FALLBACK:
            mapping = SQL_TYPE_FALLBACK.get(
                base_sql_type(column.sql_type), SEMANTIC_TO_FAKER[SemanticType.TYPE_FALLBACK]
            )
        else:
            mapping = SEMANTIC_TO_FAKER[semantic_type]
        return mapping.provider, dict(mapping.kwargs)
