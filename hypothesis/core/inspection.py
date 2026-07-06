"""Shared schema inspection workflow.

The CLI and TUI both need the same reflected schema, classifications, and
relationship summary. Keeping that workflow here prevents output-specific code
from duplicating database access and graph handling.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import create_engine

from hypothesis.core.graph import DependencyGraph
from hypothesis.core.inspector import SchemaInspector
from hypothesis.core.models import TableSchema
from hypothesis.mapping.classifier import ColumnClassifier
from hypothesis.mapping.types import ClassificationResult

ClassificationMap = dict[str, dict[str, ClassificationResult]]


@dataclass(frozen=True)
class InspectionSummary:
    """Small aggregate counts shown by human-facing renderers."""

    table_count: int
    column_count: int
    foreign_key_count: int
    low_confidence_count: int


@dataclass(frozen=True)
class InspectionResult:
    """Complete output of inspecting a database schema."""

    tables: list[TableSchema]
    classifications: ClassificationMap
    graph: DependencyGraph
    insertion_order: list[str]
    cycles: list[list[str]]
    summary: InspectionSummary


def inspect_database(
    connection_string: str, *, tables: list[str] | None = None
) -> InspectionResult:
    """Reflect and classify a database schema."""
    engine = create_engine(connection_string)
    try:
        inspector = SchemaInspector(engine)
        inspector.reflect_schema(tables=tables)
        schema_tables = inspector.get_tables()
        graph = inspector.get_dependency_graph()
    finally:
        engine.dispose()

    classifier = ColumnClassifier()
    classifications = classifier.classify_schema(schema_tables) if schema_tables else {}
    cycles = graph.detect_cycles()
    insertion_order = [] if cycles else graph.topological_sort()
    low_confidence = classifier.get_low_confidence_columns(classifications)
    summary = InspectionSummary(
        table_count=len(schema_tables),
        column_count=sum(len(table.columns) for table in schema_tables),
        foreign_key_count=sum(len(table.foreign_keys) for table in schema_tables),
        low_confidence_count=len(low_confidence),
    )
    return InspectionResult(
        tables=schema_tables,
        classifications=classifications,
        graph=graph,
        insertion_order=insertion_order,
        cycles=cycles,
        summary=summary,
    )
