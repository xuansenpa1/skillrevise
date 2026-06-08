# SWE-Skills-Bench: add-malli-schemas (batch9)

# Task: Add Malli Schemas to Metabase Collection API Endpoints

## Background

Metabase (https://github.com/metabase/metabase) is migrating its API endpoints to use Malli schemas for request/response validation. The Collection API at `src/metabase/api/collection.clj` has several endpoints that lack proper input validation and response schemas. This task adds Malli schemas to the Collection API endpoints for route params, query params, request bodies, and response types following established patterns in the codebase.

## Files to Create/Modify

- `src/metabase/api/collection.clj` (modify) — Add Malli schemas to the `GET /`, `GET /:id`, `POST /`, `PUT /:id`, and `GET /:id/items` endpoints using `api.macros/defendpoint` with route, query, body, and response schemas
- `src/metabase/api/collection_schema.clj` (create) — Define reusable named schemas for collection-related types: `::CollectionResponse`, `::CollectionListResponse`, `::CollectionItemsResponse`, `::CreateCollectionRequest`, `::UpdateCollectionRequest`
- `test/metabase/api/collection_schema_test.clj` (create) — Tests verifying schema validation accepts valid inputs and rejects invalid inputs with appropriate error messages

## Requirements

### Named Schemas (`collection_schema.clj`)

- `::CollectionResponse` — A map schema with required keys: `:id` (pos-int?), `:name` (ms/NonBlankString), `:slug` (string?), `:color` ([:maybe string?]), `:description` ([:maybe string?]), `:archived` (boolean?), `:location` (string?), `:personal_owner_id` ([:maybe pos-int?]), `:created_at` (ms/TemporalString)
- `::CollectionListResponse` — A sequential schema `[:sequential ::CollectionResponse]`
- `::CreateCollectionRequest` — A map schema: `:name` (ms/NonBlankString, required), `:color` ([:maybe [:re "^#[0-9A-Fa-f]{6}$"]], optional), `:description` ([:maybe string?], optional), `:parent_id` ([:maybe ms/PositiveInt], optional)
- `::UpdateCollectionRequest` — A map schema: `:name` ([:maybe ms/NonBlankString], optional), `:color` ([:maybe string?], optional), `:description` ([:maybe string?], optional), `:archived` ([:maybe boolean?], optional), `:parent_id` ([:maybe ms/PositiveInt], optional)
- `::CollectionItemsResponse` — A map schema: `:data` ([:sequential [:map [:id pos-int?] [:name string?] [:model [:enum "card" "dashboard" "collection" "timeline"]] [:description [:maybe string?]]]]), `:total` (int?), `:limit` ([:maybe int?]), `:offset` ([:maybe int?])

### Endpoint Schemas

- `GET /` (list collections): Add query params schema with `:archived` (boolean, default false, optional), `:namespace` ([:maybe string?], optional). Add response schema `:- ::CollectionListResponse`
- `GET /:id` (get collection): Add route params schema `[:map [:id ms/PositiveInt]]`. Add response schema `:- ::CollectionResponse`
- `POST /` (create collection): Add body params schema `:- ::CreateCollectionRequest`. Add response schema `:- ::CollectionResponse`
- `PUT /:id` (update collection): Add route params schema `[:map [:id ms/PositiveInt]]`. Add body params schema `:- ::UpdateCollectionRequest`. Add response schema `:- ::CollectionResponse`
- `GET /:id/items` (list items in collection): Add route params schema `[:map [:id ms/PositiveInt]]`. Add query params schema with `:models` ([:maybe [:sequential [:enum "card" "dashboard" "collection" "timeline"]]], optional), `:sort_column` ([:maybe [:enum "name" "last_edited_at" "model"]], optional, default "name"), `:sort_direction` ([:maybe [:enum "asc" "desc"]], optional, default "asc"), `:limit` ([:maybe ms/PositiveInt], optional), `:offset` ([:maybe ms/PositiveInt], optional). Add response schema `:- ::CollectionItemsResponse`

### Validation Behavior

- `POST /` with an empty `name` (blank string) must return a 400 error with a message referencing the `:name` field
- `POST /` with `color: "not-a-color"` must return a 400 error (fails regex validation)
- `GET /:id` with a non-integer ID (e.g., `"abc"`) must return a 400 error
- `PUT /:id` with `parent_id: -1` must return a 400 error (fails PositiveInt validation)
- `GET /:id/items` with `sort_column: "invalid"` must return a 400 error (fails enum validation)

### Expected Functionality

- `GET /api/collection/` returns a JSON array matching `::CollectionListResponse`
- `POST /api/collection/` with `{"name": "My Collection", "color": "#509EE3"}` creates and returns a collection matching `::CollectionResponse`
- `GET /api/collection/1/items?models=card&sort_column=name&sort_direction=desc` returns paginated items matching `::CollectionItemsResponse`
- Invalid requests receive 400 responses with Malli validation error messages indicating which field failed

## Acceptance Criteria

- All five endpoints in `collection.clj` have Malli schemas for route params, query params (where applicable), body params (where applicable), and response types
- Named schemas in `collection_schema.clj` use `mr/def` and reference `ms/` (metabase.lib.schema) types where available
- Schema validation rejects invalid inputs (blank names, malformed colors, negative IDs, invalid enums) with 400 responses
- Valid API calls return responses conforming to the declared response schemas
- Tests in `collection_schema_test.clj` cover all validation cases
- `python -m pytest /workspace/tests/test_add_malli_schemas.py -v --tb=short` passes
