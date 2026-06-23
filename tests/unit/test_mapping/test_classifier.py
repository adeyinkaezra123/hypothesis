"""Tests for the ColumnClassifier orchestrator."""

from typing import Any

from hypothesis.core.models import ColumnSchema, TableSchema
from hypothesis.mapping.classifier import ColumnClassifier
from hypothesis.mapping.types import SemanticType


def _col(
    name: str,
    sql_type: str = "VARCHAR(255)",
    python_type: type = str,
    **kwargs: Any,
) -> ColumnSchema:
    return ColumnSchema(
        name=name, table_name="t", sql_type=sql_type, python_type=python_type, **kwargs
    )


def test_classify_email_high_confidence() -> None:
    result = ColumnClassifier().classify_column(_col("email"))
    assert result.semantic_type == SemanticType.EMAIL
    assert result.faker_provider == "email"
    assert result.confidence >= 0.9
    assert result.needs_review is False


def test_foreign_key_classified_at_layer_1() -> None:
    result = ColumnClassifier().classify_column(
        _col("user_id", sql_type="INTEGER", python_type=int, is_foreign_key=True)
    )
    assert result.semantic_type == SemanticType.FOREIGN_KEY
    assert result.matched_layer == 1
    assert result.confidence == 1.0
    assert result.is_foreign_key is True


def test_enum_outranks_pattern() -> None:
    result = ColumnClassifier().classify_column(
        _col("status", sql_type="ENUM", enum_values=["active", "inactive"])
    )
    assert result.semantic_type == SemanticType.ENUM_VALUE
    assert result.matched_layer == 1


def test_compound_name_resolved_via_tokens() -> None:
    result = ColumnClassifier().classify_column(_col("homeZipcode"))
    assert result.semantic_type == SemanticType.POSTAL_CODE
    assert result.matched_layer == 3


def test_unrecognized_column_falls_back_and_is_flagged() -> None:
    result = ColumnClassifier().classify_column(_col("data", sql_type="VARCHAR(50)"))
    assert result.semantic_type == SemanticType.TYPE_FALLBACK
    assert result.matched_layer == 5
    assert result.needs_review is True
    assert result.faker_provider == "pystr"


def test_fallback_uses_sql_type_specific_provider() -> None:
    result = ColumnClassifier().classify_column(_col("misc", sql_type="INTEGER", python_type=int))
    assert result.semantic_type == SemanticType.TYPE_FALLBACK
    assert result.faker_provider == "random_int"


def test_table_context_disambiguates_generic_name() -> None:
    result = ColumnClassifier().classify_column(_col("name"), table_context="products")
    assert result.semantic_type == SemanticType.NAME
    assert result.matched_layer == 4


def test_classify_table_and_low_confidence_collection() -> None:
    classifier = ColumnClassifier()
    table = TableSchema(name="users", columns=[_col("email"), _col("data")])
    results = {"users": classifier.classify_table(table)}
    assert set(results["users"]) == {"email", "data"}
    low_confidence_columns = {col for _, col, _ in classifier.get_low_confidence_columns(results)}
    assert "data" in low_confidence_columns
    assert "email" not in low_confidence_columns
