"""Build database connection strings from various sources."""

import logging
import os
from getpass import getpass
from pathlib import Path

from hypothesis.config.credentials import CredentialManager
from hypothesis.config.parser import ConfigParser

logger = logging.getLogger(__name__)


def build_connection_string(
    database_name: str | None = None,
    connection: str | None = None,
    dialect: str | None = None,
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
    username: str | None = None,
    password: str | None = None,
    config_file: Path | None = None,
) -> str:
    """Build database connection string from various sources.

    Priority order:
    1. Direct connection string (if provided)
    2. Named database from config file
    3. Component flags
    4. Interactive prompts for missing values

    Args:
        database_name: Named database from config file
        connection: Full connection string
        dialect: Database dialect ('postgres' or 'mysql')
        host: Database host
        port: Database port
        database: Database name
        username: Database username
        password: Database password
        config_file: Path to config file

    Returns:
        Complete database connection string

    Raises:
        ValueError: If required parameters are missing

    Examples:
        >>> # Using named database from config
        >>> build_connection_string(database_name="production")
        'postgresql://user@db.prod.com:5432/myapp'

        >>> # Using component flags
        >>> build_connection_string(
        ...     dialect="postgres",
        ...     host="localhost",
        ...     database="mydb",
        ...     username="user"
        ... )
        'postgresql://user@localhost:5432/mydb'
    """
    # Priority 1: Direct connection string
    if connection:
        logger.debug("Using provided connection string")
        return connection

    # Priority 2: Named database from config
    if database_name:
        logger.debug(f"Loading database config for: {database_name}")
        config = ConfigParser(config_path=config_file)

        if not config.config:
            raise ValueError(f"No config file found. Searched: {ConfigParser.DEFAULT_PATHS}")

        if database_name not in config.config:
            available = ", ".join(config.config.keys())
            raise ValueError(
                f"Database '{database_name}' not found in config. Available: {available}"
            )

        db_config = config.config[database_name]

        # If config has full URL, use it
        if "url" in db_config:
            logger.debug("Using URL from config")
            return str(db_config["url"])

        # Otherwise extract components from config
        dialect = db_config.get("dialect")
        host = db_config.get("host", "localhost")
        port = db_config.get("port")
        database = db_config.get("database")
        username = db_config.get("username")
        password = db_config.get("password")

    # Priority 3: Component flags - validate required fields
    if not dialect:
        raise ValueError(
            "Database dialect required. Specify --dialect or use a named database from config."
        )

    if dialect not in ["postgres", "postgresql", "mysql"]:
        raise ValueError(f"Invalid dialect: {dialect}. Must be 'postgres' or 'mysql'.")

    if not database:
        raise ValueError(
            "Database name required. Specify --database or use a named database from config."
        )

    # Set defaults (guaranteed non-None from here on)
    resolved_host: str = host or "localhost"
    resolved_port: int = port or (5432 if dialect in ["postgres", "postgresql"] else 3306)
    resolved_username: str = username or os.getenv("USER") or "postgres"

    # Get password from various sources
    resolved_password: str | None = password
    if not resolved_password:
        resolved_password = _get_password(
            dialect=dialect,
            host=resolved_host,
            port=resolved_port,
            database=database,
            username=resolved_username,
        )

    # Build connection string
    dialect_prefix = "postgresql" if dialect in ["postgres", "postgresql"] else "mysql"
    conn_str = (
        f"{dialect_prefix}://{resolved_username}:{resolved_password}"
        f"@{resolved_host}:{resolved_port}/{database}"
    )

    logger.debug(
        f"Built connection string: {dialect_prefix}://{resolved_username}:***"
        f"@{resolved_host}:{resolved_port}/{database}"
    )

    return conn_str


def _get_password(
    dialect: str,
    host: str,
    port: int,
    database: str,
    username: str,
) -> str:
    """Get password from .pgpass, .my.cnf, or prompt.

    Args:
        dialect: Database dialect
        host: Database host
        port: Database port
        database: Database name
        username: Database username

    Returns:
        Database password
    """
    # Try .pgpass for PostgreSQL
    if dialect in ["postgres", "postgresql"]:
        password = CredentialManager.get_postgres_password(
            host=host,
            port=port,
            database=database,
            username=username,
        )
        if password:
            logger.debug("Using password from .pgpass")
            return password

    # Try .my.cnf for MySQL
    elif dialect == "mysql":
        credentials = CredentialManager.get_mysql_credentials(host=host)
        if credentials and "password" in credentials:
            logger.debug("Using password from .my.cnf")
            return credentials["password"]

    # Fallback: prompt for password
    logger.debug("Prompting for password")
    return getpass(f"Password for {username}@{host}: ")


def parse_connection_components(connection_string: str) -> dict[str, str | int | None]:
    """Parse connection string into components.

    Args:
        connection_string: Database connection URL

    Returns:
        Dictionary with connection components

    Examples:
        >>> parse_connection_components("postgresql://user@localhost:5432/mydb")
        {
            'dialect': 'postgresql',
            'username': 'user',
            'password': None,
            'host': 'localhost',
            'port': 5432,
            'database': 'mydb'
        }
    """
    from sqlalchemy.engine.url import make_url

    url = make_url(connection_string)

    return {
        "dialect": url.drivername,
        "username": url.username,
        "password": url.password,
        "host": url.host,
        "port": url.port,
        "database": url.database,
    }
