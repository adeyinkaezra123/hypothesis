"""Tests for the layered classification pipeline."""

from typing import Any

from hypothesis.core.models import ColumnSchema
from hypothesis.mapping.pipeline import (
    base_sql_type,
    layer_schema_constraints,
    layer_type_fallback,
    run_pipeline,
)
from hypothesis.mapping.types import SemanticType


def _col(name: str, sql_type: str = "VARCHAR(255)", **kwargs: Any) -> ColumnSchema:
    return ColumnSchema(name=name, table_name="t", sql_type=sql_type, python_type=str, **kwargs)


def test_base_sql_type_normalization() -> None:
    assert base_sql_type("VARCHAR(255)") == "VARCHAR"
    assert base_sql_type("DOUBLE PRECISION") == "DOUBLE"
    assert base_sql_type("timestamp without time zone") == "TIMESTAMP"


def test_layer1_enum_outranks_name_pattern() -> None:
    result = run_pipeline(_col("status", sql_type="ENUM", enum_values=["x", "y"]))
    assert result.semantic_type == SemanticType.ENUM_VALUE
    assert result.layer == 1
    assert result.confidence == 1.0


def test_layer1_foreign_key() -> None:
    result = layer_schema_constraints(_col("user_id", sql_type="INTEGER", is_foreign_key=True))
    assert result is not None
    assert result.semantic_type == SemanticType.FOREIGN_KEY


def test_layer1_check_range() -> None:
    result = layer_schema_constraints(_col("age", sql_type="INTEGER", check_min=0, check_max=120))
    assert result is not None
    assert result.semantic_type == SemanticType.CHECK_RANGE


def test_layer2_pattern_match() -> None:
    result = run_pipeline(_col("email"))
    assert result.semantic_type == SemanticType.EMAIL
    assert result.layer == 2


def test_layer3_token_signal_for_compound_name() -> None:
    result = run_pipeline(_col("homeZipcode"))
    assert result.semantic_type == SemanticType.POSTAL_CODE
    assert result.layer == 3


def test_layer5_fallback_always_returns() -> None:
    result = layer_type_fallback(_col("whatever", sql_type="INTEGER"))
    assert result.semantic_type == SemanticType.TYPE_FALLBACK
    assert result.layer == 5


def test_datetime_fallback_has_higher_confidence() -> None:
    assert layer_type_fallback(_col("ts", sql_type="TIMESTAMP")).confidence == 0.6
    assert layer_type_fallback(_col("blob", sql_type="VARCHAR")).confidence == 0.5
