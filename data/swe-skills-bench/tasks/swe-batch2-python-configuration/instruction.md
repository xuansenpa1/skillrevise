# SWE-Skills-Bench: python-configuration (batch2)

# Task: Implement Type-Safe Configuration Management for FastAPI

## Background

FastAPI (https://github.com/fastapi/fastapi) provides high-performance Python web APIs. The documentation source directory contains tutorial examples. A new tutorial module is needed that demonstrates converting hardcoded configuration values into a type-safe, environment-variable-driven settings system using pydantic-settings.

## Files to Create

- `docs_src/settings/tutorial001.py` — Tutorial demonstrating typed configuration management

## Requirements

### Settings Class

- Define a settings class that reads configuration from environment variables with type validation
- Include fields for common application settings: database connection string, API keys, debug mode toggle, allowed CORS origins, and server host/port
- Each field should have a sensible default value and appropriate type annotation
- Sensitive fields (API keys, database URLs) must be read from environment variables and never have hardcoded production values

### Validation

- Invalid environment variable values (e.g., non-integer for port, non-URL for database string) should produce clear validation errors at startup
- Required fields without defaults must cause a startup failure if the environment variable is missing

### Usage Pattern

- Demonstrate how to instantiate the settings and inject them into a FastAPI application
- Show how to override settings via environment variables and `.env` files
- The module must be importable and syntactically valid

## Expected Functionality

- Importing and instantiating the settings class with valid environment variables produces a typed settings object
- Accessing settings fields returns properly typed values (strings, integers, booleans, lists)
- Missing required environment variables raise descriptive validation errors

## Acceptance Criteria

- The tutorial demonstrates a typed settings object populated from environment variables and optional `.env` values.
- Common application settings such as database URL, host, port, debug mode, API keys, and allowed origins are type-validated.
- Invalid environment-variable values cause clear validation failures rather than silent coercion or undefined behavior.
- Required settings without defaults fail fast when not supplied.
- The example shows how the resulting settings object is used from a FastAPI application.
