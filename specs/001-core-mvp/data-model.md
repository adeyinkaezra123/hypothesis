# Data Model: Semantic Database Seeder MVP

**Feature**: 001-core-mvp  
**Date**: 2026-01-16

## Overview

This document defines the core entities, their attributes, relationships, and behaviors for the Hypothesis MVP.

---

## Core Entities

### 1. DatabaseConnection

Represents an active connection to a PostgreSQL or MySQL database.

```python
class DatabaseConnection:
    """Manages database connections with pooling and validation."""
    
    # Attributes
    connection_string: str          # Full connection URL
    engine: Engine                  # SQLAlchemy engine
    pool_size: int = 5             # Connection pool size
    max_overflow: int = 10         # Max overflow connections
    
    # Methods
    def validate() -> bool          # Check connection health
    def get_dialect() -> Literal["postgresql", "mysql"]
    def test_write_permissions() -> bool
    def get_next_sequence_value(table: str, pk_column: str) -> int
    def close() -> None
```

**Status**: ✅ Implemented in `hypothesis/core/connection.py`

---

### 2. TableSchema

Represents a reflected database table with its structure.

```python
@dataclass
class TableSchema:
    """Represents a database table's schema."""
    
    # Identity
    name: str                       # Table name
    schema: str | None = None       # Schema/namespace (e.g., "public")
    
    # Structure
    columns: list[ColumnSchema]     # Column definitions
    primary_key: list[str]          # PK column name(s)
    
    # Constraints
    foreign_keys: list[ForeignKey]  # FK relationships
    unique_constraints: list[UniqueConstraint]
    check_constraints: list[CheckConstraint]
    
    # Metadata
    is_view: bool = False           # True if VIEW, not TABLE
    row_count: int | None = None    # Estimated row count (if available)
```

---

### 3. ColumnSchema

Represents a single column within a table.

```python
@dataclass
class ColumnSchema:
    """Represents a database column's schema."""
    
    # Identity
    name: str                       # Column name
    table_name: str                 # Parent table name
    
    # Type information
    sql_type: str                   # Raw SQL type (e.g., "VARCHAR(255)")
    python_type: type               # Mapped Python type
    length: int | None = None       # For VARCHAR, CHAR
    precision: int | None = None    # For DECIMAL
    scale: int | None = None        # For DECIMAL
    
    # Constraints
    nullable: bool = True           # NULL allowed
    is_primary_key: bool = False
    is_foreign_key: bool = False
    is_unique: bool = False
    is_auto_increment: bool = False
    default: Any | None = None      # Default value expression
    
    # ENUM support
    enum_values: list[str] | None = None  # For ENUM columns
    
    # CHECK constraints
    check_min: float | None = None  # Extracted from CHECK
    check_max: float | None = None  # Extracted from CHECK
    check_values: list[Any] | None = None  # Extracted IN values
```

---

### 4. ForeignKey

Represents a foreign key relationship between tables.

```python
@dataclass
class ForeignKey:
    """Represents a foreign key constraint."""
    
    # Source (child)
    table: str                      # Child table name
    column: str                     # Child column name
    
    # Target (parent)
    referenced_table: str           # Parent table name
    referenced_column: str          # Parent column name
    
    # Metadata
    constraint_name: str | None = None
    is_self_referential: bool = False  # Same table reference
    on_delete: str | None = None    # CASCADE, SET NULL, etc.
    on_update: str | None = None
```

---

### 5. DependencyGraph

Represents table dependencies for insertion ordering.

```python
class DependencyGraph:
    """DAG of table dependencies based on foreign keys."""
    
    # Attributes
    tables: list[str]               # All table names
    edges: dict[str, set[str]]      # table → set of tables it depends on
    
    # Methods
    def build_from_foreign_keys(fks: list[ForeignKey]) -> None
    def topological_sort() -> list[str]  # Insertion order
    def detect_cycles() -> list[list[str]]  # Circular dependencies
    def get_layers() -> list[list[str]]  # Tables by dependency level
```

---

### 6. SemanticType (Enum) & Faker Mapping

The semantic type system is the **core intelligence** of Hypothesis. It maps column characteristics to appropriate Faker providers with high accuracy.

#### 6.1 SemanticType Enum

```python
class SemanticType(Enum):
    """Recognized semantic types for columns."""
    
    # Personal Information
    EMAIL = "email"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    FULL_NAME = "full_name"
    PHONE = "phone"
    USERNAME = "username"
    PASSWORD = "password"
    AGE = "age"
    GENDER = "gender"
    DATE_OF_BIRTH = "date_of_birth"
    SSN = "ssn"
    
    # Location
    ADDRESS = "address"
    STREET = "street"
    CITY = "city"
    STATE = "state"
    COUNTRY = "country"
    POSTAL_CODE = "postal_code"
    LATITUDE = "latitude"
    LONGITUDE = "longitude"
    
    # Business
    COMPANY = "company"
    JOB_TITLE = "job_title"
    DEPARTMENT = "department"
    
    # Financial
    PRICE = "price"
    AMOUNT = "amount"
    CURRENCY = "currency"
    CURRENCY_CODE = "currency_code"
    CREDIT_CARD = "credit_card"
    IBAN = "iban"
    
    # Internet
    URL = "url"
    IP_ADDRESS = "ip_address"
    IPV6_ADDRESS = "ipv6_address"
    MAC_ADDRESS = "mac_address"
    DOMAIN = "domain"
    SLUG = "slug"
    USER_AGENT = "user_agent"
    
    # Identifiers
    UUID = "uuid"
    ID = "id"
    SKU = "sku"
    BARCODE = "barcode"
    
    # Temporal
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    TIMESTAMP = "timestamp"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DELETED_AT = "deleted_at"
    EXPIRES_AT = "expires_at"
    YEAR = "year"
    MONTH = "month"
    
    # Content
    TITLE = "title"
    NAME = "name"  # Generic name (product, category, etc.)
    DESCRIPTION = "description"
    TEXT = "text"
    SUMMARY = "summary"
    BODY = "body"
    CONTENT = "content"
    COMMENT = "comment"
    NOTE = "note"
    BIO = "bio"
    
    # File/Media
    FILENAME = "filename"
    FILE_PATH = "file_path"
    MIME_TYPE = "mime_type"
    FILE_EXTENSION = "file_extension"
    IMAGE_URL = "image_url"
    
    # Color
    COLOR = "color"
    HEX_COLOR = "hex_color"
    RGB_COLOR = "rgb_color"
    
    # Boolean
    BOOLEAN_FLAG = "boolean_flag"
    
    # Numeric
    PERCENTAGE = "percentage"
    QUANTITY = "quantity"
    COUNT = "count"
    RATING = "rating"
    SCORE = "score"
    PRIORITY = "priority"
    SEQUENCE = "sequence"
    ORDER = "order"
    
    # Status/State (common domain patterns)
    STATUS = "status"
    STATE = "state"
    TYPE = "type"
    CATEGORY = "category"
    LEVEL = "level"
    ROLE = "role"
    
    # Constraint-derived (highest confidence)
    ENUM_VALUE = "enum_value"      # Schema-defined ENUM
    FOREIGN_KEY = "foreign_key"    # FK reference
    CHECK_RANGE = "check_range"    # Derived from CHECK constraint
    CHECK_VALUES = "check_values"  # Derived from CHECK IN clause
    
    # Fallback (lowest confidence)
    TYPE_FALLBACK = "type_fallback"  # SQL type-based generator
```

#### 6.2 Faker Provider Mapping

**Critical**: This mapping defines exactly which Faker method to call for each semantic type.

```python
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class FakerMapping:
    """Complete specification for generating a value."""
    provider: str                      # Faker method name
    kwargs: dict[str, Any]             # Default arguments
    post_process: Callable | None      # Optional transform
    compatible_sql_types: set[str]     # SQL types this makes sense for

# The canonical mapping
SEMANTIC_TO_FAKER: dict[SemanticType, FakerMapping] = {
    # ══════════════════════════════════════════════════════════════════
    # PERSONAL INFORMATION
    # ══════════════════════════════════════════════════════════════════
    SemanticType.EMAIL: FakerMapping(
        provider="email",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT", "CHAR"}
    ),
    SemanticType.FIRST_NAME: FakerMapping(
        provider="first_name",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT", "CHAR"}
    ),
    SemanticType.LAST_NAME: FakerMapping(
        provider="last_name",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT", "CHAR"}
    ),
    SemanticType.FULL_NAME: FakerMapping(
        provider="name",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT", "CHAR"}
    ),
    SemanticType.PHONE: FakerMapping(
        provider="phone_number",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT", "CHAR"}
    ),
    SemanticType.USERNAME: FakerMapping(
        provider="user_name",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT", "CHAR"}
    ),
    SemanticType.PASSWORD: FakerMapping(
        provider="password",
        kwargs={"length": 16, "special_chars": True},
        post_process=None,  # Or hash function for password_hash columns
        compatible_sql_types={"VARCHAR", "TEXT", "CHAR"}
    ),
    SemanticType.AGE: FakerMapping(
        provider="random_int",
        kwargs={"min": 18, "max": 85},
        post_process=None,
        compatible_sql_types={"INTEGER", "SMALLINT", "INT", "TINYINT"}
    ),
    SemanticType.GENDER: FakerMapping(
        provider="random_element",
        kwargs={"elements": ["male", "female", "non-binary", "other"]},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT", "CHAR", "ENUM"}
    ),
    SemanticType.DATE_OF_BIRTH: FakerMapping(
        provider="date_of_birth",
        kwargs={"minimum_age": 18, "maximum_age": 85},
        post_process=None,
        compatible_sql_types={"DATE", "DATETIME", "TIMESTAMP"}
    ),
    SemanticType.SSN: FakerMapping(
        provider="ssn",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "CHAR"}
    ),
    
    # ══════════════════════════════════════════════════════════════════
    # LOCATION
    # ══════════════════════════════════════════════════════════════════
    SemanticType.ADDRESS: FakerMapping(
        provider="address",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.STREET: FakerMapping(
        provider="street_address",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.CITY: FakerMapping(
        provider="city",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT", "CHAR"}
    ),
    SemanticType.STATE: FakerMapping(
        provider="state",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT", "CHAR"}
    ),
    SemanticType.COUNTRY: FakerMapping(
        provider="country",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT", "CHAR"}
    ),
    SemanticType.POSTAL_CODE: FakerMapping(
        provider="postcode",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "CHAR"}
    ),
    SemanticType.LATITUDE: FakerMapping(
        provider="latitude",
        kwargs={},
        post_process=None,
        compatible_sql_types={"DECIMAL", "FLOAT", "DOUBLE", "NUMERIC", "REAL"}
    ),
    SemanticType.LONGITUDE: FakerMapping(
        provider="longitude",
        kwargs={},
        post_process=None,
        compatible_sql_types={"DECIMAL", "FLOAT", "DOUBLE", "NUMERIC", "REAL"}
    ),
    
    # ══════════════════════════════════════════════════════════════════
    # BUSINESS
    # ══════════════════════════════════════════════════════════════════
    SemanticType.COMPANY: FakerMapping(
        provider="company",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.JOB_TITLE: FakerMapping(
        provider="job",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.DEPARTMENT: FakerMapping(
        provider="random_element",
        kwargs={"elements": ["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations", "Legal", "Support"]},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    
    # ══════════════════════════════════════════════════════════════════
    # FINANCIAL
    # ══════════════════════════════════════════════════════════════════
    SemanticType.PRICE: FakerMapping(
        provider="pydecimal",
        kwargs={"min_value": 1, "max_value": 9999, "right_digits": 2, "positive": True},
        post_process=None,
        compatible_sql_types={"DECIMAL", "NUMERIC", "MONEY", "FLOAT", "DOUBLE"}
    ),
    SemanticType.AMOUNT: FakerMapping(
        provider="pydecimal",
        kwargs={"min_value": 0, "max_value": 100000, "right_digits": 2},
        post_process=None,
        compatible_sql_types={"DECIMAL", "NUMERIC", "MONEY", "FLOAT", "DOUBLE"}
    ),
    SemanticType.CURRENCY: FakerMapping(
        provider="currency_name",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.CURRENCY_CODE: FakerMapping(
        provider="currency_code",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "CHAR"}
    ),
    SemanticType.CREDIT_CARD: FakerMapping(
        provider="credit_card_number",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "CHAR"}
    ),
    SemanticType.IBAN: FakerMapping(
        provider="iban",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "CHAR"}
    ),
    
    # ══════════════════════════════════════════════════════════════════
    # INTERNET
    # ══════════════════════════════════════════════════════════════════
    SemanticType.URL: FakerMapping(
        provider="url",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.IP_ADDRESS: FakerMapping(
        provider="ipv4",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "CHAR", "INET"}
    ),
    SemanticType.IPV6_ADDRESS: FakerMapping(
        provider="ipv6",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "CHAR", "INET"}
    ),
    SemanticType.MAC_ADDRESS: FakerMapping(
        provider="mac_address",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "CHAR", "MACADDR"}
    ),
    SemanticType.DOMAIN: FakerMapping(
        provider="domain_name",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.SLUG: FakerMapping(
        provider="slug",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.USER_AGENT: FakerMapping(
        provider="user_agent",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    
    # ══════════════════════════════════════════════════════════════════
    # IDENTIFIERS
    # ══════════════════════════════════════════════════════════════════
    SemanticType.UUID: FakerMapping(
        provider="uuid4",
        kwargs={},
        post_process=str,  # Convert UUID to string if needed
        compatible_sql_types={"UUID", "VARCHAR", "CHAR"}
    ),
    SemanticType.ID: FakerMapping(
        provider="random_int",
        kwargs={"min": 1, "max": 999999},
        post_process=None,
        compatible_sql_types={"INTEGER", "BIGINT", "INT"}
    ),
    SemanticType.SKU: FakerMapping(
        provider="bothify",
        kwargs={"text": "???-####-???"},  # ABC-1234-XYZ
        post_process=str.upper,
        compatible_sql_types={"VARCHAR", "CHAR"}
    ),
    SemanticType.BARCODE: FakerMapping(
        provider="ean13",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "CHAR", "BIGINT"}
    ),
    
    # ══════════════════════════════════════════════════════════════════
    # TEMPORAL
    # ══════════════════════════════════════════════════════════════════
    SemanticType.DATE: FakerMapping(
        provider="date_between",
        kwargs={"start_date": "-5y", "end_date": "today"},
        post_process=None,
        compatible_sql_types={"DATE"}
    ),
    SemanticType.DATETIME: FakerMapping(
        provider="date_time_between",
        kwargs={"start_date": "-5y", "end_date": "now"},
        post_process=None,
        compatible_sql_types={"DATETIME", "TIMESTAMP"}
    ),
    SemanticType.TIME: FakerMapping(
        provider="time",
        kwargs={},
        post_process=None,
        compatible_sql_types={"TIME"}
    ),
    SemanticType.TIMESTAMP: FakerMapping(
        provider="unix_time",
        kwargs={},
        post_process=None,
        compatible_sql_types={"INTEGER", "BIGINT", "TIMESTAMP"}
    ),
    SemanticType.CREATED_AT: FakerMapping(
        provider="date_time_between",
        kwargs={"start_date": "-2y", "end_date": "-1d"},
        post_process=None,
        compatible_sql_types={"DATETIME", "TIMESTAMP", "TIMESTAMPTZ"}
    ),
    SemanticType.UPDATED_AT: FakerMapping(
        provider="date_time_between",
        kwargs={"start_date": "-1d", "end_date": "now"},
        post_process=None,
        compatible_sql_types={"DATETIME", "TIMESTAMP", "TIMESTAMPTZ"}
    ),
    SemanticType.DELETED_AT: FakerMapping(
        provider="date_time_between",
        kwargs={"start_date": "-30d", "end_date": "now"},
        post_process=None,  # Note: Often NULL, handled by nullable_chance
        compatible_sql_types={"DATETIME", "TIMESTAMP", "TIMESTAMPTZ"}
    ),
    SemanticType.EXPIRES_AT: FakerMapping(
        provider="date_time_between",
        kwargs={"start_date": "now", "end_date": "+1y"},
        post_process=None,
        compatible_sql_types={"DATETIME", "TIMESTAMP", "TIMESTAMPTZ"}
    ),
    SemanticType.YEAR: FakerMapping(
        provider="year",
        kwargs={},
        post_process=None,
        compatible_sql_types={"INTEGER", "SMALLINT", "YEAR"}
    ),
    SemanticType.MONTH: FakerMapping(
        provider="month",
        kwargs={},
        post_process=None,
        compatible_sql_types={"INTEGER", "SMALLINT"}
    ),
    
    # ══════════════════════════════════════════════════════════════════
    # CONTENT
    # ══════════════════════════════════════════════════════════════════
    SemanticType.TITLE: FakerMapping(
        provider="sentence",
        kwargs={"nb_words": 6},
        post_process=lambda s: s.rstrip("."),  # Remove trailing period
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.NAME: FakerMapping(
        provider="catch_phrase",  # Good for product/category names
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.DESCRIPTION: FakerMapping(
        provider="paragraph",
        kwargs={"nb_sentences": 3},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.TEXT: FakerMapping(
        provider="text",
        kwargs={"max_nb_chars": 500},
        post_process=None,
        compatible_sql_types={"TEXT", "LONGTEXT", "CLOB"}
    ),
    SemanticType.SUMMARY: FakerMapping(
        provider="paragraph",
        kwargs={"nb_sentences": 2},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.BODY: FakerMapping(
        provider="text",
        kwargs={"max_nb_chars": 2000},
        post_process=None,
        compatible_sql_types={"TEXT", "LONGTEXT", "CLOB"}
    ),
    SemanticType.CONTENT: FakerMapping(
        provider="text",
        kwargs={"max_nb_chars": 1000},
        post_process=None,
        compatible_sql_types={"TEXT", "LONGTEXT", "CLOB"}
    ),
    SemanticType.COMMENT: FakerMapping(
        provider="sentence",
        kwargs={"nb_words": 12},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.NOTE: FakerMapping(
        provider="sentence",
        kwargs={"nb_words": 10},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.BIO: FakerMapping(
        provider="paragraph",
        kwargs={"nb_sentences": 4},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    
    # ══════════════════════════════════════════════════════════════════
    # FILE/MEDIA
    # ══════════════════════════════════════════════════════════════════
    SemanticType.FILENAME: FakerMapping(
        provider="file_name",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.FILE_PATH: FakerMapping(
        provider="file_path",
        kwargs={"depth": 3},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.MIME_TYPE: FakerMapping(
        provider="mime_type",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR"}
    ),
    SemanticType.FILE_EXTENSION: FakerMapping(
        provider="file_extension",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "CHAR"}
    ),
    SemanticType.IMAGE_URL: FakerMapping(
        provider="image_url",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    
    # ══════════════════════════════════════════════════════════════════
    # COLOR
    # ══════════════════════════════════════════════════════════════════
    SemanticType.COLOR: FakerMapping(
        provider="color_name",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "TEXT"}
    ),
    SemanticType.HEX_COLOR: FakerMapping(
        provider="hex_color",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR", "CHAR"}
    ),
    SemanticType.RGB_COLOR: FakerMapping(
        provider="rgb_color",
        kwargs={},
        post_process=None,
        compatible_sql_types={"VARCHAR"}
    ),
    
    # ══════════════════════════════════════════════════════════════════
    # BOOLEAN
    # ══════════════════════════════════════════════════════════════════
    SemanticType.BOOLEAN_FLAG: FakerMapping(
        provider="boolean",
        kwargs={"chance_of_getting_true": 50},
        post_process=None,
        compatible_sql_types={"BOOLEAN", "BOOL", "TINYINT", "BIT"}
    ),
    
    # ══════════════════════════════════════════════════════════════════
    # NUMERIC
    # ══════════════════════════════════════════════════════════════════
    SemanticType.PERCENTAGE: FakerMapping(
        provider="pydecimal",
        kwargs={"min_value": 0, "max_value": 100, "right_digits": 2},
        post_process=None,
        compatible_sql_types={"DECIMAL", "FLOAT", "DOUBLE", "INTEGER"}
    ),
    SemanticType.QUANTITY: FakerMapping(
        provider="random_int",
        kwargs={"min": 1, "max": 100},
        post_process=None,
        compatible_sql_types={"INTEGER", "SMALLINT", "INT"}
    ),
    SemanticType.COUNT: FakerMapping(
        provider="random_int",
        kwargs={"min": 0, "max": 1000},
        post_process=None,
        compatible_sql_types={"INTEGER", "BIGINT", "INT"}
    ),
    SemanticType.RATING: FakerMapping(
        provider="pydecimal",
        kwargs={"min_value": 1, "max_value": 5, "right_digits": 1},
        post_process=None,
        compatible_sql_types={"DECIMAL", "FLOAT", "DOUBLE", "INTEGER"}
    ),
    SemanticType.SCORE: FakerMapping(
        provider="random_int",
        kwargs={"min": 0, "max": 100},
        post_process=None,
        compatible_sql_types={"INTEGER", "DECIMAL", "FLOAT"}
    ),
    SemanticType.PRIORITY: FakerMapping(
        provider="random_int",
        kwargs={"min": 1, "max": 5},
        post_process=None,
        compatible_sql_types={"INTEGER", "SMALLINT", "TINYINT"}
    ),
    SemanticType.SEQUENCE: FakerMapping(
        provider="random_int",
        kwargs={"min": 1, "max": 100},
        post_process=None,
        compatible_sql_types={"INTEGER", "BIGINT"}
    ),
    SemanticType.ORDER: FakerMapping(
        provider="random_int",
        kwargs={"min": 0, "max": 999},
        post_process=None,
        compatible_sql_types={"INTEGER", "SMALLINT"}
    ),
    
    # ══════════════════════════════════════════════════════════════════
    # STATUS/STATE (domain-specific, but common patterns)
    # ══════════════════════════════════════════════════════════════════
    SemanticType.STATUS: FakerMapping(
        provider="random_element",
        kwargs={"elements": ["active", "inactive", "pending", "archived"]},
        post_process=None,
        compatible_sql_types={"VARCHAR", "ENUM"}
    ),
    SemanticType.TYPE: FakerMapping(
        provider="random_element",
        kwargs={"elements": ["default", "standard", "premium", "custom"]},
        post_process=None,
        compatible_sql_types={"VARCHAR", "ENUM"}
    ),
    SemanticType.CATEGORY: FakerMapping(
        provider="random_element",
        kwargs={"elements": ["general", "featured", "sale", "new"]},
        post_process=None,
        compatible_sql_types={"VARCHAR", "ENUM"}
    ),
    SemanticType.LEVEL: FakerMapping(
        provider="random_element",
        kwargs={"elements": ["beginner", "intermediate", "advanced", "expert"]},
        post_process=None,
        compatible_sql_types={"VARCHAR", "ENUM", "INTEGER"}
    ),
    SemanticType.ROLE: FakerMapping(
        provider="random_element",
        kwargs={"elements": ["user", "admin", "moderator", "guest"]},
        post_process=None,
        compatible_sql_types={"VARCHAR", "ENUM"}
    ),
    
    # ══════════════════════════════════════════════════════════════════
    # CONSTRAINT-DERIVED (handled specially, these are placeholders)
    # ══════════════════════════════════════════════════════════════════
    SemanticType.ENUM_VALUE: FakerMapping(
        provider="random_element",
        kwargs={"elements": []},  # Populated from schema ENUM definition
        post_process=None,
        compatible_sql_types={"ENUM", "VARCHAR"}
    ),
    SemanticType.FOREIGN_KEY: FakerMapping(
        provider="random_element",
        kwargs={"elements": []},  # Populated from parent table IDs
        post_process=None,
        compatible_sql_types={"INTEGER", "BIGINT", "UUID", "VARCHAR"}
    ),
    SemanticType.CHECK_RANGE: FakerMapping(
        provider="random_int",
        kwargs={"min": 0, "max": 100},  # Populated from CHECK constraint
        post_process=None,
        compatible_sql_types={"INTEGER", "DECIMAL", "FLOAT"}
    ),
    SemanticType.CHECK_VALUES: FakerMapping(
        provider="random_element",
        kwargs={"elements": []},  # Populated from CHECK IN clause
        post_process=None,
        compatible_sql_types={"VARCHAR", "INTEGER"}
    ),
    
    # ══════════════════════════════════════════════════════════════════
    # SQL TYPE FALLBACK (lowest confidence)
    # ══════════════════════════════════════════════════════════════════
    SemanticType.TYPE_FALLBACK: FakerMapping(
        provider="pystr",
        kwargs={"max_chars": 50},
        post_process=None,
        compatible_sql_types={"*"}  # Matches any
    ),
}
```

#### 6.3 SQL Type Fallback Mapping

When no semantic pattern matches, fall back to SQL type-based generation:

```python
SQL_TYPE_FALLBACK: dict[str, FakerMapping] = {
    # String types
    "VARCHAR": FakerMapping("pystr", {"max_chars": 50}, None, {"VARCHAR"}),
    "CHAR": FakerMapping("pystr", {"max_chars": 10}, None, {"CHAR"}),
    "TEXT": FakerMapping("text", {"max_nb_chars": 200}, None, {"TEXT"}),
    "LONGTEXT": FakerMapping("text", {"max_nb_chars": 1000}, None, {"LONGTEXT"}),
    "CLOB": FakerMapping("text", {"max_nb_chars": 1000}, None, {"CLOB"}),
    
    # Numeric types
    "INTEGER": FakerMapping("random_int", {"min": 1, "max": 10000}, None, {"INTEGER"}),
    "INT": FakerMapping("random_int", {"min": 1, "max": 10000}, None, {"INT"}),
    "SMALLINT": FakerMapping("random_int", {"min": 1, "max": 1000}, None, {"SMALLINT"}),
    "TINYINT": FakerMapping("random_int", {"min": 0, "max": 127}, None, {"TINYINT"}),
    "BIGINT": FakerMapping("random_int", {"min": 1, "max": 999999999}, None, {"BIGINT"}),
    "DECIMAL": FakerMapping("pydecimal", {"min_value": 0, "max_value": 10000, "right_digits": 2}, None, {"DECIMAL"}),
    "NUMERIC": FakerMapping("pydecimal", {"min_value": 0, "max_value": 10000, "right_digits": 2}, None, {"NUMERIC"}),
    "FLOAT": FakerMapping("pyfloat", {"min_value": 0, "max_value": 10000}, None, {"FLOAT"}),
    "DOUBLE": FakerMapping("pyfloat", {"min_value": 0, "max_value": 10000}, None, {"DOUBLE"}),
    "REAL": FakerMapping("pyfloat", {"min_value": 0, "max_value": 10000}, None, {"REAL"}),
    
    # Boolean
    "BOOLEAN": FakerMapping("boolean", {}, None, {"BOOLEAN"}),
    "BOOL": FakerMapping("boolean", {}, None, {"BOOL"}),
    "BIT": FakerMapping("random_element", {"elements": [0, 1]}, None, {"BIT"}),
    
    # Date/Time
    "DATE": FakerMapping("date_between", {"start_date": "-5y", "end_date": "today"}, None, {"DATE"}),
    "DATETIME": FakerMapping("date_time_between", {"start_date": "-5y", "end_date": "now"}, None, {"DATETIME"}),
    "TIMESTAMP": FakerMapping("date_time_between", {"start_date": "-5y", "end_date": "now"}, None, {"TIMESTAMP"}),
    "TIMESTAMPTZ": FakerMapping("date_time_between", {"start_date": "-5y", "end_date": "now"}, None, {"TIMESTAMPTZ"}),
    "TIME": FakerMapping("time", {}, None, {"TIME"}),
    "YEAR": FakerMapping("year", {}, None, {"YEAR"}),
    
    # UUID
    "UUID": FakerMapping("uuid4", {}, str, {"UUID"}),
    
    # JSON
    "JSON": FakerMapping("pydict", {"nb_elements": 5}, None, {"JSON"}),
    "JSONB": FakerMapping("pydict", {"nb_elements": 5}, None, {"JSONB"}),
    
    # Binary
    "BYTEA": FakerMapping("binary", {"length": 64}, None, {"BYTEA"}),
    "BLOB": FakerMapping("binary", {"length": 64}, None, {"BLOB"}),
    "BINARY": FakerMapping("binary", {"length": 16}, None, {"BINARY"}),
    
    # PostgreSQL-specific
    "INET": FakerMapping("ipv4", {}, None, {"INET"}),
    "MACADDR": FakerMapping("mac_address", {}, None, {"MACADDR"}),
    "CIDR": FakerMapping("ipv4", {}, lambda ip: f"{ip}/24", {"CIDR"}),
    
    # Array types (simple handling)
    "ARRAY": FakerMapping("pylist", {"nb_elements": 3}, None, {"ARRAY"}),
}
```

#### 6.4 Pattern Matching Rules

These patterns map column names to semantic types with confidence scores:

```python
@dataclass
class PatternRule:
    """A pattern matching rule for column classification."""
    semantic_type: SemanticType
    pattern_type: Literal["exact", "prefix", "suffix", "contains", "regex"]
    pattern: str
    base_confidence: float  # Before modifiers
    case_sensitive: bool = False

# Ordered by specificity (most specific first)
PATTERN_RULES: list[PatternRule] = [
    # ══════════════════════════════════════════════════════════════════
    # EXACT MATCHES (highest confidence: 0.95)
    # ══════════════════════════════════════════════════════════════════
    PatternRule(SemanticType.EMAIL, "exact", "email", 0.95),
    PatternRule(SemanticType.EMAIL, "exact", "email_address", 0.95),
    PatternRule(SemanticType.FIRST_NAME, "exact", "first_name", 0.95),
    PatternRule(SemanticType.FIRST_NAME, "exact", "firstname", 0.95),
    PatternRule(SemanticType.FIRST_NAME, "exact", "fname", 0.90),
    PatternRule(SemanticType.LAST_NAME, "exact", "last_name", 0.95),
    PatternRule(SemanticType.LAST_NAME, "exact", "lastname", 0.95),
    PatternRule(SemanticType.LAST_NAME, "exact", "lname", 0.90),
    PatternRule(SemanticType.LAST_NAME, "exact", "surname", 0.95),
    PatternRule(SemanticType.FULL_NAME, "exact", "full_name", 0.95),
    PatternRule(SemanticType.FULL_NAME, "exact", "fullname", 0.95),
    PatternRule(SemanticType.PHONE, "exact", "phone", 0.95),
    PatternRule(SemanticType.PHONE, "exact", "phone_number", 0.95),
    PatternRule(SemanticType.PHONE, "exact", "mobile", 0.90),
    PatternRule(SemanticType.PHONE, "exact", "cell", 0.85),
    PatternRule(SemanticType.PHONE, "exact", "telephone", 0.95),
    PatternRule(SemanticType.USERNAME, "exact", "username", 0.95),
    PatternRule(SemanticType.USERNAME, "exact", "user_name", 0.95),
    PatternRule(SemanticType.USERNAME, "exact", "login", 0.80),
    PatternRule(SemanticType.PASSWORD, "exact", "password", 0.95),
    PatternRule(SemanticType.PASSWORD, "exact", "password_hash", 0.95),
    PatternRule(SemanticType.PASSWORD, "exact", "hashed_password", 0.95),
    PatternRule(SemanticType.PASSWORD, "exact", "pwd", 0.85),
    PatternRule(SemanticType.AGE, "exact", "age", 0.95),
    PatternRule(SemanticType.GENDER, "exact", "gender", 0.95),
    PatternRule(SemanticType.GENDER, "exact", "sex", 0.90),
    PatternRule(SemanticType.DATE_OF_BIRTH, "exact", "date_of_birth", 0.95),
    PatternRule(SemanticType.DATE_OF_BIRTH, "exact", "dob", 0.90),
    PatternRule(SemanticType.DATE_OF_BIRTH, "exact", "birthdate", 0.95),
    PatternRule(SemanticType.DATE_OF_BIRTH, "exact", "birthday", 0.90),
    PatternRule(SemanticType.SSN, "exact", "ssn", 0.95),
    PatternRule(SemanticType.SSN, "exact", "social_security", 0.95),
    
    # Location exact matches
    PatternRule(SemanticType.ADDRESS, "exact", "address", 0.90),
    PatternRule(SemanticType.STREET, "exact", "street", 0.95),
    PatternRule(SemanticType.STREET, "exact", "street_address", 0.95),
    PatternRule(SemanticType.CITY, "exact", "city", 0.95),
    PatternRule(SemanticType.STATE, "exact", "state", 0.85),  # Ambiguous with status
    PatternRule(SemanticType.STATE, "exact", "province", 0.95),
    PatternRule(SemanticType.COUNTRY, "exact", "country", 0.95),
    PatternRule(SemanticType.COUNTRY, "exact", "country_code", 0.95),
    PatternRule(SemanticType.POSTAL_CODE, "exact", "postal_code", 0.95),
    PatternRule(SemanticType.POSTAL_CODE, "exact", "postcode", 0.95),
    PatternRule(SemanticType.POSTAL_CODE, "exact", "zip", 0.90),
    PatternRule(SemanticType.POSTAL_CODE, "exact", "zipcode", 0.95),
    PatternRule(SemanticType.POSTAL_CODE, "exact", "zip_code", 0.95),
    PatternRule(SemanticType.LATITUDE, "exact", "latitude", 0.95),
    PatternRule(SemanticType.LATITUDE, "exact", "lat", 0.90),
    PatternRule(SemanticType.LONGITUDE, "exact", "longitude", 0.95),
    PatternRule(SemanticType.LONGITUDE, "exact", "lng", 0.90),
    PatternRule(SemanticType.LONGITUDE, "exact", "lon", 0.90),
    
    # Business exact matches
    PatternRule(SemanticType.COMPANY, "exact", "company", 0.95),
    PatternRule(SemanticType.COMPANY, "exact", "company_name", 0.95),
    PatternRule(SemanticType.COMPANY, "exact", "organization", 0.90),
    PatternRule(SemanticType.JOB_TITLE, "exact", "job_title", 0.95),
    PatternRule(SemanticType.JOB_TITLE, "exact", "title", 0.70),  # Ambiguous
    PatternRule(SemanticType.JOB_TITLE, "exact", "position", 0.85),
    PatternRule(SemanticType.DEPARTMENT, "exact", "department", 0.95),
    PatternRule(SemanticType.DEPARTMENT, "exact", "dept", 0.90),
    
    # Financial exact matches
    PatternRule(SemanticType.PRICE, "exact", "price", 0.95),
    PatternRule(SemanticType.PRICE, "exact", "cost", 0.90),
    PatternRule(SemanticType.PRICE, "exact", "unit_price", 0.95),
    PatternRule(SemanticType.AMOUNT, "exact", "amount", 0.90),
    PatternRule(SemanticType.AMOUNT, "exact", "total", 0.85),
    PatternRule(SemanticType.AMOUNT, "exact", "subtotal", 0.90),
    PatternRule(SemanticType.CURRENCY, "exact", "currency", 0.95),
    PatternRule(SemanticType.CURRENCY_CODE, "exact", "currency_code", 0.95),
    PatternRule(SemanticType.CREDIT_CARD, "exact", "credit_card", 0.95),
    PatternRule(SemanticType.CREDIT_CARD, "exact", "card_number", 0.90),
    PatternRule(SemanticType.IBAN, "exact", "iban", 0.95),
    
    # Internet exact matches
    PatternRule(SemanticType.URL, "exact", "url", 0.95),
    PatternRule(SemanticType.URL, "exact", "website", 0.90),
    PatternRule(SemanticType.URL, "exact", "homepage", 0.90),
    PatternRule(SemanticType.URL, "exact", "link", 0.80),
    PatternRule(SemanticType.IP_ADDRESS, "exact", "ip_address", 0.95),
    PatternRule(SemanticType.IP_ADDRESS, "exact", "ip", 0.90),
    PatternRule(SemanticType.IPV6_ADDRESS, "exact", "ipv6", 0.95),
    PatternRule(SemanticType.MAC_ADDRESS, "exact", "mac_address", 0.95),
    PatternRule(SemanticType.MAC_ADDRESS, "exact", "mac", 0.85),
    PatternRule(SemanticType.DOMAIN, "exact", "domain", 0.90),
    PatternRule(SemanticType.DOMAIN, "exact", "domain_name", 0.95),
    PatternRule(SemanticType.SLUG, "exact", "slug", 0.95),
    PatternRule(SemanticType.SLUG, "exact", "permalink", 0.90),
    PatternRule(SemanticType.USER_AGENT, "exact", "user_agent", 0.95),
    
    # Identifier exact matches
    PatternRule(SemanticType.UUID, "exact", "uuid", 0.95),
    PatternRule(SemanticType.UUID, "exact", "guid", 0.95),
    PatternRule(SemanticType.SKU, "exact", "sku", 0.95),
    PatternRule(SemanticType.BARCODE, "exact", "barcode", 0.95),
    PatternRule(SemanticType.BARCODE, "exact", "ean", 0.90),
    PatternRule(SemanticType.BARCODE, "exact", "upc", 0.90),
    
    # Content exact matches
    PatternRule(SemanticType.DESCRIPTION, "exact", "description", 0.95),
    PatternRule(SemanticType.DESCRIPTION, "exact", "desc", 0.85),
    PatternRule(SemanticType.SUMMARY, "exact", "summary", 0.95),
    PatternRule(SemanticType.BODY, "exact", "body", 0.85),
    PatternRule(SemanticType.CONTENT, "exact", "content", 0.85),
    PatternRule(SemanticType.COMMENT, "exact", "comment", 0.90),
    PatternRule(SemanticType.COMMENT, "exact", "comments", 0.90),
    PatternRule(SemanticType.NOTE, "exact", "note", 0.90),
    PatternRule(SemanticType.NOTE, "exact", "notes", 0.90),
    PatternRule(SemanticType.BIO, "exact", "bio", 0.95),
    PatternRule(SemanticType.BIO, "exact", "biography", 0.95),
    PatternRule(SemanticType.BIO, "exact", "about", 0.80),
    
    # File exact matches
    PatternRule(SemanticType.FILENAME, "exact", "filename", 0.95),
    PatternRule(SemanticType.FILENAME, "exact", "file_name", 0.95),
    PatternRule(SemanticType.FILE_PATH, "exact", "file_path", 0.95),
    PatternRule(SemanticType.FILE_PATH, "exact", "filepath", 0.95),
    PatternRule(SemanticType.FILE_PATH, "exact", "path", 0.75),
    PatternRule(SemanticType.MIME_TYPE, "exact", "mime_type", 0.95),
    PatternRule(SemanticType.MIME_TYPE, "exact", "content_type", 0.90),
    PatternRule(SemanticType.FILE_EXTENSION, "exact", "extension", 0.85),
    PatternRule(SemanticType.FILE_EXTENSION, "exact", "file_extension", 0.95),
    
    # Color exact matches
    PatternRule(SemanticType.COLOR, "exact", "color", 0.95),
    PatternRule(SemanticType.COLOR, "exact", "colour", 0.95),
    PatternRule(SemanticType.HEX_COLOR, "exact", "hex_color", 0.95),
    PatternRule(SemanticType.HEX_COLOR, "exact", "color_hex", 0.95),
    
    # Numeric exact matches
    PatternRule(SemanticType.PERCENTAGE, "exact", "percentage", 0.95),
    PatternRule(SemanticType.PERCENTAGE, "exact", "percent", 0.90),
    PatternRule(SemanticType.QUANTITY, "exact", "quantity", 0.95),
    PatternRule(SemanticType.QUANTITY, "exact", "qty", 0.90),
    PatternRule(SemanticType.COUNT, "exact", "count", 0.90),
    PatternRule(SemanticType.RATING, "exact", "rating", 0.95),
    PatternRule(SemanticType.SCORE, "exact", "score", 0.90),
    PatternRule(SemanticType.PRIORITY, "exact", "priority", 0.95),
    PatternRule(SemanticType.SEQUENCE, "exact", "sequence", 0.90),
    PatternRule(SemanticType.ORDER, "exact", "order", 0.75),  # Ambiguous with purchase order
    PatternRule(SemanticType.ORDER, "exact", "sort_order", 0.95),
    PatternRule(SemanticType.ORDER, "exact", "display_order", 0.95),
    
    # Status/State exact matches (lower confidence - context needed)
    PatternRule(SemanticType.STATUS, "exact", "status", 0.70),
    PatternRule(SemanticType.TYPE, "exact", "type", 0.65),
    PatternRule(SemanticType.CATEGORY, "exact", "category", 0.85),
    PatternRule(SemanticType.LEVEL, "exact", "level", 0.80),
    PatternRule(SemanticType.ROLE, "exact", "role", 0.85),
    
    # ══════════════════════════════════════════════════════════════════
    # SUFFIX MATCHES (confidence: 0.85)
    # ══════════════════════════════════════════════════════════════════
    PatternRule(SemanticType.EMAIL, "suffix", "_email", 0.90),
    PatternRule(SemanticType.PHONE, "suffix", "_phone", 0.90),
    PatternRule(SemanticType.URL, "suffix", "_url", 0.90),
    PatternRule(SemanticType.UUID, "suffix", "_uuid", 0.95),
    PatternRule(SemanticType.IMAGE_URL, "suffix", "_image_url", 0.95),
    PatternRule(SemanticType.IMAGE_URL, "suffix", "_image", 0.80),
    PatternRule(SemanticType.IMAGE_URL, "suffix", "_photo", 0.80),
    PatternRule(SemanticType.IMAGE_URL, "suffix", "_avatar", 0.85),
    PatternRule(SemanticType.IMAGE_URL, "suffix", "_thumbnail", 0.85),
    
    # Temporal suffix matches (very high confidence)
    PatternRule(SemanticType.CREATED_AT, "suffix", "_at", 0.85),
    PatternRule(SemanticType.CREATED_AT, "suffix", "created_at", 0.95),
    PatternRule(SemanticType.UPDATED_AT, "suffix", "updated_at", 0.95),
    PatternRule(SemanticType.UPDATED_AT, "suffix", "modified_at", 0.95),
    PatternRule(SemanticType.DELETED_AT, "suffix", "deleted_at", 0.95),
    PatternRule(SemanticType.EXPIRES_AT, "suffix", "expires_at", 0.95),
    PatternRule(SemanticType.EXPIRES_AT, "suffix", "expiry_date", 0.95),
    PatternRule(SemanticType.DATE, "suffix", "_date", 0.85),
    PatternRule(SemanticType.DATETIME, "suffix", "_datetime", 0.95),
    PatternRule(SemanticType.TIME, "suffix", "_time", 0.80),  # Ambiguous
    
    # ══════════════════════════════════════════════════════════════════
    # PREFIX MATCHES (confidence: 0.85)
    # ══════════════════════════════════════════════════════════════════
    PatternRule(SemanticType.BOOLEAN_FLAG, "prefix", "is_", 0.90),
    PatternRule(SemanticType.BOOLEAN_FLAG, "prefix", "has_", 0.90),
    PatternRule(SemanticType.BOOLEAN_FLAG, "prefix", "can_", 0.90),
    PatternRule(SemanticType.BOOLEAN_FLAG, "prefix", "should_", 0.85),
    PatternRule(SemanticType.BOOLEAN_FLAG, "prefix", "allow_", 0.85),
    PatternRule(SemanticType.BOOLEAN_FLAG, "prefix", "enable_", 0.85),
    
    # ══════════════════════════════════════════════════════════════════
    # CONTAINS MATCHES (confidence: 0.80)
    # ══════════════════════════════════════════════════════════════════
    PatternRule(SemanticType.EMAIL, "contains", "email", 0.85),
    PatternRule(SemanticType.ADDRESS, "contains", "address", 0.80),
    PatternRule(SemanticType.PHONE, "contains", "phone", 0.85),
    PatternRule(SemanticType.PHONE, "contains", "mobile", 0.80),
    
    # ══════════════════════════════════════════════════════════════════
    # REGEX MATCHES (variable confidence)
    # ══════════════════════════════════════════════════════════════════
    PatternRule(SemanticType.BOOLEAN_FLAG, "regex", r"^(is|has|can|should|allow|enable|disable)_\w+$", 0.90),
    PatternRule(SemanticType.BOOLEAN_FLAG, "regex", r"^\w+_(enabled|disabled|active|visible|hidden|locked)$", 0.90),
    PatternRule(SemanticType.UUID, "regex", r"^[a-z]+_uuid$", 0.90),
    PatternRule(SemanticType.ID, "regex", r"^\w+_id$", 0.70),  # Could be FK, handled specially
]
```

#### 6.5 Confidence Modifiers

```python
CONFIDENCE_MODIFIERS: dict[str, float] = {
    # Positive modifiers
    "sql_type_matches": +0.05,      # VARCHAR for EMAIL, INT for AGE
    "multiple_patterns": +0.05,      # Multiple rules match same type
    "table_context_supports": +0.05, # "name" in "users" table
    
    # Negative modifiers
    "ambiguous_token": -0.20,        # status, type, code, value, data, name
    "very_short_name": -0.10,        # < 3 characters
    "sql_type_mismatch": -0.15,      # VARCHAR for expected INT
    "generic_name": -0.15,           # field, column, attr, val
}

AMBIGUOUS_TOKENS: set[str] = {
    "status", "state", "type", "code", "value", "data", "name",
    "key", "ref", "flag", "mode", "kind", "class", "attr", "field",
    "info", "meta", "extra", "misc", "other", "val", "tmp", "temp"
}
```

---

### 7. ClassificationResult

Result of classifying a column.

```python
@dataclass
class ClassificationResult:
    """Result of column classification pipeline."""
    
    # Classification
    column: ColumnSchema            # The classified column
    semantic_type: SemanticType     # Inferred type
    confidence: float               # 0.0 - 1.0
    
    # Generator assignment
    faker_provider: str             # e.g., "faker.email"
    faker_kwargs: dict[str, Any]    # Provider arguments
    
    # Debug info
    matched_layer: int              # 1-5 (which layer matched)
    matched_pattern: str | None     # Pattern that matched
    reasoning: str                  # Human-readable explanation
    
    # Flags
    needs_review: bool              # True if confidence < 0.6
    is_auto_increment: bool         # Skip generation
    is_foreign_key: bool            # Use FK resolver
```

---

### 8. GenerationConfig

User-defined configuration for data generation.

```python
@dataclass
class GenerationConfig:
    """Root configuration for data generation."""
    
    # Defaults
    default_rows: int = 1000
    batch_size: int = 1000
    locale: str = "en_US"
    null_probability: float = 0.1
    
    # Tables
    tables: dict[str, TableConfig]  # Per-table overrides
    
    # Special handling
    self_references: dict[str, SelfReferenceConfig]
    
    # Warnings
    warnings: list[ConfigWarning]   # Unparseable constraints, etc.

@dataclass
class TableConfig:
    """Per-table configuration."""
    
    rows: int | None = None         # Override default_rows
    skip: bool = False              # Skip this table
    columns: dict[str, ColumnConfig]
    foreign_keys: dict[str, ForeignKeyConfig]

@dataclass
class ColumnConfig:
    """Per-column configuration."""
    
    provider: str | None = None     # Faker provider override
    values: list[Any] | None = None # Fixed value list
    weights: list[float] | None = None  # Probability weights
    unique: bool = False            # Force uniqueness
    min: float | None = None        # Numeric min
    max: float | None = None        # Numeric max
    nullable_chance: float = 0.0    # Chance to insert NULL

@dataclass
class ForeignKeyConfig:
    """Per-FK configuration."""
    
    distribution: str = "uniform"   # uniform, exponential, normal
    sample_size: int = 1000         # Parent IDs to cache

@dataclass
class SelfReferenceConfig:
    """Self-referential FK handling."""
    
    column: str                     # FK column name
    strategy: str = "two_pass"      # Always two_pass for now
    root_probability: float = 0.1   # Chance of NULL parent
```

**Status**: Pydantic models to be implemented in `hypothesis/config/models.py`

---

### 9. GenerationSession

Runtime state during data generation.

```python
@dataclass
class GenerationSession:
    """Runtime state for a generation session."""
    
    # Configuration
    config: GenerationConfig
    connection: DatabaseConnection
    
    # Schema
    tables: list[TableSchema]
    insertion_order: list[str]      # From DependencyGraph
    classifications: dict[str, ClassificationResult]  # column_key → result
    
    # Runtime caches
    fk_cache: dict[str, list[Any]]  # table.column → parent IDs
    unique_tracker: dict[str, set]  # column_key → generated values
    
    # Progress
    rows_generated: dict[str, int]  # table → count
    rows_inserted: dict[str, int]   # table → count
    start_time: datetime
    
    # Errors
    skipped_rows: list[SkippedRow]
    warnings: list[GenerationWarning]
```

---

## Entity Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                      GenerationSession                           │
│  (orchestrates entire generation run)                            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ DatabaseConnection│  │ GenerationConfig │  │ DependencyGraph │
│ (DB operations)   │  │ (user settings)  │  │ (insertion order)│
└─────────────────┘   └─────────────────┘   └─────────────────┘
          │                     │
          ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│  TableSchema    │◄──│  TableConfig    │
│  (from DB)      │   │  (from config)  │
└────────┬────────┘   └─────────────────┘
         │
         ▼
┌─────────────────┐   ┌─────────────────────┐
│  ColumnSchema   │──►│ ClassificationResult│
│  (from DB)      │   │ (from pipeline)     │
└────────┬────────┘   └─────────────────────┘
         │
         ▼
┌─────────────────┐
│  ForeignKey     │
│  (relationships)│
└─────────────────┘
```

---

## State Transitions

### Generation Session States

```
[INIT] → [CONNECTED] → [INSPECTED] → [CLASSIFIED] → [GENERATING] → [COMPLETE]
                                                          │
                                                          ▼
                                                     [FAILED]
```

| State | Entry Condition | Exit Condition |
|-------|-----------------|----------------|
| INIT | Session created | Connection validated |
| CONNECTED | DB accessible | Schema reflected |
| INSPECTED | All tables loaded | All columns classified |
| CLASSIFIED | Pipeline complete | First batch inserted |
| GENERATING | Insertion started | All tables complete |
| COMPLETE | All rows inserted | — |
| FAILED | Any unrecoverable error | — |

---

## Validation Rules

### ColumnSchema
- `name` must not be empty
- `sql_type` must be a recognized type or logged as warning
- If `is_foreign_key`, `ForeignKey` record must exist
- If `enum_values` present, must have at least one value

### GenerationConfig
- `default_rows` must be positive
- `batch_size` must be positive and ≤ 100,000
- `null_probability` must be in [0.0, 1.0]
- `weights` if present must sum to 1.0 (normalized if not)

### ForeignKey
- `table` and `referenced_table` must exist in schema
- `column` must exist in `table`
- `referenced_column` must exist in `referenced_table`
