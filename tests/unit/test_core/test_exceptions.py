"""Tests for the exception hierarchy."""

import pytest

from hypothesis.core import exceptions as exc

_ALL_ERRORS = [
    exc.ConnectionError,
    exc.SchemaIntrospectionError,
    exc.ClassificationError,
    exc.GenerationError,
    exc.UniqueConstraintError,
    exc.ForeignKeyError,
    exc.InsertionError,
    exc.ConfigurationError,
    exc.CircularDependencyError,
]


@pytest.mark.parametrize("error_cls", _ALL_ERRORS)
def test_all_derive_from_base(error_cls: type[Exception]) -> None:
    assert issubclass(error_cls, exc.HypothesisError)


def test_generation_subfamily() -> None:
    assert issubclass(exc.UniqueConstraintError, exc.GenerationError)
    assert issubclass(exc.ForeignKeyError, exc.GenerationError)


def test_can_catch_whole_family_via_base() -> None:
    with pytest.raises(exc.HypothesisError):
        raise exc.ConnectionError("connection refused")


def test_message_is_preserved() -> None:
    err = exc.InsertionError("batch 3 failed")
    assert str(err) == "batch 3 failed"
