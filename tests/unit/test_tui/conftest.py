"""Shared fixtures for the inspect TUI tests."""

from __future__ import annotations

import pytest

from hypothesis.core.graph import DependencyGraph
from hypothesis.core.inspection import InspectionResult, InspectionSummary
from hypothesis.core.models import ColumnSchema, ForeignKey, TableSchema
from hypothesis.mapping.types import ClassificationResult, SemanticType


def _classification(
    column: ColumnSchema,
    semantic_type: SemanticType,
    *,
    confidence: float = 0.9,
    needs_review: bool = False,
    reasoning: str = "",
    matched_pattern: str | None = None,
) -> ClassificationResult:
    return ClassificationResult(
        column=column,
        semantic_type=semantic_type,
        confidence=confidence,
        faker_provider="word",
        matched_layer=2,
        needs_review=needs_review,
        reasoning=reasoning,
        matched_pattern=matched_pattern,
    )


def build_sample_result() -> InspectionResult:
    """A small users/posts schema with one foreign key and one review column."""
    user_id = ColumnSchema(
        "id",
        "users",
        "INTEGER",
        int,
        nullable=False,
        is_primary_key=True,
        is_auto_increment=True,
    )
    email = ColumnSchema("email", "users", "VARCHAR(255)", str, nullable=False, is_unique=True)
    post_id = ColumnSchema("id", "posts", "INTEGER", int, nullable=False, is_primary_key=True)
    user_fk = ColumnSchema(
        "user_id",
        "posts",
        "INTEGER",
        int,
        nullable=False,
        is_foreign_key=True,
    )
    title = ColumnSchema("title", "posts", "VARCHAR(200)", str)
    users = TableSchema(
        name="users",
        columns=[user_id, email],
        primary_key=["id"],
    )
    posts = TableSchema(
        name="posts",
        columns=[post_id, user_fk, title],
        primary_key=["id"],
        foreign_keys=[ForeignKey("posts", "user_id", "users", "id")],
    )
    graph = DependencyGraph(["users", "posts"])
    graph.build_from_foreign_keys(posts.foreign_keys)
    classifications = {
        "users": {
            "id": _classification(user_id, SemanticType.ID),
            "email": _classification(email, SemanticType.EMAIL),
        },
        "posts": {
            "id": _classification(post_id, SemanticType.ID),
            "user_id": _classification(user_fk, SemanticType.FOREIGN_KEY),
            "title": _classification(
                title,
                SemanticType.TYPE_FALLBACK,
                confidence=0.4,
                needs_review=True,
                reasoning="No semantic pattern matched; fell back to the SQL type VARCHAR.",
            ),
        },
    }
    return InspectionResult(
        tables=[users, posts],
        classifications=classifications,
        graph=graph,
        insertion_order=["users", "posts"],
        cycles=[],
        summary=InspectionSummary(
            table_count=2,
            column_count=5,
            foreign_key_count=1,
            low_confidence_count=1,
        ),
    )


@pytest.fixture
def sample_result() -> InspectionResult:
    return build_sample_result()
