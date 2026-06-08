# SWE-Skills-Bench: dbt-transformation-patterns (batch9)

# Task: Build a dbt Project for E-Commerce Analytics with Staging, Intermediate, and Marts Layers

## Background

dbt-core (https://github.com/dbt-labs/dbt-core) is the analytics engineering tool. A complete dbt project is needed for an e-commerce analytics platform that transforms raw order, customer, and product data into analytics-ready models following the medallion architecture: staging models for source cleaning, intermediate models for business logic, and mart models for the analytics layer, with schema tests, custom macros, incremental loading, and documentation.

## Files to Create/Modify

- `dbt_project.yml` (create) — Project configuration with model materialization by layer, tags, and vars
- `profiles.yml` (create) — DuckDB profile for local development (`dev`) and Snowflake profile for production (`prod`)
- `models/staging/ecommerce/_sources.yml` (create) — Source definitions for 4 raw tables: `raw_orders`, `raw_customers`, `raw_products`, `raw_order_items`
- `models/staging/ecommerce/_stg_models.yml` (create) — Column documentation and tests for all staging models
- `models/staging/ecommerce/stg_orders.sql` (create) — Staging model: clean and type-cast `raw_orders`
- `models/staging/ecommerce/stg_customers.sql` (create) — Staging model: clean `raw_customers`, normalize email to lowercase
- `models/staging/ecommerce/stg_products.sql` (create) — Staging model: clean `raw_products`, validate price > 0
- `models/staging/ecommerce/stg_order_items.sql` (create) — Staging model: join order items to products, compute line item total
- `models/intermediate/int_orders_enriched.sql` (create) — Intermediate model: join orders + order items, compute order totals, item counts
- `models/intermediate/int_customer_orders.sql` (create) — Intermediate model: aggregate per-customer order history (order count, total spend, first/last order date)
- `models/marts/core/dim_customers.sql` (create) — Customer dimension: includes customer tier (bronze/silver/gold based on spend), days since last order, lifetime value
- `models/marts/core/fct_orders.sql` (create) — Orders fact table: incremental model adding new orders since last run, with surrogate key
- `models/marts/core/_core_models.yml` (create) — Documentation and tests for mart models
- `macros/generate_surrogate_key.sql` (create) — Macro `generate_surrogate_key(field_list)` using dbt_utils or MD5 hash
- `macros/cents_to_dollars.sql` (create) — Macro `cents_to_dollars(column_name)` that divides by 100 and rounds to 2 decimals
- `tests/assert_order_total_positive.sql` (create) — Custom singular test asserting no orders have negative totals
- `tests/assert_customer_tier_valid.sql` (create) — Custom singular test asserting all customer tiers are in ('bronze', 'silver', 'gold')
- `seeds/customer_segments.csv` (create) — Seed table with segment definitions: `tier`, `min_spend`, `max_spend`

## Requirements

### dbt_project.yml

- `name: analytics`, `version: "1.0.0"`, `profile: analytics`
- `model-paths: ["models"]`, `test-paths: ["tests"]`, `seed-paths: ["seeds"]`, `macro-paths: ["macros"]`
- `vars`:
  - `start_date: "2020-01-01"`
  - `orders_incremental_days: 1`
- `models.analytics`:
  - `staging: {materialized: view, tags: ["staging"]}`
  - `intermediate: {materialized: ephemeral, tags: ["intermediate"]}`
  - `marts: {materialized: table, tags: ["marts"], +schema: analytics}`
  - `marts.core.fct_orders: {materialized: incremental, incremental_strategy: delete+insert, unique_key: order_id}`

### Source Definitions (`_sources.yml`)

- Source `ecommerce`, database `raw`, schema `public`
- 4 tables: `raw_orders` (columns: id, customer_id, status, amount_cents, created_at, updated_at), `raw_customers` (id, email, name, created_at), `raw_products` (id, name, category, price_cents, is_active), `raw_order_items` (id, order_id, product_id, quantity, unit_price_cents)
- Source freshness checks: `raw_orders` and `raw_order_items` should be loaded within 24 hours

### Staging Models

**`stg_orders.sql`**:
- Select `id as order_id`, `customer_id`, `status`, `{{ cents_to_dollars('amount_cents') }} as amount`, `created_at as ordered_at`, `updated_at`
- Filter: `where status != 'cancelled'` (staging does not filter cancelled, that's business logic — use `where status is not null`)
- Tests in `_stg_models.yml`: `order_id` (not_null, unique), `customer_id` (not_null), `status` (accepted_values: ['pending', 'processing', 'shipped', 'delivered', 'cancelled'])

**`stg_customers.sql`**:
- Select `id as customer_id`, `lower(email) as email`, `name`, `created_at as customer_created_at`
- Tests: `customer_id` (not_null, unique), `email` (not_null, unique)

**`stg_products.sql`**:
- Select `id as product_id`, `name as product_name`, `category`, `{{ cents_to_dollars('price_cents') }} as price`, `is_active`
- Tests: `product_id` (not_null, unique), `price` (not_null)

**`stg_order_items.sql`**:
- Select `id as order_item_id`, `order_id`, `product_id`, `quantity`, `{{ cents_to_dollars('unit_price_cents') }} as unit_price`, `quantity * {{ cents_to_dollars('unit_price_cents') }} as line_total`
- Tests: `order_item_id` (not_null, unique), `quantity` (not_null), relationships: `order_id → stg_orders.order_id`, `product_id → stg_products.product_id`

### Intermediate Models

**`int_orders_enriched.sql`**:
- CTE joining `stg_orders` with `stg_order_items` aggregated:
  - `sum(line_total) as order_total`
  - `count(order_item_id) as item_count`
  - `array_agg(product_id) as product_ids` (DuckDB syntax)
- Output: all order fields + `order_total`, `item_count`, `product_ids`

**`int_customer_orders.sql`**:
- Aggregation on `int_orders_enriched` grouped by `customer_id`:
  - `count(order_id) as total_orders`
  - `sum(order_total) as lifetime_value`
  - `min(ordered_at) as first_order_date`
  - `max(ordered_at) as last_order_date`
  - `avg(order_total) as avg_order_value`

### Mart Models

**`dim_customers.sql`**:
- Join `stg_customers` with `int_customer_orders` (left join, keep all customers)
- Compute `customer_tier`:
  - `lifetime_value >= 1000` → 'gold'
  - `lifetime_value >= 200` → 'silver'
  - else → 'bronze'
- `days_since_last_order`: `datediff('day', last_order_date, current_date)` — NULL for customers with no orders
- Generate surrogate key: `{{ generate_surrogate_key(['customer_id']) }} as customer_sk`

**`fct_orders.sql`** (incremental):
- Source from `int_orders_enriched`
- Add `{{ generate_surrogate_key(['order_id']) }} as order_sk`
- Incremental filter: `{% if is_incremental() %} where ordered_at > (select max(ordered_at) from {{ this }}) {% endif %}`

### Macros

**`generate_surrogate_key.sql`**:
- `{% macro generate_surrogate_key(field_list) %}` — uses `md5(cast(coalesce(field1, '') || '-' || coalesce(field2, '') || ... as varchar))` for each field in list

**`cents_to_dollars.sql`**:
- `{% macro cents_to_dollars(column_name) %}` — `round({{ column_name }}::float / 100, 2)`

### Custom Tests

**`assert_order_total_positive.sql`**:
- Returns rows where `order_total <= 0` from `fct_orders` — test fails if any rows returned

**`assert_customer_tier_valid.sql`**:
- Returns rows from `dim_customers` where `customer_tier not in ('bronze', 'silver', 'gold')` — test fails if any rows returned

### Expected Functionality

- `dbt run --select staging.*` creates 4 view models in the staging layer
- `dbt run --select marts.*` creates `dim_customers` and `fct_orders` tables
- `dbt test` runs all schema tests and singular tests
- Second run of `fct_orders` in incremental mode only processes orders after the last `ordered_at`
- `cents_to_dollars` macro correctly transforms `2999` to `29.99`

## Acceptance Criteria

- `dbt_project.yml` sets correct materializations per layer: staging=view, intermediate=ephemeral, marts=table, fct_orders=incremental
- Staging models use `{{ cents_to_dollars() }}` macro for all price columns
- `stg_customers.sql` normalizes email to lowercase
- `int_customer_orders.sql` aggregates lifetime_value, order_count, and date range per customer
- `dim_customers.sql` computes customer tier using case-when with correct spend thresholds
- `fct_orders.sql` has correct incremental strategy with `is_incremental()` filter
- Schema tests cover not_null, unique, accepted_values, and relationships
- Singular tests return 0 rows for valid data
- `python -m pytest /workspace/tests/test_dbt_transformation_patterns.py -v --tb=short` passes
