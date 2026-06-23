## Unreleased

### Feat

- **cli**: show semantic type and confidence in inspect output (T043)
- **mapping**: add 5-layer classification pipeline and ColumnClassifier
- **mapping**: add pattern rules, tokenizer, and confidence scoring
- **cli**: add the hypothesis inspect command (Phase 3, US1)
- **core**: add schema inspector and dependency graph (Phase 2)
- **config,cli**: add config models, output formatters, and SQL fixtures
- **models**: add exceptions, schema dataclasses, and semantic type system
- **core**: add database connection management and string builder
- add core database connection management, CLI commands for generate, inspect, and validate, and logging with secret redaction.
- implement config file parsers
- implement initial parameters and simple stling

### Fix

- **types**: make the whole package pass mypy --strict
