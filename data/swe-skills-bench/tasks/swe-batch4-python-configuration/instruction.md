# SWE-Skills-Bench: python-configuration (batch4)

# Task: Implement Typed Configuration System for a FastAPI Application

## Background

The FastAPI framework (https://github.com/fastapi/fastapi) is used for building modern Python APIs. A new example application needs a robust configuration management system that loads settings from environment variables with typed validation, supports multiple environments (development, staging, production), fails fast on missing or invalid configuration, and provides sensible defaults for local development while requiring explicit values for sensitive settings.

## Files to Create/Modify

- `docs_src/advanced_settings/app/config.py` (create) — Central typed settings class with environment-specific loading, validation, and computed properties
- `docs_src/advanced_settings/app/main.py` (create) — FastAPI application that wires configuration into dependency injection
- `docs_src/advanced_settings/app/dependencies.py` (create) — Dependency providers for database connections, Redis clients, and external API clients configured from settings
- `docs_src/advanced_settings/.env.example` (create) — Example environment file documenting all configuration variables
- `docs_src/advanced_settings/tests/test_config.py` (create) — Tests validating configuration behavior under various environment conditions

## Requirements

### Settings Class

- A `Settings` class loading configuration from environment variables with typed fields
- Required fields (no default, must be explicitly set): `DATABASE_URL` (string), `SECRET_KEY` (string, min 32 chars), `API_KEY` (string)
- Optional fields with development defaults: `DEBUG` (bool, default `False`), `LOG_LEVEL` (string, default `"INFO"`, one of `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`), `DB_POOL_SIZE` (int, default 5, range 1–50), `DB_POOL_TIMEOUT` (int, default 30, range 5–300), `REDIS_URL` (string, default `"redis://localhost:6379/0"`), `CORS_ORIGINS` (list of strings, default `["http://localhost:3000"]`)
- Computed property `database_url_masked` that returns the DATABASE_URL with the password portion replaced by `***`
- A `model_config` enabling `.env` file loading with `utf-8` encoding

### Environment Profiles

- An `ENVIRONMENT` variable (string, one of `"development"`, `"staging"`, `"production"`, default `"development"`)
- When `ENVIRONMENT` is `"production"`:
  - `DEBUG` must be `False`; if set to `True`, a validation error must be raised
  - `SECRET_KEY` length minimum increases to 64 characters
  - `CORS_ORIGINS` must not contain `localhost` origins; if it does, a validation error must be raised
- When `ENVIRONMENT` is `"development"`:
  - `DEBUG` defaults to `True`
  - Shorter `SECRET_KEY` is acceptable (32+ chars)

### Fail-Fast Behavior

- If any required field is missing, the application must fail at import/startup time with a clear error message listing all missing fields
- If a field value violates its constraints (e.g., `DB_POOL_SIZE=0`, `LOG_LEVEL=TRACE`), the error message must identify the field, the constraint, and the invalid value
- If multiple fields are invalid, all errors must be reported at once, not one at a time

### Dependency Integration

- A `get_settings()` dependency function that returns the singleton settings instance, usable via FastAPI's `Depends()`
- A `get_db_pool()` dependency that creates a database connection pool using settings from `Settings` (pool size, timeout, URL)
- A `get_redis()` dependency that creates a Redis client using `REDIS_URL` from settings
- Dependencies must be overridable in tests via FastAPI's dependency override mechanism

### `.env.example` File

- Must list every configuration variable with a comment describing its purpose, type, and constraints
- Required variables must be marked with `# REQUIRED`
- Sensitive variables must include a warning comment: `# SENSITIVE - do not commit actual values`

### Expected Functionality

- Setting `DATABASE_URL=postgresql://user:pass@host/db` and `SECRET_KEY=<64 chars>` and `API_KEY=xxx` starts the app successfully
- Missing `DATABASE_URL` causes startup failure with message: `DATABASE_URL: field required`
- Setting `DB_POOL_SIZE=0` causes failure with message including `greater than or equal to 1`
- Setting `ENVIRONMENT=production` and `DEBUG=True` causes failure with a message about debug mode in production
- Setting `ENVIRONMENT=production` and `CORS_ORIGINS=["http://localhost:3000"]` causes failure about localhost in production
- `settings.database_url_masked` for `postgresql://user:s3cret@host/db` returns `postgresql://user:***@host/db`
- In tests, overriding `get_settings` injects custom configuration without loading real environment variables

## Acceptance Criteria

- Settings class loads and validates all fields from environment variables at startup
- Missing required fields cause immediate startup failure with a message listing all missing fields
- Invalid field values cause failure with descriptive constraint messages
- Production-specific validation rules reject `DEBUG=True` and localhost CORS origins
- The masked database URL correctly hides the password component
- FastAPI dependencies use the settings singleton and are overridable in tests
- `.env.example` documents all variables with types, constraints, and sensitivity markers
- Tests verify fail-fast behavior, environment-specific rules, and dependency override patterns
