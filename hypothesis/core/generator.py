"""Data generation: turn classifications into concrete row values."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any, Protocol

from faker import Faker

from hypothesis.constraints.unique import UniqueConstraintHandler
from hypothesis.core.exceptions import ForeignKeyError
from hypothesis.core.models import ColumnSchema, ForeignKey, TableSchema
from hypothesis.mapping.pipeline import base_sql_type
from hypothesis.mapping.types import (
    SEMANTIC_TO_FAKER,
    SQL_TYPE_FALLBACK,
    ClassificationResult,
    SemanticType,
)


class FkValueSource(Protocol):
    """Supplies a valid foreign-key value for a parent table/column."""

    def select_fk_value(
        self, parent_table: str, parent_column: str, distribution: str = "uniform"
    ) -> Any: ...


class DataGenerator:
    """Generates row values from classification results using Faker.

    Auto-increment columns are skipped (left to the database). Foreign-key values
    are drawn from an :class:`FkValueSource` (the resolver), so references point
    at real parent rows and respect the configured distribution. ENUM and CHECK
    generators are populated from the reflected schema at generation time.
    """

    def __init__(self, faker_locale: str = "en_US", seed: int | None = None) -> None:
        self.faker = Faker(faker_locale)
        if seed is not None:
            self.faker.seed_instance(seed)

    def generate_value(self, classification: ClassificationResult) -> Any:
        """Generate a single non-foreign-key value for a classified column."""
        column = classification.column
        semantic_type = classification.semantic_type

        if semantic_type is SemanticType.ENUM_VALUE and column.enum_values:
            return self.faker.random_element(elements=column.enum_values)
        if semantic_type is SemanticType.CHECK_VALUES and column.check_values:
            return self.faker.random_element(elements=column.check_values)
        if semantic_type is SemanticType.CHECK_RANGE:
            low = int(column.check_min) if column.check_min is not None else 0
            high = int(column.check_max) if column.check_max is not None else 100
            return self.faker.random_int(min=low, max=high)

        value = getattr(self.faker, classification.faker_provider)(**classification.faker_kwargs)
        post_process = self._post_process(classification)
        return post_process(value) if post_process is not None else value

    def generate_row(
        self,
        table: TableSchema,
        classifications: dict[str, ClassificationResult],
        fk_source: FkValueSource | None = None,
        unique_handler: UniqueConstraintHandler | None = None,
        fk_distributions: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Generate one row, skipping auto-increment columns."""
        fk_by_column = {fk.column: fk for fk in table.foreign_keys}
        row: dict[str, Any] = {}
        for column in table.columns:
            if column.is_auto_increment:
                continue
            classification = classifications.get(column.name)
            if classification is None:
                continue
            factory = partial(
                self._produce_value,
                column,
                classification,
                fk_by_column,
                fk_source,
                fk_distributions,
            )
            if (column.is_unique or column.is_primary_key) and unique_handler is not None:
                row[column.name] = unique_handler.ensure_unique(
                    f"{table.name}.{column.name}", factory
                )
            else:
                row[column.name] = factory()
        return row

    def generate_batch(
        self,
        table: TableSchema,
        classifications: dict[str, ClassificationResult],
        count: int,
        fk_source: FkValueSource | None = None,
        unique_handler: UniqueConstraintHandler | None = None,
        fk_distributions: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Generate a batch of rows."""
        return [
            self.generate_row(table, classifications, fk_source, unique_handler, fk_distributions)
            for _ in range(count)
        ]

    def _produce_value(
        self,
        column: ColumnSchema,
        classification: ClassificationResult,
        fk_by_column: dict[str, ForeignKey],
        fk_source: FkValueSource | None,
        fk_distributions: dict[str, str] | None,
    ) -> Any:
        if column.is_foreign_key and fk_source is not None:
            fk = fk_by_column.get(column.name)
            if fk is not None:
                distribution = (fk_distributions or {}).get(column.name, "uniform")
                try:
                    return fk_source.select_fk_value(
                        fk.referenced_table, fk.referenced_column, distribution
                    )
                except ForeignKeyError:
                    if column.nullable:
                        return None
                    raise
        return self.generate_value(classification)

    @staticmethod
    def _post_process(classification: ClassificationResult) -> Callable[[Any], Any] | None:
        if classification.semantic_type is SemanticType.TYPE_FALLBACK:
            mapping = SQL_TYPE_FALLBACK.get(base_sql_type(classification.column.sql_type))
        else:
            mapping = SEMANTIC_TO_FAKER.get(classification.semantic_type)
        return mapping.post_process if mapping is not None else None
