"""Manual test script for a real PostgreSQL database connection."""

import os

from hypothesis.config.credentials import CredentialManager
from hypothesis.core.connection import DatabaseConnection
from hypothesis.core.connection_builder import build_connection_string

DEFAULT_CONN_STR = "postgresql://postgres@localhost:5432/postgres"


def test_direct_connection():
    """Test 1: Direct connection string."""
    print("\n=== Test 1: Direct Connection String ===")

    conn_str = os.environ.get("HYPOTHESIS_TEST_DATABASE_URL", DEFAULT_CONN_STR)

    print(f"Connecting to: {CredentialManager.sanitize_connection_string(conn_str)}")

    try:
        db = DatabaseConnection(conn_str)

        # Test connection
        if db.validate():
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")
            return

        # Test dialect detection
        dialect = db.get_dialect()
        print(f"✅ Dialect detected: {dialect}")

        # Test write permissions
        if db.test_write_permissions():
            print("✅ Write permissions confirmed!")
        else:
            print("⚠️  No write permissions")

        db.close()
        print("✅ Connection closed successfully")

    except Exception as e:
        print(f"❌ Error: {e}")


def test_component_flags():
    """Test 2: Building connection from component flags."""
    print("\n=== Test 2: Component Flags ===")

    try:
        conn_str = build_connection_string(
            dialect="postgres",
            host="localhost",
            port=5432,
            database="postgres",
            username="postgres",
            password=os.environ.get("HYPOTHESIS_TEST_DATABASE_PASSWORD"),
        )

        print(f"Built connection: {CredentialManager.sanitize_connection_string(conn_str)}")

        db = DatabaseConnection(conn_str)

        if db.validate():
            print("✅ Connection successful!")
            print(f"✅ Dialect: {db.get_dialect()}")

        db.close()

    except Exception as e:
        print(f"❌ Error: {e}")


def test_config_file():
    """Test 3: Using config file (.hypothesisrc)."""
    print("\n=== Test 3: Config File ===")
    print("Create a .hypothesisrc file with:")
    print("""
test_db:
  dialect: postgresql
  host: localhost
  port: 5432
  database: postgres
  username: postgres
  password: ${HYPOTHESIS_TEST_DATABASE_PASSWORD}
""")

    try:
        conn_str = build_connection_string(database_name="test_db")

        print(f"Loaded from config: {CredentialManager.sanitize_connection_string(conn_str)}")

        db = DatabaseConnection(conn_str)

        if db.validate():
            print("✅ Connection successful!")

        db.close()

    except Exception as e:
        print(f"❌ Error (expected if no config file): {e}")


if __name__ == "__main__":
    print("🐘 PostgreSQL Connection Tests")
    print("=" * 50)

    test_direct_connection()
    test_component_flags()
    test_config_file()

    print("\n" + "=" * 50)
    print("✅ All tests completed!")
