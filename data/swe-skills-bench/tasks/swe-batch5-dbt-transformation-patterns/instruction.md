# SWE-Skills-Bench: dbt-transformation-patterns (batch5)

# Task: Add a Marts Layer with Customer Lifetime Value Models to dbt-core Tests

## Background

dbt-core (https://github.com/dbt-labs/dbt-core) is the core framework for the dbt data transformation tool. This task requires building a sample dbt project within the test fixtures that demonstrates a marts layer pattern: staging models that clean raw data, intermediate models that join and aggregate, and a final marts model computing Customer Lifetime Value (CLV). The project should include proper schema tests, documentation, and incremental materialization.

## Files to Create/Modify

- `tests/fixtures/jaffle_shop/models/staging/stg_customers.sql` (create) — Staging model selecting and renaming columns from `raw_customers` source table.
- `tests/fixtures/jaffle_shop/models/staging/stg_orders.sql` (create) — Staging model selecting from `raw_orders`, casting `order_date` to date type, and filtering out cancelled orders.
- `tests/fixtures/jaffle_shop/models/staging/stg_payments.sql` (create) — Staging model selecting from `raw_payments`, converting `amount` from cents to dollars (divide by 100).
- `tests/fixtures/jaffle_shop/models/intermediate/int_customer_orders.sql` (create) — Intermediate model joining customers with their orders, computing `order_count`, `first_order_date`, `most_recent_order_date`, and `total_order_amount` per customer.
- `tests/fixtures/jaffle_shop/models/marts/fct_customer_ltv.sql` (create) — Marts model computing Customer Lifetime Value: joins `int_customer_orders` with payment data, computes `avg_order_value`, `customer_lifespan_days` (first to most recent order), `predicted_ltv` (avg_order_value × predicted_annual_orders × expected_lifespan_years). Uses incremental materialization with `unique_key='customer_id'`.
- `tests/fixtures/jaffle_shop/models/schema.yml` (create) — Schema file defining: sources (raw tables), model descriptions, column descriptions, and tests (`not_null`, `unique` on primary keys, `accepted_values` on status columns, `relationships` between models).
- `tests/fixtures/jaffle_shop/dbt_project.yml` (create) — dbt project configuration with `name: jaffle_shop`, model materialization defaults (staging=view, intermediate=ephemeral, marts=incremental).
- `tests/functional/test_jaffle_shop.py` (create) — Functional test that compiles the project, verifies model SQL generation, and checks schema test definitions.

## Requirements

### Staging Models

- `stg_customers`: select `id as customer_id`, `first_name`, `last_name` from `{{ source('jaffle_shop', 'raw_customers') }}`.
- `stg_orders`: select `id as order_id`, `user_id as customer_id`, `order_date::date as order_date`, `status` from source; filter `WHERE status != 'cancelled'`.
- `stg_payments`: select `id as payment_id`, `order_id`, `payment_method`, `amount / 100.0 as amount` from source.

### Intermediate Model

- `int_customer_orders`: `SELECT customer_id, COUNT(*) as order_count, MIN(order_date) as first_order_date, MAX(order_date) as most_recent_order_date, SUM(amount) as total_order_amount FROM stg_orders LEFT JOIN stg_payments USING (order_id) GROUP BY customer_id`.

### Marts Model (fct_customer_ltv)

- Joins `int_customer_orders` with `stg_customers`.
- Computes:
  - `avg_order_value = total_order_amount / NULLIF(order_count, 0)`
  - `customer_lifespan_days = DATEDIFF('day', first_order_date, most_recent_order_date)`
  - `predicted_annual_orders = order_count / NULLIF(DATEDIFF('year', first_order_date, most_recent_order_date), 0)` (default to `order_count` if lifespan < 1 year)
  - `predicted_ltv = avg_order_value * predicted_annual_orders * 3` (3-year expected lifespan)
- Materialized as `incremental` with `unique_key='customer_id'` and `on_schema_change='sync_all_columns'`.
- Incremental filter: `{% if is_incremental() %} WHERE most_recent_order_date > (SELECT MAX(most_recent_order_date) FROM {{ this }}) {% endif %}`.

### Schema Tests

- `stg_customers.customer_id`: `not_null`, `unique`.
- `stg_orders.order_id`: `not_null`, `unique`.
- `stg_orders.status`: `accepted_values: ['placed', 'shipped', 'completed', 'returned']`.
- `int_customer_orders.customer_id`: `relationships` to `stg_customers`.
- `fct_customer_ltv.customer_id`: `not_null`, `unique`.

### Expected Functionality

- `dbt compile` succeeds with no errors.
- Staging models compile to simple SELECT statements with source references.
- `fct_customer_ltv` compiles to a query with incremental logic (the `{% if is_incremental() %}` block renders correctly).
- Schema tests defined in `schema.yml` are recognized by `dbt test --select stg_customers`.

## Acceptance Criteria

- All SQL models compile without Jinja errors.
- `dbt_project.yml` configures materializations correctly per folder (staging=view, intermediate=ephemeral, marts=incremental).
- The schema file defines sources, models, columns, and at least 5 test assertions.
- The `fct_customer_ltv` model includes a correct incremental materialization block.
- The CLV calculation handles division-by-zero with `NULLIF`.
- Functional tests verify compilation output and schema test discovery.
