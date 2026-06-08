# SWE-Skills-Bench: implementing-agent-modes (batch9)

# Task: Implement a New Error Tracking Agent Mode for PostHog

## Background

PostHog (https://github.com/PostHog/posthog) uses an AI agent system with switchable modes that control available tools, prompts, and behaviors. A new "Error Tracking" agent mode is needed that allows the agent to list, search, and analyze error tracking issues, provide stack trace analysis, suggest fixes, and link errors to relevant sessions and feature flags.

## Files to Create/Modify

- `frontend/src/queries/schema/schema-assistant-messages.ts` (modify) — Add `ERROR_TRACKING = "error_tracking"` to the `AgentMode` enum
- `ee/hogai/core/agent_modes/presets/error_tracking.py` (create) — `ErrorTrackingModeDefinition` implementing `AgentModeDefinition` with mode description, toolkit class, and optional executable class
- `ee/hogai/tools/error_tracking/__init__.py` (create) — Package init
- `ee/hogai/tools/error_tracking/list_issues.py` (create) — `ListIssuesTool` that queries the error tracking API to list issues with filters (status, assignee, date range, group)
- `ee/hogai/tools/error_tracking/search_issues.py` (create) — `SearchIssuesTool` that performs full-text search across error messages and stack traces
- `ee/hogai/tools/error_tracking/analyze_issue.py` (create) — `AnalyzeIssueTool` that fetches issue details including stack trace, occurrences, affected users, and generates analysis with root cause hypotheses
- `ee/hogai/tools/error_tracking/link_sessions.py` (create) — `LinkSessionsTool` that finds session recordings associated with specific error occurrences
- `ee/hogai/tools/error_tracking/toolkit.py` (create) — `ErrorTrackingToolkit` extending `AgentToolkit`, registering all 4 tools and providing JTBD trajectory examples
- `ee/hogai/chat_agent/mode_manager.py` (modify) — Register the error tracking mode behind a feature flag using `has_error_tracking_mode_feature_flag`
- `frontend/src/scenes/max/max-constants.tsx` (modify) — Add error tracking mode to the mode selector UI with icon and label
- `tests/test_error_tracking_mode.py` (create) — Unit tests for all tools, toolkit registration, and mode manager integration

## Requirements

### Schema Update (`schema-assistant-messages.ts`)

- Add `ERROR_TRACKING = "error_tracking"` to the existing `AgentMode` enum after the last entry
- Run `pnpm run schema:build` to regenerate the schema (document this in task but don't execute)

### Mode Definition (`error_tracking.py`)

- Class `ErrorTrackingModeDefinition` implementing `AgentModeDefinition`:
  - `mode = AgentMode.ERROR_TRACKING`
  - `description` — A system prompt paragraph explaining the mode's purpose: "You are in Error Tracking mode. You can list, search, and analyze application errors. Use the available tools to help the user understand and resolve errors in their application."
  - `toolkit_class = ErrorTrackingToolkit`
  - `executable_class = None` (uses default execution loop)

### List Issues Tool (`list_issues.py`)

- Class `ListIssuesTool` with:
  - `name = "list_error_tracking_issues"`
  - `description = "List error tracking issues with optional filters"`
  - Parameters: `status` (Optional: "active", "resolved", "ignored"), `assignee` (Optional[str]), `date_from` (Optional[str], ISO format), `date_to` (Optional[str]), `limit` (int, default 25, max 100)
  - Implementation: queries `ErrorTrackingGroup` model filtered by team, applies status/assignee/date filters, orders by `last_seen` descending
  - Returns list of dicts: `{"id", "fingerprint", "title", "status", "occurrences", "users_affected", "first_seen", "last_seen", "assignee"}`

### Search Issues Tool (`search_issues.py`)

- Class `SearchIssuesTool` with:
  - `name = "search_error_tracking_issues"`
  - `description = "Search error tracking issues by error message or stack trace content"`
  - Parameters: `query` (str, required), `limit` (int, default 10)
  - Implementation: performs case-insensitive search on `ErrorTrackingGroup` title and `ErrorTrackingStackFrame` content
  - Returns matching issues with search relevance context (matching snippet)

### Analyze Issue Tool (`analyze_issue.py`)

- Class `AnalyzeIssueTool` with:
  - `name = "analyze_error_tracking_issue"`
  - `description = "Analyze a specific error tracking issue with stack trace and occurrence details"`
  - Parameters: `issue_id` (str, required)
  - Implementation:
    1. Fetch `ErrorTrackingGroup` by ID
    2. Get the latest 5 `ErrorTrackingEvent` occurrences
    3. Parse stack frames from the event data
    4. Count unique affected users
    5. Calculate occurrence velocity (events per hour over last 24h)
  - Returns: `{"id", "title", "stack_trace" (formatted), "total_occurrences", "unique_users", "velocity_per_hour", "first_seen", "last_seen", "latest_occurrence_details", "tags"}`

### Link Sessions Tool (`link_sessions.py`)

- Class `LinkSessionsTool` with:
  - `name = "link_error_sessions"`
  - `description = "Find session recordings that contain occurrences of a specific error"`
  - Parameters: `issue_id` (str, required), `limit` (int, default 5)
  - Implementation: queries session recordings where events include error occurrences matching the issue fingerprint
  - Returns list of: `{"session_id", "recording_url", "person_id", "timestamp", "duration_seconds"}`

### Toolkit (`toolkit.py`)

- Class `ErrorTrackingToolkit(AgentToolkit)`:
  - `tools = [ListIssuesTool, SearchIssuesTool, AnalyzeIssueTool, LinkSessionsTool]`
  - `trajectory_examples` — List of JTBD examples:
    1. "User wants to see recent errors" → Use `list_error_tracking_issues` with status="active" and default limit
    2. "User asks about a specific TypeError" → Use `search_error_tracking_issues` with query, then `analyze_error_tracking_issue` for the top result
    3. "User wants to see what happened in the session where error occurred" → Use `link_error_sessions` to find recordings

### Mode Manager Update (`mode_manager.py`)

- In the `mode_registry` property, add the error tracking mode behind a feature flag:
  ```python
  if has_error_tracking_mode_feature_flag(self._team, self._user):
      registry[AgentMode.ERROR_TRACKING] = error_tracking_agent
  ```
- Import `error_tracking_agent` from `ee.hogai.core.agent_modes.presets.error_tracking`

### Frontend Update (`max-constants.tsx`)

- Add error tracking to the mode entries array: `{mode: AgentMode.ERROR_TRACKING, label: "Error Tracking", icon: <IconBug />}`
- Ensure the mode only appears in the selector when the feature flag is enabled

### Expected Functionality

- Switching to Error Tracking mode makes 4 tools available: list, search, analyze, link sessions
- `list_error_tracking_issues(status="active", limit=10)` returns the 10 most recent active issues sorted by last_seen
- `search_error_tracking_issues(query="TypeError: Cannot read property")` returns matching issues with context snippets
- `analyze_error_tracking_issue(issue_id="abc123")` returns stack trace, occurrence count, velocity, and affected users
- The mode is only available when the feature flag is enabled

## Acceptance Criteria

- `AgentMode.ERROR_TRACKING` enum value exists in the schema
- Mode definition provides a descriptive system prompt and registers the toolkit
- All 4 tools accept correct parameters and return structured results
- Toolkit includes JTBD trajectory examples for common error tracking workflows
- Mode is registered in mode_manager behind a feature flag check
- Frontend mode selector includes Error Tracking with appropriate icon
- `python -m pytest /workspace/tests/test_implementing_agent_modes.py -v --tb=short` passes
