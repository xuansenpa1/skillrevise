# SWE-Skills-Bench: implementing-agent-modes (batch5)

# Task: Implement an Agent Mode System for PostHog Feature Flags

## Background

PostHog (https://github.com/PostHog/posthog) is an open-source product analytics platform. This task requires implementing an "Agent Mode" system that enables different operational behaviors for PostHog's backend services (data ingestion, query execution, export) based on configurable mode profiles. Each mode defines resource limits, feature toggles, and behavioral parameters that can be switched at runtime.

## Files to Create/Modify

- `posthog/agent_modes/models.py` (create) — Django models: `AgentMode` (name, description, is_active, priority), `ModeConfiguration` (mode FK, config_key, config_value, value_type), `ModeSchedule` (mode FK, start_time, end_time, recurrence pattern).
- `posthog/agent_modes/registry.py` (create) — `ModeRegistry` singleton that manages active modes, resolves configuration by priority, and notifies listeners on mode changes.
- `posthog/agent_modes/profiles.py` (create) — Predefined mode profiles: `NormalMode`, `HighThroughputMode`, `DegradedMode`, `MaintenanceMode` — each defining specific configuration overrides.
- `posthog/agent_modes/middleware.py` (create) — Django middleware that reads the current active mode and injects mode-specific settings into the request context.
- `posthog/agent_modes/api.py` (create) — REST API endpoints: `GET /api/agent-modes/` (list modes), `POST /api/agent-modes/{id}/activate` (activate a mode), `GET /api/agent-modes/current` (get current active mode and its resolved config).
- `posthog/agent_modes/tests/test_agent_modes.py` (create) — Tests for mode resolution, priority handling, schedule evaluation, and API endpoints.

## Requirements

### Agent Mode Model

- `AgentMode`: `name` (unique string), `description` (text), `is_active` (boolean), `priority` (integer, higher = takes precedence), `created_at`, `updated_at`.
- `ModeConfiguration`: `mode` (FK), `config_key` (string), `config_value` (string), `value_type` (choice: `int`, `float`, `bool`, `string`, `json`).
- `ModeSchedule`: `mode` (FK), `start_time` (datetime), `end_time` (datetime or null for indefinite), `is_recurring` (boolean), `cron_expression` (string, for recurring schedules).

### Mode Registry

- `ModeRegistry.get_instance()` — singleton access.
- `get_active_mode() -> AgentMode` — returns the highest-priority active mode. If multiple modes are active, the one with highest priority wins.
- `get_config(key: str, default=None)` — resolves a config key from the active mode. Casts the value to the declared `value_type`.
- `activate_mode(mode_id)` / `deactivate_mode(mode_id)` — toggle mode activation.
- `register_listener(callback)` — register a callback that is invoked with `(old_mode, new_mode)` when the active mode changes.
- Thread-safe: uses a lock for mode state changes.

### Predefined Profiles

- **NormalMode**: `query_timeout_seconds=30`, `max_concurrent_queries=50`, `ingestion_batch_size=1000`, `export_enabled=true`.
- **HighThroughputMode**: `query_timeout_seconds=60`, `max_concurrent_queries=100`, `ingestion_batch_size=5000`, `export_enabled=true`, priority 10.
- **DegradedMode**: `query_timeout_seconds=10`, `max_concurrent_queries=10`, `ingestion_batch_size=100`, `export_enabled=false`, priority 20 (overrides high throughput).
- **MaintenanceMode**: `query_timeout_seconds=5`, `max_concurrent_queries=1`, `ingestion_batch_size=0`, `export_enabled=false`, priority 100.

### Middleware

- `AgentModeMiddleware` reads the current active mode on each request.
- Adds `request.agent_mode` with the mode name and `request.mode_config` with the resolved config dict.
- If no mode is active, defaults to `NormalMode` settings.
- Caches the mode resolution for 5 seconds to avoid DB hits on every request.

### API Endpoints

- `GET /api/agent-modes/` → list all modes with their activation status and priority.
- `POST /api/agent-modes/{id}/activate` → activate the specified mode (deactivates any mode with the same or lower priority). Returns the now-active mode.
- `POST /api/agent-modes/{id}/deactivate` → deactivate the specified mode. Falls back to the next highest-priority active mode.
- `GET /api/agent-modes/current` → returns `{ mode: "DegradedMode", config: { query_timeout_seconds: 10, ... }, since: "2024-01-15T10:00:00Z" }`.

### Expected Functionality

- Activating `DegradedMode` (priority 20) overrides `NormalMode` (priority 0): `get_config("max_concurrent_queries")` returns `10` instead of `50`.
- Activating `MaintenanceMode` (priority 100) while `DegradedMode` is active → MaintenanceMode takes precedence.
- Deactivating `MaintenanceMode` → falls back to `DegradedMode`.
- Scheduled mode: `HighThroughputMode` scheduled between 02:00-06:00 UTC → automatically activates/deactivates.

## Acceptance Criteria

- Models are defined with correct fields, types, and relationships.
- `ModeRegistry` resolves the active mode by priority and is thread-safe.
- `get_config` correctly casts values to the declared type (int, float, bool, string, json).
- Mode changes trigger registered listener callbacks.
- Middleware injects mode context into requests with 5-second caching.
- API endpoints correctly activate/deactivate modes and return current configuration.
- Predefined profiles define all 4 modes with distinct configuration values.
- Tests cover priority resolution, activation/deactivation cascade, config type casting, middleware caching, and API response format.
