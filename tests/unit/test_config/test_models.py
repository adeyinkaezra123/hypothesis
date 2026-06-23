"""Tests for the Pydantic generation-config models."""

import pytest
from pydantic import ValidationError

from hypothesis.config.models import (
    ColumnConfig,
    ForeignKeyConfig,
    GenerationConfig,
    SelfReferenceConfig,
    TableConfig,
)


def test_generation_config_defaults() -> None:
    cfg = GenerationConfig()
    assert cfg.default_rows == 1000
    assert cfg.batch_size == 1000
    assert cfg.locale == "en_US"
    assert cfg.null_probability == 0.1
    assert cfg.tables == {}
    assert cfg.self_references == {}


def test_default_rows_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        GenerationConfig(default_rows=0)


def test_batch_size_has_upper_bound() -> None:
    with pytest.raises(ValidationError):
        GenerationConfig(batch_size=200_000)


def test_null_probability_must_be_a_probability() -> None:
    with pytest.raises(ValidationError):
        GenerationConfig(null_probability=1.5)


def test_weights_are_normalized() -> None:
    col = ColumnConfig(values=["a", "b", "c"], weights=[1, 1, 2])
    assert col.weights is not None
    assert sum(col.weights) == pytest.approx(1.0)
    assert col.weights == [0.25, 0.25, 0.5]


def test_weights_length_must_match_values() -> None:
    with pytest.raises(ValidationError):
        ColumnConfig(values=["a", "b"], weights=[0.5, 0.3, 0.2])


def test_foreign_key_distribution_is_constrained() -> None:
    assert ForeignKeyConfig().distribution == "uniform"
    with pytest.raises(ValidationError):
        ForeignKeyConfig.model_validate({"distribution": "weird"})


def test_nested_table_and_column_config() -> None:
    cfg = GenerationConfig(
        tables={
            "users": TableConfig(
                rows=500,
                columns={"email": ColumnConfig(provider="email", unique=True)},
            )
        }
    )
    assert cfg.tables["users"].rows == 500
    assert cfg.tables["users"].columns["email"].unique is True


def test_self_reference_config_defaults() -> None:
    ref = SelfReferenceConfig(column="manager_id")
    assert ref.strategy == "two_pass"
    assert ref.root_probability == 0.1
