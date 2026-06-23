"""Column-name tokenization and token scoring for compound names."""

from __future__ import annotations

import re

from hypothesis.mapping.patterns import find_pattern_matches
from hypothesis.mapping.types import SemanticType

# Boundaries between a lowercase/digit and an uppercase letter (fooBar), and
# between an acronym and a following word (HTTPServer -> HTTP Server).
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_SEPARATORS = re.compile(r"[^a-zA-Z0-9]+")


def tokenize(name: str) -> list[str]:
    """Split a column name into lowercase tokens.

    Handles snake_case, camelCase, PascalCase, and kebab-case, e.g.
    ``customerBillingAddress`` -> ``["customer", "billing", "address"]``.
    """
    spaced = _CAMEL_BOUNDARY.sub("_", name)
    return [token.lower() for token in _SEPARATORS.split(spaced) if token]


def score_tokens(tokens: list[str]) -> list[tuple[SemanticType, float]]:
    """Score each token by its best exact/contains pattern match."""
    scored: list[tuple[SemanticType, float]] = []
    for token in tokens:
        matches = find_pattern_matches(token)
        if matches:
            scored.append((matches[0].semantic_type, matches[0].confidence))
    return scored


def best_token_signal(name: str) -> tuple[SemanticType, float] | None:
    """Return the strongest semantic signal among a compound name's tokens.

    Uses the max-confidence token (per the research decision), or ``None`` when
    no token carries a recognizable signal.
    """
    scored = score_tokens(tokenize(name))
    if not scored:
        return None
    return max(scored, key=lambda signal: signal[1])
