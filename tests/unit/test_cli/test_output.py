"""Tests for the Rich/JSON/Markdown output formatters."""

import json
from io import StringIO

from rich.console import Console

from hypothesis.cli.output import render_json, render_markdown, render_table
from hypothesis.core.models import ColumnSchema, ForeignKey, TableSchema


def _sample_tables() -> list[TableSchema]:
    users = TableSchema(
        name="users",
        columns=[
            ColumnSchema(
                "id",
                "users",
                "INTEGER",
                int,
                is_primary_key=True,
                is_auto_increment=True,
                nullable=False,
            ),
            ColumnSchema("email", "users", "VARCHAR(255)", str, nullable=False, is_unique=True),
        ],
        primary_key=["id"],
    )
    posts = TableSchema(
        name="posts",
        columns=[
            ColumnSchema("id", "posts", "INTEGER", int, is_primary_key=True, nullable=False),
            ColumnSchema("user_id", "posts", "INTEGER", int, is_foreign_key=True, nullable=False),
        ],
        foreign_keys=[ForeignKey("posts", "user_id", "users", "id")],
    )
    return [users, posts]


def test_render_table_includes_names_and_columns() -> None:
    buf = StringIO()
    render_table(_sample_tables(), console=Console(file=buf, width=100), verbose=True)
    out = buf.getvalue()
    assert "users" in out
    assert "posts" in out
    assert "email" in out
    # verbose mode shows FK relationships
    assert "user_id" in out


def test_render_json_is_valid_and_structured() -> None:
    data = json.loads(render_json(_sample_tables()))
    assert data[0]["name"] == "users"
    column_names = {c["name"] for c in data[0]["columns"]}
    assert "email" in column_names
    assert data[0]["columns"][0]["python_type"] == "int"
    assert data[1]["foreign_keys"][0]["references"] == "users.id"


def test_render_markdown_has_headings_and_rows() -> None:
    md = render_markdown(_sample_tables())
    assert "## users" in md
    assert "| email |" in md
    assert "`user_id`" in md
