# Testing with Real PostgreSQL Database

## 🚀 Quick Start (Docker - Recommended)

### Step 1: Start PostgreSQL with Docker

```bash
# Start PostgreSQL container
docker run --name postgres-test \
  -e POSTGRES_PASSWORD="$HYPOTHESIS_TEST_DATABASE_PASSWORD" \
  -p 5432:5432 \
  -d postgres:16

# Verify it's running
docker ps | grep postgres-test
```

### Step 2: Install PostgreSQL Driver

```bash
# Install psycopg2 (PostgreSQL driver)
uv add psycopg2-binary
```

### Step 3: Run the Test Script

```bash
# Run the manual test
uv run python test_real_database.py
```

**Expected Output:**
```
🐘 PostgreSQL Connection Tests
==================================================

=== Test 1: Direct Connection String ===
Connecting to: <sanitized PostgreSQL URL>
✅ Connection successful!
✅ Dialect detected: postgresql
✅ Write permissions confirmed!
✅ Connection closed successfully

=== Test 2: Component Flags ===
Built connection: <sanitized PostgreSQL URL>
✅ Connection successful!
✅ Dialect: postgresql

=== Test 3: Config File ===
...
```

### Step 4: Test with Config File (Optional)

Create `.hypothesisrc` in the project root:

```yaml
# .hypothesisrc
test_db:
  dialect: postgresql
  host: localhost
  port: 5432
  database: postgres
  username: postgres
  password: ${HYPOTHESIS_TEST_DATABASE_PASSWORD}

local_dev:
  dialect: postgresql
  host: localhost
  database: postgres
  username: postgres
  # Password will be prompted or read from .pgpass
```

Then test:
```bash
uv run python -c "
from hypothesis.core.connection_builder import build_connection_string
from hypothesis.core.connection import DatabaseConnection

conn_str = build_connection_string(database_name='test_db')
db = DatabaseConnection(conn_str)
print(f'Connected! Dialect: {db.get_dialect()}')
db.close()
"
```

### Step 5: Test with .pgpass (Optional)

Create `~/.pgpass`:
```bash
# Create .pgpass file
cat > ~/.pgpass << 'EOF'
localhost:5432:postgres:db_user:<database-password>
EOF

# Set correct permissions
chmod 600 ~/.pgpass
```

Update `.hypothesisrc` to omit password:
```yaml
secure_db:
  dialect: postgresql
  host: localhost
  database: postgres
  username: postgres
  # No password - will use .pgpass
```

Test:
```bash
uv run python -c "
from hypothesis.core.connection_builder import build_connection_string
conn_str = build_connection_string(database_name='secure_db')
print('Password loaded from .pgpass!')
"
```

### Step 6: Cleanup

```bash
# Stop and remove container
docker stop postgres-test
docker rm postgres-test

# Remove .pgpass (optional)
rm ~/.pgpass
```

---

## 🔧 Alternative: Local PostgreSQL Installation

### macOS (Homebrew)

```bash
# Install PostgreSQL
brew install postgresql@16

# Start PostgreSQL
brew services start postgresql@16

# Create test database
createdb testdb

# Test connection
psql testdb
```

### Ubuntu/Debian

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql

# Create user and database
sudo -u postgres createuser -s $USER
createdb testdb

# Test connection
psql testdb
```

### Connection String for Local Install

```python
# Usually no password needed for local connections
conn_str = "postgresql://$(whoami)@localhost/testdb"
```

---

## 🧪 Interactive Testing

### Python REPL

```bash
uv run python
```

```python
from hypothesis.core.connection import DatabaseConnection
from hypothesis.core.connection_builder import build_connection_string

# Test connection
conn_str = "postgresql://postgres@localhost:5432/postgres"
db = DatabaseConnection(conn_str)

# Validate
print(db.validate())  # Should print: True

# Get dialect
print(db.get_dialect())  # Should print: postgresql

# Test write permissions
print(db.test_write_permissions())  # Should print: True

# Cleanup
db.close()
```

### Using pytest

```bash
# Run with real database (mark as integration test)
uv run pytest tests/integration/ -v -m "integration"
```

---

## 🐛 Troubleshooting

### Connection Refused
```
Error: connection refused
```
**Solution**: PostgreSQL not running
```bash
# Docker
docker ps | grep postgres

# Local
brew services list  # macOS
sudo systemctl status postgresql  # Linux
```

### Authentication Failed
```
Error: password authentication failed
```
**Solution**: Check credentials
```bash
# Reset password (Docker)
docker exec -it postgres-test psql -U postgres \
  -c "ALTER USER postgres PASSWORD :'database_password';" \
  --set=database_password="$HYPOTHESIS_TEST_DATABASE_PASSWORD"

# Reset password (Local)
sudo -u postgres psql \
  -c "ALTER USER postgres PASSWORD :'database_password';" \
  --set=database_password="$HYPOTHESIS_TEST_DATABASE_PASSWORD"
```

### Driver Not Found
```
Error: No module named 'psycopg2'
```
**Solution**: Install driver
```bash
uv add psycopg2-binary
```

### Port Already in Use
```
Error: port 5432 already in use
```
**Solution**: Use different port
```bash
# Docker with custom port
docker run --name postgres-test \
  -e POSTGRES_PASSWORD="$HYPOTHESIS_TEST_DATABASE_PASSWORD" \
  -p 5433:5432 \
  -d postgres:16

# Update connection string
conn_str = "postgresql://postgres@localhost:5433/postgres"
```

---

## ✅ Verification Checklist

- [ ] PostgreSQL is running
- [ ] psycopg2-binary is installed
- [ ] Can connect with direct connection string
- [ ] Can connect with component flags
- [ ] Can connect with config file
- [ ] Dialect detection works
- [ ] Write permissions confirmed
- [ ] Connection closes cleanly

---

## 📝 Next Steps

Once connection works:
1. Create test schema with tables
2. Test schema introspection
3. Test data generation
4. Test with MySQL (similar process)
