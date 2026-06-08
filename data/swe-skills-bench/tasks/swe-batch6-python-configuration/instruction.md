# SWE-Skills-Bench: python-configuration (batch6)

# Task: Add Typed Configuration Management to FastAPI Tutorial Application

## Background

The FastAPI repository (https://github.com/fastapi/fastapi) includes a tutorial/example application under `docs_src/` that demonstrates framework patterns. Currently, example applications use hardcoded values for database URLs, secret keys, CORS origins, and feature flags scattered across multiple files. A centralized, typed configuration management system is needed so that all environment-specific settings are loaded from environment variables at startup, validated, and accessed through a single settings object.

## Files to Create/Modify

- `docs_src/settings/app_config.py` (create) — Central typed settings class using pydantic-settings, with database, auth, CORS, and feature flag configuration
- `docs_src/settings/main.py` (create) — FastAPI application that loads and uses the centralized settings, demonstrating dependency injection of configuration
- `docs_src/settings/.env.example` (create) — Example environment file documenting all available configuration variables with placeholder values
- `docs_src/settings/test_settings.py` (create) — Tests verifying settings loading, validation, defaults, and fail-fast behavior on missing required values

## Requirements

### Settings Class

- Define a `Settings` class inheriting from `pydantic_settings.BaseSettings`.
- The class must include the following fields:
  - `database_url` (str, required, alias `DATABASE_URL`) — no default, must be set
  - `database_pool_size` (int, default 5, alias `DATABASE_POOL_SIZE`)
  - `database_pool_overflow` (int, default 10, alias `DATABASE_POOL_OVERFLOW`)
  - `secret_key` (str, required, alias `SECRET_KEY`) — no default
  - `access_token_expire_minutes` (int, default 30, alias `ACCESS_TOKEN_EXPIRE_MINUTES`)
  - `cors_origins` (list[str], default `["http://localhost:3000"]`, alias `CORS_ORIGINS`)
  - `debug` (bool, default False, alias `DEBUG`)
  - `log_level` (str, default `"INFO"`, alias `LOG_LEVEL`, must be one of: DEBUG, INFO, WARNING, ERROR)
  - `redis_url` (str, default `"redis://localhost:6379"`, alias `REDIS_URL`)
  - `enable_signup` (bool, default True, alias `ENABLE_SIGNUP`)
- The class must support loading from a `.env` file.
- A module-level singleton `settings` instance must be created at import time.
- If required fields are missing, the application must exit immediately with a clear error listing all missing variables.

### Validation Rules

- `database_url` must start with `postgresql://` or `postgresql+asyncpg://`; otherwise a `ValidationError` is raised at startup.
- `log_level` must be one of `DEBUG`, `INFO`, `WARNING`, `ERROR` (case-insensitive input, stored uppercase).
- `cors_origins` must be parseable from a comma-separated string in the environment variable (e.g., `CORS_ORIGINS=http://localhost:3000,https://app.example.com`).
- `database_pool_size` must be between 1 and 100 (inclusive).
- `access_token_expire_minutes` must be a positive integer.

### FastAPI Integration

- The FastAPI app in `main.py` must use the settings object for:
  - Configuring CORS middleware with `settings.cors_origins`
  - A `/health` endpoint that returns `{"status": "ok", "debug": settings.debug}`
  - A `/config/public` endpoint that returns non-sensitive settings (debug, log_level, enable_signup) — must NOT expose secret_key, database_url, or redis_url
- Settings must be injectable via FastAPI's `Depends()` mechanism using a `get_settings` function that returns the singleton.

### Environment File

- `.env.example` must list all configuration variables with descriptive comments and safe placeholder values.
- It must clearly mark which variables are required vs. optional.

### Expected Functionality

- Application starts successfully when `DATABASE_URL=postgresql://localhost/mydb` and `SECRET_KEY=my-secret` are set → `/health` returns `{"status": "ok", "debug": false}`.
- Application refuses to start when `DATABASE_URL` is missing → prints "CONFIGURATION ERROR" followed by the missing field name and exits with code 1.
- `DATABASE_URL=mysql://localhost/db` → validation error stating URL must start with `postgresql://`.
- `LOG_LEVEL=debug` → stored as `"DEBUG"` (case-normalized).
- `CORS_ORIGINS=http://a.com,http://b.com` → parsed into `["http://a.com", "http://b.com"]`.
- `DATABASE_POOL_SIZE=0` → validation error (must be ≥ 1).
- `/config/public` endpoint → returns `{"debug": false, "log_level": "INFO", "enable_signup": true}` and does NOT include any secret or connection string.

## Acceptance Criteria

- A typed `Settings` class validates all configuration at startup and fails fast with clear messages on missing or invalid values.
- Required fields (`database_url`, `secret_key`) cause immediate exit with descriptive output when unset.
- Custom validators enforce the database URL prefix, log level enum, pool size range, and CORS parsing rules.
- The FastAPI application uses the settings singleton for CORS configuration and endpoint behavior.
- The `/config/public` endpoint exposes only non-sensitive settings.
- A `.env.example` file documents all variables with comments indicating required vs. optional.
- Tests cover: successful loading with valid env, reject missing required fields, reject invalid values, default behavior, and CORS parsing.
