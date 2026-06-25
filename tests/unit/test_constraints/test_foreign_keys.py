"""Tests for the foreign-key resolver against in-memory SQLite."""

from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine, text

from hypothesis.constraints.foreign_keys import ForeignKeyResolver
from hypothesis.core.exceptions import ForeignKeyError


@pytest.fixture
def engine() -> Iterator[Engine]:
    eng = create_engine("sqlite:///:memory:")
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        conn.execute(text("INSERT INTO users (id) VALUES (1), (2), (3), (4), (5)"))
        conn.execute(text("CREATE TABLE empty (id INTEGER PRIMARY KEY)"))
    yield eng
    eng.dispose()


def test_cache_parent_ids(engine: Engine) -> None:
    resolver = ForeignKeyResolver(engine)
    ids = resolver.cache_parent_ids("users", "id")
    assert sorted(ids) == [1, 2, 3, 4, 5]
    assert resolver.get_cached_ids("users", "id") == ids


def test_get_cached_ids_returns_none_before_caching(engine: Engine) -> None:
    assert ForeignKeyResolver(engine).get_cached_ids("users", "id") is None


def test_select_returns_valid_parent_value(engine: Engine) -> None:
    resolver = ForeignKeyResolver(engine)
    for _ in range(20):
        assert resolver.select_fk_value("users", "id") in {1, 2, 3, 4, 5}


def test_select_caches_lazily(engine: Engine) -> None:
    resolver = ForeignKeyResolver(engine)
    resolver.select_fk_value("users", "id")
    assert resolver.get_cached_ids("users", "id") is not None


@pytest.mark.parametrize("distribution", ["uniform", "exponential", "normal"])
def test_distributions_stay_within_parent_set(engine: Engine, distribution: str) -> None:
    resolver = ForeignKeyResolver(engine)
    for _ in range(50):
        assert resolver.select_fk_value("users", "id", distribution) in {1, 2, 3, 4, 5}


def test_empty_parent_raises(engine: Engine) -> None:
    resolver = ForeignKeyResolver(engine)
    with pytest.raises(ForeignKeyError):
        resolver.select_fk_value("empty", "id")


def test_sample_size_limits_cache(engine: Engine) -> None:
    resolver = ForeignKeyResolver(engine, sample_size=2)
    assert len(resolver.cache_parent_ids("users", "id")) == 2
