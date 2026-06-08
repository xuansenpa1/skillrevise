# SWE-Skills-Bench: dbt-transformation-patterns (batch4)

# Task: Build a dbt Project with Staging, Intermediate, and Marts Layers for an E-Commerce Data Warehouse

## Background

The dbt-core repository (https://github.com/dbt-labs/dbt-core) is the open-source data build tool for analytics engineering. A new example dbt project is needed that demonstrates a properly structured analytics warehouse for an e-commerce business: source definitions with freshness checks, staging models for Stripe and Shopify data, intermediate transformations, marts with dimension and fact tables, comprehensive data tests, and incremental materialization for large tables.

## Files to Create/Modify

- `examples/ecommerce_analytics/dbt_project.yml` (create) — dbt project configuration with model paths, materializations per layer, and vars
- `examples/ecommerce_analytics/models/staging/stripe/_stripe__sources.yml` (create) — Stripe source definitions with freshness and column tests
- `examples/ecommerce_analytics/models/staging/stripe/stg_stripe__customers.sql` (create) — Staging model for Stripe customers (rename, cast, deduplicate)
- `examples/ecommerce_analytics/models/staging/stripe/stg_stripe__payments.sql` (create) — Staging model for Stripe payments (rename, currency conversion, status mapping)
- `examples/ecommerce_analytics/models/staging/shopify/_shopify__sources.yml` (create) — Shopify source definitions
- `examples/ecommerce_analytics/models/staging/shopify/stg_shopify__orders.sql` (create) — Staging model for Shopify orders
- `examples/ecommerce_analytics/models/intermediate/int_payments_pivoted.sql` (create) — Intermediate model pivoting payments by method (credit_card, bank_transfer, gift_card)
- `examples/ecommerce_analytics/models/marts/core/dim_customers.sql` (create) — Customer dimension with order summary metrics
- `examples/ecommerce_analytics/models/marts/core/fct_orders.sql` (create) — Order fact table joining payments, with incremental materialization
- `examples/ecommerce_analytics/models/marts/core/_core__models.yml` (create) — Model documentation and tests for dim_customers and fct_orders
- `examples/ecommerce_analytics/macros/cents_to_dollars.sql` (create) — Macro to convert cents to dollars with rounding
- `tests/test_dbt_transformation_patterns.py` (create) — Python tests validating SQL syntax, YAML structure, and dbt conventions

## Requirements

### dbt_project.yml

- Project name: `ecommerce_analytics`, version: `1.0.0`, profile: `ecommerce`
- Model paths: `["models"]`, test paths: `["tests"]`, macro paths: `["macros"]`
- Materializations: staging → `view`, intermediate → `ephemeral`, marts → `table`
- Vars: `start_date: "2023-01-01"`, `payment_methods: ["credit_card", "bank_transfer", "gift_card"]`

### Source Definitions

**Stripe sources** (`_stripe__sources.yml`):
- Source `stripe`, database `raw`, schema `stripe`, loader `fivetran`
- `loaded_at_field: _fivetran_synced`, freshness: warn after 12 hours, error after 24 hours
- Table `customers`: columns `id` (unique, not_null), `email`, `created`
- Table `payments`: columns `id` (unique, not_null), `customer_id` (not_null, relationships to `customers`), `amount`, `status`, `payment_method`, `created`

**Shopify sources** (`_shopify__sources.yml`):
- Source `shopify`, database `raw`, schema `shopify`
- Table `orders`: columns `id` (unique, not_null), `customer_id`, `order_date`, `status`, `total_amount`

### Staging Models

**stg_stripe__customers.sql**:
- Select from `{{ source('stripe', 'customers') }}`
- Rename `id → customer_id`, `created → created_at`
- Cast `created_at` to timestamp
- Deduplicate by `customer_id` keeping the latest record

**stg_stripe__payments.sql**:
- Select from `{{ source('stripe', 'payments') }}`
- Rename `id → payment_id`, `created → payment_date`
- Convert `amount` from cents to dollars using the `{{ cents_to_dollars('amount') }}` macro
- Map status to standardized values: `'success' → 'completed'`, `'fail' → 'failed'`, else keep original

**stg_shopify__orders.sql**:
- Select from `{{ source('shopify', 'orders') }}`
- Rename `id → order_id`, `order_date → ordered_at`
- Filter: only non-deleted orders (`status != 'deleted'`)

### Intermediate Model

**int_payments_pivoted.sql**:
- Group by `order_id`
- For each payment method in `{{ var('payment_methods') }}`, sum the amount as a separate column
- Use a Jinja for-loop over the payment methods variable to generate the pivot columns dynamically

### Marts Models

**dim_customers.sql**:
- Join `stg_stripe__customers` with aggregated order data from `stg_shopify__orders`
- Columns: `customer_id`, `email`, `first_order_date`, `last_order_date`, `total_orders`, `total_amount_spent`, `customer_since`

**fct_orders.sql**:
- Incremental materialization with `unique_key='order_id'`
- Join `stg_shopify__orders` with `int_payments_pivoted`
- Columns: `order_id`, `customer_id`, `ordered_at`, `status`, `credit_card_amount`, `bank_transfer_amount`, `gift_card_amount`, `total_amount`
- Incremental filter: `{% if is_incremental() %} where ordered_at > (select max(ordered_at) from {{ this }}) {% endif %}`

### Model Tests (_core__models.yml)

- `dim_customers`: `customer_id` is unique and not_null; `total_orders >= 0`
- `fct_orders`: `order_id` is unique and not_null; `total_amount >= 0`; `customer_id` references `dim_customers`

### Macro

**cents_to_dollars.sql**: `{% macro cents_to_dollars(column_name) %} round({{ column_name }} / 100.0, 2) {% endmacro %}`

### Expected Functionality

- `dbt run --select staging` materializes all staging models as views
- `dbt run --select marts` materializes dim_customers as a table and fct_orders incrementally
- `dbt test` runs all column-level tests (unique, not_null, relationships, accepted_values)
- `dbt source freshness` checks Stripe source freshness against the warn/error thresholds
- The payment pivot dynamically generates columns for each payment method in the project vars

## Acceptance Criteria

- dbt_project.yml correctly configures materialization strategies per model layer
- Source definitions include freshness checks, column descriptions, and referential integrity tests
- Staging models correctly rename, cast, and deduplicate source data using CTE patterns
- Intermediate model dynamically pivots payment methods using Jinja templating
- Marts models join staging data into properly denormalized dimension and fact tables
- fct_orders uses incremental materialization with a correct incremental filter
- The `cents_to_dollars` macro correctly converts integer cents to decimal dollars with 2-decimal rounding
- Tests validate SQL syntax, YAML structure, Jinja variable usage, and dbt conventions
