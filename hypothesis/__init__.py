"""Hypothesis - Semantic Database Seeder

Automatically generate semantically-aware fake data for PostgreSQL and MySQL databases.
"""

__version__ = "0.1.0"

from hypothesis.core.connection import DatabaseConnection
from hypothesis.core.inspector import SchemaInspector
from hypothesis.core.generator import DataGenerator

__all__ = [
    "DatabaseConnection",
    "SchemaInspector",
    "DataGenerator",
]
