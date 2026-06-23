"""Tests for confidence score calculation."""

import pytest

from hypothesis.mapping.confidence import calculate_confidence, is_ambiguous


def test_base_score_passes_through() -> None:
    assert calculate_confidence(0.9) == pytest.approx(0.9)


def test_positive_modifier_raises_score() -> None:
    assert calculate_confidence(0.90, sql_type_matches=True) == pytest.approx(0.95)


def test_ambiguous_token_penalty() -> None:
    assert calculate_confidence(0.70, ambiguous_token=True) == pytest.approx(0.50)


def test_score_is_clamped_to_one() -> None:
    score = calculate_confidence(
        0.99, sql_type_matches=True, multiple_patterns=True, table_context_supports=True
    )
    assert score == 1.0


def test_score_is_clamped_to_zero() -> None:
    assert calculate_confidence(0.10, ambiguous_token=True) == 0.0


def test_is_ambiguous() -> None:
    assert is_ambiguous("status")
    assert is_ambiguous("TYPE")
    assert not is_ambiguous("email")
