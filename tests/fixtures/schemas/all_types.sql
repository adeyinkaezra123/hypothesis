-- PostgreSQL fixture: exercises the full range of supported column types,
-- plus an ENUM type and several CHECK constraints.

CREATE TYPE mood AS ENUM ('happy', 'neutral', 'sad');

CREATE TABLE all_types (
    id SERIAL PRIMARY KEY,
    col_varchar VARCHAR(255),
    col_char CHAR(10),
    col_text TEXT,
    col_int INTEGER,
    col_smallint SMALLINT,
    col_bigint BIGINT,
    col_decimal DECIMAL(12, 4),
    col_numeric NUMERIC(8, 2),
    col_real REAL,
    col_double DOUBLE PRECISION,
    col_boolean BOOLEAN,
    col_date DATE,
    col_time TIME,
    col_timestamp TIMESTAMP,
    col_timestamptz TIMESTAMPTZ,
    col_uuid UUID,
    col_json JSON,
    col_jsonb JSONB,
    col_bytea BYTEA,
    col_inet INET,
    col_enum mood,
    age INTEGER CHECK (age >= 0 AND age <= 150),
    rating SMALLINT CHECK (rating BETWEEN 1 AND 5),
    state VARCHAR(20) CHECK (state IN ('open', 'closed', 'pending'))
);
