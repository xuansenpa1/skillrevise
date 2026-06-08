# SWE-Skills-Bench: python-configuration (batch8)

# Task: Add Typed Configuration Management to a FastAPI Application

## Background

FastAPI (https://github.com/fastapi/fastapi) provides extensive examples in its `docs_src/` directory. The project currently lacks a comprehensive example demonstrating externalized, typed configuration management — a pattern essential for deploying the same application across development, staging, and production environments. A new example application is needed that manages database connections, external API integrations, and feature flags through environment variables validated at startup.

## Files to Create/Modify

- `docs_src/settings/app.py` (create) — FastAPI application with multiple routers dependent on typed settings
- `docs_src/settings/config.py` (create) — Central `Settings` class using `pydantic-settings` with environment-specific validation, typed fields, and sensible defaults
- `docs_src/settings/database.py` (create) — Database connection factory that consumes settings for host, port, credentials, and pool size
- `docs_src/settings/dependencies.py` (create) — FastAPI dependency functions that inject `Settings` and database connections into route handlers
- `docs_src/settings/.env.example` (create) — Template environment file documenting all required and optional variables
- `tests/test_settings/test_config.py` (create) — Tests validating settings loading, defaults, validation errors, and environment overrides

## Requirements

### Settings Class

- `Settings` must extend `pydantic_settings.BaseSettings` with the following fields:
  - `app_name`: `str`, default `"FastAPI App"`
  - `debug`: `bool`, default `False`
  - `database_url`: `str`, required (no default) — full connection URI
  - `database_pool_min`: `int`, default `2`, must be ≥ 1
  - `database_pool_max`: `int`, default `10`, must be ≥ `database_pool_min`
  - `redis_url`: `str`, default `"redis://localhost:6379/0"`
  - `api_secret_key`: `str`, required (no default)
  - `external_api_base_url`: `str`, required (no default) — must start with `https://` in non-debug mode
  - `external_api_timeout`: `float`, default `30.0`, must be > 0
  - `enable_feature_x`: `bool`, default `False`
  - `cors_origins`: `list[str]`, default `["http://localhost:3000"]`
  - `log_level`: `str`, default `"INFO"`, must be one of `["DEBUG", "INFO", "WARNING", "ERROR"]`
- All fields must load from environment variables (e.g., `DATABASE_URL`, `API_SECRET_KEY`)
- The class must support loading from a `.env` file
- A `@model_validator` must enforce: `database_pool_max >= database_pool_min`
- A `@field_validator` on `external_api_base_url` must reject non-HTTPS URLs when `debug` is `False`

### Startup Validation

- The application must instantiate `Settings()` at import time of `config.py`
- If any required field is missing, the application must print a structured error listing every missing field and exit with code 1 — not start with a broken configuration
- If validation fails (e.g., `database_pool_max < database_pool_min`), the error message must include the field names and the constraint violated

### Dependency Injection

- A FastAPI dependency `get_settings()` must return the singleton `Settings` instance
- A FastAPI dependency `get_db()` must return a database connection/session from the pool configured via settings
- Route handlers must receive configuration through dependency injection, never by importing the `settings` object directly at the module level in router files

### API Endpoints

- `GET /health` — returns `{"status": "ok", "app_name": settings.app_name, "debug": settings.debug}`
- `GET /config/features` — returns `{"feature_x": settings.enable_feature_x}` (only non-secret settings)
- `GET /items/{item_id}` — a sample route demonstrating database dependency injection; returns mock item data
- No endpoint may expose `api_secret_key`, `database_url`, or other secrets in its response

### Environment File

- `.env.example` must list every environment variable with a comment describing its purpose, type, and whether it is required
- Secrets (`API_SECRET_KEY`, `DATABASE_URL`) must have placeholder values like `changeme` with a comment marking them as required

## Expected Functionality

- Starting the application without `DATABASE_URL` set prints `"CONFIGURATION ERROR"` with the missing field listed and exits with code 1
- Starting with `DATABASE_POOL_MIN=5` and `DATABASE_POOL_MAX=2` fails at startup with a validation error mentioning both fields
- Setting `EXTERNAL_API_BASE_URL=http://insecure.example.com` with `DEBUG=false` fails at startup with a validation error about HTTPS
- Setting `EXTERNAL_API_BASE_URL=http://insecure.example.com` with `DEBUG=true` succeeds (relaxed validation in debug mode)
- `GET /health` returns the configured app name and debug flag
- `GET /config/features` returns feature flag state without exposing secrets
- All settings can be overridden via environment variables or a `.env` file

## Acceptance Criteria

- `Settings` class loads all configuration from environment variables with proper types, defaults, and validation constraints
- Missing required fields at startup produce a clear error message and exit before the server starts accepting requests
- Cross-field validation (`pool_max >= pool_min`, HTTPS enforcement in non-debug mode) is enforced at startup
- Route handlers receive settings and database connections through FastAPI's dependency injection system
- No API endpoint exposes secret values (`api_secret_key`, `database_url`) in its response body
- The `.env.example` file documents all environment variables with types and required/optional status
- Tests verify successful loading with valid config, proper defaults, startup failure on missing fields, and validation error messages
