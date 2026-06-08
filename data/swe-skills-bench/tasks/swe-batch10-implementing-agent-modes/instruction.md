# SWE-Skills-Bench: implementing-agent-modes (batch10)

# Task: Implement SQL Query Agent Mode with Feature Flag

## Background
PostHog's AI assistant (Max) uses a mode system defined in `ee/hogai/core/agent_modes/presets/` to scope available tools and context to specific product areas. Each mode consists of an `AgentToolkit` subclass and an `AgentModeDefinition`, registered in `ee/hogai/chat_agent/mode_manager.py`. A new SQL mode is needed that restricts the agent to HogQL data queries and excludes product analytics and feature flag authoring tools.

## Files to Create/Modify
- `ee/hogai/core/agent_modes/presets/sql.py` - `SQLAgentToolkit` and `sql_agent` mode definition (new)
- `ee/hogai/core/agent_modes/presets/tests/test_sql.py` - Unit tests for the toolkit and mode registration (new)
- `frontend/src/queries/schema/schema-assistant-messages.ts` - Add `SQL = "sql"` to `AgentMode` enum (modify)
- `posthog/models/feature_flag/flag_definitions.py` - Add `HOGAI_SQL_MODE` constant (modify)
- `ee/hogai/chat_agent/mode_manager.py` - Register SQL mode behind the new feature flag (modify)

## Requirements

### AgentMode Schema
- Add `SQL = "sql"` to the `AgentMode` discriminated union in `schema-assistant-messages.ts`
- Run `pnpm run schema:build` after the change; the generated Python schema must contain `AgentMode.SQL`

### SQLAgentToolkit
- Class `SQLAgentToolkit` must subclass `AssistantToolkit`
- Expose exactly two tools: `execute_hogql_query` (from `ee/hogai/tools/`) and `read_data`
- Must NOT expose `create_feature_flag`, `create_experiment`, `create_insight`, or any product analytics tool
- `trajectory_examples` property must return at least two JTBD-style dicts showing a natural-language query resolved via `execute_hogql_query`

### AgentModeDefinition
- Module-level variable `sql_agent: AgentModeDefinition` with `mode=AgentMode.SQL`
- `description` field must describe the mode as limited to querying PostHog data via HogQL
- `toolkit_class` set to `SQLAgentToolkit`
- No custom `executable_class` — use the default

### Feature Flag & Mode Registration
- Add `HOGAI_SQL_MODE = "hogai-sql-mode"` to `flag_definitions.py` next to existing `HOGAI_*` constants
- Implement `has_hogai_sql_mode_feature_flag(team, user) -> bool` in the same module as `has_error_tracking_mode_feature_flag`
- In `mode_manager.py`, guard `registry[AgentMode.SQL] = sql_agent` behind `has_hogai_sql_mode_feature_flag`
- If flag is disabled, `AgentMode.SQL` must be absent from `mode_registry`

### Unit Tests (`test_sql.py`)
- `TestSQLToolkitTools`: assert toolkit `get_tools()` contains `execute_hogql_query` and `read_data`; assert it does NOT contain `create_feature_flag`
- `TestSQLModeDefinition`: assert `sql_agent.mode == AgentMode.SQL` and `sql_agent.toolkit_class is SQLAgentToolkit`
- `TestSQLModeRegistrationEnabled`: mock `has_hogai_sql_mode_feature_flag` to return `True`; assert `AgentMode.SQL` is in `mode_manager.mode_registry`
- `TestSQLModeRegistrationDisabled`: mock returns `False`; assert `AgentMode.SQL` is NOT in `mode_registry`

### Expected Functionality
- Feature flag off → `AgentMode.SQL` absent from registry
- Feature flag on → `AgentMode.SQL` maps to `sql_agent`
- Toolkit instantiated → `get_tools()` returns exactly `[execute_hogql_query, read_data]`
- `trajectory_examples` returns at least 2 entries

## Acceptance Criteria
- `pytest ee/hogai/core/agent_modes/presets/tests/test_sql.py` passes with all 4 tests green
- `AgentMode.SQL` present in generated Python schema after `pnpm run schema:build`
- `sql_agent` importable as `from ee.hogai.core.agent_modes.presets.sql import sql_agent`
- `SQLAgentToolkit` imports no symbol from `ee.hogai.tools.feature_flags` or `ee.hogai.tools.experiments`
- `HOGAI_SQL_MODE` string value is exactly `"hogai-sql-mode"`
- Existing mode registry tests in `ee/hogai/chat_agent/tests/` continue to pass
