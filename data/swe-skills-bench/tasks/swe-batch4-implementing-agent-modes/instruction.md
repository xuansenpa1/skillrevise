# SWE-Skills-Bench: implementing-agent-modes (batch4)

# Task: Implement a New Agent Mode for Error Tracking in PostHog

## Background

The PostHog repository (https://github.com/PostHog/posthog) is an open-source product analytics platform with an AI agent system. A new agent mode is needed for "Error Tracking" that enables the agent to list, search, filter, and analyze error tracking issues, with dedicated tools, a mode definition, trajectory examples, and proper feature flag gating — following the existing mode architecture in the codebase.

## Files to Create/Modify

- `frontend/src/queries/schema/schema-assistant-messages.ts` (modify) — Add `ERROR_TRACKING` to the `AgentMode` enum
- `ee/hogai/core/agent_modes/presets/error_tracking/__init__.py` (create) — Package init exporting the mode definition
- `ee/hogai/core/agent_modes/presets/error_tracking/toolkit.py` (create) — `ErrorTrackingToolkit` with tools for listing, searching, and analyzing error issues
- `ee/hogai/core/agent_modes/presets/error_tracking/mode_definition.py` (create) — `AgentModeDefinition` binding mode metadata, toolkit, and description
- `ee/hogai/tools/error_tracking_tools.py` (create) — Backend tool implementations for error tracking operations
- `ee/hogai/chat_agent/mode_manager.py` (modify) — Register the new mode behind a feature flag
- `tests/test_implementing_agent_modes.py` (create) — Tests for mode registration, toolkit, tool execution, and feature flag gating

## Requirements

### AgentMode Enum

- Add `ERROR_TRACKING = "error_tracking"` to the `AgentMode` enum in the schema file
- Regenerate the schema after the change (the build step is: `pnpm run schema:build`)

### ErrorTrackingToolkit (toolkit.py)

- Class inheriting from `AgentToolkit`
- Tools:
  - `list_issues(status: str = "active", limit: int = 20) -> list[dict]` — returns recent error tracking issues filtered by status (`"active"`, `"resolved"`, `"ignored"`, `"all"`)
  - `search_issues(query: str) -> list[dict]` — searches issues by title, message, or stack trace content
  - `get_issue_details(issue_id: str) -> dict` — returns full issue details including stack trace, event count, first/last seen, assignee
  - `analyze_issue(issue_id: str) -> dict` — returns an AI-generated root cause analysis summary (delegates to the agent's LLM)
- Each returned issue dict must include: `id`, `title`, `status`, `event_count`, `first_seen`, `last_seen`, `assignee`
- Trajectory examples (in the toolkit's `trajectory_examples` property):
  - "List all active errors" → calls `list_issues(status="active")`
  - "Find issues related to payment" → calls `search_issues(query="payment")`
  - "Analyze error ETI-42" → calls `get_issue_details(issue_id="ETI-42")` then `analyze_issue(issue_id="ETI-42")`

### Mode Definition (mode_definition.py)

- `AgentModeDefinition` with:
  - `mode`: `AgentMode.ERROR_TRACKING`
  - `description`: A system prompt describing the Error Tracking mode capabilities (listing, searching, analyzing issues, suggesting fixes)
  - `toolkit_class`: `ErrorTrackingToolkit`
  - `executables`: empty list (uses default execution loop)

### Tool Implementations (error_tracking_tools.py)

- `list_error_tracking_issues(team_id: int, status: str, limit: int) -> list[dict]` — queries the `ErrorTrackingIssue` model filtered by team and status, ordered by `last_seen` descending
- `search_error_tracking_issues(team_id: int, query: str) -> list[dict]` — performs a case-insensitive search on `title` and `description` fields
- `get_error_tracking_issue_details(team_id: int, issue_id: str) -> dict` — returns the full issue including `stack_trace`, `metadata`, `events_count`
- Each tool must validate that `team_id` is provided and return an empty list / error dict if the issue is not found

### Feature Flag Gating

- In `mode_manager.py`, the `ERROR_TRACKING` mode must only be registered when `has_error_tracking_mode_feature_flag(team, user)` returns True
- When the flag is off, the mode must not appear in the mode registry
- Switching to the error tracking mode when the flag is off must raise an appropriate error

### Expected Functionality

- With the feature flag enabled, the agent can `switch_mode("error_tracking")` and gain access to error tracking tools
- `list_issues(status="active")` returns the 20 most recent active error issues for the team
- `search_issues(query="NullPointerException")` returns issues whose title or description matches
- `get_issue_details(issue_id="ETI-42")` returns full details including stack trace
- Without the feature flag, the error tracking mode is not available in the registry

## Acceptance Criteria

- `AgentMode` enum includes `ERROR_TRACKING`
- ErrorTrackingToolkit exposes the four tools (list, search, details, analyze) with correct signatures
- Mode definition binds the toolkit to the `ERROR_TRACKING` mode with a descriptive system prompt
- Trajectory examples demonstrate the three main user journeys (list, search, analyze)
- Tool implementations query the data model with proper team scoping and input validation
- Feature flag gating ensures the mode is only available when the flag is active
- Tests verify mode registration, tool availability with/without feature flag, and tool execution with mock data
