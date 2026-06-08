# SWE-Skills-Bench: python-configuration (batch7)

# Task: Add a Typed Configuration System to FastAPI's Tutorial Examples

## Background

FastAPI (https://github.com/fastapi/fastapi) provides documentation examples that demonstrate best practices. The task is to create a configuration management example that shows how to load application settings from environment variables with typed validation, nested configuration groups, fail-fast behavior, and dependency injection into FastAPI endpoints.

## Files to Create/Modify

- `docs_src/settings/tutorial001.py` (create) — FastAPI application demonstrating typed settings loaded from environment variables and injected as dependencies
- `docs_src/settings/config.py` (create) — Settings classes with nested groups, validators, and environment-specific defaults
- `tests/test_tutorial/test_settings/test_tutorial001.py` (create) — Tests for the settings tutorial application covering validation, defaults, and endpoint behavior
- `tests/test_tutorial/test_settings/__init__.py` (create) — Package init

## Requirements

### Settings Classes (`config.py`)

#### `DatabaseSettings`
- `host` — `str`, default `"localhost"`, env var `DATABASE_HOST`
- `port` — `int`, default `5432`, env var `DATABASE_PORT`
- `name` — `str`, required (no default), env var `DATABASE_NAME`
- `user` — `str`, required, env var `DATABASE_USER`
- `password` — `str`, required, env var `DATABASE_PASSWORD`
- `pool_size` — `int`, default `5`, env var `DATABASE_POOL_SIZE`, must be between 1 and 100 (validated)
- Computed property `url` — Returns `postgresql://{user}:{password}@{host}:{port}/{name}`

#### `RedisSettings`
- `url` — `str`, default `"redis://localhost:6379/0"`, env var `REDIS_URL`
- `max_connections` — `int`, default `10`, env var `REDIS_MAX_CONNECTIONS`

#### `AuthSettings`
- `secret_key` — `str`, required, env var `AUTH_SECRET_KEY`
- `algorithm` — `str`, default `"HS256"`, env var `AUTH_ALGORITHM`
- `access_token_expire_minutes` — `int`, default `30`, env var `AUTH_ACCESS_TOKEN_EXPIRE_MINUTES`

#### `AppSettings` (root settings)
- `app_name` — `str`, default `"My App"`, env var `APP_NAME`
- `debug` — `bool`, default `False`, env var `DEBUG`
- `environment` — Literal `"local"`, `"staging"`, `"production"`, default `"local"`, env var `ENVIRONMENT`
- `allowed_hosts` — `list[str]`, default `["localhost"]`, env var `ALLOWED_HOSTS` (comma-separated string parsed via validator)
- `database` — `DatabaseSettings` (nested)
- `redis` — `RedisSettings` (nested)
- `auth` — `AuthSettings` (nested)
- Computed property `is_production` — Returns `True` when `environment == "production"`
- Model config: use `env_nested_delimiter = "__"` so env vars like `DATABASE__HOST` map to `database.host`
- Model config: support `.env` file loading with `env_file = ".env"`

#### Validation Rules
- If `environment` is `"production"`, `debug` must be `False` (raise `ValueError` otherwise)
- If `environment` is `"production"`, `auth.secret_key` must be at least 32 characters (raise `ValueError` otherwise)
- `allowed_hosts` validator: if the value is a string, split by commas and strip whitespace; if already a list, pass through

### FastAPI Application (`tutorial001.py`)

- Create a `FastAPI` app instance
- Implement `get_settings()` dependency that returns a cached `AppSettings` singleton (use `@lru_cache`)
- Endpoints:
  - `GET /info` — Returns `{"app_name": settings.app_name, "environment": settings.environment, "debug": settings.debug}`
  - `GET /health` — Returns `{"status": "healthy", "database_url": settings.database.url, "redis_url": settings.redis.url}` (redact the password in database_url: replace the password with `"***"`)
  - `GET /settings/validate` — Attempts to load settings; returns `{"valid": true}` if successful or `{"valid": false, "errors": [...]}` with a list of validation error messages if settings are invalid

### Fail-Fast Behavior

- When the application starts, `AppSettings` must be instantiated immediately (not lazily on first request)
- If any required environment variable is missing, the application must fail to start with a clear error message listing all missing variables
- The error message format: `"Configuration error: Missing required settings: DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD, AUTH_SECRET_KEY"`

## Expected Functionality

- With env vars `DATABASE_NAME=mydb`, `DATABASE_USER=admin`, `DATABASE_PASSWORD=secret`, `AUTH_SECRET_KEY=my-secret-key-for-dev`:
  - `GET /info` returns `{"app_name": "My App", "environment": "local", "debug": false}`
  - `GET /health` returns database URL with `"***"` replacing the password
- With `ENVIRONMENT=production` and `DEBUG=true`: app fails to start with validation error
- With `DATABASE__HOST=db.prod.com` and `DATABASE__PORT=5433`: settings override the defaults via nested delimiter
- With `ALLOWED_HOSTS=api.example.com, admin.example.com`: `allowed_hosts` is parsed to `["api.example.com", "admin.example.com"]`

## Acceptance Criteria

- `AppSettings` loads all nested groups (`database`, `redis`, `auth`) from environment variables using `__` delimiter
- Required settings without defaults raise `ValidationError` when missing
- The `allowed_hosts` validator correctly splits comma-separated strings
- Production environment validation rejects `debug=True` and short secret keys
- `GET /info` returns the current app configuration (name, environment, debug)
- `GET /health` returns connection URLs with the database password redacted
- Settings are cached (singleton) — multiple dependency injections return the same instance
- All tests pass when appropriate environment variables are set in the test setup
