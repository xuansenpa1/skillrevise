# SWE-Skills-Bench: dbt-transformation-patterns (batch3)

# Task: Implement a Medallion Architecture dbt Project with Incremental Models

## Background

dbt-core (https://github.com/dbt-labs/dbt-core) is a data transformation tool that enables analytics engineers to transform data in their warehouse using SQL. The project needs a reference dbt project demonstrating the medallion architecture (staging → intermediate → marts), incremental materialization strategies, and proper testing patterns.

## Files to Create/Modify

- `tests/functional/medallion/models/staging/stg_orders.sql` (create) — Staging model for raw orders data
- `tests/functional/medallion/models/staging/stg_customers.sql` (create) — Staging model for raw customer data
- `tests/functional/medallion/models/staging/stg_payments.sql` (create) — Staging model for raw payment data
- `tests/functional/medallion/models/staging/schema.yml` (create) — Schema tests and documentation for staging models
- `tests/functional/medallion/models/intermediate/int_orders_with_payments.sql` (create) — Intermediate model joining orders with payments
- `tests/functional/medallion/models/intermediate/schema.yml` (create) — Schema for intermediate models
- `tests/functional/medallion/models/marts/fct_orders.sql` (create) — Fact table for completed orders
- `tests/functional/medallion/models/marts/dim_customers.sql` (create) — Customer dimension with lifetime value
- `tests/functional/medallion/models/marts/schema.yml` (create) — Schema and tests for mart models
- `tests/functional/medallion/dbt_project.yml` (create) — dbt project configuration

## Requirements

### Staging Layer

- `stg_orders`: select from `{{ source('raw', 'orders') }}`, rename columns to snake_case, cast types (order_id as integer, created_at as timestamp, amount as decimal(10,2)), filter out deleted records (`where is_deleted = false`)
- `stg_customers`: select from `{{ source('raw', 'customers') }}`, rename columns, cast types, deduplicate by `customer_id` keeping the most recent record (using `row_number()` window function)
- `stg_payments`: select from `{{ source('raw', 'payments') }}`, rename columns, cast types, pivot payment status enum values (`1='pending'`, `2='completed'`, `3='failed'`, `4='refunded'`) using a `case` statement
- All staging models materialized as `view` (lightweight, always up-to-date)
- Schema YAML defines sources with `freshness` checks: `warn_after: {count: 12, period: hour}`, `error_after: {count: 24, period: hour}`

### Intermediate Layer

- `int_orders_with_payments`: join `stg_orders` with `stg_payments` on `order_id`, aggregate payment amounts per order, compute `total_paid` (sum of completed payments), `total_refunded` (sum of refunded payments), and `net_amount` (`total_paid - total_refunded`)
- Materialized as `table` (materialized once, referenced by multiple mart models)
- Include a `_loaded_at` timestamp column using `{{ run_started_at }}`

### Marts Layer

- `fct_orders`: incremental model pulling from `int_orders_with_payments`
  - Include columns: `order_id`, `customer_id`, `order_date`, `total_paid`, `total_refunded`, `net_amount`, `payment_status` (derived: `'paid'` if net_amount > 0, `'refunded'` if total_refunded >= total_paid, `'pending'` otherwise)
  - Use `is_incremental()` to filter: `where created_at > (select max(created_at) from {{ this }})` for efficient updates
  - Set `unique_key = 'order_id'` for merge behavior on incremental runs
  - Use `on_schema_change = 'sync_all_columns'`
- `dim_customers`: table model aggregating customer-level metrics
  - Include: `customer_id`, `first_name`, `last_name`, `first_order_date` (min order date), `most_recent_order_date` (max), `number_of_orders`, `lifetime_value` (sum of net_amount across all orders)
  - Only include customers with at least one completed order

### Schema Tests and Documentation

- Staging schema YAML:
  - `stg_orders`: test `unique` and `not_null` on `order_id`, `accepted_values` on `status` column
  - `stg_customers`: test `unique` and `not_null` on `customer_id`
  - `stg_payments`: test `relationships` between `order_id` and `stg_orders.order_id`
- Marts schema YAML:
  - `fct_orders`: test `unique` on `order_id`, `not_null` on critical columns, custom test that `net_amount >= 0` for all paid orders
  - `dim_customers`: test `unique` on `customer_id`, test `lifetime_value >= 0`
- All models have `description` fields in the schema YAML

### dbt Project Configuration

- Project name: `medallion_demo`
- Configure materializations by folder: `staging: view`, `intermediate: table`, `marts: incremental` (with fallback to `table`)
- Configure `vars` for the project: `start_date: '2020-01-01'`

### Expected Functionality

- `dbt run` materializes all models in the correct dependency order: staging → intermediate → marts
- `dbt run --select fct_orders` on an incremental run only processes new rows since the last run
- `dbt test` runs all schema tests and custom data tests
- `dbt source freshness` checks source table freshness
- `dim_customers.lifetime_value` accurately sums all net order amounts per customer
- Changing source data and running `dbt run` incrementally updates `fct_orders` without full refresh

## Acceptance Criteria

- Staging models correctly rename, cast, and filter source data
- Customer deduplication uses `row_number()` to keep only the latest record
- Payment status is pivoted from integer codes to human-readable strings
- Intermediate model correctly aggregates payments per order with total_paid, total_refunded, and net_amount
- `fct_orders` uses incremental materialization with `is_incremental()` filter and `unique_key` for merge behavior
- `dim_customers` includes only customers with completed orders and correctly computes lifetime_value
- Schema tests cover uniqueness, not-null, accepted values, relationships, and custom data quality checks
- `dbt_project.yml` configures per-folder materializations correctly
- Source freshness checks are defined with warn and error thresholds
- All models have descriptions in their schema YAML files
