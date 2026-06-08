# SWE-Skills-Bench: add-malli-schemas (batch10)

# Task: Add Malli Schemas to Metabase Field API Endpoints

## Background

The Metabase `/api/field/` endpoints currently lack comprehensive input validation and response schemas. Malli schemas must be added to the field-related API routes so that route params, query params, request bodies, and responses are validated at the API boundary. The field API is defined in `src/metabase/api/field.clj` and exposes endpoints for retrieving, updating, and querying database field metadata.

## Files to Create/Modify

- `src/metabase/api/field.clj` (modify) — Add Malli schemas to all `defendpoint` declarations: route params, query params, body params, and response schemas
- `test/metabase/api/field_test.clj` (modify) — Add tests that exercise schema validation: invalid route params, missing required body fields, invalid enum values, and correct response shape

## Requirements

### Route Parameter Schemas

- `GET /api/field/:id` — `id` must be validated as `ms/PositiveInt`
- `PUT /api/field/:id` — `id` must be validated as `ms/PositiveInt`
- `GET /api/field/:id/summary` — `id` must be validated as `ms/PositiveInt`
- `GET /api/field/:id/related` — `id` must be validated as `ms/PositiveInt`
- `GET /api/field/:id/remapping` — `id` must be validated as `ms/PositiveInt`
- `POST /api/field/:id/dimension` — `id` must be validated as `ms/PositiveInt`
- `DELETE /api/field/:id/dimension` — `id` must be validated as `ms/PositiveInt`
- `POST /api/field/:id/values` — `id` must be validated as `ms/PositiveInt`
- Route params must use separately destructured maps from query and body params

### Query Parameter Schemas

- `GET /api/field/:id` — optional `include_editable_data_model` query param with schema `[:maybe ms/BooleanValue]` and `{:optional true}`
- `GET /api/field/:id/remapping` — required `remapped_value` query param with schema `ms/NonBlankString`
- Any query param that has a default behavior when absent must use `{:optional true}` and where appropriate `{:default <value>}`

### Request Body Schemas (POST/PUT)

- `PUT /api/field/:id` body must accept a map with:
  - `:display_name` — `{:optional true} [:maybe ms/NonBlankString]`
  - `:description` — `{:optional true} [:maybe ms/NonBlankString]`
  - `:semantic_type` — `{:optional true} [:maybe :keyword]`
  - `:visibility_type` — `{:optional true} [:maybe [:enum "normal" "details-only" "hidden" "retired"]]`
  - `:has_field_values` — `{:optional true} [:maybe [:enum "none" "list" "search"]]`
  - `:settings` — `{:optional true} [:maybe ms/Map]`
  - `:nfc_path` — `{:optional true} [:maybe [:sequential ms/NonBlankString]]`
- `POST /api/field/:id/dimension` body must accept:
  - `:type` — required, `[:enum "external" "internal"]`
  - `:name` — required, `ms/NonBlankString`
  - `:human_readable_field_id` — `{:optional true} [:maybe ms/PositiveInt]`
- `POST /api/field/:id/values` body must accept:
  - `:values` — required, `[:sequential [:sequential :any]]`

### Response Schemas

- Define a named schema `::FieldResponse` using `mr/def`:
  - `:id` — `pos-int?`
  - `:name` — `:string`
  - `:display_name` — `:string`
  - `:description` — `[:maybe :string]`
  - `:base_type` — `:keyword`
  - `:semantic_type` — `[:maybe :keyword]`
  - `:visibility_type` — `:keyword`
  - `:table_id` — `pos-int?`
  - `:has_field_values` — `[:maybe :string]`
  - `:created_at` — `:any` (temporal fields in responses are Java Time objects before serialization)
  - `:updated_at` — `:any`
- `GET /api/field/:id` returns `:- ::FieldResponse`
- `PUT /api/field/:id` returns `:- ::FieldResponse`
- `GET /api/field/:id/summary` returns `:- [:sequential [:map [:distinct-count :any] [:sum :any]]]` (inline response schema)
- `GET /api/field/:id/related` returns `:- [:map [:tables [:sequential :any]] [:fields [:sequential :any]]]`

### Expected Functionality

- `GET /api/field/abc` → HTTP 400 with validation error (non-integer route param)
- `PUT /api/field/1` with body `{"visibility_type": "invalid-value"}` → HTTP 400 with error referencing the enum constraint
- `PUT /api/field/1` with body `{"display_name": "Revenue"}` → HTTP 200 with response matching `::FieldResponse` shape
- `POST /api/field/1/dimension` with body `{}` (missing `:type` and `:name`) → HTTP 400 with validation errors for both missing keys
- `POST /api/field/1/dimension` with body `{"type": "external", "name": "State", "human_readable_field_id": 42}` → HTTP 200
- `POST /api/field/1/dimension` with body `{"type": "unknown", "name": "X"}` → HTTP 400 with error about invalid enum value for `:type`
- `GET /api/field/1/remapping` without `remapped_value` param → HTTP 400 (required query param missing)
- `GET /api/field/1/remapping?remapped_value=California` → HTTP 200
- `DELETE /api/field/abc/dimension` → HTTP 400 (non-integer route param)
- `POST /api/field/1/values` with body `{"values": [[1, "foo"], [2, "bar"]]}` → HTTP 200

## Acceptance Criteria

- All `defendpoint` forms in `src/metabase/api/field.clj` have Malli schemas for route params, and where applicable, query params, body params, and response schemas
- Route params are destructured separately from query params and body params in the `defendpoint` argument vector
- `GET /api/field/:id` with a non-integer id returns HTTP 400, not HTTP 500
- `PUT /api/field/:id` rejects unknown `visibility_type` values at the schema level before reaching business logic
- `POST /api/field/:id/dimension` with a missing required `:type` field returns HTTP 400 with a field-level error
- The `::FieldResponse` named schema is defined with `mr/def` and reused across `GET` and `PUT` response positions
- Temporal response fields (`:created_at`, `:updated_at`) use `:any` in response schemas, not `ms/TemporalString`
- All existing tests in `test/metabase/api/field_test.clj` continue to pass
- New tests validate that invalid inputs are rejected and valid inputs produce correctly-shaped responses
