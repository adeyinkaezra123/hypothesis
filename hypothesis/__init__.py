"""Hypothesis - Semantic Database Seeder

Automatically generate semantically-aware fake data for PostgreSQL and MySQL databases.
"""

from hypothesis.core.connection import DatabaseConnection
from hypothesis.core.connection_builder import build_connection_string, parse_connection_components
from hypothesis.core.inspector import SchemaInspector

# from hypothesis.core.generator import DataGenerator

__all__ = [
    "DatabaseConnection",
    "SchemaInspector",
    "build_connection_string",
    "parse_connection_components",
]


__version__ = "0.1.0"
