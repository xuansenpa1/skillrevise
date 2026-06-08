# SWE-Skills-Bench: add-malli-schemas (batch7)

# Task: Add Malli Schemas to the Metabase Bookmark API Endpoints

## Background

Metabase (https://github.com/metabase/metabase) is migrating its API endpoints to use Malli schemas for request validation and response documentation. The `/api/bookmark` endpoints — which manage user bookmarks for cards, collections, and dashboards — currently lack schema definitions for their route parameters, query parameters, request bodies, and response shapes. The task is to add complete Malli schemas to all bookmark API endpoints.

## Files to Create/Modify

- `src/metabase/api/bookmark.clj` (modify) — Add Malli schemas for route parameters, query parameters, request bodies, and response shapes to all `defendpoint` definitions
- `test/metabase/api/bookmark_test.clj` (modify) — Add tests that verify schema validation rejects invalid inputs and accepts valid inputs for each endpoint

## Requirements

### Schema Definitions

Define the following named schemas using `mr/def` in the `metabase.api.bookmark` namespace:

#### `::BookmarkType`
- `[:enum "card" "dashboard" "collection"]`

#### `::BookmarkResponse`
- A map with:
  - `:id` — `ms/PositiveInt`
  - `:type` — `::BookmarkType`
  - `:item_id` — `ms/PositiveInt`
  - `:name` — `ms/NonBlankString`
  - `:description` — `[:maybe string?]`
  - `:created_at` — `:any` (Java Time object before JSON serialization)

#### `::BookmarkOrderingEntry`
- A map with:
  - `:type` — `::BookmarkType`
  - `:item_id` — `ms/PositiveInt`

### Endpoint Schemas

#### `POST /api/bookmark/:type/:item-id`
- Route params: `{:keys [type item-id]}` with schema `[:map [:type ::BookmarkType] [:item-id ms/PositiveInt]]`
- Response schema: `::BookmarkResponse`

#### `DELETE /api/bookmark/:type/:item-id`
- Route params: `{:keys [type item-id]}` with schema `[:map [:type ::BookmarkType] [:item-id ms/PositiveInt]]`
- Response schema: `nil` (no body on success)

#### `GET /api/bookmark`
- No parameters required
- Response schema: `[:sequential ::BookmarkResponse]`

#### `PUT /api/bookmark/ordering`
- Request body: `{:keys [orderings]}` with schema `[:map [:orderings [:sequential ::BookmarkOrderingEntry]]]`
- Response schema: `nil`

### Validation Behavior

- `POST /api/bookmark/invalid-type/1` must return HTTP 400 with a validation error indicating the type is not one of `"card"`, `"dashboard"`, `"collection"`
- `POST /api/bookmark/card/abc` must return HTTP 400 with a validation error indicating item-id must be a positive integer
- `PUT /api/bookmark/ordering` with an empty orderings list is valid (no error)
- `PUT /api/bookmark/ordering` with `orderings` containing an entry missing the `type` field must return HTTP 400

### Schema Integration

- Use `api.macros/defendpoint` with the `:- ResponseSchema` syntax for response schemas
- Use `ms/PositiveInt` for all integer fields (not `pos-int?`)
- Use `ms/NonBlankString` for name fields (not `:string`)
- Use `:any` for temporal fields in response schemas (since schemas validate before JSON serialization)
- Apply `{:optional true}` and `[:maybe ...]` for nullable fields

## Expected Functionality

- `POST /api/bookmark/card/42` with valid authentication creates a bookmark and returns a `::BookmarkResponse` with `:type "card"` and `:item_id 42`
- `GET /api/bookmark` returns a list of bookmarks, each conforming to `::BookmarkResponse`
- `PUT /api/bookmark/ordering` with `{:orderings [{:type "card" :item_id 1} {:type "dashboard" :item_id 5}]}` updates the ordering
- Requests with invalid parameter types or missing required fields return HTTP 400 with descriptive error messages

## Acceptance Criteria

- All four bookmark endpoints have complete Malli schemas for route parameters, request body, and response shapes
- Named schemas `::BookmarkType`, `::BookmarkResponse`, and `::BookmarkOrderingEntry` are defined with `mr/def`
- Invalid route parameters (wrong type enum, non-integer item-id) produce HTTP 400 responses
- Invalid request bodies (missing required fields, wrong types) produce HTTP 400 responses
- Valid requests continue to function identically to before the schema addition
- All existing bookmark tests pass without modification
