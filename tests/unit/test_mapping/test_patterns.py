"""Tests for column-name pattern rules and the matching engine."""

from hypothesis.mapping.patterns import (
    AMBIGUOUS_TOKENS,
    CONFIDENCE_MODIFIERS,
    PATTERN_RULES,
    find_pattern_matches,
    match_contains,
    match_exact,
    match_prefix,
    match_regex,
    match_suffix,
)
from hypothesis.mapping.types import SEMANTIC_TO_FAKER, SemanticType


def _top(name: str) -> SemanticType | None:
    matches = find_pattern_matches(name)
    return matches[0].semantic_type if matches else None


def test_individual_matchers() -> None:
    assert match_exact("email", "email")
    assert match_exact("Email", "email")  # case-insensitive by default
    assert not match_exact("user_email", "email")
    assert match_prefix("is_active", "is_")
    assert match_suffix("created_at", "_at")
    assert match_contains("user_email_address", "email")
    assert match_regex("user_id", r"^\w+_id$")


def test_case_sensitive_matching() -> None:
    assert match_exact("email", "email", case_sensitive=True)
    assert not match_exact("Email", "email", case_sensitive=True)


def test_common_names_resolve_to_expected_type() -> None:
    assert _top("email") == SemanticType.EMAIL
    assert _top("first_name") == SemanticType.FIRST_NAME
    assert _top("created_at") == SemanticType.CREATED_AT
    assert _top("is_active") == SemanticType.BOOLEAN_FLAG
    assert _top("price") == SemanticType.PRICE


def test_matches_are_sorted_by_confidence_descending() -> None:
    confidences = [match.confidence for match in find_pattern_matches("created_at")]
    assert confidences == sorted(confidences, reverse=True)


def test_unknown_name_has_no_matches() -> None:
    assert find_pattern_matches("xyzzy_qux") == []


def test_foreign_key_style_name_matches_id_via_regex() -> None:
    assert SemanticType.ID in {m.semantic_type for m in find_pattern_matches("user_id")}


def test_every_rule_targets_a_mapped_semantic_type() -> None:
    unmapped = {
        rule.semantic_type.name
        for rule in PATTERN_RULES
        if rule.semantic_type not in SEMANTIC_TO_FAKER
    }
    assert not unmapped, f"PATTERN_RULES reference unmapped semantic types: {unmapped}"


def test_rule_count_meets_spec() -> None:
    assert len(PATTERN_RULES) >= 100


def test_modifiers_and_ambiguous_tokens() -> None:
    assert CONFIDENCE_MODIFIERS["ambiguous_token"] == -0.20
    assert {"status", "type", "code"} <= AMBIGUOUS_TOKENS
