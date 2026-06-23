"""Tests for connection builder."""

from pathlib import Path

import pytest

from hypothesis.core.connection_builder import (
    build_connection_string,
    parse_connection_components,
)


def _url_with_credential(prefix: str, username: str, credential: str, suffix: str) -> str:
    """Build credential-bearing URLs without embedding them as literals."""
    return f"{prefix}://{username}" + ":" + credential + "@" + suffix


class TestBuildConnectionString:
    """Test build_connection_string function."""

    def test_direct_connection_string(self) -> None:
        """Test using direct connection string (highest priority)."""
        credential = "fixture_credential"
        conn_str = _url_with_credential("postgresql", "user", credential, "localhost/mydb")

        result = build_connection_string(connection=conn_str)

        assert result == conn_str

    def test_component_flags(self) -> None:
        """Test building from component flags."""
        credential = "fixture-credential"
        result = build_connection_string(
            dialect="postgres",
            host="localhost",
            port=5432,
            database="testdb",
            username="testuser",
            password=credential,
        )

        assert result == _url_with_credential(
            "postgresql", "testuser", credential, "localhost:5432/testdb"
        )

    def test_mysql_connection(self) -> None:
        """Test building MySQL connection string."""
        credential = "fixture_credential"
        result = build_connection_string(
            dialect="mysql",
            host="localhost",
            database="testdb",
            username="root",
            password=credential,
        )

        assert result == _url_with_credential("mysql", "root", credential, "localhost:3306/testdb")
        assert ":3306/" in result  # Default MySQL port

    def test_default_values(self) -> None:
        """Test that defaults are applied correctly."""
        credential = "fixture_credential"
        result = build_connection_string(
            dialect="postgres",
            database="testdb",
            username="user",
            password=credential,
        )

        assert "localhost" in result  # Default host
        assert ":5432/" in result  # Default PostgreSQL port

    def test_missing_dialect_raises_error(self) -> None:
        """Test that missing dialect raises ValueError."""
        credential = "fixture_credential"
        with pytest.raises(ValueError, match="dialect required"):
            build_connection_string(
                database="testdb",
                username="user",
                password=credential,
            )

    def test_missing_database_raises_error(self) -> None:
        """Test that missing database name raises ValueError."""
        credential = "fixture_credential"
        with pytest.raises(ValueError, match="Database name required"):
            build_connection_string(
                dialect="postgres",
                username="user",
                password=credential,
            )

    def test_invalid_dialect_raises_error(self) -> None:
        """Test that invalid dialect raises ValueError."""
        credential = "fixture_credential"
        with pytest.raises(ValueError, match="Invalid dialect"):
            build_connection_string(
                dialect="sqlite",  # Not supported
                database="testdb",
                username="user",
                password=credential,
            )

    def test_named_database_from_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test loading named database from config file."""
        monkeypatch.chdir(tmp_path)

        # Create config file
        config_file = tmp_path / ".hypothesisrc"
        credential = "fixture-credential"
        config_content = f"""
development:
  dialect: postgresql
  host: localhost
  port: 5432
  database: myapp_dev
  username: dev_user
  password: {credential}
"""
        config_file.write_text(config_content)

        result = build_connection_string(database_name="development")

        assert result == _url_with_credential(
            "postgresql", "dev_user", credential, "localhost:5432/myapp_dev"
        )

    def test_named_database_with_url(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading named database with full URL from config."""
        monkeypatch.chdir(tmp_path)

        config_file = tmp_path / ".hypothesisrc"
        credential = "fixture-credential"
        url = _url_with_credential(
            "postgresql", "prod_user", credential, "db.example.com:5432/myapp_prod"
        )
        config_content = f"""
production:
  url: {url}
"""
        config_file.write_text(config_content)

        result = build_connection_string(database_name="production")

        assert result == url

    def test_named_database_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test error when named database doesn't exist in config."""
        monkeypatch.chdir(tmp_path)

        config_file = tmp_path / ".hypothesisrc"
        config_file.write_text("development:\n  dialect: postgres\n")

        with pytest.raises(ValueError, match="not found in config"):
            build_connection_string(database_name="production")


class TestParseConnectionComponents:
    """Test parse_connection_components function."""

    def test_parse_postgresql_url(self) -> None:
        """Test parsing PostgreSQL connection string."""
        credential = "fixture_credential"
        conn_str = _url_with_credential("postgresql", "user", credential, "localhost:5432/mydb")

        result = parse_connection_components(conn_str)

        assert result["dialect"] == "postgresql"
        assert result["username"] == "user"
        assert result["password"] == credential
        assert result["host"] == "localhost"
        assert result["port"] == 5432
        assert result["database"] == "mydb"

    def test_parse_mysql_url(self) -> None:
        """Test parsing MySQL connection string."""
        credential = "fixture_credential"
        conn_str = _url_with_credential("mysql", "root", credential, "db.example.com:3306/testdb")

        result = parse_connection_components(conn_str)

        assert result["dialect"] == "mysql"
        assert result["username"] == "root"
        assert result["password"] == credential
        assert result["host"] == "db.example.com"
        assert result["port"] == 3306
        assert result["database"] == "testdb"

    def test_parse_url_without_password(self) -> None:
        """Test parsing connection string without password."""
        conn_str = "postgresql://user@localhost/mydb"

        result = parse_connection_components(conn_str)

        assert result["username"] == "user"
        assert result["password"] is None
