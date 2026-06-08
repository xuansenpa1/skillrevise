# SWE-Skills-Bench: python-configuration (batch9)

# Task: Add a Typed Configuration System to a FastAPI Application

## Background

FastAPI (https://github.com/fastapi/fastapi) applications need robust configuration management that externalizes secrets and environment-specific settings. This task adds a comprehensive typed configuration system to the FastAPI project's test application using pydantic-settings, with validation, environment-specific overrides, secret management, and a configuration health check endpoint.

## Files to Create/Modify

- `docs_src/settings/app_config.py` (create) — Main `Settings` class using `pydantic_settings.BaseSettings` with all application configuration fields, nested model for database config, and custom validators
- `docs_src/settings/app.py` (create) — FastAPI application using the Settings class, with a dependency-injected settings provider and a `/health/config` endpoint
- `docs_src/settings/.env.example` (create) — Example environment file with all required variables documented
- `docs_src/settings/.env.test` (create) — Test environment file with safe defaults for CI
- `tests/test_settings/test_app_config.py` (create) — Tests for configuration loading, validation, defaults, environment overrides, and error handling

## Requirements

### Settings Class (`app_config.py`)

- Class `DatabaseSettings(BaseModel)`:
  - `host: str` with default `"localhost"`
  - `port: int` with default `5432`, must be between 1 and 65535 (use `Field(ge=1, le=65535)`)
  - `name: str` with default `"app_db"`
  - `user: str` (required, no default)
  - `password: SecretStr` (required, no default)
  - `pool_size: int` with default `10`, must be between 1 and 100
  - `pool_timeout: int` with default `30`, in seconds
  - Property `url` that returns `postgresql://{user}:{password}@{host}:{port}/{name}` (with password revealed)

- Class `Settings(BaseSettings)`:
  - `app_name: str` with default `"My FastAPI App"`
  - `app_version: str` with default `"0.1.0"`
  - `debug: bool` with default `False`
  - `environment: Literal["development", "staging", "production"]` with default `"development"`
  - `log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]` with default `"INFO"`
  - `allowed_hosts: list[str]` with default `["*"]`, parsed from comma-separated env var `ALLOWED_HOSTS`
  - `cors_origins: list[str]` with default `["http://localhost:3000"]`, parsed from comma-separated env var `CORS_ORIGINS`
  - `api_key: SecretStr` (required)
  - `jwt_secret: SecretStr` (required)
  - `jwt_algorithm: str` with default `"HS256"`
  - `jwt_expiry_minutes: int` with default `30`, must be positive
  - `database: DatabaseSettings` — Nested model loaded from env vars with prefix `DB_`
  - `redis_url: str` with default `"redis://localhost:6379/0"`
  - `sentry_dsn: str | None` with default `None`
  - `rate_limit_per_minute: int` with default `60`, must be positive
  - Custom validator: if `environment == "production"`, `debug` must be `False` and `allowed_hosts` must not contain `"*"` — raise `ValueError` otherwise
  - `model_config` with `env_file = ".env"`, `env_file_encoding = "utf-8"`, `env_nested_delimiter = "__"`

### FastAPI Application (`app.py`)

- Create a `get_settings()` dependency function annotated with `@lru_cache` that returns a `Settings` instance
- Use `Depends(get_settings)` in endpoint signatures
- `GET /health/config` — Returns a JSON object with: `app_name`, `environment`, `debug`, `log_level`, `database_host` (from settings.database.host), `database_name`, `redis_url`, and `config_valid: true`. Must NOT expose secrets (no API key, JWT secret, or database password in the response)
- Application startup must fail with a clear error if required env vars (`API_KEY`, `JWT_SECRET`, `DB_USER`, `DB_PASSWORD`) are missing

### Environment Files

- `.env.example` must include all environment variables with placeholder values and comments explaining each
- `.env.test` must include safe defaults that allow tests to run without external services: `API_KEY=test-api-key-not-for-production`, `JWT_SECRET=test-jwt-secret-not-for-production`, `DB_USER=test`, `DB_PASSWORD=test`, `ENVIRONMENT=development`, `DEBUG=true`

### Expected Functionality

- With `.env.test` loaded, `Settings()` creates a valid configuration with all fields populated
- Setting `ENVIRONMENT=production` and `DEBUG=true` raises a `ValidationError` at startup
- Setting `ALLOWED_HOSTS=*` with `ENVIRONMENT=production` raises a `ValidationError`
- Setting `DB_PORT=99999` raises a `ValidationError` (exceeds 65535)
- The `/health/config` endpoint returns configuration metadata without any secret values
- `settings.database.url` returns the full connection string with the actual password
- `settings.api_key.get_secret_value()` returns the actual key, while `str(settings.api_key)` returns `"**********"`

## Acceptance Criteria

- `Settings` loads all configuration from environment variables with correct types and defaults
- `SecretStr` fields do not appear in string representations or JSON serialization
- Nested `DatabaseSettings` loads from `DB_` prefixed env vars using `env_nested_delimiter`
- Production environment validator rejects `debug=True` and wildcard allowed hosts
- Port and pool_size validators enforce numeric range constraints
- `GET /health/config` returns configuration metadata without secrets
- `lru_cache` ensures `Settings` is instantiated only once per process
- Missing required env vars cause immediate startup failure with descriptive error
- `python -m pytest /workspace/tests/test_python_configuration.py -v --tb=short` passes
