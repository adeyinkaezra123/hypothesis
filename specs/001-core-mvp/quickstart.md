# Developer Quickstart: Semantic Database Seeder MVP

**Feature**: 001-core-mvp  
**Date**: 2026-01-16

## Prerequisites

- Python 3.11+
- uv (Python package manager)
- Docker (for integration tests)
- PostgreSQL or MySQL database (for manual testing)

## Project Setup

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/adeyinkaezra123/hypothesis.git
cd hypothesis

# Install dependencies with uv
uv sync

# Verify installation
uv run hypothesis --version
```

### 2. Activate Virtual Environment

```bash
# Option A: Use uv run prefix for commands
uv run pytest tests/

# Option B: Activate venv directly
source .venv/bin/activate
hypothesis --version
```

## Development Workflow

### Running Tests

```bash
# All unit tests
uv run pytest tests/unit/ -v

# Specific test file
uv run pytest tests/unit/test_mapping/test_classifier.py -v

# With coverage
uv run pytest tests/unit/ --cov=hypothesis --cov-report=term-missing

# Integration tests (requires Docker)
docker compose up -d postgres mysql
uv run pytest tests/integration/ -v
```

### Code Quality

```bash
# Run all checks
uv run ruff check hypothesis/ tests/
uv run mypy hypothesis/
uv run black --check hypothesis/ tests/

# Auto-fix formatting
uv run black hypothesis/ tests/
uv run ruff check --fix hypothesis/ tests/
```

### Test Database Setup

```bash
# Start PostgreSQL and MySQL containers
docker compose up -d

# PostgreSQL: localhost:5432, user configured in compose
# MySQL: localhost:3306, user configured in compose

# Stop containers
docker compose down
```

## Key Components

### 1. Database Connection

```python
import os

from hypothesis.core.connection import DatabaseConnection
from hypothesis.core.connection_builder import build_connection_string

# Build connection string from components
conn_str = build_connection_string(
    dialect="postgresql",
    host="localhost",
    port=5432,
    database="testdb",
    username="user",
    password=os.environ["HYPOTHESIS_TEST_DATABASE_PASSWORD"]
)

# Create connection with pooling
conn = DatabaseConnection(conn_str)
assert conn.validate()
print(f"Connected to {conn.get_dialect()}")
conn.close()
```

### 2. Schema Inspection (TODO)

```python
from hypothesis.core.inspector import SchemaInspector

inspector = SchemaInspector(conn.engine)
inspector.reflect_schema()

for table in inspector.get_tables():
    print(f"Table: {table.name}")
    for col in table.columns:
        print(f"  {col.name}: {col.sql_type}")
```

### 3. Column Classification (TODO)

```python
from hypothesis.mapping.classifier import ColumnClassifier

classifier = ColumnClassifier()

for table in inspector.get_tables():
    results = classifier.classify_table(table)
    for col_name, result in results.items():
        status = "⚠️" if result.needs_review else "✅"
        print(f"{status} {col_name}: {result.semantic_type} ({result.confidence:.2f})")
```

### 4. Data Generation (TODO)

```python
from hypothesis.core.generator import DataGenerator
from hypothesis.core.inserter import BulkInserter

generator = DataGenerator(faker_locale="en_US")
inserter = BulkInserter(conn.engine, batch_size=1000)

# Generate and insert
rows = generator.generate_batch(table, classifications, count=1000, ...)
result = inserter.insert_batch(table.name, rows)
print(f"Inserted {result.rows_inserted} rows")
```

## CLI Usage

### Inspect Schema

```bash
# Inspect all tables
hypothesis inspect postgresql://user@localhost/testdb

# Inspect specific tables
hypothesis inspect "postgresql://user@localhost/testdb" --tables users --tables orders

# JSON output
hypothesis inspect "postgresql://user@localhost/testdb" --format json
```

### Analyze and Generate Config (TODO)

```bash
# Generate config file
hypothesis analyze "postgresql://user@localhost/testdb" --output seed-config.yml

# Update existing config (add new tables, preserve overrides)
hypothesis analyze "postgresql://user@localhost/testdb" --output seed-config.yml --update
```

### Generate Data (TODO)

```bash
# Generate 1000 rows per table
hypothesis generate "postgresql://user@localhost/testdb" --rows 1000

# Use config file
hypothesis generate "postgresql://user@localhost/testdb" --config seed-config.yml

# Dry run (show what would be generated)
hypothesis generate "postgresql://user@localhost/testdb" --dry-run

# Truncate existing data first
hypothesis generate "postgresql://user@localhost/testdb" --truncate
```

## Configuration File Format

```yaml
# seed-config.yml

defaults:
  rows: 1000
  batch_size: 1000
  locale: en_US
  null_probability: 0.1

tables:
  users:
    rows: 5000  # Override default
    columns:
      email:
        provider: faker.email
        unique: true
      age:
        provider: faker.random_int
        min: 18
        max: 100
      status:
        values: [active, inactive, pending]
        weights: [0.7, 0.2, 0.1]
    foreign_keys:
      department_id:
        distribution: exponential  # Power law distribution
        
  orders:
    columns:
      user_id:
        # FK auto-detected, uses cached parent IDs
      total_amount:
        provider: faker.pydecimal
        min: 10
        max: 10000
        
  employees:
    self_references:
      manager_id:
        strategy: two_pass
        root_probability: 0.1  # 10% are top-level managers

# Warnings (auto-generated, for review)
warnings:
  - "Low confidence (0.45): users.status - using type fallback"
  - "CHECK constraint on orders.quantity could not be fully parsed"
```

## Architecture Overview

```
CLI Layer (hypothesis/cli/)
    │
    ▼
Library Layer (hypothesis/core/, hypothesis/mapping/, hypothesis/constraints/)
    │
    ▼
SQLAlchemy + Faker
    │
    ▼
PostgreSQL / MySQL
```

### Key Design Decisions

1. **Library-first**: All logic in library modules, CLI is thin wrapper
2. **Streaming generation**: Values generated on-demand, not pre-computed
3. **Batch inserts**: 1000 rows per INSERT for performance
4. **Confidence scoring**: Low-confidence mappings flagged for review
5. **Graceful degradation**: Unknown types fall back to generic generators

## Troubleshooting

### Connection Issues

```bash
# Test connection manually
uv run python -c "
from hypothesis.core.connection import DatabaseConnection
conn = DatabaseConnection('postgresql://user@localhost/testdb')
print('Valid:', conn.validate())
"
```

### Type Errors

```bash
# Run mypy with verbose output
uv run mypy hypothesis/ --show-error-codes --pretty
```

### Test Failures

```bash
# Run failing test with verbose output
uv run pytest tests/unit/test_mapping/test_classifier.py -vv --tb=long
```

## File Locations

| Purpose | Location |
|---------|----------|
| Main package | `hypothesis/` |
| CLI commands | `hypothesis/cli/commands/` |
| Core library | `hypothesis/core/` |
| Semantic mapping | `hypothesis/mapping/` |
| Constraint handlers | `hypothesis/constraints/` |
| Configuration | `hypothesis/config/` |
| Unit tests | `tests/unit/` |
| Integration tests | `tests/integration/` |
| Feature specs | `specs/001-core-mvp/` |
| Documentation | `docs/` |
