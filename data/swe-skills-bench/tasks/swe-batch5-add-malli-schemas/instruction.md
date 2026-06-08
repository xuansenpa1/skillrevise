# SWE-Skills-Bench: add-malli-schemas (batch5)

# Task: Add Malli Schemas for Metabase Dashboard and Card Entities

## Background

Metabase (https://github.com/metabase/metabase) is migrating from hand-written validation to Malli schemas for data validation. This task requires defining Malli schemas for the Dashboard and Card (Question) entities in Metabase's Clojure backend, including nested schemas for visualization settings, parameter mappings, and query definitions. The schemas must validate both API input and database round-trip data.

## Files to Create/Modify

- `src/metabase/models/dashboard/schema.clj` (create) — Malli schemas for `Dashboard`, `DashboardCard`, `ParameterMapping`, and `DashboardFilter`.
- `src/metabase/models/card/schema.clj` (create) — Malli schemas for `Card` (Question), `DatasetQuery`, `NativeQuery`, `StructuredQuery`, and `VisualizationSettings`.
- `src/metabase/models/schema_registry.clj` (create) — Schema registry that registers all schemas with `mr/set-default-registry!` and provides lookup by keyword.
- `test/metabase/models/dashboard/schema_test.clj` (create) — Tests validating Dashboard schemas with valid and invalid data.
- `test/metabase/models/card/schema_test.clj` (create) — Tests validating Card schemas.

## Requirements

### Dashboard Schema

```clojure
(def Dashboard
  [:map {:closed true}
   [:id {:optional true} pos-int?]
   [:name [:string {:min 1, :max 255}]]
   [:description {:optional true} [:maybe :string]]
   [:collection_id {:optional true} [:maybe pos-int?]]
   [:parameters {:optional true} [:vector DashboardParameter]]
   [:dashcards {:optional true} [:vector DashboardCard]]
   [:enable_embedding {:optional true} :boolean]
   [:cache_ttl {:optional true} [:maybe pos-int?]]
   [:created_at {:optional true} inst?]
   [:updated_at {:optional true} inst?]])
```

### DashboardCard Schema

```clojure
(def DashboardCard
  [:map
   [:id {:optional true} pos-int?]
   [:card_id [:maybe pos-int?]]  ;; nil for virtual cards (text, heading)
   [:dashboard_id pos-int?]
   [:row int?]
   [:col int?]
   [:size_x pos-int?]
   [:size_y pos-int?]
   [:parameter_mappings {:optional true} [:vector ParameterMapping]]
   [:visualization_settings {:optional true} :map]])
```

### ParameterMapping Schema

```clojure
(def ParameterMapping
  [:map
   [:parameter_id :string]
   [:card_id pos-int?]
   [:target [:tuple [:enum "dimension" "variable"] :any]]])
```

### Card (Question) Schema

```clojure
(def Card
  [:map {:closed true}
   [:id {:optional true} pos-int?]
   [:name [:string {:min 1, :max 255}]]
   [:description {:optional true} [:maybe :string]]
   [:display [:enum "table" "bar" "line" "pie" "scalar" "row" "area" "map" "funnel" "progress"]]
   [:dataset_query DatasetQuery]
   [:visualization_settings VisualizationSettings]
   [:collection_id {:optional true} [:maybe pos-int?]]
   [:result_metadata {:optional true} [:vector ResultColumn]]
   [:type {:optional true} [:enum "question" "model"]]
   [:created_at {:optional true} inst?]])
```

### DatasetQuery Schema (Multi-method)

```clojure
(def DatasetQuery
  [:multi {:dispatch :type}
   ["native" [:map
              [:type [:= "native"]]
              [:native NativeQuery]
              [:database pos-int?]]]
   ["query" [:map
             [:type [:= "query"]]
             [:query StructuredQuery]
             [:database pos-int?]]]])
```

### NativeQuery and StructuredQuery

- **NativeQuery**: `[:map [:query :string] [:template-tags {:optional true} :map]]`.
- **StructuredQuery**: `[:map [:source-table [:or pos-int? :string]] [:filter {:optional true} :any] [:aggregation {:optional true} [:vector :any]] [:breakout {:optional true} [:vector :any]] [:order-by {:optional true} [:vector :any]] [:limit {:optional true} pos-int?]]`.

### VisualizationSettings

- Open map (not `:closed`) — allows arbitrary keys for different visualization types.
- Known keys: `[:graph.x_axis {:optional true} :map]`, `[:graph.y_axis {:optional true} :map]`, `[:table.columns {:optional true} [:vector :map]]`, `[:graph.colors {:optional true} [:vector :string]]`.

### Schema Registry

- `(register-schemas!)` — registers all schemas under qualified keywords (e.g., `:metabase.dashboard/Dashboard`).
- `(validate entity-keyword data)` — validates data against the registered schema; returns `nil` on success, error map on failure.
- `(coerce entity-keyword data)` — validates and coerces data (string dates to instants, string numbers to ints).

### Expected Functionality

- Valid dashboard: `{:name "My Dashboard", :dashcards [{:card_id 1, :dashboard_id 5, :row 0, :col 0, :size_x 4, :size_y 3}]}` → validates successfully.
- Invalid dashboard: `{:name ""}` → fails with `:name` min length error.
- Valid card with native query: `{:name "SQL Query", :display "table", :dataset_query {:type "native", :native {:query "SELECT 1"}, :database 1}, :visualization_settings {}}` → validates.
- Card with invalid display: `{:display "unknown_type"}` → fails with `:display` enum error.
- Multi-method dispatch: `DatasetQuery` with `{:type "native", ...}` validates against `NativeQuery` branch, `{:type "query", ...}` validates against `StructuredQuery` branch.

## Acceptance Criteria

- All Malli schemas are defined with correct types, constraints, and optionality.
- `Dashboard` schema validates nested `DashboardCard` and `ParameterMapping` arrays.
- `Card` schema uses multi-method dispatch for `DatasetQuery` to validate native vs. structured queries.
- `VisualizationSettings` is an open map (accepts arbitrary keys).
- Schema registry registers and looks up schemas by keyword.
- Validation returns descriptive error maps on failure.
- Tests cover: valid data passes, each invalid field produces the correct error, multi-method dispatch, nested validation, and edge cases (empty arrays, nil optional fields).
