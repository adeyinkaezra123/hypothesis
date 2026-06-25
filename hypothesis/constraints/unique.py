"""Unique-constraint tracking with regeneration on collision."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from hypothesis.core.exceptions import UniqueConstraintError


class UniqueConstraintHandler:
    """Tracks generated values per column key and retries on collision.

    Values are tracked in Python sets (O(1) membership). When a freshly
    generated value collides, the factory is called again up to ``max_attempts``
    times before giving up with :class:`UniqueConstraintError`.
    """

    def __init__(self, max_attempts: int = 10) -> None:
        self.max_attempts = max_attempts
        self._seen: dict[str, set[Any]] = {}

    def reset(self) -> None:
        """Forget all tracked values."""
        self._seen.clear()

    def register(self, key: str, value: Any) -> None:
        """Record an externally produced value as already used (e.g. existing rows)."""
        self._seen.setdefault(key, set()).add(value)

    def ensure_unique(self, key: str, factory: Callable[[], Any]) -> Any:
        """Return a value from ``factory()`` not yet seen for ``key``.

        Raises:
            UniqueConstraintError: if no unique value is produced within
                ``max_attempts`` calls.
        """
        seen = self._seen.setdefault(key, set())
        for _ in range(self.max_attempts):
            value = factory()
            if value not in seen:
                seen.add(value)
                return value
        raise UniqueConstraintError(
            f"Could not generate a unique value for '{key}' after {self.max_attempts} attempts"
        )
