# SWE-Skills-Bench: python-configuration (batch5)

# Task: Add Typed Configuration Management to the FastAPI Full-Stack Template

## Background

FastAPI (https://github.com/fastapi/fastapi) uses environment variables for configuration in its project templates, but the full-stack template currently scatters `os.environ.get()` calls across multiple modules without centralized validation. This task requires introducing a structured, typed configuration system that validates all required settings at application startup, supports multiple environments (development, testing, production), and fails fast with clear error messages when configuration is invalid.

## Files to Create/Modify

- `fastapi/config.py` (create) — Central configuration module defining typed settings classes for the application, database, CORS, and auth subsystems.
- `fastapi/config_loader.py` (create) — Configuration loader that reads from environment variables and `.env` files, resolves environment-specific overrides, and validates all settings at import time.
- `tests/test_config.py` (create) — Tests for validation behavior: missing required vars, type coercion errors, environment-specific defaults, and `.env` file loading.

## Requirements

### Settings Structure

- `AppSettings`: `app_name` (str, required), `debug` (bool, default `False`), `environment` (literal `"development"` | `"testing"` | `"production"`, required), `log_level` (str, default `"INFO"`), `allowed_hosts` (list of strings, default `["*"]`).
- `DatabaseSettings`: `database_url` (str, required), `pool_size` (int, default 5, must be 1–50), `pool_timeout` (int, default 30, must be > 0), `echo_sql` (bool, default `False`).
- `AuthSettings`: `secret_key` (str, required, min 32 characters), `access_token_expire_minutes` (int, default 30, must be > 0), `algorithm` (str, default `"HS256"`).
- `CorsSettings`: `allow_origins` (list of strings, default `["*"]`), `allow_methods` (list of strings, default `["*"]`), `allow_credentials` (bool, default `True`).

### Validation Rules

- All settings are loaded and validated when the module is first imported; if any required field is missing or invalid, a descriptive error is raised before the application starts.
- `database_url` must start with a recognized scheme (`postgresql://`, `sqlite://`, `mysql://`).
- `secret_key` with fewer than 32 characters raises a validation error that names the field and the constraint.
- `pool_size` outside the range [1, 50] raises a validation error.
- `environment` must be one of the three allowed literals; any other value is rejected.

### Environment Support

- Settings are read from environment variables with a `APP_` prefix (e.g., `APP_DATABASE_URL`, `APP_SECRET_KEY`).
- A `.env` file in the project root is loaded automatically if it exists but does not override already-set environment variables.
- Environment-specific defaults: `debug=True` and `echo_sql=True` when `environment="development"`; `debug=False` and `echo_sql=False` otherwise.

### Expected Functionality

- With `APP_ENVIRONMENT=production`, `APP_DATABASE_URL=postgresql://...`, `APP_SECRET_KEY=<valid 64-char key>` set → settings load successfully, `debug` is `False`.
- With `APP_ENVIRONMENT=development` set and no `APP_DEBUG` → `debug` defaults to `True`.
- Missing `APP_DATABASE_URL` → startup error: `"Field 'database_url' is required but not set"`.
- `APP_SECRET_KEY=short` (under 32 chars) → startup error: `"Field 'secret_key' must be at least 32 characters"`.
- `APP_DATABASE_URL=ftp://bad.scheme` → validation error naming the invalid scheme.
- `APP_POOL_SIZE=100` → validation error: `"pool_size must be between 1 and 50"`.

## Acceptance Criteria

- All four settings classes (`AppSettings`, `DatabaseSettings`, `AuthSettings`, `CorsSettings`) are defined with typed fields, defaults, and constraints.
- Required fields that are missing at startup produce a clear error message naming the field.
- Type coercion (string → int, string → bool, comma-separated → list) works correctly for all fields.
- Environment-specific defaults apply correctly for `development`, `testing`, and `production`.
- `.env` file is loaded when present but does not override existing environment variables.
- Tests cover: valid configuration, each required-field-missing case, each constraint violation, and environment-specific default behavior.
