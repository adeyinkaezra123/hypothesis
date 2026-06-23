"""Semantic type system: the core intelligence of Hypothesis.

Defines the :class:`SemanticType` enum, the :class:`FakerMapping` specification,
and the canonical ``SEMANTIC_TO_FAKER`` / ``SQL_TYPE_FALLBACK`` tables that map a
classified column to a concrete Faker provider. Also defines
:class:`ClassificationResult`, the output of the classification pipeline.

Provider names and kwargs are transcribed from
``specs/001-core-mvp/data-model.md`` and validated against the installed Faker
in ``tests/unit/test_mapping/test_types.py``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from hypothesis.core.models import ColumnSchema


class SemanticType(Enum):
    """Recognized semantic types for columns."""

    # Personal Information
    EMAIL = "email"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    FULL_NAME = "full_name"
    PHONE = "phone"
    USERNAME = "username"
    PASSWORD = "password"  # nosec B105
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

    # Status/State (common domain patterns).
    # Note: STATE is defined once under Location above; it doubles as the
    # status-style "state" and is disambiguated by table context, not by a
    # separate enum member.
    STATUS = "status"
    TYPE = "type"
    CATEGORY = "category"
    LEVEL = "level"
    ROLE = "role"

    # Constraint-derived (highest confidence)
    ENUM_VALUE = "enum_value"  # Schema-defined ENUM
    FOREIGN_KEY = "foreign_key"  # FK reference
    CHECK_RANGE = "check_range"  # Derived from CHECK constraint
    CHECK_VALUES = "check_values"  # Derived from CHECK IN clause

    # Fallback (lowest confidence)
    TYPE_FALLBACK = "type_fallback"  # SQL type-based generator


@dataclass
class FakerMapping:
    """Complete specification for generating a value with Faker."""

    provider: str  # Faker method name
    kwargs: dict[str, Any]  # Default arguments
    post_process: Callable[[Any], Any] | None  # Optional transform
    compatible_sql_types: set[str]  # SQL types this makes sense for


# The canonical mapping: SemanticType -> how to generate it.
SEMANTIC_TO_FAKER: dict[SemanticType, FakerMapping] = {
    # Personal information
    SemanticType.EMAIL: FakerMapping("email", {}, None, {"VARCHAR", "TEXT", "CHAR"}),
    SemanticType.FIRST_NAME: FakerMapping("first_name", {}, None, {"VARCHAR", "TEXT", "CHAR"}),
    SemanticType.LAST_NAME: FakerMapping("last_name", {}, None, {"VARCHAR", "TEXT", "CHAR"}),
    SemanticType.FULL_NAME: FakerMapping("name", {}, None, {"VARCHAR", "TEXT", "CHAR"}),
    SemanticType.PHONE: FakerMapping("phone_number", {}, None, {"VARCHAR", "TEXT", "CHAR"}),
    SemanticType.USERNAME: FakerMapping("user_name", {}, None, {"VARCHAR", "TEXT", "CHAR"}),
    SemanticType.PASSWORD: FakerMapping(
        "password", {"length": 16, "special_chars": True}, None, {"VARCHAR", "TEXT", "CHAR"}
    ),
    SemanticType.AGE: FakerMapping(
        "random_int", {"min": 18, "max": 85}, None, {"INTEGER", "SMALLINT", "INT", "TINYINT"}
    ),
    SemanticType.GENDER: FakerMapping(
        "random_element",
        {"elements": ["male", "female", "non-binary", "other"]},
        None,
        {"VARCHAR", "TEXT", "CHAR", "ENUM"},
    ),
    SemanticType.DATE_OF_BIRTH: FakerMapping(
        "date_of_birth",
        {"minimum_age": 18, "maximum_age": 85},
        None,
        {"DATE", "DATETIME", "TIMESTAMP"},
    ),
    SemanticType.SSN: FakerMapping("ssn", {}, None, {"VARCHAR", "CHAR"}),
    # Location
    SemanticType.ADDRESS: FakerMapping("address", {}, None, {"VARCHAR", "TEXT"}),
    SemanticType.STREET: FakerMapping("street_address", {}, None, {"VARCHAR", "TEXT"}),
    SemanticType.CITY: FakerMapping("city", {}, None, {"VARCHAR", "TEXT", "CHAR"}),
    SemanticType.STATE: FakerMapping("state", {}, None, {"VARCHAR", "TEXT", "CHAR"}),
    SemanticType.COUNTRY: FakerMapping("country", {}, None, {"VARCHAR", "TEXT", "CHAR"}),
    SemanticType.POSTAL_CODE: FakerMapping("postcode", {}, None, {"VARCHAR", "CHAR"}),
    SemanticType.LATITUDE: FakerMapping(
        "latitude", {}, None, {"DECIMAL", "FLOAT", "DOUBLE", "NUMERIC", "REAL"}
    ),
    SemanticType.LONGITUDE: FakerMapping(
        "longitude", {}, None, {"DECIMAL", "FLOAT", "DOUBLE", "NUMERIC", "REAL"}
    ),
    # Business
    SemanticType.COMPANY: FakerMapping("company", {}, None, {"VARCHAR", "TEXT"}),
    SemanticType.JOB_TITLE: FakerMapping("job", {}, None, {"VARCHAR", "TEXT"}),
    SemanticType.DEPARTMENT: FakerMapping(
        "random_element",
        {
            "elements": [
                "Engineering",
                "Sales",
                "Marketing",
                "HR",
                "Finance",
                "Operations",
                "Legal",
                "Support",
            ]
        },
        None,
        {"VARCHAR", "TEXT"},
    ),
    # Financial
    SemanticType.PRICE: FakerMapping(
        "pydecimal",
        {"min_value": 1, "max_value": 9999, "right_digits": 2, "positive": True},
        None,
        {"DECIMAL", "NUMERIC", "MONEY", "FLOAT", "DOUBLE"},
    ),
    SemanticType.AMOUNT: FakerMapping(
        "pydecimal",
        {"min_value": 0, "max_value": 100000, "right_digits": 2},
        None,
        {"DECIMAL", "NUMERIC", "MONEY", "FLOAT", "DOUBLE"},
    ),
    SemanticType.CURRENCY: FakerMapping("currency_name", {}, None, {"VARCHAR", "TEXT"}),
    SemanticType.CURRENCY_CODE: FakerMapping("currency_code", {}, None, {"VARCHAR", "CHAR"}),
    SemanticType.CREDIT_CARD: FakerMapping("credit_card_number", {}, None, {"VARCHAR", "CHAR"}),
    SemanticType.IBAN: FakerMapping("iban", {}, None, {"VARCHAR", "CHAR"}),
    # Internet
    SemanticType.URL: FakerMapping("url", {}, None, {"VARCHAR", "TEXT"}),
    SemanticType.IP_ADDRESS: FakerMapping("ipv4", {}, None, {"VARCHAR", "CHAR", "INET"}),
    SemanticType.IPV6_ADDRESS: FakerMapping("ipv6", {}, None, {"VARCHAR", "CHAR", "INET"}),
    SemanticType.MAC_ADDRESS: FakerMapping("mac_address", {}, None, {"VARCHAR", "CHAR", "MACADDR"}),
    SemanticType.DOMAIN: FakerMapping("domain_name", {}, None, {"VARCHAR", "TEXT"}),
    SemanticType.SLUG: FakerMapping("slug", {}, None, {"VARCHAR", "TEXT"}),
    SemanticType.USER_AGENT: FakerMapping("user_agent", {}, None, {"VARCHAR", "TEXT"}),
    # Identifiers
    SemanticType.UUID: FakerMapping("uuid4", {}, str, {"UUID", "VARCHAR", "CHAR"}),
    SemanticType.ID: FakerMapping(
        "random_int", {"min": 1, "max": 999999}, None, {"INTEGER", "BIGINT", "INT"}
    ),
    SemanticType.SKU: FakerMapping(
        "bothify", {"text": "???-####-???"}, str.upper, {"VARCHAR", "CHAR"}
    ),
    SemanticType.BARCODE: FakerMapping("ean13", {}, None, {"VARCHAR", "CHAR", "BIGINT"}),
    # Temporal
    SemanticType.DATE: FakerMapping(
        "date_between", {"start_date": "-5y", "end_date": "today"}, None, {"DATE"}
    ),
    SemanticType.DATETIME: FakerMapping(
        "date_time_between",
        {"start_date": "-5y", "end_date": "now"},
        None,
        {"DATETIME", "TIMESTAMP"},
    ),
    SemanticType.TIME: FakerMapping("time", {}, None, {"TIME"}),
    SemanticType.TIMESTAMP: FakerMapping("unix_time", {}, None, {"INTEGER", "BIGINT", "TIMESTAMP"}),
    SemanticType.CREATED_AT: FakerMapping(
        "date_time_between",
        {"start_date": "-2y", "end_date": "-1d"},
        None,
        {"DATETIME", "TIMESTAMP", "TIMESTAMPTZ"},
    ),
    SemanticType.UPDATED_AT: FakerMapping(
        "date_time_between",
        {"start_date": "-1d", "end_date": "now"},
        None,
        {"DATETIME", "TIMESTAMP", "TIMESTAMPTZ"},
    ),
    SemanticType.DELETED_AT: FakerMapping(
        "date_time_between",
        {"start_date": "-30d", "end_date": "now"},
        None,
        {"DATETIME", "TIMESTAMP", "TIMESTAMPTZ"},
    ),
    SemanticType.EXPIRES_AT: FakerMapping(
        "date_time_between",
        {"start_date": "now", "end_date": "+1y"},
        None,
        {"DATETIME", "TIMESTAMP", "TIMESTAMPTZ"},
    ),
    SemanticType.YEAR: FakerMapping("year", {}, None, {"INTEGER", "SMALLINT", "YEAR"}),
    SemanticType.MONTH: FakerMapping("month", {}, None, {"INTEGER", "SMALLINT"}),
    # Content
    SemanticType.TITLE: FakerMapping(
        "sentence", {"nb_words": 6}, lambda s: s.rstrip("."), {"VARCHAR", "TEXT"}
    ),
    SemanticType.NAME: FakerMapping("catch_phrase", {}, None, {"VARCHAR", "TEXT"}),
    SemanticType.DESCRIPTION: FakerMapping(
        "paragraph", {"nb_sentences": 3}, None, {"VARCHAR", "TEXT"}
    ),
    SemanticType.TEXT: FakerMapping(
        "text", {"max_nb_chars": 500}, None, {"TEXT", "LONGTEXT", "CLOB"}
    ),
    SemanticType.SUMMARY: FakerMapping("paragraph", {"nb_sentences": 2}, None, {"VARCHAR", "TEXT"}),
    SemanticType.BODY: FakerMapping(
        "text", {"max_nb_chars": 2000}, None, {"TEXT", "LONGTEXT", "CLOB"}
    ),
    SemanticType.CONTENT: FakerMapping(
        "text", {"max_nb_chars": 1000}, None, {"TEXT", "LONGTEXT", "CLOB"}
    ),
    SemanticType.COMMENT: FakerMapping("sentence", {"nb_words": 12}, None, {"VARCHAR", "TEXT"}),
    SemanticType.NOTE: FakerMapping("sentence", {"nb_words": 10}, None, {"VARCHAR", "TEXT"}),
    SemanticType.BIO: FakerMapping("paragraph", {"nb_sentences": 4}, None, {"VARCHAR", "TEXT"}),
    # File/Media
    SemanticType.FILENAME: FakerMapping("file_name", {}, None, {"VARCHAR", "TEXT"}),
    SemanticType.FILE_PATH: FakerMapping("file_path", {"depth": 3}, None, {"VARCHAR", "TEXT"}),
    SemanticType.MIME_TYPE: FakerMapping("mime_type", {}, None, {"VARCHAR"}),
    SemanticType.FILE_EXTENSION: FakerMapping("file_extension", {}, None, {"VARCHAR", "CHAR"}),
    SemanticType.IMAGE_URL: FakerMapping("image_url", {}, None, {"VARCHAR", "TEXT"}),
    # Color
    SemanticType.COLOR: FakerMapping("color_name", {}, None, {"VARCHAR", "TEXT"}),
    SemanticType.HEX_COLOR: FakerMapping("hex_color", {}, None, {"VARCHAR", "CHAR"}),
    SemanticType.RGB_COLOR: FakerMapping("rgb_color", {}, None, {"VARCHAR"}),
    # Boolean
    SemanticType.BOOLEAN_FLAG: FakerMapping(
        "boolean", {"chance_of_getting_true": 50}, None, {"BOOLEAN", "BOOL", "TINYINT", "BIT"}
    ),
    # Numeric
    SemanticType.PERCENTAGE: FakerMapping(
        "pydecimal",
        {"min_value": 0, "max_value": 100, "right_digits": 2},
        None,
        {"DECIMAL", "FLOAT", "DOUBLE", "INTEGER"},
    ),
    SemanticType.QUANTITY: FakerMapping(
        "random_int", {"min": 1, "max": 100}, None, {"INTEGER", "SMALLINT", "INT"}
    ),
    SemanticType.COUNT: FakerMapping(
        "random_int", {"min": 0, "max": 1000}, None, {"INTEGER", "BIGINT", "INT"}
    ),
    SemanticType.RATING: FakerMapping(
        "pydecimal",
        {"min_value": 1, "max_value": 5, "right_digits": 1},
        None,
        {"DECIMAL", "FLOAT", "DOUBLE", "INTEGER"},
    ),
    SemanticType.SCORE: FakerMapping(
        "random_int", {"min": 0, "max": 100}, None, {"INTEGER", "DECIMAL", "FLOAT"}
    ),
    SemanticType.PRIORITY: FakerMapping(
        "random_int", {"min": 1, "max": 5}, None, {"INTEGER", "SMALLINT", "TINYINT"}
    ),
    SemanticType.SEQUENCE: FakerMapping(
        "random_int", {"min": 1, "max": 100}, None, {"INTEGER", "BIGINT"}
    ),
    SemanticType.ORDER: FakerMapping(
        "random_int", {"min": 0, "max": 999}, None, {"INTEGER", "SMALLINT"}
    ),
    # Status/State (domain-specific, but common patterns)
    SemanticType.STATUS: FakerMapping(
        "random_element",
        {"elements": ["active", "inactive", "pending", "archived"]},
        None,
        {"VARCHAR", "ENUM"},
    ),
    SemanticType.TYPE: FakerMapping(
        "random_element",
        {"elements": ["default", "standard", "premium", "custom"]},
        None,
        {"VARCHAR", "ENUM"},
    ),
    SemanticType.CATEGORY: FakerMapping(
        "random_element",
        {"elements": ["general", "featured", "sale", "new"]},
        None,
        {"VARCHAR", "ENUM"},
    ),
    SemanticType.LEVEL: FakerMapping(
        "random_element",
        {"elements": ["beginner", "intermediate", "advanced", "expert"]},
        None,
        {"VARCHAR", "ENUM", "INTEGER"},
    ),
    SemanticType.ROLE: FakerMapping(
        "random_element",
        {"elements": ["user", "admin", "moderator", "guest"]},
        None,
        {"VARCHAR", "ENUM"},
    ),
    # Constraint-derived placeholders. ``elements`` is populated at runtime from
    # the schema (ENUM values / parent IDs) or the parsed CHECK constraint.
    SemanticType.ENUM_VALUE: FakerMapping(
        "random_element", {"elements": []}, None, {"ENUM", "VARCHAR"}
    ),
    SemanticType.FOREIGN_KEY: FakerMapping(
        "random_element", {"elements": []}, None, {"INTEGER", "BIGINT", "UUID", "VARCHAR"}
    ),
    SemanticType.CHECK_RANGE: FakerMapping(
        "random_int", {"min": 0, "max": 100}, None, {"INTEGER", "DECIMAL", "FLOAT"}
    ),
    SemanticType.CHECK_VALUES: FakerMapping(
        "random_element", {"elements": []}, None, {"VARCHAR", "INTEGER"}
    ),
    # SQL type fallback (lowest confidence)
    SemanticType.TYPE_FALLBACK: FakerMapping("pystr", {"max_chars": 50}, None, {"*"}),
}


# When no semantic pattern matches, fall back to SQL type-based generation.
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
    "DECIMAL": FakerMapping(
        "pydecimal", {"min_value": 0, "max_value": 10000, "right_digits": 2}, None, {"DECIMAL"}
    ),
    "NUMERIC": FakerMapping(
        "pydecimal", {"min_value": 0, "max_value": 10000, "right_digits": 2}, None, {"NUMERIC"}
    ),
    "FLOAT": FakerMapping("pyfloat", {"min_value": 0, "max_value": 10000}, None, {"FLOAT"}),
    "DOUBLE": FakerMapping("pyfloat", {"min_value": 0, "max_value": 10000}, None, {"DOUBLE"}),
    "REAL": FakerMapping("pyfloat", {"min_value": 0, "max_value": 10000}, None, {"REAL"}),
    # Boolean
    "BOOLEAN": FakerMapping("boolean", {}, None, {"BOOLEAN"}),
    "BOOL": FakerMapping("boolean", {}, None, {"BOOL"}),
    "BIT": FakerMapping("random_element", {"elements": [0, 1]}, None, {"BIT"}),
    # Date/Time
    "DATE": FakerMapping(
        "date_between", {"start_date": "-5y", "end_date": "today"}, None, {"DATE"}
    ),
    "DATETIME": FakerMapping(
        "date_time_between", {"start_date": "-5y", "end_date": "now"}, None, {"DATETIME"}
    ),
    "TIMESTAMP": FakerMapping(
        "date_time_between", {"start_date": "-5y", "end_date": "now"}, None, {"TIMESTAMP"}
    ),
    "TIMESTAMPTZ": FakerMapping(
        "date_time_between", {"start_date": "-5y", "end_date": "now"}, None, {"TIMESTAMPTZ"}
    ),
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


@dataclass
class ClassificationResult:
    """Result of running a column through the classification pipeline."""

    column: ColumnSchema
    semantic_type: SemanticType
    confidence: float
    faker_provider: str
    matched_layer: int  # 1-5: which pipeline layer produced this result
    faker_kwargs: dict[str, Any] = field(default_factory=dict)
    matched_pattern: str | None = None
    reasoning: str = ""
    needs_review: bool = False
    is_auto_increment: bool = False
    is_foreign_key: bool = False
