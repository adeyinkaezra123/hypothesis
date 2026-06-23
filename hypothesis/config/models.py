"""Pydantic models for the generation configuration file.

These validate and normalize a user's YAML config (see
``specs/001-core-mvp/data-model.md`` for the entity definitions and validation
rules). Pydantic gives clear error messages on malformed config, which the
``validate`` command surfaces to the user.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ColumnConfig(BaseModel):
    """Per-column generation overrides."""

    provider: str | None = None
    values: list[Any] | None = None
    weights: list[float] | None = None
    unique: bool = False
    min: float | None = None
    max: float | None = None
    nullable_chance: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _check_weights(self) -> ColumnConfig:
        if self.weights is not None:
            if self.values is not None and len(self.weights) != len(self.values):
                raise ValueError("`weights` must have the same length as `values`")
            total = sum(self.weights)
            if total <= 0:
                raise ValueError("`weights` must sum to a positive value")
            # Normalize so weights always sum to 1.0.
            if abs(total - 1.0) > 1e-9:
                self.weights = [w / total for w in self.weights]
        return self


class ForeignKeyConfig(BaseModel):
    """Per-foreign-key generation overrides."""

    distribution: Literal["uniform", "exponential", "normal"] = "uniform"
    sample_size: int = Field(default=1000, gt=0)


class SelfReferenceConfig(BaseModel):
    """Self-referential FK handling via the two-pass strategy."""

    column: str
    strategy: Literal["two_pass"] = "two_pass"
    root_probability: float = Field(default=0.1, ge=0.0, le=1.0)


class TableConfig(BaseModel):
    """Per-table generation overrides."""

    rows: int | None = Field(default=None, gt=0)
    skip: bool = False
    columns: dict[str, ColumnConfig] = Field(default_factory=dict)
    foreign_keys: dict[str, ForeignKeyConfig] = Field(default_factory=dict)


class ConfigWarning(BaseModel):
    """A warning emitted while building a config (e.g., unparseable CHECK)."""

    message: str
    table: str | None = None
    column: str | None = None
    constraint: str | None = None


class GenerationConfig(BaseModel):
    """Root configuration for a generation run."""

    default_rows: int = Field(default=1000, gt=0)
    batch_size: int = Field(default=1000, gt=0, le=100_000)
    locale: str = "en_US"
    null_probability: float = Field(default=0.1, ge=0.0, le=1.0)
    tables: dict[str, TableConfig] = Field(default_factory=dict)
    self_references: dict[str, SelfReferenceConfig] = Field(default_factory=dict)
    warnings: list[ConfigWarning] = Field(default_factory=list)
