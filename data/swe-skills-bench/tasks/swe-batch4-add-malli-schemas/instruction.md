# SWE-Skills-Bench: add-malli-schemas (batch4)

# Task: Add Malli Schemas to Metabase Bookmark API Endpoints

## Background

The Metabase application (https://github.com/metabase/metabase) uses Malli schemas for API input validation and response typing. The bookmark API endpoints in the codebase currently lack schema definitions, leaving route parameters, query parameters, request bodies, and response shapes unvalidated. Malli schemas need to be added to these endpoints to enforce type safety, provide meaningful validation errors, and document the API contract.

## Files to Create/Modify

- `src/metabase/api/bookmark.clj` (modify) — Add Malli schemas to all `defendpoint` definitions for route params, query params, request bodies, and response types
- `src/metabase/models/bookmark.clj` (modify) — Add named Malli schema definitions for bookmark entities used in response schemas

## Requirements

### Route Parameter Schemas

- All route parameters that represent entity IDs (`id`, `card-id`, `dashboard-id`, `collection-id`) must use `ms/PositiveInt` from the `metabase.util.malli.schema` namespace
- Route parameter maps must use the `:- [:map ...]` annotation syntax after the destructuring form

### Query Parameter Schemas

- The `GET /api/bookmark` endpoint that lists bookmarks must accept an optional `type` query parameter with schema `[:maybe [:enum "card" "dashboard" "collection"]]` and `{:optional true}`
- Any ordering parameter (e.g., `ordering`) must use `[:maybe ms/NonBlankString]` with `{:optional true}`

### Request Body Schemas

- The `POST /api/bookmark` endpoint must validate a body with:
  - `type` — required, `[:enum "card" "dashboard" "collection"]`
  - `item_id` — required, `ms/PositiveInt`
- The `PUT /api/bookmark/ordering` endpoint must validate a body with:
  - `orderings` — required, `[:sequential [:map [:type [:enum "card" "dashboard" "collection"]] [:item_id ms/PositiveInt]]]`

### Response Schemas

- Define a named schema `::Bookmark` in the models file using `mr/def`:
  ```
  [:map
   [:id pos-int?]
   [:type [:enum "card" "dashboard" "collection"]]
   [:item_id pos-int?]
   [:user_id pos-int?]
   [:created_at :any]
   [:updated_at :any]]
  ```
- `GET /api/bookmark` response schema: `[:sequential ::Bookmark]`
- `POST /api/bookmark` response schema: `::Bookmark`
- `DELETE /api/bookmark/:id` must return the response schema `[:map [:success :boolean]]`
- Temporal fields in response schemas must use `:any` (not `ms/TemporalString`) because response validation occurs before JSON serialization

### Validation Behavior

- A `POST /api/bookmark` with `type: "invalid"` must return a 400-level error with a message indicating the value is not one of the allowed enum values
- A `POST /api/bookmark` with `item_id: -5` must return a 400-level error from the `ms/PositiveInt` schema
- A `POST /api/bookmark` missing the `type` field must return a 400-level error indicating the required field is missing
- A `PUT /api/bookmark/ordering` with an empty `orderings` array must be accepted (empty sequence is valid)
- A `PUT /api/bookmark/ordering` with a malformed entry (wrong type value) in the orderings array must return a validation error

### Expected Functionality

- `GET /api/bookmark` returns a JSON array of bookmark objects matching the `::Bookmark` schema
- `GET /api/bookmark?type=card` returns only card bookmarks
- `POST /api/bookmark` with `{"type": "dashboard", "item_id": 42}` creates a bookmark and returns a `::Bookmark` response
- `POST /api/bookmark` with `{"type": "unknown", "item_id": 42}` returns `400` with a validation error message
- `DELETE /api/bookmark/1` returns `{"success": true}`
- `PUT /api/bookmark/ordering` with `{"orderings": [{"type": "card", "item_id": 1}, {"type": "dashboard", "item_id": 2}]}` succeeds

## Acceptance Criteria

- All `defendpoint` forms in `bookmark.clj` have Malli schema annotations for route params, query params (where applicable), request bodies (for POST/PUT), and response types
- Named schema `::Bookmark` is defined in the models file and reused across endpoints
- Route param IDs use `ms/PositiveInt`; enum fields use `[:enum ...]`; temporal response fields use `:any`
- Invalid request payloads are rejected with descriptive validation errors before reaching handler logic
- Valid requests continue to work identically to their pre-schema behavior
- The application starts and serves the bookmark API endpoints without schema compilation errors
