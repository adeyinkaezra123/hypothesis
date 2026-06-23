# Implementation Plan: Semantic Database Seeder MVP

**Branch**: `001-core-mvp` | **Date**: 2026-01-16 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-core-mvp/spec.md`

## Summary

Build a production-ready CLI tool that automatically generates semantically-aware fake data for PostgreSQL and MySQL databases. The tool introspects database schemas, intelligently maps column names to appropriate data generators using a 5-layer classification pipeline, and generates realistic test data while respecting all database constraints.

**Key Technical Approach:**
- SQLAlchemy 2.x for schema reflection and database operations
- Layered classification pipeline: Schema Constraints → Pattern Matching → Token Analysis → Table Context → Type Fallback
- Confidence scoring (0.0-1.0) to flag low-confidence mappings for user review
- Batch inserts with streaming generation for performance (10K+ rows/sec target)
- Dual interface: Library-first with CLI wrapper via Typer

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: SQLAlchemy 2.x, Typer, Rich, Faker, Pydantic, PyYAML  
**Storage**: PostgreSQL 12+, MySQL 8.0+ (target databases, not internal storage)  
**Testing**: pytest with pytest-cov, Docker containers for integration tests  
**Target Platform**: Linux, macOS, Windows (cross-platform CLI)  
**Project Type**: Single project (Python package with CLI)  
**Performance Goals**: 10K rows/sec (simple), 5K rows/sec (with FKs), 1M rows < 5 min  
**Constraints**: Memory < 500MB for 1M rows, batch size configurable (default 1000)  
**Scale/Scope**: Typical schema: 10-20 tables, 5-100 columns per table

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| **I. Dual Interface** | Library-first, CLI wrapper | ✅ PASS | Core in `hypothesis/core/`, `hypothesis/mapping/`, `hypothesis/constraints/`; CLI in `hypothesis/cli/` |
| **II. Semantic Intelligence** | 80%+ accuracy, multi-tier matching | ✅ PASS | 5-layer pipeline defined, 85% accuracy target in spec |
| **III. Test-Driven Development** | TDD, 85%+ coverage | ✅ PASS | pytest with integration tests, coverage gate in CI |
| **IV. Performance** | 10K rows/sec, < 500MB memory | ✅ PASS | Streaming generation, batch inserts, explicit targets |
| **V. Graceful Degradation** | Fallbacks, clear errors | ✅ PASS | Type fallback layer, retry logic, contextual errors |
| **Tech Stack** | Python 3.11+, SQLAlchemy 2.x, Typer, Rich, Faker, Pydantic | ✅ PASS | Exact match with user input |
| **Code Quality** | mypy strict, ruff, black, 85% coverage | ✅ PASS | Already configured in pyproject.toml |

**Gate Result: ✅ PASS** - All constitution principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/001-core-mvp/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (internal API contracts)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
hypothesis/
├── __init__.py                    # Package exports, version
├── __main__.py                    # Entry point for `python -m hypothesis`
│
├── cli/                           # CLI layer (Typer wrapper)
│   ├── __init__.py
│   ├── app.py                     # Main Typer app, version, help
│   ├── output.py                  # Rich formatters (table, json, markdown)
│   └── commands/
│       ├── __init__.py
│       ├── inspect.py             # `hypothesis inspect` command
│       ├── analyze.py             # `hypothesis analyze` command (NEW)
│       ├── generate.py            # `hypothesis generate` command
│       └── validate.py            # `hypothesis validate` command
│
├── core/                          # Core library (database operations)
│   ├── __init__.py
│   ├── connection.py              # ✅ IMPLEMENTED - DatabaseConnection class
│   ├── connection_builder.py      # ✅ IMPLEMENTED - Connection string builder
│   ├── inspector.py               # Schema introspection (SchemaInspector)
│   ├── generator.py               # Data generation engine
│   ├── inserter.py                # Bulk insert with batching
│   └── graph.py                   # Dependency graph (topological sort)
│
├── mapping/                       # Semantic classification
│   ├── __init__.py
│   ├── classifier.py              # Main ColumnClassifier orchestrator
│   ├── pipeline.py                # LayeredPipeline implementation
│   ├── patterns.py                # Pattern definitions (30+ semantic types)
│   ├── tokenizer.py               # Compound name tokenization
│   ├── types.py                   # SQL type to Faker mapping
│   └── confidence.py              # Confidence score calculation
│
├── constraints/                   # Constraint handling
│   ├── __init__.py
│   ├── foreign_keys.py            # FK resolution, parent ID caching
│   ├── unique.py                  # Unique constraint tracking, retry
│   ├── check.py                   # CHECK constraint parsing
│   └── self_reference.py          # Two-pass generation for self-refs
│
├── config/                        # Configuration
│   ├── __init__.py
│   ├── parser.py                  # ✅ IMPLEMENTED - YAML parsing, env vars
│   ├── credentials.py             # ✅ IMPLEMENTED - .pgpass, .my.cnf
│   ├── models.py                  # Pydantic config models
│   └── generator.py               # Config file generator (analyze command)
│
└── utils/                         # Utilities
    ├── __init__.py
    ├── logging.py                 # ✅ IMPLEMENTED - Logging with redaction
    └── batch.py                   # Batching utilities

tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── fixtures/
│   ├── __init__.py
│   ├── configs/                   # ✅ IMPLEMENTED - Sample configs
│   │   └── sample_configs.py
│   └── schemas/                   # Test SQL schemas
│       ├── __init__.py
│       ├── simple.sql             # Tables with no FKs
│       ├── relationships.sql      # Parent-child FKs
│       ├── complex.sql            # Self-refs, circular FKs
│       └── all_types.sql          # All supported data types
├── unit/
│   ├── __init__.py
│   ├── test_config/               # ✅ IMPLEMENTED - Config tests
│   ├── test_core/
│   │   ├── test_connection.py     # Connection class tests
│   │   ├── test_connection_builder.py  # ✅ IMPLEMENTED
│   │   ├── test_inspector.py      # Schema inspection tests
│   │   └── test_graph.py          # Dependency graph tests
│   ├── test_mapping/
│   │   ├── test_classifier.py     # Classification pipeline tests
│   │   ├── test_patterns.py       # Pattern matching tests
│   │   ├── test_tokenizer.py      # Tokenization tests
│   │   └── test_confidence.py     # Confidence scoring tests
│   └── test_constraints/
│       ├── test_foreign_keys.py
│       ├── test_unique.py
│       └── test_check.py
└── integration/
    ├── __init__.py
    ├── conftest.py                # Docker container fixtures
    ├── test_postgres.py           # PostgreSQL integration
    ├── test_mysql.py              # MySQL integration
    └── test_end_to_end.py         # Full workflow tests
```

**Structure Decision**: Single Python package following the existing project layout. The structure separates concerns into:
- `cli/` - Thin CLI wrapper (no business logic per constitution)
- `core/` - Database operations and generation engine
- `mapping/` - Semantic classification pipeline
- `constraints/` - Constraint handling logic
- `config/` - Configuration management (partially implemented)

## Complexity Tracking

> No constitution violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | — | — |

---

## Phase 0: Research Summary

All technical decisions are resolved based on the spec, constitution, and user input. No external research required.

See [research.md](./research.md) for detailed decisions and rationale.

---

## Phase 1: Design Artifacts

### Artifacts Generated

1. **[research.md](./research.md)** - Technical decisions and rationale
2. **[data-model.md](./data-model.md)** - Entity definitions and relationships
3. **[contracts/internal-api.md](./contracts/internal-api.md)** - Internal library API contracts
4. **[quickstart.md](./quickstart.md)** - Developer quickstart guide

---

## Implementation Phases

### Phase A: Complete Foundation (P1 - Inspect Command)
**Dependencies**: None  
**Delivers**: User Story 1 (Inspect Database Schema)

1. Schema introspection (`core/inspector.py`)
2. Dependency graph builder (`core/graph.py`)
3. CLI inspect command with Rich output
4. JSON/Markdown output formatters

### Phase B: Classification Pipeline (P2 - Semantic Recognition)
**Dependencies**: Phase A  
**Delivers**: User Story 3 (Semantic Column Recognition)

1. Pattern definitions (`mapping/patterns.py`)
2. Column classifier (`mapping/classifier.py`)
3. Tokenizer for compound names (`mapping/tokenizer.py`)
4. Confidence scoring (`mapping/confidence.py`)
5. Type mapper (`mapping/types.py`)

### Phase C: Data Generation Engine (P1 - Generate Command)
**Dependencies**: Phase A, Phase B  
**Delivers**: User Story 2 (Generate Basic Test Data)

1. Data generator (`core/generator.py`)
2. Bulk inserter (`core/inserter.py`)
3. FK constraint handler (`constraints/foreign_keys.py`)
4. Unique constraint handler (`constraints/unique.py`)
5. CLI generate command

### Phase D: Analyze Command (P2 - Config Generation)
**Dependencies**: Phase B  
**Delivers**: User Story 1.5 (Analyze Schema)

1. Config generator (`config/generator.py`)
2. CLI analyze command
3. Config update/merge logic

### Phase E: Advanced Features (P3)
**Dependencies**: Phase C  
**Delivers**: User Stories 5, 6

1. Dry run mode
2. Truncate/append modes
3. Self-referential FK handling
4. CHECK constraint parsing

### Phase F: Polish & Documentation
**Dependencies**: All previous phases

1. Error message improvements
2. README with examples
3. Performance benchmarking
4. Integration tests completion
