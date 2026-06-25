"""Foreign-key value resolution by caching parent primary keys."""

from __future__ import annotations

import random
from typing import Any

from sqlalchemy import Engine, text

from hypothesis.core.exceptions import ForeignKeyError


class ForeignKeyResolver:
    """Caches parent ids in memory and selects valid foreign-key values.

    Selection uses a private :class:`random.Random` seeded per resolver, so the
    global RNG is never touched and ``--seed`` runs are reproducible.
    """

    def __init__(self, engine: Engine, sample_size: int = 1000, seed: int | None = None) -> None:
        self.engine = engine
        self.sample_size = sample_size
        self._rng = random.Random(seed)
        self._cache: dict[str, list[Any]] = {}

    @staticmethod
    def _key(parent_table: str, parent_column: str) -> str:
        return f"{parent_table}.{parent_column}"

    def cache_parent_ids(self, parent_table: str, parent_column: str) -> list[Any]:
        """Query and cache up to ``sample_size`` ids from a parent column.

        The query is ``ORDER BY`` the id column: an unspecified row order (e.g.
        Postgres heap order) would otherwise vary between runs and defeat
        ``--seed`` reproducibility of foreign-key selection.
        """
        with self.engine.connect() as conn:
            result = conn.execute(
                text(
                    f"SELECT {parent_column} FROM {parent_table} "
                    f"ORDER BY {parent_column} LIMIT :limit"
                ),
                {"limit": self.sample_size},
            )
            ids = [row[0] for row in result]
        self._cache[self._key(parent_table, parent_column)] = ids
        return ids

    def get_cached_ids(self, parent_table: str, parent_column: str) -> list[Any] | None:
        """Return cached ids for a parent column, or ``None`` if not cached."""
        return self._cache.get(self._key(parent_table, parent_column))

    def select_fk_value(
        self, parent_table: str, parent_column: str, distribution: str = "uniform"
    ) -> Any:
        """Select a foreign-key value, caching parent ids on first use.

        Raises:
            ForeignKeyError: if the parent table has no rows to reference.
        """
        ids = self.get_cached_ids(parent_table, parent_column)
        if ids is None:
            ids = self.cache_parent_ids(parent_table, parent_column)
        if not ids:
            raise ForeignKeyError(
                f"No parent rows available for {self._key(parent_table, parent_column)}; "
                f"insert '{parent_table}' before its children"
            )
        return self._select(ids, distribution)

    def _select(self, ids: list[Any], distribution: str) -> Any:
        """Pick an id according to a distribution (approximate for non-uniform)."""
        count = len(ids)
        if distribution == "exponential":
            # Bias toward the front so a few parents accumulate many children.
            return ids[min(int(self._rng.expovariate(1.0) / 3 * count), count - 1)]
        if distribution == "normal":
            return ids[min(max(int(self._rng.gauss(count / 2, count / 6)), 0), count - 1)]
        return self._rng.choice(ids)
