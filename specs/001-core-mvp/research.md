# Research: Semantic Database Seeder MVP

**Feature**: 001-core-mvp  
**Date**: 2026-01-16

## Overview

This document captures technical decisions, rationale, and alternatives considered for the Hypothesis MVP implementation.

---

## Decision 1: Classification Pipeline Architecture

### Decision
Implement a 5-layer classification pipeline with confidence scoring:
1. Schema Constraints (ENUM, FK, CHECK) → confidence 0.95-1.0
2. Pattern Matching (exact, regex, suffix) → confidence 0.85-0.95
3. Token Analysis (compound names) → confidence varies
4. Table Context (disambiguation) → confidence 0.65-0.70
5. SQL Type Fallback → confidence 0.50-0.60

### Rationale
- **Layered approach** ensures high-confidence sources (schema) are checked first
- **Confidence scores** enable flagging low-confidence mappings for user review
- **Fallback chain** guarantees every column gets a generator (graceful degradation)
- Aligns with constitution principle V (Graceful Degradation)

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| Single ML classifier | Over-engineered for MVP; patterns work for 85%+ of cases |
| LLM-only classification | Adds latency, cost, and external dependency for core flow |
| No confidence scoring | Would silently use wrong generators; poor UX |

---

## Decision 2: Batch Insert Strategy

### Decision
Use SQLAlchemy Core `executemany()` with configurable batch sizes (default 1000), per-batch transactions with savepoints.

### Rationale
- **SQLAlchemy Core** (not ORM) for raw performance - avoids object overhead
- **Batch size 1000** balances memory vs. transaction overhead (benchmarked in similar tools)
- **Per-batch transactions** enable partial recovery on failure
- **Savepoints** allow fine-grained rollback within batch

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| Row-by-row inserts | 100-1000x slower than batched |
| Single giant transaction | All-or-nothing; no partial recovery |
| COPY/LOAD DATA | DB-specific; requires temp files; complex |

---

## Decision 3: Foreign Key Resolution

### Decision
Cache parent IDs in memory with configurable sample size (default 1000). Support three distribution strategies: uniform, exponential (power law), normal.

### Rationale
- **Memory cache** avoids repeated DB queries during generation
- **Sample size 1000** covers most FK relationships without excessive memory
- **Distribution strategies** model real-world data (e.g., some users have many orders)

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| Query parent on each row | Too slow (N queries for N rows) |
| Load all parent IDs | Memory explosion for large parent tables |
| Random ID generation | Would violate FK constraints |

---

## Decision 4: Unique Constraint Handling

### Decision
Track generated values in Python sets. On collision, regenerate (max 10 attempts). Skip row and log warning if exhausted.

### Rationale
- **Set-based tracking** is O(1) lookup
- **10 retries** handles most collision scenarios
- **Skip and continue** prevents one bad column from halting entire generation
- Aligns with constitution principle V (Graceful Degradation)

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| DB-level dedup | Requires insert → check → retry; slower |
| Pre-generate all values | Memory explosion for large datasets |
| UUID for everything | Doesn't respect user's column semantics |

---

## Decision 5: Self-Referential FK Handling

### Decision
Two-pass generation strategy:
1. First pass: Insert all rows with self-ref FK as NULL
2. Second pass: UPDATE rows to establish parent relationships (configurable root probability)

### Rationale
- **Two-pass** is the only way to satisfy self-refs without disabling constraints
- **Root probability** (default 10%) ensures some rows have no parent (e.g., top-level managers)
- Explicit in generated config for user visibility

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| Disable FK, insert, re-enable | Risky; might fail on re-enable |
| Skip self-ref tables | Leaves important tables empty |
| Only generate root nodes | Unrealistic data distribution |

---

## Decision 6: CHECK Constraint Parsing

### Decision
Use regex patterns for common CHECK patterns (ranges, value lists). Skip complex constraints (function calls, subqueries) with warning.

### Rationale
- **Regex** covers ~80% of real-world CHECKs (`BETWEEN`, `IN`, `>=`, `<=`)
- **Complex parsing** would require SQL parser; out of scope for MVP
- **Skip with warning** aligns with graceful degradation

### Patterns Supported
```
age BETWEEN 18 AND 100          → range(18, 100)
status IN ('active', 'pending') → ['active', 'pending']
price >= 0                      → min=0
quantity <= 1000                → max=1000
```

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| Full SQL parser | Heavy dependency; overkill for CHECK constraints |
| Ignore all CHECKs | Leads to constraint violations |
| Always use type fallback | Misses easy wins (ranges, lists) |

---

## Decision 7: CLI Output Formats

### Decision
Support three output formats via `--format` flag:
- `table` (default): Rich tables with colors
- `json`: Machine-readable, pipe-friendly
- `markdown`: Documentation-ready

### Rationale
- **table** for interactive use (developer at terminal)
- **json** for scripting, CI/CD pipelines
- **markdown** for documentation, reports
- Minimal implementation cost with clear user value

---

## Decision 8: Configuration File Format

### Decision
YAML with shell-style environment variable interpolation (`${VAR}`, `${VAR:-default}`).

### Rationale
- **YAML** is human-readable and widely used for configs
- **Shell-style interpolation** matches Docker, K8s conventions
- **Default values** reduce boilerplate for common cases
- Already implemented in `config/parser.py`

---

## Decision 9: LLM Integration (Optional Feature)

### Decision
Opt-in via `--ai` flag. Send only schema metadata (never data). Batch ambiguous columns into single request. Cache responses. Configurable provider.

### Rationale
- **Opt-in** respects users who don't want external dependencies
- **Schema-only** protects sensitive data
- **Batching** reduces API costs/latency
- **Caching** avoids redundant calls on unchanged schemas
- **Configurable provider** avoids vendor lock-in

---

## Decision 10: Confidence Threshold

### Decision
Use 0.6 as the threshold for "low confidence" flagging.

### Rationale
- **0.6** balances false positives (too many warnings) vs. false negatives (missed ambiguity)
- Type-fallback columns are capped at 0.5, so they're always flagged
- High-confidence patterns (exact match) are 0.85+, so they're never flagged
- Specified in FR-014.5, confirmed in spec clarification

---

## Performance Targets Summary

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Simple table generation | 10,000+ rows/sec | Benchmark with 100K rows, no FKs |
| FK table generation | 5,000+ rows/sec | Benchmark with 100K rows, 3 FKs |
| Total throughput | 1M rows < 5 min | Benchmark with 20-table schema |
| Memory usage | < 500MB | Profile during 1M row generation |
| Inspect latency | < 10 sec | Time schema reflection |
| Analyze latency | < 30 sec | Time classification + config gen |

---

## Technology Validation

All technologies confirmed as appropriate:

| Technology | Purpose | Validation |
|------------|---------|------------|
| Python 3.11+ | Runtime | Modern type hints, performance, wide adoption |
| SQLAlchemy 2.x | DB operations | Industry standard, excellent reflection API |
| Typer | CLI framework | Type-safe, Pydantic integration, Rich support |
| Rich | Terminal output | Beautiful tables, progress bars, colors |
| Faker | Data generation | Comprehensive providers, localization support |
| Pydantic | Config validation | Type safety, clear error messages |
| PyYAML | Config parsing | Standard YAML library |
| pytest | Testing | Industry standard, excellent fixtures |
