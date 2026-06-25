"""Data generation: turn classifications into concrete row values."""

from __future__ import annotations

import random
from collections.abc import Callable
from functools import partial
from typing import Any

from faker import Faker

from hypothesis.constraints.unique import UniqueConstraintHandler
from hypothesis.core.models import TableSchema
from hypothesis.mapping.pipeline import base_sql_type
from hypothesis.mapping.types import (
    SEMANTIC_TO_FAKER,
    SQL_TYPE_FALLBACK,
    ClassificationResult,
    SemanticType,
)

FkCache = dict[str, list[Any]]


class DataGenerator:
    """Generates row values from classification results using Faker.

    Auto-increment columns are skipped (left to the database). Foreign keys are
    drawn from a cache of parent ids keyed by ``"table.column"``. ENUM and CHECK
    generators are populated from the reflected schema at generation time.
    """

    def __init__(self, faker_locale: str = "en_US", seed: int | None = None) -> None:
        self.faker = Faker(faker_locale)
        if seed is not None:
            self.faker.seed_instance(seed)
            random.seed(seed)

    def generate_value(
        self, classification: ClassificationResult, fk_cache: FkCache | None = None
    ) -> Any:
        """Generate a single value for a classified column."""
        column = classification.column
        semantic_type = classification.semantic_type

        if classification.is_foreign_key:
            values = (fk_cache or {}).get(f"{column.table_name}.{column.name}")
            return random.choice(values) if values else None

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
        fk_cache: FkCache | None = None,
        unique_handler: UniqueConstraintHandler | None = None,
    ) -> dict[str, Any]:
        """Generate one row, skipping auto-increment columns."""
        row: dict[str, Any] = {}
        for column in table.columns:
            if column.is_auto_increment:
                continue
            classification = classifications.get(column.name)
            if classification is None:
                continue
            if (column.is_unique or column.is_primary_key) and unique_handler is not None:
                key = f"{table.name}.{column.name}"
                row[column.name] = unique_handler.ensure_unique(
                    key, partial(self.generate_value, classification, fk_cache)
                )
            else:
                row[column.name] = self.generate_value(classification, fk_cache)
        return row

    def generate_batch(
        self,
        table: TableSchema,
        classifications: dict[str, ClassificationResult],
        count: int,
        fk_cache: FkCache | None = None,
        unique_handler: UniqueConstraintHandler | None = None,
    ) -> list[dict[str, Any]]:
        """Generate a batch of rows."""
        return [
            self.generate_row(table, classifications, fk_cache, unique_handler)
            for _ in range(count)
        ]

    @staticmethod
    def _post_process(classification: ClassificationResult) -> Callable[[Any], Any] | None:
        if classification.semantic_type is SemanticType.TYPE_FALLBACK:
            mapping = SQL_TYPE_FALLBACK.get(base_sql_type(classification.column.sql_type))
        else:
            mapping = SEMANTIC_TO_FAKER.get(classification.semantic_type)
        return mapping.post_process if mapping is not None else None
