# Hypothesis

Hypothesis is a command-line tool that generates realistic, semantically-aware
test data for PostgreSQL and MySQL. It reflects a database schema, infers what
each column represents from its name, type, and constraints, and fills the
tables with fake data that respects foreign keys, unique constraints, and other
relationships.

## Status

Early development. The connection, configuration, and schema-modelling layers
are implemented and tested. Schema introspection and column classification are
available through `hypothesis inspect`; data generation is still in progress.
The design and task breakdown live in `specs/001-core-mvp/`.

## Requirements

- Python 3.11 or newer
- A PostgreSQL or MySQL database to seed
- [uv](https://github.com/astral-sh/uv) for dependency management

## Installation

```bash
uv sync                     # core dependencies
uv sync --extra postgres    # PostgreSQL driver (psycopg2)
uv sync --extra mysql       # MySQL driver (PyMySQL)
```

## Commands

```bash
hypothesis inspect  <connection>              # show tables, columns, and relationships
hypothesis analyze  <connection> -o seed.yml  # write a starter config from the schema
hypothesis generate <connection> --rows 1000  # generate and insert data
hypothesis validate seed.yml                  # check a config against the schema
```

A connection is a standard database URL, for example
`postgresql://user@localhost:5432/mydb`. Passwords can be provided through
`.pgpass`, `.my.cnf`, config interpolation, or your database driver's normal
credential flow.

## Configuration

Generation can be customised with a YAML file: per-table row counts, column
overrides, fixed value lists with weights, and foreign-key distributions.
Environment variables are interpolated using `${VAR}` syntax. The full reference
is in `specs/001-core-mvp/`.

## Development

```bash
uv run pytest          # run the test suite with coverage
uv run ruff check .    # lint
uv run mypy hypothesis tests # type-check source and tests
```

## License

Released under the MIT License. See [LICENSE](LICENSE).
