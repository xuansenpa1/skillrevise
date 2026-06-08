# SWE-Skills-Bench: implementing-agent-modes (batch6)

# Task: Create a Data Explorer Agent Mode for PostHog

## Background

PostHog (https://github.com/PostHog/posthog) has an AI agent system that supports multiple modes for different product areas. A new "Data Explorer" mode is needed that enables users to interactively explore event data, create ad-hoc queries, and drill down into trends through the agent's conversational interface. This mode must integrate with PostHog's existing tool infrastructure and follow the established mode architecture.

## Files to Create/Modify

- `frontend/src/queries/schema/schema-assistant-messages.ts` (modify) — Add `DATA_EXPLORER` to the `AgentMode` enum
- `ee/hogai/core/agent_modes/presets/data_explorer/__init__.py` (create) — Module initialization exporting the mode definition
- `ee/hogai/core/agent_modes/presets/data_explorer/toolkit.py` (create) — `DataExplorerToolkit` class with mode-specific tools and trajectory examples
- `ee/hogai/core/agent_modes/presets/data_explorer/definition.py` (create) — `AgentModeDefinition` for the Data Explorer mode with description, toolkit, and executables
- `ee/hogai/chat_agent/mode_manager.py` (modify) — Register the Data Explorer mode in the mode registry behind a feature flag
- `frontend/src/scenes/max/max-constants.tsx` (modify) — Add Data Explorer mode to the mode selector UI with label and icon
- `ee/hogai/core/agent_modes/presets/data_explorer/tests/test_data_explorer_toolkit.py` (create) — Tests for the toolkit's tool exposure and trajectory examples
- `posthog/models/feature_flag/feature_flag.py` (modify) — Add feature flag constant `HOGAI_DATA_EXPLORER_MODE`

## Requirements

### AgentMode Schema

- Add `DATA_EXPLORER = "data_explorer"` to the `AgentMode` enum in the schema file.
- Regenerate the schema after modification (the command `pnpm run schema:build` should succeed).

### Mode Definition

- The `AgentModeDefinition` must include:
  - `mode`: `AgentMode.DATA_EXPLORER`
  - `description`: A multi-line string explaining that this mode helps users explore event data, build queries, analyze trends, and drill down into segments. The description is injected into the agent's context.
  - `toolkit_class`: `DataExplorerToolkit`
  - `executable_classes`: use the default executables (no custom executor needed).

### Toolkit

- The `DataExplorerToolkit` must expose the following tools from existing PostHog tool libraries:
  - `read_data` — for querying event data
  - `search` — for searching events, properties, and definitions
  - `list_data` — for listing available events and properties
  - `create_insight` — for creating saved insights from queries
  - `trends_query` — for building trend visualizations
- The toolkit must NOT include tools for: experiment creation, feature flag management, session recording, or survey creation (those belong to other modes).
- The toolkit must include at least 3 trajectory examples demonstrating:
  1. **Event exploration**: User asks "What are the top events this week?" → agent uses `list_data` to get events, then `read_data` to query counts, and presents a summary.
  2. **Trend analysis**: User asks "Show me signup trends for the last 30 days" → agent uses `trends_query` to build the query and returns a visualization.
  3. **Drill-down**: User asks "Break down page views by country" → agent uses `read_data` with breakdown parameters and presents results grouped by property.

### Feature Flag

- Define a feature flag constant `HOGAI_DATA_EXPLORER_MODE`.
- The mode must only appear in the mode registry when this feature flag is enabled for the team.
- In `mode_manager.py`, register the mode conditionally:
  ```python
  if has_data_explorer_mode_feature_flag(self._team, self._user):
      registry[AgentMode.DATA_EXPLORER] = data_explorer_agent
  ```

### Frontend Integration

- Add the Data Explorer mode to the mode selector in `max-constants.tsx` with:
  - Label: `"Data Explorer"`
  - Icon: use the existing `IconTrends` or `IconGraph` component
  - Description: `"Explore events, build queries, and analyze trends"`
- The mode must only be visible when the `HOGAI_DATA_EXPLORER_MODE` feature flag is active.

### Expected Functionality

- With the feature flag enabled, the mode selector shows "Data Explorer" as an option.
- Switching to Data Explorer mode → the agent's context includes the mode description, and only the 5 specified tools are available.
- User asks "What events happened today?" → agent uses `list_data` and `read_data` tools to answer.
- User asks "Create a feature flag" → agent recognizes this is outside the mode's scope and suggests switching to the appropriate mode.
- With the feature flag disabled, the Data Explorer mode does not appear in the registry or the UI.

## Acceptance Criteria

- `DATA_EXPLORER` is added to the `AgentMode` enum and the schema regenerates successfully.
- The mode definition includes a descriptive context string, the `DataExplorerToolkit`, and default executables.
- The toolkit exposes exactly the 5 specified tools (`read_data`, `search`, `list_data`, `create_insight`, `trends_query`) and no others.
- At least 3 trajectory examples are included in the toolkit covering event exploration, trend analysis, and drill-down scenarios.
- The mode is registered in the mode manager behind a feature flag and does not appear when the flag is off.
- The frontend mode selector includes the Data Explorer option with correct label, icon, and description.
- Tests verify that the toolkit exposes the correct set of tools and that trajectory examples are present and well-formed.
