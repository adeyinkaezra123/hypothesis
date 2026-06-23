"""Tests for column-name tokenization and token scoring."""

from hypothesis.mapping.tokenizer import best_token_signal, score_tokens, tokenize
from hypothesis.mapping.types import SemanticType


def test_snake_case_splitting() -> None:
    assert tokenize("customer_billing_address") == ["customer", "billing", "address"]


def test_camel_case_splitting() -> None:
    assert tokenize("firstName") == ["first", "name"]
    assert tokenize("emailAddress") == ["email", "address"]


def test_acronym_boundaries() -> None:
    assert tokenize("HTTPSConnection") == ["https", "connection"]


def test_kebab_and_mixed_separators() -> None:
    assert tokenize("user-id.value") == ["user", "id", "value"]


def test_best_token_signal_finds_embedded_semantic() -> None:
    signal = best_token_signal("customer_billing_address")
    assert signal is not None
    assert signal[0] == SemanticType.ADDRESS


def test_score_tokens_skips_opaque_tokens() -> None:
    assert score_tokens(["xyz", "qux"]) == []


def test_no_signal_for_opaque_name() -> None:
    assert best_token_signal("xyz_qux") is None
