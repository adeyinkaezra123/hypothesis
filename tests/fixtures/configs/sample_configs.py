"""Sample configuration files for testing."""

# Sample YAML config with environment variable interpolation
SAMPLE_CONFIG_WITH_ENV_VARS = """
production:
  dialect: postgresql
  host: ${DB_HOST}
  port: ${DB_PORT}
  database: myapp_production
  username: app_user

development:
  dialect: postgresql
  host: ${DEV_HOST:-localhost}
  port: ${DEV_PORT:-5432}
  database: myapp_development
"""

# Simple config without environment variables
SIMPLE_CONFIG = """
development:
  dialect: postgresql
  host: localhost
  port: 5432
  database: myapp_dev

production:
  dialect: postgresql
  host: db.example.com
  port: 5432
  database: myapp_prod
"""

# Config with multiple databases
MULTI_DATABASE_CONFIG = """
primary:
  dialect: postgresql
  host: db-primary.example.com
  port: 5432
  database: myapp_primary

replica:
  dialect: postgresql
  host: db-replica.example.com
  port: 5432
  database: myapp_primary

analytics:
  dialect: mysql
  host: analytics.example.com
  port: 3306
  database: analytics_db
"""

# Config with connection URL
URL_CONFIG = """
production:
  url: ${DATABASE_URL}

development:
  url: postgresql://localhost/myapp_dev
"""
