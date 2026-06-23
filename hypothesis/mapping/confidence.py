"""Confidence score calculation for column classification."""

from __future__ import annotations

from hypothesis.mapping.patterns import AMBIGUOUS_TOKENS, CONFIDENCE_MODIFIERS


def calculate_confidence(
    base: float,
    *,
    sql_type_matches: bool = False,
    multiple_patterns: bool = False,
    table_context_supports: bool = False,
    ambiguous_token: bool = False,
    very_short_name: bool = False,
    sql_type_mismatch: bool = False,
    generic_name: bool = False,
) -> float:
    """Apply the confidence modifiers to a base score, clamped to ``[0.0, 1.0]``."""
    flags = {
        "sql_type_matches": sql_type_matches,
        "multiple_patterns": multiple_patterns,
        "table_context_supports": table_context_supports,
        "ambiguous_token": ambiguous_token,
        "very_short_name": very_short_name,
        "sql_type_mismatch": sql_type_mismatch,
        "generic_name": generic_name,
    }
    score = base + sum(CONFIDENCE_MODIFIERS[name] for name, active in flags.items() if active)
    return max(0.0, min(1.0, score))


def is_ambiguous(name: str) -> bool:
    """True if the column name is a known ambiguous token (e.g. status, type)."""
    return name.lower() in AMBIGUOUS_TOKENS
