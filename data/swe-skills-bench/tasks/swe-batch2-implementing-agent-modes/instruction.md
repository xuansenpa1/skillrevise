# SWE-Skills-Bench: implementing-agent-modes (batch2)

# Task: Add an AI Agent Mode to PostHog

## Background

PostHog (https://github.com/PostHog/posthog) is an open-source product analytics platform. The API capture endpoint (`posthog/api/capture.py`) handles event ingestion. A new "agent mode" is needed that allows AI agents to submit enriched events through the capture API with additional metadata fields for agent identification, session tracking, and action attribution.

## Files to Create/Modify

- `posthog/api/capture.py` — Extend the capture endpoint to support agent mode events

## Requirements

### Agent Mode Detection

- Add logic to detect when an incoming event request originates from an AI agent
- Detection should check for an `agent_mode` field in the event payload or an `X-Agent-Mode` request header
- When agent mode is detected, apply agent-specific processing

### Agent Metadata

- Accept and validate additional metadata fields for agent events:
  - `agent_id` — unique identifier for the agent instance
  - `agent_session_id` — session identifier grouping related agent actions
  - `agent_action` — the action the agent performed
- Store these fields as event properties

### Backward Compatibility

- Regular (non-agent) events must continue to be processed unchanged
- The capture endpoint's existing behavior, response format, and error handling must be preserved

### Validation

- Reject agent mode events that are missing required agent fields (`agent_id`, `agent_action`) with a descriptive error
- The file must remain syntactically valid Python

## Expected Functionality

- AI agents can submit events with agent metadata via the capture endpoint
- Non-agent events are processed exactly as before
- Missing required agent fields result in a clear error response

## Acceptance Criteria

- Agent-mode events can be submitted through the capture endpoint with the required agent metadata fields.
- Normal events continue to be processed without any agent-specific fields or behavior changes.
- Requests marked as agent mode but missing required metadata are rejected with a clear validation response.
- Agent metadata is stored as event properties in a way that preserves the existing capture API contract.
- Agent mode can be detected from either the request payload or the dedicated request header.
