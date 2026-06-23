"""Exception hierarchy for Hypothesis.

Every custom exception derives from :class:`HypothesisError`, so callers can
catch the entire family with a single ``except HypothesisError`` clause while
still being able to target specific failures.
"""


class HypothesisError(Exception):
    """Base exception for all Hypothesis errors."""


class ConnectionError(HypothesisError):
    """Database connection failed.

    Note: intentionally shadows the builtin ``ConnectionError`` within this
    package so the error surface is uniform under ``HypothesisError``.
    """


class SchemaIntrospectionError(HypothesisError):
    """Schema reflection failed."""


class ClassificationError(HypothesisError):
    """Column classification failed."""


class GenerationError(HypothesisError):
    """Data generation failed."""


class UniqueConstraintError(GenerationError):
    """Could not generate a unique value after the maximum retries."""


class ForeignKeyError(GenerationError):
    """Foreign key resolution failed."""


class InsertionError(HypothesisError):
    """Batch insert failed."""


class ConfigurationError(HypothesisError):
    """Configuration parsing or validation failed."""


class CircularDependencyError(HypothesisError):
    """Circular foreign key dependencies detected."""
