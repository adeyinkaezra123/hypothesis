<!--
  Sync Impact Report
  ==================
  Version Change: 0.0.0 → 1.0.0
  Bump Rationale: Initial constitution creation (MAJOR)
  
  Added Sections:
    - I. Dual Interface Architecture
    - II. Semantic Intelligence
    - III. Test-Driven Development
    - IV. Performance & Scalability
    - V. Graceful Degradation
    - Technical Standards
    - Quality Gates
    - Governance
  
  Templates Requiring Updates:
    ✅ plan-template.md - Constitution Check section compatible
    ✅ spec-template.md - Requirements format aligned
    ✅ tasks-template.md - Task categorization compatible
  
  Follow-up TODOs: None
-->

# Hypothesis Constitution

## Core Principles

### I. Dual Interface Architecture

Hypothesis MUST function as both a standalone CLI tool and an importable Python library.
All core functionality MUST be exposed through the library interface first, with the CLI
serving as a thin wrapper via Typer. This ensures testability, composability, and enables
programmatic usage in scripts and pipelines.

**Non-negotiables:**
- Core logic lives in `hypothesis/core/`, `hypothesis/mapping/`, `hypothesis/constraints/`
- CLI commands in `hypothesis/cli/` import and orchestrate library functions
- No business logic in CLI command handlers

### II. Semantic Intelligence

The tool's primary value proposition is generating contextually-appropriate fake data through
semantic column name matching. Hypothesis MUST maintain a robust mapping system that infers
data types from column names with at least 80% accuracy on common patterns.

**Non-negotiables:**
- Multi-tier matching: exact match → substring match → pattern match → type fallback
- All default mappings MUST be overridable via configuration
- New semantic mappings MUST NOT break existing configurations
- Custom user mappings MUST take priority over defaults

### III. Test-Driven Development

All features MUST be developed using TDD methodology. Tests are written first, verified to
fail, then implementation proceeds. This is non-negotiable for any code that handles database
operations, constraint management, or data generation.

**Non-negotiables:**
- Unit tests for all mapping and constraint logic
- Integration tests against real PostgreSQL and MySQL databases (Docker containers)
- Contract tests for public library API
- Test coverage MUST remain above 85%

### IV. Performance & Scalability

Hypothesis MUST meet production-grade performance requirements for data generation at scale.
The tool MUST generate 1M rows in under 5 minutes for typical schemas.

**Non-negotiables:**
- 10K+ rows/sec for simple tables (no foreign keys)
- 5K+ rows/sec for tables with foreign key relationships
- Memory usage MUST stay under 500MB for 1M row generation
- Batch processing with configurable batch sizes (default: 1000)
- Streaming generation to avoid memory exhaustion

### V. Graceful Degradation

When encountering unsupported features, unknown data types, or constraint violations,
Hypothesis MUST fail gracefully with clear, actionable error messages. The tool SHOULD
continue operation when possible rather than halting entirely.

**Non-negotiables:**
- Unsupported data types fall back to generic generators with logged warnings
- Circular FK dependencies: detect, warn, and attempt resolution via nullable columns
- Unique constraint collisions: retry logic (max 10 attempts) before failing
- All errors MUST include context: table name, column name, constraint type

## Technical Standards

### Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Python | 3.11+ | Modern type hints, performance improvements |
| CLI Framework | Typer | Type-safe, modern, excellent developer experience |
| Database | SQLAlchemy 2.x | Industry-standard ORM with reflection capabilities |
| Data Generation | Faker | Comprehensive fake data providers |
| TUI | Rich | Beautiful terminal output, progress bars |
| Package Management | uv | Fast, modern Python packaging |
| Validation | Pydantic | Config parsing and validation |

### Database Support

- **Tier 1 (Full Support):** PostgreSQL 12+, MySQL 8.0+
- **Tier 2 (Planned):** SQLite (future)
- **Unsupported:** SQL Server, Oracle (no current plans)

### Code Quality

- **Type Safety:** 100% mypy strict mode compliance
- **Linting:** ruff for linting, black for formatting
- **Documentation:** All public APIs MUST have docstrings
- **Commit Style:** Conventional Commits (feat:, fix:, docs:, etc.)

## Quality Gates

### Pre-Merge Requirements

All pull requests MUST pass:
1. All unit and integration tests
2. mypy strict type checking
3. ruff linting with zero errors
4. black formatting compliance
5. Test coverage ≥ 85%

### Pre-Release Requirements

1. All pre-merge requirements
2. Manual testing against PostgreSQL and MySQL
3. Performance benchmarks meet targets
4. Documentation updated for new features
5. CHANGELOG.md updated

## Governance

### Amendment Process

1. Amendments to this constitution MUST be documented with rationale
2. Breaking changes to principles require MAJOR version bump
3. New principles or expansions require MINOR version bump
4. Clarifications and wording changes are PATCH bumps

### Compliance

- All code reviews MUST verify compliance with these principles
- Constitution violations block merge
- Exceptions require explicit documentation with justification in PR

### Runtime Guidance

For day-to-day development decisions, consult:
- `README.md` for project overview and quickstart
- `docs/` for detailed guides
- Implementation plans in `.specify/specs/` for feature context

**Version**: 1.0.0 | **Ratified**: 2026-01-11 | **Last Amended**: 2026-01-11
