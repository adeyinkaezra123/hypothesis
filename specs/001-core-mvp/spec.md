# Feature Specification: Semantic Database Seeder MVP

**Feature Branch**: `001-core-mvp`  
**Created**: 2026-01-11  
**Updated**: 2026-01-12 🆕  
**Status**: Draft  
**Input**: User description: "Core MVP implementation for semantic database seeder with schema introspection, semantic mapping, and data generation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspect Database Schema (Priority: P1)

A developer wants to understand the structure of their database before generating test data. They run a command to inspect their PostgreSQL or MySQL database and see a formatted view of all tables, columns, data types, constraints, and relationships.

**Why this priority**: This is the foundation. Users must see and understand their schema before they can generate meaningful data. It validates connectivity and builds confidence in the tool.

**Independent Test**: Can be fully tested by connecting to any PostgreSQL or MySQL database and displaying its schema. Delivers immediate value by providing schema visibility.

**Acceptance Scenarios**:

1. **Given** a valid PostgreSQL connection string, **When** user runs the inspect command, **Then** all tables are listed with their columns, data types, and constraints displayed in a formatted table view
2. **Given** a valid MySQL connection string, **When** user runs the inspect command, **Then** all tables are listed with their columns, data types, and constraints displayed in a formatted table view
3. **Given** a database with foreign key relationships, **When** user runs inspect with verbose mode, **Then** relationships between tables are clearly shown with parent-child connections
4. **Given** an invalid connection string, **When** user runs inspect, **Then** a clear error message explains the connection failure with suggested fixes
5. 🆕 **Given** a database schema, **When** user runs inspect, **Then** each column shows the inferred semantic type with a confidence indicator (✓ for high confidence, ⚠️ for low confidence)
6. 🆕 **Given** a database with ENUM columns, **When** user runs inspect, **Then** ENUM values are displayed alongside the column definition
7. 🆕 **Given** a database with CHECK constraints, **When** user runs inspect, **Then** parseable constraints show their extracted rules (e.g., "age: 18-150")
8. 🆕 **Given** a database schema, **When** user runs inspect with `--format json`, **Then** output is valid JSON suitable for programmatic consumption
9. 🆕 **Given** a database schema, **When** user runs inspect with `--format markdown`, **Then** output is valid Markdown suitable for documentation

---

### 🆕 User Story 1.5 - Analyze Schema and Generate Configuration (Priority: P2)

A developer wants to generate a starter configuration file with intelligent defaults based on their schema. They run an analyze command that produces a YAML config file with semantic mappings, suggested row counts, and flagged columns that need manual review.

**Why this priority**: Bridges inspection and generation. Reduces manual config effort significantly while keeping humans in the loop for ambiguous cases.

**Independent Test**: Can be tested by running analyze on any schema and verifying the output config is valid, loadable, and reflects the schema structure.

**Acceptance Scenarios**:

1. 🆕 **Given** a valid database connection, **When** user runs `analyze -o config.yaml`, **Then** a complete YAML configuration file is generated with all tables and columns mapped
2. 🆕 **Given** columns with high-confidence semantic matches (email, phone, name), **When** config is generated, **Then** those columns have appropriate Faker providers assigned without warning markers
3. 🆕 **Given** columns with low-confidence matches (generic names like "data", "value", "code"), **When** config is generated, **Then** those columns are marked with `# ⚠️ LOW CONFIDENCE - please review` comments
4. 🆕 **Given** ENUM columns in the schema, **When** config is generated, **Then** the enum values are automatically populated as allowed values with equal weights
5. 🆕 **Given** foreign key relationships, **When** config is generated, **Then** FK columns include distribution hints (uniform, exponential) with sensible defaults
6. 🆕 **Given** tables with varying expected sizes (reference tables vs. transactional tables), **When** config is generated, **Then** row count suggestions reflect typical ratios (e.g., 50 countries, 1000 users, 5000 orders)
7. 🆕 **Given** self-referential foreign keys (e.g., employees.manager_id), **When** config is generated, **Then** a `self_reference` section is included with two-pass strategy configuration
8. 🆕 **Given** an existing config file, **When** user runs `analyze --update`, **Then** new columns/tables are added while preserving existing customizations
9. 🆕 **Given** the `--ai` flag and valid API credentials, **When** analyze runs, **Then** ambiguous columns are sent to LLM for enhanced inference with results shown as suggestions for user approval

---

### User Story 2 - Generate Basic Test Data (Priority: P1)

A developer wants to populate their empty development database with realistic test data. They run a generate command specifying how many rows they want, and the tool automatically creates appropriate fake data for each table, respecting foreign key relationships.

**Why this priority**: This is the core value proposition. Without data generation, the tool provides no utility beyond schema viewing.

**Independent Test**: Can be tested by generating data into an empty database with foreign key relationships and verifying referential integrity is maintained.

**Acceptance Scenarios**:

1. **Given** an empty database with tables having no foreign keys, **When** user runs generate with 1000 rows, **Then** each table receives 1000 rows of fake data appropriate to column types
2. **Given** a database with parent-child foreign key relationships, **When** user runs generate, **Then** parent tables are populated before child tables and all foreign key references are valid
3. **Given** a table with unique constraints, **When** user runs generate, **Then** all generated values respect uniqueness with no constraint violations
4. **Given** a table with NOT NULL columns, **When** user runs generate, **Then** all NOT NULL columns have values and no NULLs are inserted
5. **Given** a large generation request (100K+ rows), **When** user runs generate, **Then** progress is displayed showing tables being processed and estimated completion time

---

### User Story 3 - Semantic Column Recognition (Priority: P2)

A developer wants the tool to automatically recognize that columns like "email", "first_name", or "phone_number" should contain contextually appropriate fake data, not random strings. The tool should intelligently map column names to appropriate data generators.

**Why this priority**: This differentiates Hypothesis from basic data generators. Semantic intelligence is the key value add, but basic generation must work first.

**Independent Test**: Can be tested by creating a table with common column names (email, name, phone, address) and verifying the generated data matches expected formats.

**Acceptance Scenarios**:

1. **Given** a column named "email" or containing "email" substring, **When** data is generated, **Then** values are valid email formats (e.g., user@domain.com)
2. **Given** a column named "first_name", "last_name", or "name", **When** data is generated, **Then** values are realistic human names
3. **Given** a column named "phone" or "mobile", **When** data is generated, **Then** values are realistic phone number formats
4. **Given** a column ending in "_at" (created_at, updated_at), **When** data is generated, **Then** values are appropriate datetime values
5. **Given** a column named "address", "street", "city", or "country", **When** data is generated, **Then** values are realistic geographic data
6. **Given** a column the system doesn't recognize, **When** data is generated, **Then** fallback to data type-appropriate random values (random string for VARCHAR, random int for INTEGER, etc.)
7. 🆕 **Given** a compound column name like "customer_billing_address", **When** the system classifies it, **Then** tokenization correctly identifies "address" as the semantic signal
8. 🆕 **Given** a column name in camelCase (firstName, emailAddress), **When** the system classifies it, **Then** the name is normalized to tokens before matching
9. 🆕 **Given** an ambiguous column name and table context (e.g., "code" in "products" table), **When** the system classifies it, **Then** table name is used as a disambiguation hint (product code vs. error code)

---

### User Story 4 - Configuration File Support (Priority: P2)

A developer wants to customize data generation rules for their specific schema. They create a YAML configuration file specifying row counts per table, custom column mappings, and value constraints, then run the tool using that configuration.

**Why this priority**: Customization enables real-world usage beyond simple demos. Different projects have different needs.

**Independent Test**: Can be tested by creating a config file with custom mappings and verifying the generated data follows those rules.

**Acceptance Scenarios**:

1. **Given** a config file specifying 5000 rows for "users" table and 10000 for "posts", **When** generate runs, **Then** those exact row counts are created
2. **Given** a config file with custom column mapping (status column should only contain "active", "inactive", "pending"), **When** data is generated, **Then** only those values appear with optional weights
3. **Given** a config file with environment variable references (${DB_HOST}), **When** the tool loads config, **Then** environment variables are interpolated correctly
4. **Given** no config file exists, **When** user runs generate, **Then** sensible defaults are used (1000 rows per table, automatic semantic mapping)

---

### User Story 5 - Dry Run Preview (Priority: P3)

A developer wants to preview what data will be generated before actually inserting it into the database. They run a dry run command that shows sample rows for each table without making any database changes.

**Why this priority**: Reduces risk of unwanted data insertion. Helpful for validation but not essential for core functionality.

**Independent Test**: Can be tested by running dry run and verifying no database writes occur while sample data is displayed.

**Acceptance Scenarios**:

1. **Given** any valid database connection, **When** user runs generate with dry-run flag, **Then** 5 sample rows per table are displayed in formatted tables
2. **Given** a dry run request, **When** the command completes, **Then** no data has been inserted into the database (row counts unchanged)
3. **Given** a dry run with verbose mode, **When** executed, **Then** the semantic mappings being used for each column are displayed
4. 🆕 **Given** a dry run, **When** executed, **Then** each column shows its confidence score and the reasoning chain (column name → pattern → generator)
5. 🆕 **Given** columns with low confidence scores (<60%), **When** dry run completes, **Then** a summary lists all low-confidence columns with suggested config overrides

---

### User Story 6 - Handle Existing Data (Priority: P3)

A developer wants to add more test data to a database that already has some data, or wants to start fresh by truncating existing data first. The tool should provide options for both scenarios.

**Why this priority**: Important for real-world usage where databases aren't always empty, but basic generation on empty databases should work first.

**Independent Test**: Can be tested by generating into a database with existing data and verifying correct behavior based on flags used.

**Acceptance Scenarios**:

1. **Given** a database with existing data, **When** user runs generate without flags, **Then** an error is shown explaining the table has data with instructions to use --truncate or --append
2. **Given** a database with existing data, **When** user runs generate with --truncate flag, **Then** existing data is deleted and new data is inserted
3. **Given** a database with existing auto-increment IDs, **When** user runs generate with --append flag, **Then** new data is added with IDs continuing from the current maximum

---

### Edge Cases

- What happens when database has circular foreign key dependencies? System should detect cycles, warn user, and attempt resolution via nullable FK columns with a two-pass insert strategy
- What happens when unique constraint cannot be satisfied after maximum retry attempts (10)? System should log warning, skip that row, and continue with remaining rows
- What happens when database has unsupported column types (geometry, spatial)? System should skip those columns with a logged warning and continue generating other columns
- What happens when connection is lost mid-generation? System should rollback current batch, log progress, and provide clear error with rows successfully inserted
- What happens when database has no tables? System should display friendly message that no tables were found
- What happens when user specifies a table that doesn't exist? System should list available tables and suggest similar names if possible
- 🆕 What happens when CHECK constraint uses complex expressions (function calls, subqueries)? System should log that constraint cannot be parsed and fall back to type-based generation with a warning
- 🆕 What happens when LLM API is unavailable during `--ai` analyze? System should fall back to pattern matching, log warning, and continue without AI enhancement
- 🆕 What happens when schema changes after config was generated? The `analyze --update` command should detect new/removed columns and show a diff

## Requirements *(mandatory)*

### Functional Requirements

**Database Connectivity**
- **FR-001**: System MUST connect to PostgreSQL databases version 12 or higher
- **FR-002**: System MUST connect to MySQL databases version 8.0 or higher
- **FR-003**: System MUST validate database connections before attempting any operations
- **FR-004**: System MUST verify write permissions before data generation
- **FR-005**: System MUST support connection via direct connection string (postgresql://..., mysql://...)
- **FR-006**: System MUST support connection via named database from configuration file
- **FR-007**: System MUST read credentials from standard credential files (.pgpass for PostgreSQL, .my.cnf for MySQL)

**Schema Introspection**
- **FR-008**: System MUST reflect complete database schema including all tables, columns, and constraints
- **FR-009**: System MUST identify all foreign key relationships between tables
- **FR-010**: System MUST detect unique constraints on columns and column combinations
- **FR-011**: System MUST determine correct table insertion order based on foreign key dependencies
- **FR-012**: System MUST identify ENUM column types and extract their allowed values
- **FR-013**: System MUST distinguish between base tables and views (skip views)
- 🆕 **FR-013.1**: System MUST parse simple CHECK constraints to extract value ranges and allowed values
- 🆕 **FR-013.2**: System MUST detect self-referential foreign keys and flag them for special handling
- 🆕 **FR-013.3**: System MUST identify which tables reference each table (reverse FK mapping)

**🆕 Semantic Classification Pipeline**

- 🆕 **FR-014**: System MUST classify columns using a layered approach in the following priority order:
  1. Schema constraints (ENUM values, CHECK constraints, FK references)
  2. Pattern matching on column names
  3. Token-based analysis for compound names
  4. SQL type fallback
- 🆕 **FR-014.1**: System MUST normalize column names before matching (camelCase → snake_case, lowercase)
- 🆕 **FR-014.2**: System MUST tokenize compound column names and score individual tokens for semantic signals
- 🆕 **FR-014.3**: System MUST use table name as disambiguation context for ambiguous column names
- 🆕 **FR-014.4**: System MUST assign a confidence score (0.0-1.0) to each column classification
- 🆕 **FR-014.5**: System MUST flag columns with confidence below 0.6 as requiring user review

**Semantic Mapping** *(Updated)*
- 🆕 ~~FR-014~~ **FR-015**: System MUST recognize at least 30 common column name patterns across these categories:
  - Personal: email, first_name, last_name, full_name, phone, username, password, age, gender, date_of_birth, ssn
  - Location: address, street, city, state, country, postal_code, latitude, longitude
  - Business: company, job_title
  - Financial: price, currency, credit_card
  - Internet: url, ip_address, domain, slug
  - Identifiers: uuid, id
  - Temporal: date, datetime, time, created_at, updated_at
  - Content: title, description, text
  - Boolean: is_*, has_*, *_enabled, *_active
- 🆕 ~~FR-015~~ **FR-016**: System MUST support exact match, substring match, regex pattern match, and token-based match for column name recognition
- **FR-017**: System MUST allow users to override default mappings via configuration file
- **FR-018**: System MUST fall back to data type-based generation when column name is not recognized
- **FR-019**: Custom user mappings MUST take priority over default semantic mappings
- 🆕 **FR-019.1**: System MUST boost confidence score when SQL type aligns with inferred semantic type (e.g., "email" + VARCHAR = higher confidence)
- 🆕 **FR-019.2**: System MUST reduce confidence score for known ambiguous tokens (e.g., "status", "type", "code", "value", "data")

**Data Generation** *(renumbered)*
- **FR-020**: System MUST generate valid data for all common data types (VARCHAR, TEXT, INTEGER, BIGINT, DECIMAL, FLOAT, DATE, DATETIME, TIMESTAMP, BOOLEAN, JSON, UUID)
- **FR-021**: System MUST respect NOT NULL constraints by always generating values for required columns
- **FR-022**: System MUST respect unique constraints by tracking generated values and regenerating on collision
- **FR-023**: System MUST respect foreign key constraints by selecting valid parent record IDs
- **FR-024**: System MUST handle nullable columns by optionally generating NULL values (configurable probability)
- **FR-025**: System MUST support configurable row counts per table
- **FR-026**: System MUST support weighted random selection for value lists
- 🆕 **FR-026.1**: System MUST respect extracted CHECK constraint ranges when generating numeric values
- 🆕 **FR-026.2**: System MUST select from ENUM values for ENUM columns (no semantic inference needed)
- 🆕 **FR-026.3**: System MUST handle self-referential FKs using two-pass generation (NULL first pass, update second pass)

**Performance** *(renumbered)*
- **FR-027**: System MUST use batch inserts for efficient data loading
- **FR-028**: System MUST support configurable batch sizes (default 1000 rows)
- **FR-029**: System MUST display progress during long-running generation operations
- **FR-030**: System MUST use streaming generation to avoid memory exhaustion on large datasets

**Configuration** *(renumbered)*
- **FR-031**: System MUST support YAML configuration files
- **FR-032**: System MUST support environment variable interpolation in configuration values
- **FR-033**: System MUST search for configuration in standard locations (.hypothesisrc, .hypothesis.yml)
- **FR-034**: System MUST support per-table configuration (row counts, column overrides, skip flags)
- 🆕 **FR-034.1**: Generated config files MUST include comments explaining each section
- 🆕 **FR-034.2**: Generated config files MUST include warning comments on low-confidence mappings

**CLI Interface** *(renumbered and expanded)*
- **FR-035**: System MUST provide an "inspect" command to view database schema
- 🆕 **FR-035.1**: Inspect command MUST show confidence indicators for each column's semantic classification
- 🆕 **FR-035.2**: Inspect command MUST show table dependency order for seeding
- 🆕 **FR-035.3**: Inspect command MUST show detected constraints (ENUMs, CHECKs, FKs) per column
- 🆕 **FR-035.4**: Inspect command MUST support `--format` flag with options: table (default), json, markdown
- **FR-036**: System MUST provide a "generate" command to create and insert fake data
- 🆕 **FR-036.1**: Generate command MUST warn (but continue) when low-confidence columns are encountered by default
- 🆕 **FR-036.2**: Generate command MUST support `--strict` flag that blocks generation until all low-confidence columns are resolved
- 🆕 **FR-036.3**: Generate command MUST support `--interactive` flag that prompts user to resolve low-confidence columns before generation
- 🆕 **FR-036.4**: In `--strict` mode, system MUST list all low-confidence columns and suggest resolution methods (`--interactive`, `--ai`, or manual config edit)
- **FR-037**: System MUST provide a "validate" command to check configuration without executing
- 🆕 **FR-038**: System MUST provide an "analyze" command to generate a configuration file from schema
- 🆕 **FR-038.1**: Analyze command MUST output a complete, valid YAML configuration file
- 🆕 **FR-038.2**: Analyze command MUST include all tables and columns from the schema
- 🆕 **FR-038.3**: Analyze command MUST flag low-confidence mappings with warning comments
- 🆕 **FR-038.4**: Analyze command MUST suggest realistic row count ratios based on table relationships
- 🆕 **FR-038.5**: Analyze command MUST support `--update` flag to merge with existing config
- 🆕 **FR-038.6**: Analyze command MUST support `--ai` flag for LLM-enhanced inference (optional feature)
- **FR-039**: System MUST provide formatted, colorized output for better readability
- **FR-040**: System MUST provide helpful error messages with suggested fixes

**🆕 LLM Integration (Optional)**
- 🆕 **FR-041**: LLM integration MUST be opt-in via `--ai` flag, never enabled by default
- 🆕 **FR-042**: LLM requests MUST only send schema metadata (table names, column names, types, constraints), never actual data
- 🆕 **FR-043**: LLM suggestions MUST be presented for user review, not automatically applied
- 🆕 **FR-044**: System MUST function fully without LLM access (graceful degradation)
- 🆕 **FR-045**: LLM responses MUST be cached to avoid redundant API calls for unchanged schemas
- 🆕 **FR-046**: System MUST batch all ambiguous columns into a single LLM request per schema (not per-column)
- 🆕 **FR-047**: System MUST support configurable LLM provider (OpenAI, Anthropic, local) via environment variables

**Security** *(renumbered)*
- **FR-048**: System MUST never log or display passwords in plain text
- **FR-049**: System MUST redact sensitive information from all log output
- **FR-050**: System MUST respect file permission requirements for credential files
- 🆕 **FR-051**: System MUST never send actual database content to external services (LLM or otherwise)

### Key Entities

- **Database Connection**: Represents a connection to a PostgreSQL or MySQL database, including host, port, database name, and credentials
- **Table Schema**: Represents a database table with its columns, data types, constraints, and relationships to other tables
- **Column Mapping**: Represents the association between a column name/type and a data generator strategy
- **Generation Configuration**: Represents user-defined rules for data generation including row counts, custom mappings, and table-specific settings
- **Dependency Graph**: Represents the directed acyclic graph of table dependencies based on foreign key relationships
- 🆕 **Classification Result**: Represents the semantic type, confidence score, and generator assignment for a single column
- 🆕 **Semantic Type**: Enumeration of recognized column semantics (EMAIL, PHONE, NAME, ADDRESS, etc.) with associated Faker providers

### Assumptions

- Users have valid credentials and network access to their target databases
- Target databases have standard schemas (no exotic custom types beyond what's documented)
- Users understand basic database concepts (tables, columns, foreign keys)
- Configuration files are trusted (no sandboxing of config-defined values)
- PostgreSQL and MySQL drivers are installed separately based on user's target database
- 🆕 LLM API credentials are user's responsibility to configure if using `--ai` feature
- 🆕 Well-named columns (following common conventions) will achieve higher accuracy than poorly-named columns

---

## 🆕 Classification Architecture

### Layered Classification Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  Input: Column "status" | Type: VARCHAR(50) | Constraints: —    │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Schema Constraints                                     │
│  ─────────────────────────────────────────────────────────────── │
│  • Is it an ENUM? → Use enum values (confidence: 1.0)           │
│  • Is it a Foreign Key? → Sample from parent (confidence: 1.0)  │
│  • Has CHECK constraint? → Parse and apply (confidence: 0.95)   │
└────────────────────────────┬────────────────────────────────────┘
                             │ No constraint match
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: Pattern Matching                                       │
│  ─────────────────────────────────────────────────────────────── │
│  • Exact match: "email" → EMAIL (confidence: 0.95)              │
│  • Regex match: /phone|mobile|cell/ → PHONE (confidence: 0.90)  │
│  • Suffix match: /_at$/ → DATETIME (confidence: 0.85)           │
└────────────────────────────┬────────────────────────────────────┘
                             │ No pattern match
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: Token Analysis                                         │
│  ─────────────────────────────────────────────────────────────── │
│  • Tokenize: "customer_billing_address" → [customer,billing,address]
│  • Score tokens: "address" has weight 0.8 for ADDRESS           │
│  • Check combinations: {billing, address} → STREET (0.85)       │
└────────────────────────────┬────────────────────────────────────┘
                             │ No strong token signal
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 4: Table Context (disambiguation)                         │
│  ─────────────────────────────────────────────────────────────── │
│  • "code" in products table → product_code (confidence: 0.7)    │
│  • "code" in errors table → error_code (confidence: 0.7)        │
│  • "type" in payments table → payment_type (confidence: 0.65)   │
└────────────────────────────┬────────────────────────────────────┘
                             │ No context match
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 5: SQL Type Fallback                                      │
│  ─────────────────────────────────────────────────────────────── │
│  • VARCHAR/TEXT → faker.sentence() (confidence: 0.5)            │
│  • INTEGER → faker.random_int() (confidence: 0.5)               │
│  • TIMESTAMP → faker.date_time() (confidence: 0.6)              │
│  • ⚠️ Flag for user review                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Confidence Score Modifiers

| Factor | Modifier |
|--------|----------|
| SQL type aligns with semantic type | +0.05 |
| Multiple patterns match same type | +0.05 |
| Table name supports inference | +0.05 |
| Known ambiguous token (status, type, code, value) | -0.20 |
| Very short column name (< 3 chars) | -0.10 |
| No pattern match, pure type fallback | cap at 0.50 |

---

## 🆕 Analyze Command Specification

### Command Syntax

```bash
# Generate new config
hypothesis analyze <connection> -o seed_config.yaml

# Generate with LLM enhancement
hypothesis analyze <connection> -o seed_config.yaml --ai

# Update existing config with schema changes  
hypothesis analyze <connection> --config existing.yaml --update

# Preview without writing file
hypothesis analyze <connection> --dry-run
```

### Output Format

```yaml
# Generated by: hypothesis analyze
# Database: postgres://localhost/myapp_development
# Generated at: 2024-01-15T10:30:00Z
# Classification accuracy: 87% high-confidence, 13% needs review
#
# Columns marked with ⚠️ have low confidence and should be reviewed.

defaults:
  rows: 1000
  batch_size: 5000
  locale: en_US
  null_probability: 0.1

tables:
  # ═══════════════════════════════════════════════════════════════
  # Tier 1: No dependencies (seeded first)
  # ═══════════════════════════════════════════════════════════════
  
  users:
    rows: 1000
    columns:
      id:
        generator: auto  # SERIAL - handled by database
      email:
        provider: email
        unique: true
        confidence: 0.95  # Matched pattern: /email/
      password_hash:
        provider: sha256
        confidence: 0.90  # Matched pattern: /password|pwd/
      first_name:
        provider: first_name
        confidence: 0.95  # Matched pattern: /first.?name/
      # ⚠️ LOW CONFIDENCE (0.45) - please review
      role:
        provider: random_element
        values: [admin, user, moderator]  # Suggested - adjust to your domain
        confidence: 0.45
      # ⚠️ LOW CONFIDENCE (0.40) - please review
      metadata:
        provider: pydict
        confidence: 0.40
        # Consider specifying structure:
        # schema:
        #   preferences: object
        #   settings: array

  # ═══════════════════════════════════════════════════════════════
  # Tier 2: Depends on users
  # ═══════════════════════════════════════════════════════════════
  
  orders:
    rows: 5000  # Suggested: 5x users (typical ratio)
    columns:
      user_id:
        generator: foreign_key
        reference: users.id
        distribution: exponential  # Some users have many orders
      status:
        generator: enum  # ENUM detected in schema
        values: [pending, processing, shipped, delivered, cancelled]
        weights: [0.1, 0.1, 0.2, 0.5, 0.1]

# ═══════════════════════════════════════════════════════════════
# Special handling
# ═══════════════════════════════════════════════════════════════

self_references:
  employees:
    column: manager_id
    strategy: two_pass
    root_probability: 0.1  # 10% have no manager

# Unparseable constraints (manual handling required)
warnings:
  - table: payments
    column: metadata  
    constraint: "jsonb_typeof(metadata) = 'object'"
    message: "Complex JSON constraint cannot be auto-parsed"
```

### Interactive Mode (with --ai)

```
$ hypothesis analyze postgres://localhost/mydb -o config.yaml --ai

Analyzing schema...
  ✓ 12 tables detected
  ✓ 47 columns analyzed
  ✓ 41 high-confidence mappings (87%)
  ✓ 6 low-confidence mappings (13%)

Consulting AI for ambiguous columns...

┌─────────────────────────────────────────────────────────────────────┐
│  AI Suggestions (review before accepting)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  users.role                                                          │
│    Pattern match: random_element([admin, user, moderator])          │
│    AI suggests:   random_element([customer, admin, support])        │
│    Reasoning:     "E-commerce schema; 'customer' more likely"       │
│    Accept? [y/n/edit]: y                                            │
│                                                                      │
│  orders.source                                                       │
│    Pattern match: pystr (fallback)                                  │
│    AI suggests:   random_element([web, mobile, api, in_store])      │
│    Reasoning:     "Order source typically indicates channel"        │
│    Accept? [y/n/edit]: e                                            │
│    Enter values: web, ios_app, android_app, phone                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

Config written to: config.yaml
  - 41 auto-mapped columns
  - 6 AI-assisted columns (2 edited)
  
Run `hypothesis generate --config config.yaml` to seed database.
```

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can connect and inspect any PostgreSQL or MySQL database schema in under 10 seconds
- **SC-002**: Users can generate 10,000 rows per table at a rate of 10,000+ rows per second for simple tables (no foreign keys)
- **SC-003**: Users can generate 10,000 rows per table at a rate of 5,000+ rows per second for tables with foreign key relationships
- **SC-004**: System generates 1 million total rows in under 5 minutes for typical schemas (10-20 tables)
- **SC-005**: Memory usage stays under 500MB when generating 1 million rows
- **SC-006**: Semantic column recognition achieves 85%+ accuracy on common column naming patterns (email, name, phone, address, date, etc.) 🆕 *(increased from 80%)*
- **SC-007**: 100% of generated data passes database constraint validation (no foreign key violations, no unique constraint violations, no NOT NULL violations)
- **SC-008**: Users can set up and generate their first test data within 5 minutes of installation
- **SC-009**: Error messages enable users to resolve connection or configuration issues without consulting documentation in 90% of cases
- **SC-010**: All 30+ default semantic mappings work correctly across both PostgreSQL and MySQL databases 🆕 *(increased from 20+)*
- 🆕 **SC-011**: Analyze command generates valid, loadable config for any supported schema in under 30 seconds
- 🆕 **SC-012**: Low-confidence columns (<0.6) are correctly flagged in 95%+ of cases
- 🆕 **SC-013**: ENUM columns achieve 100% accuracy (values directly from schema)
- 🆕 **SC-014**: Foreign key columns achieve 100% accuracy (always reference valid parent records)
- 🆕 **SC-015**: Parseable CHECK constraints are respected in 90%+ of cases

---

## Implementation Status

This section tracks what has been implemented versus what remains to be built.

### Implemented ✅

| Component | Status | Notes |
|-----------|--------|-------|
| Project structure & dependencies | ✅ Complete | pyproject.toml, uv.lock configured |
| Configuration file parser | ✅ Complete | YAML parsing, env var interpolation |
| Credential management | ✅ Complete | .pgpass, .my.cnf support, redaction |
| Database connection | ✅ Complete | Connection pooling, validation, dialect detection |
| Connection string builder | ✅ Complete | Multiple source priority, interactive prompts |
| Logging with secret redaction | ✅ Complete | Automatic password/token redaction |
| CLI skeleton | ✅ Partial | App configured, commands not implemented |

### Not Implemented ❌

| Component | Status | Notes |
|-----------|--------|-------|
| Schema introspection | ❌ Not started | Core inspector class needed |
| Dependency graph builder | ❌ Not started | Topological sort for FK ordering |
| 🆕 Classification pipeline | ❌ Not started | Layered classifier with confidence scoring |
| 🆕 Pattern matcher | ❌ Not started | Regex-based column name matching |
| 🆕 Token analyzer | ❌ Not started | Compound name tokenization and scoring |
| Semantic column mapper | ❌ Not started | Name pattern matching |
| Type mapper | ❌ Not started | SQL type to Faker mapping |
| 🆕 Confidence scorer | ❌ Not started | Score calculation with modifiers |
| Data generator engine | ❌ Not started | Row generation logic |
| Bulk inserter | ❌ Not started | Batch insert with transactions |
| FK constraint handler | ❌ Not started | Parent ID caching and selection |
| Unique constraint handler | ❌ Not started | Value tracking and retry logic |
| 🆕 CHECK constraint parser | ❌ Not started | Extract ranges/values from CHECK |
| 🆕 Self-reference handler | ❌ Not started | Two-pass generation for self-referential FKs |
| CLI inspect command | ❌ Not started | File exists but empty |
| 🆕 CLI analyze command | ❌ Not started | Config generation from schema |
| CLI generate command | ❌ Not started | File exists but empty |
| CLI validate command | ❌ Not started | File exists but empty |
| 🆕 JSON/Markdown output formatters | ❌ Not started | Alternative output formats |
| 🆕 LLM integration (optional) | ❌ Not started | Optional AI enhancement for analyze |

### Estimated Completion: ~25% of MVP 🆕 *(revised down due to expanded scope)*

---

## Clarifications

### Session 2026-01-16

- Q: How should low-confidence columns be handled during generation? → A: Strict mode optional — default warns but continues, `--strict` flag requires resolution

---

## 🆕 Open Design Decisions

| Decision | Options | Recommendation | Status |
|----------|---------|----------------|--------|
| Confidence threshold for "low" | 0.5, 0.6, or 0.7 | 0.6 (balanced) | ✅ Resolved (FR-014.5) |
| Token scoring algorithm | Weighted sum vs. max token | Max token with combo bonus | Deferred to planning |
| CHECK constraint parser | Regex vs. SQL parser | Regex for simple cases, skip complex | Deferred to planning |
| LLM provider default | OpenAI, Anthropic, configurable | Configurable, no default | ✅ Resolved (FR-047) |
| Config comment style | Inline vs. block | Inline with `# ⚠️` markers | Deferred to planning |
| Low-confidence resolution | Block vs. Warn vs. Strict mode | Strict mode optional | ✅ Resolved (Session 2026-01-16) |