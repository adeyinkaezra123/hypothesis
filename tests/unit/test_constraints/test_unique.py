"""Tests for the unique-constraint handler."""

import itertools

import pytest

from hypothesis.constraints.unique import UniqueConstraintHandler
from hypothesis.core.exceptions import UniqueConstraintError


def test_returns_distinct_values() -> None:
    handler = UniqueConstraintHandler()
    counter = itertools.count()
    values = [handler.ensure_unique("users.id", lambda: next(counter)) for _ in range(5)]
    assert values == [0, 1, 2, 3, 4]


def test_regenerates_on_collision() -> None:
    handler = UniqueConstraintHandler()
    # factory yields a duplicate first, then a fresh value.
    sequence = iter([7, 7, 8])
    handler.ensure_unique("t.c", lambda: 7)  # seed "7" as seen
    assert handler.ensure_unique("t.c", lambda: next(sequence)) == 8


def test_raises_after_max_attempts() -> None:
    handler = UniqueConstraintHandler(max_attempts=3)
    handler.ensure_unique("t.c", lambda: "x")
    with pytest.raises(UniqueConstraintError):
        handler.ensure_unique("t.c", lambda: "x")


def test_keys_are_independent() -> None:
    handler = UniqueConstraintHandler()
    assert handler.ensure_unique("a", lambda: 1) == 1
    # Same value is fine under a different key.
    assert handler.ensure_unique("b", lambda: 1) == 1


def test_register_marks_value_used() -> None:
    handler = UniqueConstraintHandler(max_attempts=1)
    handler.register("t.c", "taken")
    with pytest.raises(UniqueConstraintError):
        handler.ensure_unique("t.c", lambda: "taken")


def test_reset_clears_tracking() -> None:
    handler = UniqueConstraintHandler()
    handler.ensure_unique("t.c", lambda: 1)
    handler.reset()
    assert handler.ensure_unique("t.c", lambda: 1) == 1
