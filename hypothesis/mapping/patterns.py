"""Column-name pattern rules and the matching engine.

The rules map column-name patterns to :class:`SemanticType` values with a base
confidence. ``find_pattern_matches`` runs a name against every rule and returns
the matches; the classification pipeline picks among them. Rule data is
transcribed from ``specs/001-core-mvp/data-model.md`` (sections 6.4 and 6.5).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from hypothesis.mapping.types import SemanticType

PatternType = Literal["exact", "prefix", "suffix", "contains", "regex"]


@dataclass(frozen=True)
class PatternRule:
    """A single column-name matching rule."""

    semantic_type: SemanticType
    pattern_type: PatternType
    pattern: str
    base_confidence: float
    case_sensitive: bool = False


@dataclass(frozen=True)
class PatternMatch:
    """A rule that matched a column name."""

    semantic_type: SemanticType
    confidence: float
    pattern: str
    pattern_type: PatternType


def match_exact(name: str, pattern: str, *, case_sensitive: bool = False) -> bool:
    return name == pattern if case_sensitive else name.lower() == pattern.lower()


def match_prefix(name: str, pattern: str, *, case_sensitive: bool = False) -> bool:
    return name.startswith(pattern) if case_sensitive else name.lower().startswith(pattern.lower())


def match_suffix(name: str, pattern: str, *, case_sensitive: bool = False) -> bool:
    return name.endswith(pattern) if case_sensitive else name.lower().endswith(pattern.lower())


def match_contains(name: str, pattern: str, *, case_sensitive: bool = False) -> bool:
    return pattern in name if case_sensitive else pattern.lower() in name.lower()


def match_regex(name: str, pattern: str, *, case_sensitive: bool = False) -> bool:
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.search(pattern, name, flags) is not None


_MATCHERS: dict[PatternType, Callable[..., bool]] = {
    "exact": match_exact,
    "prefix": match_prefix,
    "suffix": match_suffix,
    "contains": match_contains,
    "regex": match_regex,
}


def rule_matches(rule: PatternRule, name: str) -> bool:
    """True if ``name`` satisfies ``rule``."""
    return _MATCHERS[rule.pattern_type](name, rule.pattern, case_sensitive=rule.case_sensitive)


def find_pattern_matches(name: str) -> list[PatternMatch]:
    """Return every pattern rule that matches ``name``, highest confidence first."""
    matches = [
        PatternMatch(rule.semantic_type, rule.base_confidence, rule.pattern, rule.pattern_type)
        for rule in PATTERN_RULES
        if rule_matches(rule, name)
    ]
    matches.sort(key=lambda match: match.confidence, reverse=True)
    return matches


# Ordered roughly by specificity (most specific first).
PATTERN_RULES: list[PatternRule] = [
    # Personal — exact
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
    # Location — exact
    PatternRule(SemanticType.ADDRESS, "exact", "address", 0.90),
    PatternRule(SemanticType.STREET, "exact", "street", 0.95),
    PatternRule(SemanticType.STREET, "exact", "street_address", 0.95),
    PatternRule(SemanticType.CITY, "exact", "city", 0.95),
    PatternRule(SemanticType.STATE, "exact", "state", 0.85),
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
    # Business — exact
    PatternRule(SemanticType.COMPANY, "exact", "company", 0.95),
    PatternRule(SemanticType.COMPANY, "exact", "company_name", 0.95),
    PatternRule(SemanticType.COMPANY, "exact", "organization", 0.90),
    PatternRule(SemanticType.JOB_TITLE, "exact", "job_title", 0.95),
    PatternRule(SemanticType.JOB_TITLE, "exact", "title", 0.70),
    PatternRule(SemanticType.JOB_TITLE, "exact", "position", 0.85),
    PatternRule(SemanticType.DEPARTMENT, "exact", "department", 0.95),
    PatternRule(SemanticType.DEPARTMENT, "exact", "dept", 0.90),
    # Financial — exact
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
    # Internet — exact
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
    # Identifiers — exact
    PatternRule(SemanticType.UUID, "exact", "uuid", 0.95),
    PatternRule(SemanticType.UUID, "exact", "guid", 0.95),
    PatternRule(SemanticType.SKU, "exact", "sku", 0.95),
    PatternRule(SemanticType.BARCODE, "exact", "barcode", 0.95),
    PatternRule(SemanticType.BARCODE, "exact", "ean", 0.90),
    PatternRule(SemanticType.BARCODE, "exact", "upc", 0.90),
    # Content — exact
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
    # File — exact
    PatternRule(SemanticType.FILENAME, "exact", "filename", 0.95),
    PatternRule(SemanticType.FILENAME, "exact", "file_name", 0.95),
    PatternRule(SemanticType.FILE_PATH, "exact", "file_path", 0.95),
    PatternRule(SemanticType.FILE_PATH, "exact", "filepath", 0.95),
    PatternRule(SemanticType.FILE_PATH, "exact", "path", 0.75),
    PatternRule(SemanticType.MIME_TYPE, "exact", "mime_type", 0.95),
    PatternRule(SemanticType.MIME_TYPE, "exact", "content_type", 0.90),
    PatternRule(SemanticType.FILE_EXTENSION, "exact", "extension", 0.85),
    PatternRule(SemanticType.FILE_EXTENSION, "exact", "file_extension", 0.95),
    # Color — exact
    PatternRule(SemanticType.COLOR, "exact", "color", 0.95),
    PatternRule(SemanticType.COLOR, "exact", "colour", 0.95),
    PatternRule(SemanticType.HEX_COLOR, "exact", "hex_color", 0.95),
    PatternRule(SemanticType.HEX_COLOR, "exact", "color_hex", 0.95),
    # Numeric — exact
    PatternRule(SemanticType.PERCENTAGE, "exact", "percentage", 0.95),
    PatternRule(SemanticType.PERCENTAGE, "exact", "percent", 0.90),
    PatternRule(SemanticType.QUANTITY, "exact", "quantity", 0.95),
    PatternRule(SemanticType.QUANTITY, "exact", "qty", 0.90),
    PatternRule(SemanticType.COUNT, "exact", "count", 0.90),
    PatternRule(SemanticType.RATING, "exact", "rating", 0.95),
    PatternRule(SemanticType.SCORE, "exact", "score", 0.90),
    PatternRule(SemanticType.PRIORITY, "exact", "priority", 0.95),
    PatternRule(SemanticType.SEQUENCE, "exact", "sequence", 0.90),
    PatternRule(SemanticType.ORDER, "exact", "order", 0.75),
    PatternRule(SemanticType.ORDER, "exact", "sort_order", 0.95),
    PatternRule(SemanticType.ORDER, "exact", "display_order", 0.95),
    # Status / state — exact (low confidence, need context)
    PatternRule(SemanticType.STATUS, "exact", "status", 0.70),
    PatternRule(SemanticType.TYPE, "exact", "type", 0.65),
    PatternRule(SemanticType.CATEGORY, "exact", "category", 0.85),
    PatternRule(SemanticType.LEVEL, "exact", "level", 0.80),
    PatternRule(SemanticType.ROLE, "exact", "role", 0.85),
    # Suffix
    PatternRule(SemanticType.EMAIL, "suffix", "_email", 0.90),
    PatternRule(SemanticType.PHONE, "suffix", "_phone", 0.90),
    PatternRule(SemanticType.URL, "suffix", "_url", 0.90),
    PatternRule(SemanticType.UUID, "suffix", "_uuid", 0.95),
    PatternRule(SemanticType.IMAGE_URL, "suffix", "_image_url", 0.95),
    PatternRule(SemanticType.IMAGE_URL, "suffix", "_image", 0.80),
    PatternRule(SemanticType.IMAGE_URL, "suffix", "_photo", 0.80),
    PatternRule(SemanticType.IMAGE_URL, "suffix", "_avatar", 0.85),
    PatternRule(SemanticType.IMAGE_URL, "suffix", "_thumbnail", 0.85),
    PatternRule(SemanticType.CREATED_AT, "suffix", "_at", 0.85),
    PatternRule(SemanticType.CREATED_AT, "suffix", "created_at", 0.95),
    PatternRule(SemanticType.UPDATED_AT, "suffix", "updated_at", 0.95),
    PatternRule(SemanticType.UPDATED_AT, "suffix", "modified_at", 0.95),
    PatternRule(SemanticType.DELETED_AT, "suffix", "deleted_at", 0.95),
    PatternRule(SemanticType.EXPIRES_AT, "suffix", "expires_at", 0.95),
    PatternRule(SemanticType.EXPIRES_AT, "suffix", "expiry_date", 0.95),
    PatternRule(SemanticType.DATE, "suffix", "_date", 0.85),
    PatternRule(SemanticType.DATETIME, "suffix", "_datetime", 0.95),
    PatternRule(SemanticType.TIME, "suffix", "_time", 0.80),
    # Prefix
    PatternRule(SemanticType.BOOLEAN_FLAG, "prefix", "is_", 0.90),
    PatternRule(SemanticType.BOOLEAN_FLAG, "prefix", "has_", 0.90),
    PatternRule(SemanticType.BOOLEAN_FLAG, "prefix", "can_", 0.90),
    PatternRule(SemanticType.BOOLEAN_FLAG, "prefix", "should_", 0.85),
    PatternRule(SemanticType.BOOLEAN_FLAG, "prefix", "allow_", 0.85),
    PatternRule(SemanticType.BOOLEAN_FLAG, "prefix", "enable_", 0.85),
    # Contains
    PatternRule(SemanticType.EMAIL, "contains", "email", 0.85),
    PatternRule(SemanticType.ADDRESS, "contains", "address", 0.80),
    PatternRule(SemanticType.PHONE, "contains", "phone", 0.85),
    PatternRule(SemanticType.PHONE, "contains", "mobile", 0.80),
    # Regex
    PatternRule(
        SemanticType.BOOLEAN_FLAG,
        "regex",
        r"^(is|has|can|should|allow|enable|disable)_\w+$",
        0.90,
    ),
    PatternRule(
        SemanticType.BOOLEAN_FLAG,
        "regex",
        r"^\w+_(enabled|disabled|active|visible|hidden|locked)$",
        0.90,
    ),
    PatternRule(SemanticType.UUID, "regex", r"^[a-z]+_uuid$", 0.90),
    PatternRule(SemanticType.ID, "regex", r"^\w+_id$", 0.70),
]


# Confidence adjustments applied on top of a rule's base confidence.
CONFIDENCE_MODIFIERS: dict[str, float] = {
    "sql_type_matches": +0.05,
    "multiple_patterns": +0.05,
    "table_context_supports": +0.05,
    "ambiguous_token": -0.20,
    "very_short_name": -0.10,
    "sql_type_mismatch": -0.15,
    "generic_name": -0.15,
}

# Tokens whose presence makes a classification ambiguous.
AMBIGUOUS_TOKENS: set[str] = {
    "status",
    "state",
    "type",
    "code",
    "value",
    "data",
    "name",
    "key",
    "ref",
    "flag",
    "mode",
    "kind",
    "class",
    "attr",
    "field",
    "info",
    "meta",
    "extra",
    "misc",
    "other",
    "val",
    "tmp",
    "temp",
}
