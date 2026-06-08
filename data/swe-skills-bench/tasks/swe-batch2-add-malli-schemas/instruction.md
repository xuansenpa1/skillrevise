# SWE-Skills-Bench: add-malli-schemas (batch2)

# Task: Add Malli Schema Validation to Metabase Alert API Endpoints

## Background

Metabase (https://github.com/metabase/metabase) is an open-source BI tool built with Clojure. The alert API endpoints currently lack input validation schemas. Malli schemas need to be added to validate request payloads for alert creation and modification endpoints, ensuring data integrity before processing.

## Files to Create/Modify

- `src/metabase/api/alert.clj` (modify) — Wire Malli schema validation into alert API endpoint handlers
- `src/metabase/api/schema/alert.clj` (create) — Malli schema definitions for alert creation and modification payloads

## Requirements

### Schema Definitions

- Define Malli schemas covering the fields required for alert creation (e.g., alert name, trigger conditions, notification channels, schedule configuration)
- Use appropriate Malli types for each field (strings, integers, enums, nested maps, sequences)
- Mark required vs. optional fields correctly

### Validation Integration

- Wire the schemas into the API endpoint handlers so that incoming requests are validated before business logic executes
- Return structured error responses when validation fails, indicating which fields failed and why

### Error Handling

- Invalid payloads should return HTTP 400 with a machine-readable error body
- Missing required fields, wrong types, and out-of-range values should all be caught

## Expected Functionality

- A valid alert creation request passes schema validation and is processed normally
- A request with missing required fields is rejected with a clear validation error
- A request with wrong field types (e.g., string where integer expected) is rejected
- Existing API behavior for valid requests is unchanged

## Acceptance Criteria

- Alert creation and update endpoints validate request bodies against explicit Malli schemas before business logic runs.
- Valid payloads continue through the normal request flow without changing existing successful behavior.
- Missing required fields, wrong field types, and out-of-range values are rejected with structured HTTP 400 validation responses.
- Error responses identify which fields failed validation and why in a machine-readable format.
- Schema integration is applied consistently to both create and modify alert operations.
