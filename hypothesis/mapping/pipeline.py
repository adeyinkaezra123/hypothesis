"""The layered column-classification pipeline.

Runs a column through five layers in priority order and returns the first match.
The final layer (SQL type fallback) always produces a result, so the pipeline
never returns ``None``.

  1. Schema constraints (ENUM / FK / CHECK)   — highest confidence
  2. Pattern matching on the column name
  3. Token analysis for compound names
  4. Table-context disambiguation
  5. SQL type fallback                         — lowest confidence
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from hypothesis.core.models import ColumnSchema
from hypothesis.mapping.confidence import calculate_confidence, is_ambiguous
from hypothesis.mapping.patterns import find_pattern_matches
from hypothesis.mapping.tokenizer import best_token_signal
from hypothesis.mapping.types import SEMANTIC_TO_FAKER, SemanticType

_DATETIME_TYPES = {"TIMESTAMP", "TIMESTAMPTZ", "DATETIME"}
_CONTEXT_GUESSES: dict[str, SemanticType] = {
    "name": SemanticType.NAME,
    "label": SemanticType.NAME,
}


@dataclass
class LayerResult:
    """A classification produced by one pipeline layer."""

    semantic_type: SemanticType
    confidence: float
    layer: int
    matched_pattern: str | None
    reasoning: str


def base_sql_type(sql_type: str) -> str:
    """Reduce ``VARCHAR(255)`` / ``DOUBLE PRECISION`` to the leading type token."""
    return re.split(r"[(\s]", sql_type.upper(), maxsplit=1)[0]


def _sql_type_aligns(semantic_type: SemanticType, column: ColumnSchema) -> bool:
    mapping = SEMANTIC_TO_FAKER.get(semantic_type)
    if mapping is None:
        return False
    return "*" in mapping.compatible_sql_types or base_sql_type(column.sql_type) in (
        mapping.compatible_sql_types
    )


def layer_schema_constraints(column: ColumnSchema) -> LayerResult | None:
    """Layer 1: ENUM / FK / CHECK constraints (authoritative)."""
    if column.enum_values:
        return LayerResult(
            SemanticType.ENUM_VALUE, 1.0, 1, None, f"ENUM ({len(column.enum_values)} values)"
        )
    if column.is_foreign_key:
        return LayerResult(SemanticType.FOREIGN_KEY, 1.0, 1, None, "foreign key reference")
    if column.check_values:
        return LayerResult(SemanticType.CHECK_VALUES, 0.95, 1, None, "CHECK IN (...) values")
    if column.check_min is not None or column.check_max is not None:
        return LayerResult(
            SemanticType.CHECK_RANGE,
            0.95,
            1,
            None,
            f"CHECK range [{column.check_min}, {column.check_max}]",
        )
    return None


def layer_pattern_matching(column: ColumnSchema) -> LayerResult | None:
    """Layer 2: exact / prefix / suffix / contains / regex name patterns."""
    matches = find_pattern_matches(column.name)
    if not matches:
        return None
    best = matches[0]
    multiple = sum(1 for match in matches if match.semantic_type == best.semantic_type) > 1
    confidence = calculate_confidence(
        best.confidence,
        sql_type_matches=_sql_type_aligns(best.semantic_type, column),
        multiple_patterns=multiple,
        ambiguous_token=is_ambiguous(column.name),
    )
    return LayerResult(
        best.semantic_type,
        confidence,
        2,
        best.pattern,
        f"matched {best.pattern_type} pattern '{best.pattern}'",
    )


def layer_token_analysis(column: ColumnSchema) -> LayerResult | None:
    """Layer 3: strongest semantic signal among a compound name's tokens."""
    signal = best_token_signal(column.name)
    if signal is None:
        return None
    semantic_type, base = signal
    confidence = calculate_confidence(
        base, sql_type_matches=_sql_type_aligns(semantic_type, column)
    )
    return LayerResult(semantic_type, confidence, 3, None, f"token signal -> {semantic_type.value}")


def layer_table_context(column: ColumnSchema, table_context: str | None) -> LayerResult | None:
    """Layer 4: disambiguate generic names using the table name."""
    if table_context is None:
        return None
    guess = _CONTEXT_GUESSES.get(column.name.lower())
    if guess is None:
        return None
    confidence = calculate_confidence(0.65, table_context_supports=True)
    return LayerResult(guess, confidence, 4, None, f"'{column.name}' in table '{table_context}'")


def layer_type_fallback(column: ColumnSchema) -> LayerResult:
    """Layer 5: SQL type-based fallback. Always returns a result."""
    base = base_sql_type(column.sql_type)
    confidence = 0.6 if base in _DATETIME_TYPES else 0.5
    return LayerResult(
        SemanticType.TYPE_FALLBACK, confidence, 5, None, f"SQL type fallback for {base}"
    )


def run_pipeline(column: ColumnSchema, table_context: str | None = None) -> LayerResult:
    """Run a column through all layers, returning the first match."""
    return (
        layer_schema_constraints(column)
        or layer_pattern_matching(column)
        or layer_token_analysis(column)
        or layer_table_context(column, table_context)
        or layer_type_fallback(column)
    )
