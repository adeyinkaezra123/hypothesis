# Tasks: Semantic Database Seeder MVP

**Input**: Design documents from `/specs/001-core-mvp/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

## Current Status (updated 2026-06-23)

**Pre-task foundation** (predates T-numbering, now committed):

- ✅ Database connection + pooling/validation (`core/connection.py`, `core/connection_builder.py`)
- ✅ Config parsing + env interpolation (`config/parser.py`) and credential files (`config/credentials.py`)
- ✅ Logging with secret redaction (`utils/logging.py`) — configured by the CLI entry point
- ✅ Typer CLI skeleton (`cli/app.py`) with the `inspect` subcommand wired
- ✅ Tests green (config parser, connection builder); coverage reporting now enabled via `uv run pytest`

**Formal task progress:** Phases 1–4 complete (T001–T043). The `hypothesis inspect` command
works end-to-end — table / JSON / markdown output, `--tables`, `--verbose`, insertion-order
display, semantic classifications, confidence indicators, and opt-in PostgreSQL dialect/CLI
integration tests — on top of the schema inspector and dependency graph. The source package and
tests pass mypy --strict, and the repository passes ruff.
**Phase 5 (US2 — the `generate` command) is next.**
The `generate` and `validate` command files are still to be (re)created by T055 and T068.

**Tests**: Constitution mandates TDD with 85%+ coverage. Unit tests are included for core components,
and pytest enforces the 85% coverage gate.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, etc.)
- All file paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Complete project initialization and foundational models

- [x] T001 [P] Create error hierarchy in hypothesis/core/exceptions.py (HypothesisError, ConnectionError, SchemaIntrospectionError, ClassificationError, GenerationError, InsertionError, ConfigurationError) — also added UniqueConstraintError, ForeignKeyError, CircularDependencyError per contract
- [x] T002 [P] Create dataclass models in hypothesis/core/models.py (TableSchema, ColumnSchema, ForeignKey, UniqueConstraint, CheckConstraint)
- [x] T003 [P] Create SemanticType enum in hypothesis/mapping/types.py with 60+ semantic types (Personal, Location, Business, Financial, Internet, Identifiers, Temporal, Content, File/Media, Color, Boolean, Numeric, Status/State, Constraint-derived, Fallback)
- [x] T003a [P] Create FakerMapping dataclass in hypothesis/mapping/types.py (provider, kwargs, post_process, compatible_sql_types)
- [x] T003b [P] Create SEMANTIC_TO_FAKER mapping dict in hypothesis/mapping/types.py - explicit Faker method for each SemanticType
- [x] T003c [P] Create SQL_TYPE_FALLBACK mapping dict in hypothesis/mapping/types.py for all SQL types (VARCHAR, TEXT, INTEGER, DECIMAL, BOOLEAN, DATE, UUID, JSON, etc.)
- [x] T004 [P] Create ClassificationResult dataclass in hypothesis/mapping/types.py
- [x] T005 [P] Create Pydantic config models in hypothesis/config/models.py (GenerationConfig, TableConfig, ColumnConfig, ForeignKeyConfig, SelfReferenceConfig)
- [x] T006 [P] Create Rich output formatters in hypothesis/cli/output.py (table, json, markdown renderers)
- [x] T007 [P] Create test fixtures SQL schemas in tests/fixtures/schemas/ (simple.sql, relationships.sql, complex.sql, all_types.sql)

**Checkpoint**: Core models and shared infrastructure ready for all user stories

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T008 Implement SchemaInspector.reflect_schema() in hypothesis/core/inspector.py (SQLAlchemy reflection for tables, columns, constraints)
- [x] T009 Implement SchemaInspector.get_tables() and get_table() in hypothesis/core/inspector.py
- [x] T010 Implement SchemaInspector.get_foreign_keys() in hypothesis/core/inspector.py
- [x] T011 Implement CHECK constraint extraction in hypothesis/core/inspector.py (parse simple ranges, IN values)
- [x] T012 Implement ENUM value extraction in hypothesis/core/inspector.py (PostgreSQL and MySQL) — surfaced via type.enums; verified by Postgres/MySQL integration tests (SQLite has no ENUM)
- [x] T013 [P] Write unit tests for SchemaInspector in tests/unit/test_core/test_inspector.py (in-memory SQLite)
- [x] T014 Implement DependencyGraph class in hypothesis/core/graph.py (build_from_foreign_keys, topological_sort, detect_cycles, get_layers)
- [x] T015 [P] Write unit tests for DependencyGraph in tests/unit/test_core/test_graph.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Inspect Database Schema (Priority: P1) 🎯 MVP

**Goal**: Users can connect to PostgreSQL/MySQL and view formatted schema with tables, columns, types, constraints, and relationships

**Independent Test**: Run `hypothesis inspect postgresql://...` and verify Rich table output shows all schema elements

### Tests for User Story 1

- [x] T016 [P] [US1] Write unit tests for inspect command logic in tests/unit/test_cli/test_inspect.py
- [x] T017 [P] [US1] Write integration test for PostgreSQL inspection — covered by tests/integration/test_inspect_cli_postgres.py (PostgreSQL CLI inspect, skipped without a DB URL); dialect ENUM reflection is covered by tests/integration/test_inspector_dialects.py

### Implementation for User Story 1

- [x] T018 [US1] Implement table output formatter in hypothesis/cli/output.py (render TableSchema as Rich table) — done in Phase 1 (T006)
- [x] T019 [US1] Implement JSON output formatter in hypothesis/cli/output.py (serialize to JSON) — done in Phase 1 (T006)
- [x] T020 [US1] Implement Markdown output formatter in hypothesis/cli/output.py (render as MD table) — done in Phase 1 (T006)
- [x] T021 [US1] Implement inspect command handler in hypothesis/cli/commands/inspect.py (connect, reflect, format, display)
- [x] T022 [US1] Add --format flag support (table|json|markdown) in hypothesis/cli/commands/inspect.py
- [x] T023 [US1] Add --tables filter flag in hypothesis/cli/commands/inspect.py
- [x] T024 [US1] Add --verbose flag showing FK relationships in hypothesis/cli/commands/inspect.py (short flag is -V to avoid clashing with global -v/--version)
- [x] T025 [US1] Add insertion order display in inspect output in hypothesis/cli/commands/inspect.py
- [x] T026 [US1] Register inspect command in hypothesis/cli/app.py

**Checkpoint**: User Story 1 complete - `hypothesis inspect` command works with all output formats

---

## Phase 4: User Story 3 - Semantic Column Recognition (Priority: P2)

**Goal**: Columns like "email", "first_name", "phone_number" are automatically mapped to appropriate Faker generators with confidence scores

**Independent Test**: Create table with common column names, classify them, verify 85%+ accuracy on patterns

### Tests for User Story 3

- [x] T027 [P] [US3] Write unit tests for pattern definitions in tests/unit/test_mapping/test_patterns.py
- [x] T028 [P] [US3] Write unit tests for tokenizer in tests/unit/test_mapping/test_tokenizer.py
- [x] T029 [P] [US3] Write unit tests for confidence scoring in tests/unit/test_mapping/test_confidence.py
- [x] T030 [P] [US3] Write unit tests for ColumnClassifier in tests/unit/test_mapping/test_classifier.py

### Implementation for User Story 3

- [x] T031 [P] [US3] Create PatternRule dataclass in hypothesis/mapping/patterns.py (semantic_type, pattern_type, pattern, base_confidence, case_sensitive)
- [x] T031a [P] [US3] Define PATTERN_RULES list in hypothesis/mapping/patterns.py with 100+ pattern rules: exact matches (email, phone, address, etc.), suffix matches (_at, _url, _id), prefix matches (is_, has_, can_), contains matches, regex patterns for compound names
- [x] T031b [P] [US3] Define CONFIDENCE_MODIFIERS dict in hypothesis/mapping/patterns.py (+0.05 for sql_type_matches, -0.20 for ambiguous_token, etc.)
- [x] T031c [P] [US3] Define AMBIGUOUS_TOKENS set in hypothesis/mapping/patterns.py (status, type, code, value, data, name, key, etc.)
- [x] T032 [US3] Implement pattern matching engine in hypothesis/mapping/patterns.py (match_exact, match_suffix, match_prefix, match_contains, match_regex)
- [x] T033 [US3] Implement name tokenizer in hypothesis/mapping/tokenizer.py (camelCase, snake_case splitting)
- [x] T034 [US3] Implement token scoring in hypothesis/mapping/tokenizer.py (semantic weight per token)
- [x] T035 [US3] Implement confidence calculator in hypothesis/mapping/confidence.py (base score + modifiers)
- [x] T036 [US3] Implement Layer 1 (Schema Constraints) in hypothesis/mapping/pipeline.py (ENUM, FK, CHECK detection)
- [x] T037 [US3] Implement Layer 2 (Pattern Matching) in hypothesis/mapping/pipeline.py (exact, regex, suffix)
- [x] T038 [US3] Implement Layer 3 (Token Analysis) in hypothesis/mapping/pipeline.py (compound name scoring)
- [x] T039 [US3] Implement Layer 4 (Table Context) in hypothesis/mapping/pipeline.py (disambiguation using table name)
- [x] T040 [US3] Implement Layer 5 (Type Fallback) in hypothesis/mapping/pipeline.py (SQL type based defaults)
- [x] T041 [US3] Implement ColumnClassifier orchestrator in hypothesis/mapping/classifier.py (classify_column, classify_table, classify_schema)
- [x] T042 [US3] Add get_low_confidence_columns() to ColumnClassifier in hypothesis/mapping/classifier.py
- [x] T043 [US3] Add confidence indicators to inspect output in hypothesis/cli/commands/inspect.py (✓ for high, ⚠️ for low)

**Checkpoint**: User Story 3 complete - semantic classification pipeline works with 85%+ accuracy

---

## Phase 5: User Story 2 - Generate Basic Test Data (Priority: P1)

**Goal**: Generate and insert realistic fake data respecting FK relationships and constraints at 10K+ rows/sec

**Independent Test**: Generate 1000 rows into database with FKs, verify all FK constraints pass and unique values are unique

### Tests for User Story 2

- [ ] T044 [P] [US2] Write unit tests for DataGenerator in tests/unit/test_core/test_generator.py
- [ ] T045 [P] [US2] Write unit tests for ForeignKeyResolver in tests/unit/test_constraints/test_foreign_keys.py
- [ ] T046 [P] [US2] Write unit tests for UniqueConstraintHandler in tests/unit/test_constraints/test_unique.py
- [ ] T047 [P] [US2] Write unit tests for BulkInserter in tests/unit/test_core/test_inserter.py

### Implementation for User Story 2

- [ ] T048 [US2] Implement ForeignKeyResolver in hypothesis/constraints/foreign_keys.py (cache_parent_ids, select_fk_value with distributions)
- [ ] T049 [US2] Implement UniqueConstraintHandler in hypothesis/constraints/unique.py (track values, retry on collision)
- [ ] T050 [US2] Implement DataGenerator.generate_value() in hypothesis/core/generator.py (dispatch to Faker based on classification)
- [ ] T051 [US2] Implement DataGenerator.generate_row() in hypothesis/core/generator.py (generate all columns for one row)
- [ ] T052 [US2] Implement DataGenerator.generate_batch() in hypothesis/core/generator.py (streaming batch generation)
- [ ] T053 [US2] Implement BulkInserter.insert_batch() in hypothesis/core/inserter.py (SQLAlchemy Core executemany)
- [ ] T054 [US2] Implement BulkInserter.insert_table() in hypothesis/core/inserter.py (batched inserts with progress callback)
- [ ] T055 [US2] Implement generate command handler in hypothesis/cli/commands/generate.py (orchestrate full workflow)
- [ ] T056 [US2] Add Rich progress bars for generation in hypothesis/cli/commands/generate.py
- [ ] T057 [US2] Add --rows flag in hypothesis/cli/commands/generate.py
- [ ] T058 [US2] Add --batch-size flag in hypothesis/cli/commands/generate.py
- [ ] T059 [US2] Add --locale flag in hypothesis/cli/commands/generate.py
- [ ] T060 [US2] Register generate command in hypothesis/cli/app.py

**Checkpoint**: User Story 2 complete - `hypothesis generate` creates valid data respecting all constraints

---

## Phase 6: User Story 4 - Configuration File Support (Priority: P2)

**Goal**: Users can customize generation via YAML config with per-table row counts, column overrides, and value constraints

**Independent Test**: Create config file with custom mappings, run generate, verify config rules are applied

### Tests for User Story 4

- [ ] T061 [P] [US4] Write unit tests for Pydantic config validation in tests/unit/test_config/test_models.py

### Implementation for User Story 4

- [ ] T062 [US4] Add config loading to generate command in hypothesis/cli/commands/generate.py (merge config with defaults)
- [ ] T063 [US4] Implement per-table row count overrides in hypothesis/core/generator.py
- [ ] T064 [US4] Implement column provider overrides in hypothesis/core/generator.py (respect config.columns.provider)
- [ ] T065 [US4] Implement fixed value lists with weights in hypothesis/core/generator.py
- [ ] T066 [US4] Implement numeric min/max constraints in hypothesis/core/generator.py
- [ ] T067 [US4] Implement nullable_chance per column in hypothesis/core/generator.py
- [ ] T068 [US4] Implement validate command in hypothesis/cli/commands/validate.py (parse config, check against schema)
- [ ] T069 [US4] Register validate command in hypothesis/cli/app.py

**Checkpoint**: User Story 4 complete - config file customization works for all generation options

---

## Phase 7: User Story 1.5 - Analyze Schema and Generate Configuration (Priority: P2)

**Goal**: Auto-generate starter YAML config from schema with intelligent defaults and flagged low-confidence columns

**Independent Test**: Run analyze on any schema, verify output is valid YAML that can be loaded by generate command

### Tests for User Story 1.5

- [ ] T070 [P] [US1.5] Write unit tests for ConfigGenerator in tests/unit/test_config/test_generator.py

### Implementation for User Story 1.5

- [ ] T071 [US1.5] Implement ConfigGenerator.generate_config() in hypothesis/config/generator.py (build GenerationConfig from schema + classifications)
- [ ] T072 [US1.5] Implement ConfigGenerator.to_yaml() in hypothesis/config/generator.py (serialize with comments)
- [ ] T073 [US1.5] Implement low-confidence warning comments in YAML output in hypothesis/config/generator.py
- [ ] T074 [US1.5] Implement row count suggestions based on FK relationships in hypothesis/config/generator.py
- [ ] T075 [US1.5] Implement self_references section generation in hypothesis/config/generator.py
- [ ] T076 [US1.5] Implement ConfigGenerator.merge_with_existing() in hypothesis/config/generator.py (preserve user customizations)
- [ ] T077 [US1.5] Create analyze.py command file in hypothesis/cli/commands/analyze.py
- [ ] T078 [US1.5] Implement analyze command handler in hypothesis/cli/commands/analyze.py (connect, inspect, classify, generate config)
- [ ] T079 [US1.5] Add --output flag for config file path in hypothesis/cli/commands/analyze.py
- [ ] T080 [US1.5] Add --update flag for merging with existing in hypothesis/cli/commands/analyze.py
- [ ] T081 [US1.5] Add --dry-run flag for preview without write in hypothesis/cli/commands/analyze.py
- [ ] T082 [US1.5] Register analyze command in hypothesis/cli/app.py

**Checkpoint**: User Story 1.5 complete - `hypothesis analyze` generates valid starter configs

---

## Phase 8: User Story 5 - Dry Run Preview (Priority: P3)

**Goal**: Preview generated data and mappings without inserting into database

**Independent Test**: Run generate with --dry-run, verify no database writes occur and sample data is displayed

### Implementation for User Story 5

- [ ] T083 [US5] Add --dry-run flag to generate command in hypothesis/cli/commands/generate.py
- [ ] T084 [US5] Implement dry run logic in hypothesis/cli/commands/generate.py (generate samples, display, skip insert)
- [ ] T085 [US5] Display sample rows as Rich table (5 per table) in hypothesis/cli/commands/generate.py
- [ ] T086 [US5] Display classification reasoning chain in verbose dry run in hypothesis/cli/commands/generate.py
- [ ] T087 [US5] Display low-confidence summary at end of dry run in hypothesis/cli/commands/generate.py

**Checkpoint**: User Story 5 complete - dry run shows preview without database changes

---

## Phase 9: User Story 6 - Handle Existing Data (Priority: P3)

**Goal**: Support --truncate and --append modes for databases with existing data

**Independent Test**: Generate into non-empty database with each mode, verify correct behavior

### Implementation for User Story 6

- [ ] T088 [US6] Add existing data detection in hypothesis/cli/commands/generate.py (check row counts before generate)
- [ ] T089 [US6] Add --truncate flag in hypothesis/cli/commands/generate.py
- [ ] T090 [US6] Implement truncate logic in hypothesis/core/inserter.py (DELETE FROM with FK order)
- [ ] T091 [US6] Add --append flag in hypothesis/cli/commands/generate.py
- [ ] T092 [US6] Implement append logic in hypothesis/core/inserter.py (continue from max ID)
- [ ] T093 [US6] Add clear error when existing data found without flags in hypothesis/cli/commands/generate.py
- [ ] T094 [P] [US6] Write unit tests for truncate/append in tests/unit/test_core/test_inserter.py

**Checkpoint**: User Story 6 complete - existing data scenarios handled correctly

---

## Phase 10: Advanced Features

**Purpose**: Additional features from spec that enhance core functionality

### Self-Referential FK Handling

- [ ] T095 [P] Write unit tests for SelfReferenceHandler in tests/unit/test_constraints/test_self_reference.py
- [ ] T096 Implement SelfReferenceHandler in hypothesis/constraints/self_reference.py (two-pass insert strategy)
- [ ] T097 Integrate self-reference handling into generate workflow in hypothesis/core/generator.py

### CHECK Constraint Support

- [ ] T098 [P] Write unit tests for CHECK parser in tests/unit/test_constraints/test_check.py
- [ ] T099 Implement CheckConstraintParser in hypothesis/constraints/check.py (BETWEEN, IN, >=, <= patterns)
- [ ] T100 Integrate CHECK constraints into generator in hypothesis/core/generator.py (respect parsed ranges/values)

**Checkpoint**: Advanced constraint handling complete

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T101 [P] Add comprehensive error messages with context in hypothesis/core/exceptions.py
- [ ] T102 [P] Create Docker Compose for integration tests in docker-compose.yml (PostgreSQL + MySQL)
- [ ] T103 [P] Create integration test fixtures in tests/integration/conftest.py (container setup/teardown)
- [ ] T104 Write end-to-end integration test in tests/integration/test_end_to_end.py
- [ ] T105 [P] Update README.md with usage examples and quickstart
- [ ] T106 [P] Create example configs in examples/ directory
- [ ] T107 Run performance benchmark and document results (10K rows/sec target)
- [ ] T108 Run mypy strict mode and fix all type errors
- [ ] T109 Run ruff and fix all linting issues
- [ ] T110 Verify test coverage ≥ 85%

**Checkpoint**: Project polished and ready for release

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user stories
- **Phase 3-9 (User Stories)**: All depend on Phase 2 completion
- **Phase 10 (Advanced)**: Depends on Phase 5 (US2)
- **Phase 11 (Polish)**: Depends on all core stories complete

### User Story Dependencies

```
Phase 2: Foundational (SchemaInspector, DependencyGraph)
    │
    ├─► Phase 3: US1 (Inspect) ─► No dependencies on other stories
    │
    ├─► Phase 4: US3 (Classification) ─► No dependencies on other stories
    │       │
    │       ├─► Phase 5: US2 (Generate) ─► Requires US3 for classification
    │       │       │
    │       │       ├─► Phase 8: US5 (Dry Run) ─► Requires US2 framework
    │       │       │
    │       │       ├─► Phase 9: US6 (Existing Data) ─► Requires US2 framework
    │       │       │
    │       │       └─► Phase 10 (Advanced) ─► Requires US2 framework
    │       │
    │       └─► Phase 7: US1.5 (Analyze) ─► Requires US3 for classification
    │
    └─► Phase 6: US4 (Config Support) ─► Can start in parallel, integrates with US2
```

### Critical Path to MVP

1. Phase 1 (Setup) → Phase 2 (Foundation) → Phase 3 (US1 Inspect) → **MVP Checkpoint 1**
2. Continue: Phase 4 (US3 Classification) → Phase 5 (US2 Generate) → **MVP Checkpoint 2 (Core Complete)**

### Parallel Opportunities

| Phase | Parallel Tasks |
|-------|----------------|
| Phase 1 | T001-T007 (all models, enums, fixtures) |
| Phase 2 | T013, T015 (tests can run after implementation) |
| Phase 3 | T016-T017 (tests before implementation) |
| Phase 4 | T027-T030 (all classification tests), T031-T032 (patterns, types) |
| Phase 5 | T044-T047 (all generation tests) |
| Phase 11 | T101-T103, T105-T106 (independent polish tasks) |

---

## Parallel Example: Phase 4 (Classification Pipeline)

```bash
# Launch all tests in parallel:
Task: T027 "Write unit tests for pattern definitions in tests/unit/test_mapping/test_patterns.py"
Task: T028 "Write unit tests for tokenizer in tests/unit/test_mapping/test_tokenizer.py"
Task: T029 "Write unit tests for confidence scoring in tests/unit/test_mapping/test_confidence.py"
Task: T030 "Write unit tests for ColumnClassifier in tests/unit/test_mapping/test_classifier.py"

# Launch parallel implementation:
Task: T031 "Define 30+ pattern rules in hypothesis/mapping/patterns.py"
Task: T032 "Implement SQL type to Faker mapping in hypothesis/mapping/types.py"
```

---

## Implementation Strategy

### MVP First (Phases 1-3, then 4-5)

1. Complete Phase 1: Setup (models, enums, fixtures)
2. Complete Phase 2: Foundational (SchemaInspector, DependencyGraph)
3. Complete Phase 3: US1 (Inspect command)
4. **STOP and VALIDATE**: Test `hypothesis inspect` independently
5. Complete Phase 4: US3 (Classification pipeline)
6. Complete Phase 5: US2 (Generate command)
7. **STOP and VALIDATE**: Test full `hypothesis generate` workflow

### Incremental Delivery

1. **v0.1**: Inspect command only (Phase 1-3)
2. **v0.2**: Add generation (Phase 4-5)
3. **v0.3**: Add analyze command (Phase 7)
4. **v0.4**: Add advanced features (Phase 6, 8-10)
5. **v1.0**: Polish and release (Phase 11)

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Tasks** | 117 |
| **Phase 1 (Setup)** | 10 tasks (expanded for semantic intelligence) |
| **Phase 2 (Foundational)** | 8 tasks |
| **US1 (Inspect)** | 11 tasks |
| **US3 (Classification)** | 21 tasks (expanded for pattern rules) |
| **US2 (Generate)** | 17 tasks |
| **US4 (Config Support)** | 8 tasks |
| **US1.5 (Analyze)** | 13 tasks |
| **US5 (Dry Run)** | 5 tasks |
| **US6 (Existing Data)** | 7 tasks |
| **Phase 10 (Advanced)** | 6 tasks |
| **Phase 11 (Polish)** | 10 tasks |
| **Parallel Opportunities** | 42 tasks marked [P] |
| **MVP Scope** | Phases 1-5 (US1 + US3 + US2) = 67 tasks |

---

## Notes

- [P] tasks can run in parallel (different files, no dependencies)
- [Story] label maps task to specific user story
- Constitution requires TDD: write tests first, verify they fail, then implement
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
- Performance target: 10K rows/sec (verify with T107)
- Coverage target: 85%+ (verify with T110)
