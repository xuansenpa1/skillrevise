# SWE-Skills-Bench: python-configuration (batch1)

# Task: Implement Type-Safe Configuration with pydantic-settings

## Background
   Transform FastAPI's hardcoded configuration into a type-safe configuration
   system using pydantic-settings BaseSettings.

## Files to Create/Modify
   - docs_src/settings/tutorial001.py
   - docs_src/settings/tutorial001_test.py

## Requirements
   
   Settings Class:
   - Inherit from pydantic_settings.BaseSettings
   - Fields:
     * app_name: str
     * admin_email: EmailStr
     * database_url: PostgresDsn
     * debug: bool (default: False)
     * max_connections: PositiveInt (default: 10)
   
   Singleton Pattern:
   - Use @lru_cache decorator for lazy loading
   - Single instance throughout application
   
   Dependency Injection:
   - Use FastAPI Depends to inject into routes
   - Proper type annotations

### Expected Functionality

   1) Environment variables set via monkeypatch → config loads correctly
   2) Missing required field admin_email → raises ValidationError
   3) Invalid database_url format → error message contains field name
   4) Default values applied when not specified

## Acceptance Criteria

   - Settings class validates all fields properly
   - Error messages are descriptive
