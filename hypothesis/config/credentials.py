"""Secure credential management for database connections."""

import configparser
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CredentialManager:
    """Manage database credentials from .pgpass and .my.cnf files."""

    @staticmethod
    def get_postgres_password(host: str, port: int, database: str, username: str) -> str | None:
        """Read password from PostgreSQL .pgpass file.

        File format: hostname:port:database:username:password
        Supports wildcards (*) in any field.

        Args:
            host: Database host
            port: Database port
            database: Database name
            username: Database username

        Returns:
            Password if found, None otherwise
        """
        pgpass_path = Path.home() / ".pgpass"

        if not pgpass_path.exists():
            logger.debug(".pgpass file not found at %s", pgpass_path)
            return None

        # Security check: .pgpass must have 0600 permissions
        file_stat = pgpass_path.stat()
        if file_stat.st_mode & 0o077:  # Check if group/other have any permissions
            logger.warning(
                ".pgpass file has insecure permissions (%o). Should be 0600. Ignoring file.",
                file_stat.st_mode & 0o777,
            )
            return None

        try:
            with open(pgpass_path) as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    parts = line.split(":")
                    if len(parts) != 5:
                        logger.debug(
                            ".pgpass line %d has invalid format (expected 5 fields, got %d)",
                            line_num,
                            len(parts),
                        )
                        continue

                    p_host, p_port, p_db, p_user, p_pass = parts

                    # Match with wildcards
                    if (
                        (p_host == "*" or p_host == host)
                        and (p_port == "*" or p_port == str(port))
                        and (p_db == "*" or p_db == database)
                        and (p_user == "*" or p_user == username)
                    ):
                        logger.debug("Found matching entry in .pgpass")
                        return p_pass

        except PermissionError:
            logger.warning("Permission denied reading .pgpass file")
            return None
        except Exception as e:
            logger.warning("Error reading .pgpass file: %s", e)
            return None

        logger.debug("No matching entry found in .pgpass")
        return None

    @staticmethod
    def get_mysql_credentials(host: str | None = None) -> dict[str, str]:
        """Read credentials from MySQL .my.cnf file.

        Searches in order:
        1. ~/.my.cnf
        2. /etc/my.cnf
        3. /etc/mysql/my.cnf

        Args:
            host: Optional host to match (not commonly used in .my.cnf)

        Returns:
            Dictionary with 'host', 'user', 'password', 'database' keys (if found)
        """
        search_paths = [
            Path.home() / ".my.cnf",
            Path("/etc/my.cnf"),
            Path("/etc/mysql/my.cnf"),
        ]

        for cnf_path in search_paths:
            if not cnf_path.exists():
                continue

            # Security check for user-specific file
            if cnf_path.parent == Path.home():
                file_stat = cnf_path.stat()
                if file_stat.st_mode & 0o077:
                    logger.warning(
                        ".my.cnf file has insecure permissions (%o). Should be 0600. Ignoring file.",
                        file_stat.st_mode & 0o777,
                    )
                    continue

            try:
                config = configparser.ConfigParser()
                config.read(cnf_path)

                if "client" in config:
                    client_section = config["client"]
                    credentials = {}

                    # Extract common credential fields
                    for key in ["host", "user", "password", "database", "port"]:
                        if key in client_section:
                            credentials[key] = client_section[key]

                    if credentials:
                        logger.debug("Found credentials in %s", cnf_path)
                        return credentials

            except Exception as e:
                logger.warning("Error reading %s: %s", cnf_path, e)
                continue

        logger.debug("No MySQL credentials found in .my.cnf files")
        return {}

    @staticmethod
    def sanitize_connection_string(conn_str: str) -> str:
        """Remove password from connection string for safe logging.

        Args:
            conn_str: Database connection string

        Returns:
            Connection string with password replaced by ***
        """
        from sqlalchemy.engine.url import make_url

        try:
            url = make_url(conn_str)
            return url.render_as_string(hide_password=True)
        except Exception:
            # If parsing fails, do basic string replacement
            import re

            # Match password in connection strings like user:<password>@host
            return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", conn_str)
