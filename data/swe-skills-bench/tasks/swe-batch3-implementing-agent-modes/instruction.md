# SWE-Skills-Bench: implementing-agent-modes (batch3)

# Task: Implement Agent Mode Definition and Toolkit System for PostHog

## Background

PostHog (https://github.com/PostHog/posthog) is an open-source product analytics platform. The project needs an agent mode system that allows defining different operational modes for AI agents with distinct capabilities, tool configurations, and behavioral constraints. This should be implemented within PostHog's existing Python backend structure under the `posthog/` directory.

## Files to Create/Modify

- `posthog/agent/mode_definition.py` (create) — `AgentModeDefinition` class with mode configuration, capability constraints, and feature flags
- `posthog/agent/toolkit.py` (create) — `AgentToolkit` class managing available tools per mode with permission checks
- `posthog/agent/trajectory.py` (create) — Trajectory tracking for agent actions within a mode session
- `posthog/agent/tests/test_mode_definition.py` (create) — Tests for mode definition and toolkit
- `posthog/agent/tests/test_trajectory.py` (create) — Tests for trajectory tracking

## Requirements

### Agent Mode Definition

- Implement an `AgentModeDefinition` dataclass with fields:
  - `name` (str, required, e.g., `"analysis"`, `"exploration"`, `"automation"`)
  - `description` (str)
  - `allowed_tools` (list of tool name strings that this mode can use)
  - `max_iterations` (int, default 10 — maximum tool calls per session)
  - `timeout_seconds` (int, default 300)
  - `feature_flags` (dict of string to bool — feature flags controlling mode behavior)
  - `constraints` (dict with optional keys: `max_data_rows` (int), `allow_mutations` (bool), `require_confirmation` (bool))
- Validate: `name` must be non-empty and alphanumeric with underscores only; `max_iterations` must be ≥ 1; `timeout_seconds` must be ≥ 1
- Implement `is_tool_allowed(tool_name: str) -> bool` and `check_constraint(key: str) -> Any`
- Provide a `merge(overrides: dict) -> AgentModeDefinition` method that creates a new mode with selectively overridden fields

### Agent Toolkit

- Implement an `AgentToolkit` class that manages a registry of tools available to an agent:
  - `register_tool(name, function, description, required_mode=None)` — register a tool, optionally restricted to a specific mode
  - `get_tools(mode: AgentModeDefinition) -> list[Tool]` — return tools available in the given mode (intersection of mode's `allowed_tools` and registered tools)
  - `execute_tool(name, mode, **kwargs)` — execute a tool after checking mode permissions; raise `ToolNotAllowedError` if not in the mode's allowed list
- If a mode's `constraints["require_confirmation"]` is True, `execute_tool` must raise `ConfirmationRequired` instead of executing, passing the tool name and arguments for user review
- If a mode's `constraints["allow_mutations"]` is False and the tool is tagged with `mutation=True`, raise `MutationNotAllowedError`
- Track tool execution count per session; raise `IterationLimitExceeded` when `max_iterations` is reached

### Trajectory Tracking

- Implement a `Trajectory` class that records the sequence of actions taken by an agent:
  - `add_step(action: str, tool_name: str, inputs: dict, output: Any, duration_ms: float, success: bool)`
  - `get_steps() -> list[TrajectoryStep]` — returns all steps in order
  - `summary() -> TrajectorySummary` with: `total_steps`, `successful_steps`, `failed_steps`, `total_duration_ms`, `tools_used` (set), `success_rate` (float)
- Support serialization: `to_dict() -> dict` and `from_dict(data) -> Trajectory`
- Implement `replay(trajectory: Trajectory, toolkit: AgentToolkit, mode: AgentModeDefinition)` that re-executes the recorded tool calls and compares outputs for determinism testing

### Feature Flag Integration

- Modes support feature flags: `mode.feature_flags["new_analysis_v2"]` returns `True` or `False`
- Implement `is_feature_enabled(flag_name: str, default: bool = False) -> bool` that checks the mode's feature flags, using `default` for undefined flags
- Feature flags can modify tool behavior: if a tool checks `mode.is_feature_enabled("beta_tool_v2")`, it can switch between implementations

### Expected Functionality

- Mode `"analysis"` with `allowed_tools=["query", "aggregate", "export"]` and `max_iterations=20` allows running "query" but blocks "delete"
- Calling `execute_tool("delete", analysis_mode)` raises `ToolNotAllowedError`
- Mode with `require_confirmation=True`: calling `execute_tool("query", mode)` raises `ConfirmationRequired`
- Mode with `allow_mutations=False`: calling a mutation-tagged tool raises `MutationNotAllowedError`
- After 10 tool executions in a mode with `max_iterations=10`, the 11th call raises `IterationLimitExceeded`
- A trajectory with 5 steps (4 successful, 1 failed) has `success_rate = 0.8`
- `trajectory.to_dict()` followed by `Trajectory.from_dict()` produces an equivalent trajectory

## Acceptance Criteria

- `AgentModeDefinition` validates all fields and provides tool permission checking
- `merge()` creates a new mode with selectively overridden fields without mutating the original
- `AgentToolkit` filters tools by mode, enforces iteration limits, and checks mutation/confirmation constraints
- `ToolNotAllowedError`, `ConfirmationRequired`, `MutationNotAllowedError`, and `IterationLimitExceeded` are raised in the correct scenarios
- `Trajectory` records steps and produces accurate summaries with correct success rates
- Serialization round-trip via `to_dict/from_dict` preserves all trajectory data
- Feature flag checking uses the default value for undefined flags
- Tests cover mode validation, tool permission checks, constraint enforcement, iteration limits, trajectory recording, and serialization
