"""Constraint handlers for data generation (foreign keys, uniqueness)."""

from hypothesis.constraints.foreign_keys import ForeignKeyResolver
from hypothesis.constraints.unique import UniqueConstraintHandler

__all__ = ["ForeignKeyResolver", "UniqueConstraintHandler"]
