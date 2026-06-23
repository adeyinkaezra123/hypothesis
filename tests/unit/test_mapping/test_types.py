"""Tests for the semantic type system and Faker mappings.

The provider/kwargs tests double as a transcription check: every provider named
in ``SEMANTIC_TO_FAKER`` / ``SQL_TYPE_FALLBACK`` must exist on Faker and be
callable with its declared kwargs.
"""

from faker import Faker

from hypothesis.core.models import ColumnSchema
from hypothesis.mapping.types import (
    SEMANTIC_TO_FAKER,
    SQL_TYPE_FALLBACK,
    ClassificationResult,
    FakerMapping,
    SemanticType,
)

_ALL_MAPPINGS = list(SEMANTIC_TO_FAKER.values()) + list(SQL_TYPE_FALLBACK.values())


def test_every_semantic_type_has_a_mapping() -> None:
    missing = [s.name for s in SemanticType if s not in SEMANTIC_TO_FAKER]
    assert not missing, f"SemanticTypes without a FakerMapping: {missing}"


def test_mappings_are_well_formed() -> None:
    for mapping in _ALL_MAPPINGS:
        assert isinstance(mapping, FakerMapping)
        assert isinstance(mapping.compatible_sql_types, set)
        assert mapping.compatible_sql_types, "compatible_sql_types must not be empty"


def test_all_providers_exist_on_faker() -> None:
    faker = Faker()
    missing = [m.provider for m in _ALL_MAPPINGS if not hasattr(faker, m.provider)]
    assert not missing, f"Faker has no such providers: {sorted(set(missing))}"


def test_all_providers_callable_with_their_kwargs() -> None:
    faker = Faker()
    faker.seed_instance(1234)
    for mapping in _ALL_MAPPINGS:
        # Constraint-derived placeholders carry an empty ``elements`` list that
        # is filled in at runtime; calling them now would raise.
        if mapping.kwargs.get("elements") == []:
            continue
        value = getattr(faker, mapping.provider)(**mapping.kwargs)
        if mapping.post_process is not None:
            mapping.post_process(value)


def test_state_is_defined_once() -> None:
    states = [s for s in SemanticType if s.value == "state"]
    assert len(states) == 1


def test_type_fallback_matches_any_sql_type() -> None:
    assert SEMANTIC_TO_FAKER[SemanticType.TYPE_FALLBACK].compatible_sql_types == {"*"}


def test_classification_result_minimal() -> None:
    col = ColumnSchema(name="email", table_name="users", sql_type="VARCHAR", python_type=str)
    result = ClassificationResult(
        column=col,
        semantic_type=SemanticType.EMAIL,
        confidence=0.95,
        faker_provider="email",
        matched_layer=2,
    )
    assert result.faker_kwargs == {}
    assert result.matched_pattern is None
    assert result.needs_review is False
    assert result.is_foreign_key is False
