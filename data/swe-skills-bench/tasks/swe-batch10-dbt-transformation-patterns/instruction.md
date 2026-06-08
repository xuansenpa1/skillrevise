# SWE-Skills-Bench: dbt-transformation-patterns (batch10)

# Task: Implement a Three-Layer dbt Transformation Pipeline for E-commerce Order Analytics

## Background

The `dbt-labs/dbt-core` repository contains the core dbt framework and integration tests under `tests/`. A new end-to-end dbt project fixture is needed inside `tests/functional/` that demonstrates the full medallion architecture (staging → intermediate → marts) using a synthetic e-commerce schema, including source freshness checks, generic and singular tests, and an incremental model.

## Files to Create/Modify

- `tests/functional/fixtures/ecommerce_project/dbt_project.yml` (create) — dbt project config with model materialization settings: staging as `view`, intermediate as `ephemeral`, marts as `table`
- `tests/functional/fixtures/ecommerce_project/models/staging/ecommerce/_ecommerce__sources.yml` (create) — Source definition for tables `raw_orders`, `raw_customers`, `raw_products` with freshness thresholds (warn after 6h, error after 24h) and `not_null`/`unique` column tests
- `tests/functional/fixtures/ecommerce_project/models/staging/ecommerce/stg_ecommerce__orders.sql` (create) — Staging model that selects from `{{ source('ecommerce', 'raw_orders') }}`, renames columns to snake_case, casts `order_date` to `date`, and filters out rows where `status = 'test'`
- `tests/functional/fixtures/ecommerce_project/models/staging/ecommerce/stg_ecommerce__customers.sql` (create) — Staging model for customers with column renames and `email` lowercased via SQL
- `tests/functional/fixtures/ecommerce_project/models/intermediate/int_orders_with_customers.sql` (create) — Intermediate model joining `stg_ecommerce__orders` to `stg_ecommerce__customers` on `customer_id`, adding `is_returning_customer` boolean based on whether a customer has prior orders
- `tests/functional/fixtures/ecommerce_project/models/marts/fct_orders.sql` (create) — Incremental mart model aggregating order totals per customer per month; when run incrementally, filters to `order_date >= {{ var('start_date') }}`
- `tests/functional/fixtures/ecommerce_project/models/marts/_core__models.yml` (create) — Schema YAML for `fct_orders` with column descriptions and tests: `not_null` on `customer_id` and `order_month`, `accepted_values` on `order_status` for values `['placed', 'shipped', 'delivered', 'cancelled']`
- `tests/functional/fixtures/ecommerce_project/tests/assert_no_negative_totals.sql` (create) — Singular test that selects rows from `fct_orders` where `order_total < 0`; the test fails if any rows are returned

## Requirements

### Staging Models

- `stg_ecommerce__orders.sql` must reference the source using `{{ source('ecommerce', 'raw_orders') }}` (not a hardcoded table name)
- Column aliases must convert camelCase source column names (`orderId`, `customerId`, `orderDate`, `orderStatus`, `totalAmount`) to snake_case (`order_id`, `customer_id`, `order_date`, `order_status`, `total_amount`)
- Rows where `order_status = 'test'` must be excluded via a `WHERE` clause in the staging model itself

### Intermediate Model

- `int_orders_with_customers.sql` must reference staging models using `{{ ref('stg_ecommerce__orders') }}` and `{{ ref('stg_ecommerce__customers') }}`
- `is_returning_customer` must be computed as `TRUE` if the customer has at least one prior order with `order_date < current order_date`, else `FALSE`
- The join must be a `LEFT JOIN` so orders without a matching customer record are retained

### Incremental Mart Model

- `fct_orders.sql` must use `{{ config(materialized='incremental', unique_key='customer_month_key') }}`
- The `unique_key` column `customer_month_key` must be a surrogate key combining `customer_id` and `order_month` (e.g., via `{{ dbt_utils.generate_surrogate_key(['customer_id', 'order_month']) }}` or equivalent)
- The incremental filter block must use `{% if is_incremental() %}` to restrict to `order_date >= (select max(order_date) from {{ this }})` when running incrementally
- Aggregations must include: `count(order_id) as order_count`, `sum(total_amount) as order_total`, `min(order_date) as first_order_date`, `max(order_date) as last_order_date`

### Tests and Documentation

- `_ecommerce__sources.yml` must define `unique` and `not_null` tests on the primary key column of each source table
- `_core__models.yml` must define `not_null` on `customer_id` and `order_month` and `accepted_values` on `order_status`
- The singular test `assert_no_negative_totals.sql` must be a plain `SELECT` returning violating rows (dbt convention: non-empty result = failure)

### Expected Functionality

- `dbt compile` on the project resolves all `{{ ref() }}` and `{{ source() }}` calls without errors
- `dbt test` on `fct_orders` passes when no negative totals exist and fails when a seed row with `total_amount = -5` is present
- Running `fct_orders` twice with `--full-refresh` on the second run replaces all data; incremental run only merges new rows matching `unique_key`
- A customer with two orders in the same month has one aggregated row in `fct_orders` with `order_count = 2`

## Acceptance Criteria

- All eight files exist with valid SQL and YAML syntax that `dbt parse` accepts without errors
- `stg_ecommerce__orders` excludes `status = 'test'` rows and uses `{{ source() }}` references only
- `fct_orders` uses `{{ config(materialized='incremental') }}` with a `unique_key` and guards incremental logic inside `{% if is_incremental() %}`
- `_core__models.yml` contains `not_null` tests on `customer_id` and `order_month` and an `accepted_values` test on `order_status`
- The singular test `assert_no_negative_totals.sql` returns rows for a dataset containing negative `order_total` values and returns no rows for a clean dataset
