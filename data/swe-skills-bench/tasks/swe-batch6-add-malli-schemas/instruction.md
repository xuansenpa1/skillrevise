# SWE-Skills-Bench: add-malli-schemas (batch6)

# Task: Add Malli Validation Schemas to Three Metabase API Endpoints

## Background

Metabase (https://github.com/metabase/metabase) uses Malli schemas for API request and response validation. Several core API endpoints currently lack schema annotations for their route parameters, query parameters, request bodies, and response types. Three high-traffic endpoints need Malli schemas added: the Card (Question) creation endpoint, the Dashboard update endpoint, and the Dataset query endpoint.

## Files to Create/Modify

- `src/metabase/api/card.clj` (modify) — Add Malli schemas to the `POST /api/card` endpoint for route params, body params, and response
- `src/metabase/api/dashboard.clj` (modify) — Add Malli schemas to the `PUT /api/dashboard/:id` endpoint for route params, body params, and response
- `src/metabase/api/dataset.clj` (modify) — Add Malli schemas to the `POST /api/dataset` endpoint for body params and response

## Requirements

### POST /api/card — Create a Saved Question

- Request body schema must validate:
  - `name` — required, non-blank string (`ms/NonBlankString`)
  - `dataset_query` — required, map with:
    - `type` — required, enum of `"native"` or `"structured"`
    - `database` — required, positive integer (`ms/PositiveInt`)
    - `native` — optional, map with `:query` (non-blank string) and optional `:template-tags` (map)
    - `query` — optional, map (for structured queries)
  - `display` — required, non-blank string (e.g., `"table"`, `"bar"`, `"line"`, `"scalar"`)
  - `description` — optional, nullable string
  - `collection_id` — optional, nullable positive integer
  - `visualization_settings` — optional, map
  - `result_metadata` — optional, nullable sequence of maps

- Response schema (`:- ::CardResponse`) must define a named schema including:
  - `id` — positive integer
  - `name` — string
  - `display` — string
  - `dataset_query` — map
  - `creator_id` — positive integer
  - `created_at` — temporal string (`ms/TemporalString`)
  - `updated_at` — temporal string
  - `collection_id` — nullable positive integer

- Validation behavior:
  - Missing `name` → 400 error with message indicating `name` is required
  - `dataset_query.type` set to `"invalid"` → 400 error indicating invalid enum value
  - `dataset_query.database` set to `"abc"` → 400 error indicating expected positive integer

### PUT /api/dashboard/:id — Update a Dashboard

- Route params schema: `[:map [:id ms/PositiveInt]]`

- Request body schema must validate:
  - `name` — optional, non-blank string
  - `description` — optional, nullable string
  - `parameters` — optional, sequence of parameter maps, each with:
    - `id` — required, non-blank string
    - `name` — required, non-blank string
    - `type` — required, non-blank string (e.g., `"category"`, `"date/single"`, `"id"`)
    - `slug` — required, non-blank string
    - `default` — optional, any value
  - `enable_embedding` — optional, boolean
  - `embedding_params` — optional, nullable map
  - `collection_id` — optional, nullable positive integer
  - `archived` — optional, boolean with default `false`
  - `cache_ttl` — optional, nullable positive integer

- Response schema must include: `id`, `name`, `description`, `parameters`, `created_at`, `updated_at`.

- Validation behavior:
  - Non-integer `:id` in route → 400 error
  - `parameters` containing an entry missing `id` → 400 error
  - `cache_ttl` set to `-1` → 400 error indicating expected positive integer

### POST /api/dataset — Execute a Query

- Request body schema must validate:
  - `database` — required, positive integer
  - `type` — required, enum `"native"` or `"structured"`
  - `native` — conditional, required when `type` is `"native"`, map with:
    - `query` — required, non-blank string
    - `template-tags` — optional, map
  - `query` — conditional, used when `type` is `"structured"`, map
  - `constraints` — optional, map with:
    - `max-results` — optional, positive integer
    - `max-results-bare-rows` — optional, positive integer
  - `parameters` — optional, sequence of maps

- Response schema must include:
  - `data` — map with `rows` (sequence) and `cols` (sequence of maps)
  - `status` — enum `"completed"` or `"failed"`
  - `row_count` — non-negative integer
  - `running_time` — non-negative integer (milliseconds)

- Validation behavior:
  - Missing `database` → 400 error
  - `type` set to `"graphql"` → 400 error indicating invalid enum
  - `constraints.max-results` set to `0` → 400 error indicating expected positive integer

### Expected Functionality

- `POST /api/card` with valid body → 200 response matching `::CardResponse` schema.
- `POST /api/card` with missing `name` field → 400 response with validation error specifying the missing field.
- `PUT /api/dashboard/42` with valid body → 200 response matching dashboard response schema.
- `PUT /api/dashboard/abc` → 400 error (route param validation fails).
- `POST /api/dataset` with `{"database": 1, "type": "native", "native": {"query": "SELECT 1"}}` → response matching dataset response schema.
- `POST /api/dataset` with `{"type": "native"}` (missing `database`) → 400 error.

## Acceptance Criteria

- All three endpoints have Malli schemas for their request parameters (route, query, body) and response types using `defendpoint :- ::Schema` syntax.
- Named schemas (via `mr/def`) are used for complex, reusable types like `::DatasetQuery`, `::CardResponse`, and `::DashboardParameter`.
- Existing Metabase schema types from the `ms` namespace (e.g., `ms/PositiveInt`, `ms/NonBlankString`, `ms/TemporalString`, `ms/BooleanValue`) are used where applicable.
- Invalid request bodies receive 400 responses with descriptive error messages indicating which field failed validation and why.
- Valid requests continue to function identically to before the schema additions.
- Optional fields use `{:optional true}` and nullable fields use `[:maybe ...]` appropriately.
