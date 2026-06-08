# SWE-Skills-Bench: python-configuration (batch3)

# Task: Add Typed Configuration Management to FastAPI Application Settings

## Background

FastAPI (https://github.com/fastapi/fastapi) is a modern Python web framework. The framework's own documentation examples and internal test applications use ad-hoc configuration approaches. This task adds a structured, validated, environment-aware configuration module to the FastAPI project's test/example application that demonstrates production-grade configuration management with type safety, validation at boot time, and support for multiple deployment environments.

## Files to Create/Modify

- `tests/test_app/config.py` (create) — Typed settings classes with validation, environment-specific overrides, and secret handling
- `tests/test_app/app.py` (modify) — Wire the configuration into the FastAPI app lifecycle (startup validation, dependency injection)
- `tests/test_app/test_config.py` (create) — Tests for configuration loading, validation, environment switching, and error cases

## Requirements

### Settings Structure

- Define a `DatabaseSettings` class with fields: `host` (str, required), `port` (int, default 5432, must be 1–65535), `name` (str, required), `user` (str, required), `password` (str, required, must not appear in logs or repr), `pool_size` (int, default 5, must be 1–100), `ssl_mode` (str, one of `"disable"`, `"require"`, `"verify-ca"`, `"verify-full"`, default `"require"`)
- Define a `RedisSettings` class with fields: `url` (str, required, must start with `redis://` or `rediss://`), `max_connections` (int, default 10), `key_prefix` (str, default `"fastapi:"`)
- Define a `AppSettings` class with fields: `debug` (bool, default False), `environment` (str, one of `"development"`, `"staging"`, `"production"`), `secret_key` (str, required, minimum 32 characters), `allowed_hosts` (list of strings, default `["*"]` in development, empty list in production), `log_level` (str, one of `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, default depends on environment), `database` (nested `DatabaseSettings`), `redis` (nested `RedisSettings`)
- All settings must be loadable from environment variables with a prefix: `APP_` for AppSettings, `APP_DATABASE_` for DatabaseSettings, `APP_REDIS_` for RedisSettings

### Validation Rules

- If `environment` is `"production"`, `debug` must be `False`; raise `ValueError` if both `environment="production"` and `debug=True`
- If `environment` is `"production"`, `allowed_hosts` must not contain `"*"`; raise `ValueError` if it does
- `secret_key` shorter than 32 characters must raise `ValueError` with a message about minimum length
- `database.port` outside 1–65535 range must raise `ValueError`
- `redis.url` not starting with `redis://` or `rediss://` must raise `ValueError`
- All validation errors must be raised at settings construction time, not deferred to first use

### Boot-Time Behavior

- On application startup, load and validate all settings; if any validation fails, the application must not start and must print all validation errors (not just the first one)
- Provide a `get_settings()` dependency function that returns the cached singleton `AppSettings` instance
- Secret fields (`password`, `secret_key`) must never appear in string representations, logs, or error messages

### Expected Functionality

- Setting `APP_ENVIRONMENT=production`, `APP_SECRET_KEY=<64-char-string>`, `APP_DEBUG=false`, `APP_DATABASE_HOST=db.example.com`, etc. produces a valid `AppSettings` instance
- Setting `APP_ENVIRONMENT=production` and `APP_DEBUG=true` raises `ValueError` mentioning the conflict
- Setting `APP_DATABASE_PORT=99999` raises `ValueError` mentioning the valid range
- Omitting `APP_DATABASE_HOST` raises a validation error mentioning the missing field
- `str(settings)` and `repr(settings)` show `"***"` instead of actual secret values
- Setting `APP_ENVIRONMENT=development` without `APP_LOG_LEVEL` defaults `log_level` to `"DEBUG"`
- Setting `APP_ENVIRONMENT=production` without `APP_LOG_LEVEL` defaults `log_level` to `"WARNING"`

## Acceptance Criteria

- Settings classes load values from environment variables with the correct prefixes
- All validation rules fire at construction time and produce descriptive error messages
- Production environment rejects `debug=True` and `allowed_hosts=["*"]`
- Secret fields are masked in `__repr__`, `__str__`, and any logged output
- Missing required fields raise validation errors listing all missing fields, not just the first
- `get_settings()` returns the same cached singleton across multiple dependency injection calls
- Environment-specific defaults (log_level, allowed_hosts) apply correctly per environment
- Tests cover all validation rules, environment combinations, and error scenarios
