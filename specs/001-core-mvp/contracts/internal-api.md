# Internal API Contracts: Semantic Database Seeder MVP

**Feature**: 001-core-mvp  
**Date**: 2026-01-16

## Overview

This document defines the internal library API contracts for Hypothesis. These APIs are exposed for programmatic usage and are wrapped by the CLI commands.

---

## Module: `hypothesis.core.inspector`

### `SchemaInspector`

```python
class SchemaInspector:
    """Reflects database schema and builds metadata."""
    
    def __init__(self, engine: Engine) -> None:
        """Initialize with SQLAlchemy engine."""
        
    def reflect_schema(
        self, 
        tables: list[str] | None = None,
        include_views: bool = False
    ) -> None:
        """
        Reflect database schema.
        
        Args:
            tables: Specific tables to reflect, or None for all
            include_views: Whether to include views (skipped by default)
        
        Raises:
            SchemaIntrospectionError: If reflection fails
        """
        
    def get_tables(self) -> list[TableSchema]:
        """Return all reflected tables."""
        
    def get_table(self, name: str) -> TableSchema:
        """
        Get specific table by name.
        
        Raises:
            KeyError: If table not found
        """
        
    def get_foreign_keys(self) -> list[ForeignKey]:
        """Return all foreign key relationships."""
        
    def get_dependency_graph(self) -> DependencyGraph:
        """Build and return dependency graph."""
        
    def get_insertion_order(self) -> list[str]:
        """Return table names in topological order for insertion."""
```

---

## Module: `hypothesis.mapping.classifier`

### `ColumnClassifier`

```python
class ColumnClassifier:
    """Classifies columns using layered pipeline."""
    
    def __init__(
        self,
        custom_patterns: dict[str, str] | None = None,
        confidence_threshold: float = 0.6
    ) -> None:
        """
        Initialize classifier.
        
        Args:
            custom_patterns: User-defined column name → Faker provider mappings
            confidence_threshold: Below this, column is flagged for review
        """
        
    def classify_column(
        self,
        column: ColumnSchema,
        table_context: str | None = None
    ) -> ClassificationResult:
        """
        Classify a single column.
        
        Args:
            column: Column schema to classify
            table_context: Parent table name for disambiguation
            
        Returns:
            ClassificationResult with semantic type and confidence
        """
        
    def classify_table(
        self,
        table: TableSchema
    ) -> dict[str, ClassificationResult]:
        """
        Classify all columns in a table.
        
        Returns:
            Dict mapping column name → ClassificationResult
        """
        
    def classify_schema(
        self,
        tables: list[TableSchema]
    ) -> dict[str, dict[str, ClassificationResult]]:
        """
        Classify all columns in all tables.
        
        Returns:
            Dict mapping table_name → column_name → ClassificationResult
        """
        
    def get_low_confidence_columns(
        self,
        results: dict[str, dict[str, ClassificationResult]]
    ) -> list[tuple[str, str, ClassificationResult]]:
        """
        Return columns below confidence threshold.
        
        Returns:
            List of (table_name, column_name, result) tuples
        """
```

---

## Module: `hypothesis.core.generator`

### `DataGenerator`

```python
class DataGenerator:
    """Generates fake data based on classification results."""
    
    def __init__(
        self,
        faker_locale: str = "en_US",
        seed: int | None = None
    ) -> None:
        """
        Initialize generator.
        
        Args:
            faker_locale: Faker locale for data generation
            seed: Random seed for reproducibility (optional)
        """
        
    def generate_value(
        self,
        classification: ClassificationResult,
        fk_cache: dict[str, list[Any]] | None = None,
        unique_tracker: set | None = None
    ) -> Any:
        """
        Generate a single value for a column.
        
        Args:
            classification: Classification result with generator info
            fk_cache: Cached parent IDs for FK columns
            unique_tracker: Set of already-generated values for unique columns
            
        Returns:
            Generated value appropriate for the column
            
        Raises:
            UniqueConstraintError: If unique value cannot be generated after retries
        """
        
    def generate_row(
        self,
        table: TableSchema,
        classifications: dict[str, ClassificationResult],
        fk_cache: dict[str, list[Any]],
        unique_trackers: dict[str, set]
    ) -> dict[str, Any]:
        """
        Generate a single row for a table.
        
        Returns:
            Dict mapping column name → generated value
        """
        
    def generate_batch(
        self,
        table: TableSchema,
        classifications: dict[str, ClassificationResult],
        count: int,
        fk_cache: dict[str, list[Any]],
        unique_trackers: dict[str, set]
    ) -> list[dict[str, Any]]:
        """
        Generate a batch of rows.
        
        Returns:
            List of row dictionaries
        """
```

---

## Module: `hypothesis.core.inserter`

### `BulkInserter`

```python
class BulkInserter:
    """Handles bulk insert with batching and transactions."""
    
    def __init__(
        self,
        engine: Engine,
        batch_size: int = 1000
    ) -> None:
        """
        Initialize inserter.
        
        Args:
            engine: SQLAlchemy engine
            batch_size: Rows per insert batch
        """
        
    def insert_batch(
        self,
        table_name: str,
        rows: list[dict[str, Any]],
        use_savepoint: bool = True
    ) -> int:
        """
        Insert a batch of rows.
        
        Args:
            table_name: Target table
            rows: List of row dictionaries
            use_savepoint: Whether to use savepoint for rollback
            
        Returns:
            Number of rows successfully inserted
            
        Raises:
            InsertionError: If batch insert fails
        """
        
    def insert_table(
        self,
        table_name: str,
        row_generator: Iterator[dict[str, Any]],
        total_rows: int,
        progress_callback: Callable[[int, int], None] | None = None
    ) -> InsertionResult:
        """
        Insert all rows for a table with progress tracking.
        
        Args:
            table_name: Target table
            row_generator: Iterator yielding row dictionaries
            total_rows: Total expected rows (for progress)
            progress_callback: Called with (inserted, total) for progress
            
        Returns:
            InsertionResult with counts and timing
        """
```

---

## Module: `hypothesis.constraints.foreign_keys`

### `ForeignKeyResolver`

```python
class ForeignKeyResolver:
    """Resolves foreign key values from parent tables."""
    
    def __init__(
        self,
        engine: Engine,
        sample_size: int = 1000
    ) -> None:
        """
        Initialize resolver.
        
        Args:
            engine: SQLAlchemy engine
            sample_size: Number of parent IDs to cache
        """
        
    def cache_parent_ids(
        self,
        parent_table: str,
        parent_column: str
    ) -> list[Any]:
        """
        Query and cache parent IDs.
        
        Returns:
            List of sampled parent ID values
        """
        
    def select_fk_value(
        self,
        parent_table: str,
        parent_column: str,
        distribution: str = "uniform"
    ) -> Any:
        """
        Select a foreign key value.
        
        Args:
            parent_table: Parent table name
            parent_column: Parent column name
            distribution: "uniform", "exponential", or "normal"
            
        Returns:
            Selected parent ID value
        """
        
    def get_cached_ids(
        self,
        parent_table: str,
        parent_column: str
    ) -> list[Any] | None:
        """Return cached IDs or None if not cached."""
```

---

## Module: `hypothesis.config.generator`

### `ConfigGenerator`

```python
class ConfigGenerator:
    """Generates YAML configuration from schema analysis."""
    
    def __init__(
        self,
        inspector: SchemaInspector,
        classifier: ColumnClassifier
    ) -> None:
        """
        Initialize config generator.
        
        Args:
            inspector: Schema inspector with reflected schema
            classifier: Column classifier with results
        """
        
    def generate_config(
        self,
        include_confidence: bool = True,
        include_warnings: bool = True
    ) -> GenerationConfig:
        """
        Generate configuration from schema.
        
        Args:
            include_confidence: Include confidence scores in output
            include_warnings: Include warning comments for low confidence
            
        Returns:
            Complete GenerationConfig object
        """
        
    def to_yaml(
        self,
        config: GenerationConfig,
        output_path: Path | None = None
    ) -> str:
        """
        Serialize config to YAML.
        
        Args:
            config: Configuration to serialize
            output_path: If provided, write to file
            
        Returns:
            YAML string
        """
        
    def merge_with_existing(
        self,
        new_config: GenerationConfig,
        existing_path: Path
    ) -> GenerationConfig:
        """
        Merge new config with existing, preserving user customizations.
        
        Args:
            new_config: Newly generated config
            existing_path: Path to existing config file
            
        Returns:
            Merged configuration
        """
```

---

## Error Hierarchy

```python
class HypothesisError(Exception):
    """Base exception for Hypothesis."""
    pass

class ConnectionError(HypothesisError):
    """Database connection failed."""
    pass

class SchemaIntrospectionError(HypothesisError):
    """Schema reflection failed."""
    pass

class ClassificationError(HypothesisError):
    """Column classification failed."""
    pass

class GenerationError(HypothesisError):
    """Data generation failed."""
    pass

class UniqueConstraintError(GenerationError):
    """Could not generate unique value after max retries."""
    pass

class ForeignKeyError(GenerationError):
    """Foreign key resolution failed."""
    pass

class InsertionError(HypothesisError):
    """Batch insert failed."""
    pass

class ConfigurationError(HypothesisError):
    """Configuration parsing or validation failed."""
    pass

class CircularDependencyError(HypothesisError):
    """Circular foreign key dependencies detected."""
    pass
```

---

## CLI Command Signatures

### `hypothesis inspect`

```python
@app.command()
def inspect(
    database: Annotated[str, typer.Argument(help="Connection string or config name")],
    tables: Annotated[list[str] | None, typer.Option("--tables", "-t")] = None,
    format: Annotated[str, typer.Option("--format", "-f")] = "table",
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
    config: Annotated[Path | None, typer.Option("--config", "-c")] = None,
) -> None:
    """Inspect database schema and show structure."""
```

### `hypothesis analyze`

```python
@app.command()
def analyze(
    database: Annotated[str, typer.Argument(help="Connection string or config name")],
    output: Annotated[Path, typer.Option("--output", "-o")],
    update: Annotated[bool, typer.Option("--update")] = False,
    ai: Annotated[bool, typer.Option("--ai")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    config: Annotated[Path | None, typer.Option("--config", "-c")] = None,
) -> None:
    """Analyze schema and generate configuration file."""
```

### `hypothesis generate`

```python
@app.command()
def generate(
    database: Annotated[str, typer.Argument(help="Connection string or config name")],
    rows: Annotated[int, typer.Option("--rows", "-r")] = 1000,
    tables: Annotated[list[str] | None, typer.Option("--tables", "-t")] = None,
    config: Annotated[Path | None, typer.Option("--config", "-c")] = None,
    truncate: Annotated[bool, typer.Option("--truncate")] = False,
    append: Annotated[bool, typer.Option("--append")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    batch_size: Annotated[int, typer.Option("--batch-size")] = 1000,
    locale: Annotated[str, typer.Option("--locale")] = "en_US",
) -> None:
    """Generate and insert fake data."""
```

### `hypothesis validate`

```python
@app.command()
def validate(
    config: Annotated[Path, typer.Argument(help="Path to config file")],
    database: Annotated[str | None, typer.Option("--database", "-d")] = None,
) -> None:
    """Validate configuration file."""
```

---

## Return Types

### `InsertionResult`

```python
@dataclass
class InsertionResult:
    """Result of table insertion."""
    
    table_name: str
    rows_requested: int
    rows_inserted: int
    rows_skipped: int
    duration_seconds: float
    rows_per_second: float
    errors: list[str]
```

### `InspectionResult`

```python
@dataclass
class InspectionResult:
    """Result of schema inspection."""
    
    tables: list[TableSchema]
    foreign_keys: list[ForeignKey]
    insertion_order: list[str]
    classifications: dict[str, dict[str, ClassificationResult]]
    low_confidence_count: int
    high_confidence_count: int
```

### `AnalysisResult`

```python
@dataclass
class AnalysisResult:
    """Result of schema analysis."""
    
    config: GenerationConfig
    yaml_output: str
    tables_analyzed: int
    columns_analyzed: int
    high_confidence: int
    low_confidence: int
    warnings: list[str]
```
