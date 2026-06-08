# SWE-Skills-Bench: python-configuration (batch10)

# Task: Add Typed Configuration System to FastAPI Application Settings

## Background

FastAPI (https://github.com/fastapi/fastapi) currently lacks a centralized, validated configuration module. Environment-specific settings (database URLs, API keys, feature flags, CORS origins) are read ad-hoc via `os.getenv()` calls scattered across the codebase. A new configuration module must be added that loads all settings from environment variables at startup, validates them into typed Python objects, and crashes immediately with clear error messages when required values are missing.

## Files to Create/Modify

- `fastapi/config.py` (new) — Central configuration module defining typed settings classes, environment-specific behavior, and a module-level singleton instance
- `tests/test_config.py` (new) — Unit tests covering loading, validation, defaults, type coercion, nesting, and failure modes

## Requirements

### Settings Class (`config.py`)

- Define a `Settings` class using `pydantic_settings.BaseSettings` with the following fields:
  - `db_host: str` (env var `DB_HOST`, default `"localhost"`)
  - `db_port: int` (env var `DB_PORT`, default `5432`)
  - `db_name: str` (env var `DB_NAME`, required, no default)
  - `db_user: str` (env var `DB_USER`, required, no default)
  - `db_password: str` (env var `DB_PASSWORD`, required, no default)
  - `redis_url: str` (env var `REDIS_URL`, default `"redis://localhost:6379"`)
  - `redis_max_connections: int` (env var `REDIS_MAX_CONNECTIONS`, default `10`)
  - `api_secret_key: str` (env var `API_SECRET_KEY`, required, no default)
  - `debug: bool` (env var `DEBUG`, default `False`)
  - `log_level: str` (env var `LOG_LEVEL`, default `"INFO"`)
  - `allowed_hosts: list[str]` (env var `ALLOWED_HOSTS`, default empty list, parsed from comma-separated string)
  - `environment: str` (env var `ENVIRONMENT`, default `"local"`, must be one of `"local"`, `"staging"`, `"production"`)
  - `auth_token_expiry_seconds: int` (env var `AUTH_TOKEN_EXPIRY_SECONDS`, default `3600`)
  - `feature_beta_ui: bool` (env var `FEATURE_BETA_UI`, default `False`)
- Configure `model_config` with `env_file = ".env"` and `env_file_encoding = "utf-8"`

### Nested Configuration Group

- Define a `DatabaseSettings(BaseModel)` submodel with fields `host`, `port`, `name`, `user`, `password`
- Define a `RedisSettings(BaseModel)` submodel with fields `url`, `max_connections`
- Add a second settings class `NestedSettings(BaseSettings)` that uses `env_nested_delimiter = "__"` and contains `database: DatabaseSettings` and `redis: RedisSettings`
- `NestedSettings` must load from env vars like `DATABASE__HOST`, `DATABASE__PORT`, `REDIS__URL`, etc.

### Computed Properties

- `Settings` must expose a computed property `is_production -> bool` returning `True` when `environment == "production"`
- `Settings` must expose a computed property `is_local -> bool` returning `True` when `environment == "local"`
- `Settings` must expose a computed property `database_url -> str` that constructs `postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}`

### Validation Rules

- `environment` must be validated against the set `{"local", "staging", "production"}`; any other value must raise `ValidationError`
- `log_level` must be one of `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`; invalid values must raise `ValidationError`
- `db_port` must be between 1 and 65535; out-of-range values must raise `ValidationError`
- `auth_token_expiry_seconds` must be positive (> 0)
- `allowed_hosts` must be parsed from a comma-separated string (e.g., `"example.com, api.example.com"`) with whitespace stripped; empty string → empty list

### Fail-Fast Behavior

- Instantiate the `Settings` singleton at module import time (`settings = Settings()`)
- If any required field (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `API_SECRET_KEY`) is missing from the environment, the module must call `sys.exit(1)` after printing a structured error listing each missing field
- The error output must include the text `"CONFIGURATION ERROR"` and list each missing field name

### Type Coercion

- `debug=true`, `debug=1`, `debug=yes` in env → `Settings.debug == True`
- `db_port=5432` as string in env → `Settings.db_port == 5432` as int
- `redis_max_connections=50` as string → `Settings.redis_max_connections == 50` as int

### Expected Functionality

- All required env vars set with valid values → `Settings()` instantiates without error; `settings.db_name` returns the value of `DB_NAME`
- `DB_NAME` missing from env → `sys.exit(1)` with output containing `"CONFIGURATION ERROR"` and `"db_name"`
- `ENVIRONMENT=production` → `settings.is_production == True`, `settings.is_local == False`
- `ENVIRONMENT=invalid` → `ValidationError` raised during construction
- `ALLOWED_HOSTS="example.com, api.example.com , localhost"` → `settings.allowed_hosts == ["example.com", "api.example.com", "localhost"]`
- `ALLOWED_HOSTS=""` → `settings.allowed_hosts == []`
- `DB_PORT=99999` → `ValidationError` mentioning port constraint
- `LOG_LEVEL=TRACE` → `ValidationError`
- `DATABASE__HOST=db.prod.internal` with `NestedSettings` → `nested_settings.database.host == "db.prod.internal"`
- `settings.database_url` with `db_user="admin"`, `db_password="secret"`, `db_host="localhost"`, `db_port=5432`, `db_name="myapp"` → `"postgresql://admin:secret@localhost:5432/myapp"`
- `.env` file with `DEBUG=true` and no `DEBUG` env var exported → `settings.debug == True` (file-based loading)

## Acceptance Criteria

- `Settings` class is importable from `fastapi.config` and uses `pydantic_settings.BaseSettings`
- All 14 fields are defined with correct types, env var aliases, and defaults as specified
- `NestedSettings` loads nested configuration via `__` delimiter in env var names
- Missing required fields cause the process to exit with a clear `"CONFIGURATION ERROR"` listing each missing field
- Validation rejects invalid `environment`, `log_level`, `db_port`, and `auth_token_expiry_seconds` values with descriptive errors
- `allowed_hosts` correctly parses comma-separated strings with whitespace trimming
- Computed properties `is_production`, `is_local`, and `database_url` return correct values
- Type coercion handles string-to-bool, string-to-int conversions
- All tests in `tests/test_config.py` pass via `python -m pytest tests/test_config.py -v`
