# SWE-Skills-Bench: add-malli-schemas (batch8)

# Task: Add Malli Schemas to the Metabase Actions API Endpoints

## Background

Metabase's API layer uses Malli schemas for request validation and response typing on API endpoints. The Actions API (`src/metabase/actions/api.clj`) currently has several endpoints that lack proper Malli schema annotations for route parameters, query parameters, request bodies, and response types. These schemas need to be added to enforce runtime validation and provide accurate API documentation.

## Files to Create/Modify

- `src/metabase/actions/api.clj` (modify) — Add Malli schemas to all `defendpoint` declarations for route params, query params, request bodies, and response types
- `src/metabase/actions/models.clj` (modify) — Define named Malli schemas for Action entity types (HTTP Action, Query Action, Implicit Action) and their create/update payloads
- `test/metabase/actions/api_test.clj` (modify) — Add test cases verifying schema validation rejects invalid inputs and accepts valid inputs

## Requirements

### Named Schema Definitions

- Define `::Action` schema as a discriminated map with a `:type` field that must be one of `"http"`, `"query"`, or `"implicit"`
- Define `::HttpActionDetails` schema: `[:map [:url ms/NonBlankString] [:method [:enum "GET" "POST" "PUT" "DELETE" "PATCH"]] [:headers {:optional true} [:maybe [:map-of :string :string]]] [:body_template {:optional true} [:maybe :string]] [:parameters {:optional true} [:maybe [:sequential [:map [:id ms/NonBlankString] [:type [:enum "string" "number" "boolean"]]]]]]]`
- Define `::QueryActionDetails` schema: `[:map [:dataset_query [:map [:database ms/PositiveInt] [:type [:= "native"]] [:native [:map [:query ms/NonBlankString] [:template-tags {:optional true} :any]]]]]]`
- Define `::CreateActionRequest` schema combining the type-specific details with common fields: `[:map [:name ms/NonBlankString] [:model_id ms/PositiveInt] [:type [:enum "http" "query" "implicit"]] [:description {:optional true} [:maybe :string]] [:parameters {:optional true} [:maybe [:sequential :map]]]]`
- Define `::ActionResponse` schema including all common fields plus `:id ms/PositiveInt`, `:created_at ms/TemporalString`, `:updated_at ms/TemporalString`, `:creator_id ms/PositiveInt`

### Endpoint Schema Annotations

- `GET /api/action/` — Response schema: `[:sequential ::ActionResponse]`; optional query params `[:map [:model_id {:optional true} [:maybe ms/PositiveInt]]]`
- `GET /api/action/:id` — Route params: `[:map [:id ms/PositiveInt]]`; Response schema: `::ActionResponse`
- `POST /api/action/` — Request body schema: `::CreateActionRequest`; Response schema: `::ActionResponse`
- `PUT /api/action/:id` — Route params: `[:map [:id ms/PositiveInt]]`; Request body: partial update schema where all fields except `:type` are optional; Response schema: `::ActionResponse`
- `DELETE /api/action/:id` — Route params: `[:map [:id ms/PositiveInt]]`; Response: `nil`

### Validation Behavior

- A `POST /api/action/` with a missing `:name` field must return a 400 error with a Malli validation error message indicating the missing required field
- A `POST /api/action/` with `:type "http"` but an invalid `:method "INVALID"` must return a 400 error referencing the `:method` enum validation
- A `PUT /api/action/:id` with `:id` as a non-numeric string must return a 400 error for the route parameter validation
- A `GET /api/action/` with `?model_id=abc` (non-numeric) must return a 400 error
- Valid requests that pass schema validation must proceed to the handler logic as before

### Expected Functionality

- `POST /api/action/` with `{"name": "Send Webhook", "model_id": 1, "type": "http", "url": "https://example.com/hook", "method": "POST"}` → 200 response matching `::ActionResponse` schema
- `POST /api/action/` with `{"model_id": 1, "type": "http"}` (missing name) → 400 with validation error for `:name`
- `GET /api/action/?model_id=5` → 200 with array of actions filtered by model_id, each matching `::ActionResponse`
- `PUT /api/action/7` with `{"description": "Updated description"}` → 200 with full action response including the updated description
- `DELETE /api/action/7` → 204 with no body

## Acceptance Criteria

- All five Actions API endpoints have Malli schema annotations for route params, query params, request bodies, and response types using the `defendpoint :- schema` syntax
- Named schemas (`::Action`, `::HttpActionDetails`, `::QueryActionDetails`, `::CreateActionRequest`, `::ActionResponse`) are properly defined using `mr/def` and reuse existing `ms/` schema types
- Invalid requests are rejected with 400 errors containing Malli validation error details before reaching handler logic
- Valid requests continue to work as before with no behavioral regression
- Tests verify that schema validation correctly rejects malformed inputs and accepts well-formed inputs for each endpoint
