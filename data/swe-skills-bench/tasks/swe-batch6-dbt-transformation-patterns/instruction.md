# SWE-Skills-Bench: dbt-transformation-patterns (batch6)

# Task: Build a dbt Analytics Pipeline for an E-Commerce Data Warehouse

## Background

An e-commerce company needs a dbt project that transforms raw data from three source systems (Stripe, Shopify, PostgreSQL application database) into a structured analytics warehouse. The project follows the medallion architecture (staging → intermediate → marts) with proper testing, documentation, incremental models for high-volume tables, and snapshot models for tracking slowly-changing dimensions.

## Files to Create/Modify

- `dbt_project.yml` (create) — dbt project configuration with model materializations, vars, and paths
- `models/staging/stripe/_stripe__sources.yml` (create) — Stripe source definitions with freshness checks
- `models/staging/stripe/stg_stripe__payments.sql` (create) — Staging model for Stripe payments
- `models/staging/stripe/stg_stripe__customers.sql` (create) — Staging model for Stripe customers
- `models/staging/shopify/_shopify__sources.yml` (create) — Shopify source definitions
- `models/staging/shopify/stg_shopify__orders.sql` (create) — Staging model for Shopify orders
- `models/staging/shopify/stg_shopify__order_items.sql` (create) — Staging model for Shopify order line items
- `models/staging/app/_app__sources.yml` (create) — Application DB source definitions
- `models/staging/app/stg_app__users.sql` (create) — Staging model for application users
- `models/staging/app/stg_app__products.sql` (create) — Staging model for products
- `models/intermediate/int_orders_enriched.sql` (create) — Join orders with payments and customer data
- `models/intermediate/int_order_items_with_products.sql` (create) — Join order items with product details
- `models/intermediate/int_customer_orders.sql` (create) — Aggregate orders per customer for lifetime metrics
- `models/marts/core/dim_customers.sql` (create) — Customer dimension with lifetime metrics
- `models/marts/core/dim_products.sql` (create) — Product dimension with category hierarchy
- `models/marts/core/fct_orders.sql` (create) — Order fact table (incremental)
- `models/marts/finance/fct_revenue.sql` (create) — Revenue fact table with daily aggregation (incremental)
- `models/marts/core/_core__models.yml` (create) — Model documentation and tests for core marts
- `models/marts/finance/_finance__models.yml` (create) — Model documentation and tests for finance marts
- `snapshots/snap_products.sql` (create) — Snapshot tracking product price changes (SCD Type 2)
- `macros/cents_to_dollars.sql` (create) — Macro converting cents integer to dollars decimal
- `macros/generate_surrogate_key.sql` (create) — Macro generating MD5 surrogate key from columns
- `tests/assert_positive_revenue.sql` (create) — Custom singular test: no negative revenue rows in fct_revenue
- `seeds/country_codes.csv` (create) — Seed file mapping ISO country codes to country names

## Requirements

### Project Config (`dbt_project.yml`)

```yaml
name: "ecommerce_analytics"
version: "1.0.0"
profile: "ecommerce"

model-paths: ["models"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

vars:
  start_date: "2023-01-01"
  stripe_database: "raw"
  shopify_database: "raw"
  app_database: "raw"

models:
  ecommerce_analytics:
    staging:
      +materialized: view
      +schema: staging
    intermediate:
      +materialized: ephemeral
    marts:
      core:
        +materialized: table
        +schema: analytics
      finance:
        +materialized: table
        +schema: finance
```

### Source Definitions

**Stripe (`_stripe__sources.yml`):**
- Database: `{{ var('stripe_database') }}`, schema: `stripe`.
- Loader: `fivetran`, loaded_at_field: `_fivetran_synced`.
- Freshness: warn after 12 hours, error after 24 hours.
- Tables:
  - `payments`: columns `id` (unique, not_null), `customer_id` (not_null, relationship to `customers.id`), `amount` (not_null), `status`, `created_at`.
  - `customers`: columns `id` (unique, not_null), `email`, `name`, `created_at`.

**Shopify (`_shopify__sources.yml`):**
- Database: `{{ var('shopify_database') }}`, schema: `shopify`.
- Tables:
  - `orders`: columns `id`, `customer_email`, `total_price`, `currency`, `financial_status`, `created_at`, `updated_at`.
  - `order_line_items`: columns `id`, `order_id` (relationship to `orders.id`), `product_id`, `quantity`, `price`.

**App DB (`_app__sources.yml`):**
- Tables:
  - `users`: columns `id`, `email`, `first_name`, `last_name`, `country_code`, `created_at`, `is_active`.
  - `products`: columns `id`, `name`, `category`, `subcategory`, `price_cents`, `is_active`, `created_at`, `updated_at`.

### Staging Models

Each staging model:
- CTE-based: `with source as (select * from {{ source(...) }})`, then `renamed as (...)` CTE for column renaming and light transformations.
- Rename columns to snake_case consistent naming.
- Cast types: timestamps to `timestamp`, IDs to `varchar`, amounts to appropriate numeric types.
- Filter out soft-deleted records where applicable (`_fivetran_deleted = false`).

`stg_stripe__payments.sql`:
- Select: `payment_id` (renamed from `id`), `customer_id`, `amount_cents` (from `amount`), `{{ cents_to_dollars('amount') }} as amount_dollars`, `status`, `created_at`.
- Filter: `status != 'failed'`.

`stg_shopify__orders.sql`:
- Select: `order_id`, `customer_email`, `total_price`, `currency`, `financial_status`, `created_at`, `updated_at`.
- Filter: `financial_status != 'voided'`.

`stg_app__users.sql`:
- Select: `user_id`, `email`, `first_name`, `last_name`, `country_code`, `created_at`, `is_active`.
- Join with `{{ ref('country_codes') }}` seed to add `country_name`.

### Intermediate Models

`int_orders_enriched.sql`:
- Join `stg_shopify__orders` with `stg_stripe__payments` on `customer_email` matching logic.
- Join with `stg_stripe__customers` for customer name.
- Output: `order_id`, `customer_email`, `customer_name`, `total_price`, `payment_amount_dollars`, `payment_status`, `order_created_at`, `payment_created_at`.

`int_order_items_with_products.sql`:
- Join `stg_shopify__order_items` with `stg_app__products`.
- Calculate `line_total` as `quantity * price`.
- Output: `order_item_id`, `order_id`, `product_id`, `product_name`, `category`, `subcategory`, `quantity`, `unit_price`, `line_total`.

`int_customer_orders.sql`:
- Aggregate from `int_orders_enriched`:
  - `customer_email`, `first_order_date` (min), `most_recent_order_date` (max), `order_count`, `total_lifetime_revenue` (sum of total_price).

### Marts

`dim_customers.sql`:
- Join `stg_app__users` with `int_customer_orders` on email.
- Surrogate key: `{{ generate_surrogate_key(['user_id', 'email']) }}`.
- Columns: `customer_key` (surrogate), `user_id`, `email`, `full_name` (concat first + last), `country_name`, `first_order_date`, `most_recent_order_date`, `order_count` (default 0), `total_lifetime_revenue` (default 0), `customer_segment` (CASE: >10 orders → 'VIP', >3 → 'Regular', >0 → 'New', else 'Prospect'), `is_active`, `created_at`.

`fct_orders.sql` (incremental):
- `{{ config(materialized='incremental', unique_key='order_id', incremental_strategy='merge', on_schema_change='append_new_columns') }}`.
- Select from `int_orders_enriched`.
- Incremental filter: `{% if is_incremental() %} where order_created_at > (select max(order_created_at) from {{ this }}) {% endif %}`.

`fct_revenue.sql` (incremental):
- Daily aggregation: `date_trunc('day', order_created_at) as revenue_date`, `sum(total_price) as daily_revenue`, `count(distinct order_id) as order_count`, `count(distinct customer_email) as unique_customers`.
- Group by `revenue_date`.
- Incremental on `revenue_date`.

### Model Tests (`_core__models.yml`)

For `dim_customers`:
- `customer_key`: unique, not_null.
- `email`: unique, not_null.
- `customer_segment`: accepted_values `['VIP', 'Regular', 'New', 'Prospect']`.
- `order_count`: `dbt_utils.expression_is_true` expression `order_count >= 0`.

For `fct_orders`:
- `order_id`: unique, not_null.
- `total_price`: not_null, `dbt_utils.expression_is_true` expression `total_price > 0`.

### Snapshot (`snapshots/snap_products.sql`)

```sql
{% snapshot snap_products %}
{{ config(
    target_schema='snapshots',
    unique_key='product_id',
    strategy='timestamp',
    updated_at='updated_at',
    invalidate_hard_deletes=True
) }}
select * from {{ source('app', 'products') }}
{% endsnapshot %}
```

### Macros

`cents_to_dollars.sql`:
```sql
{% macro cents_to_dollars(column_name) %}
    ({{ column_name }}::numeric / 100)::numeric(16,2)
{% endmacro %}
```

`generate_surrogate_key.sql`:
```sql
{% macro generate_surrogate_key(columns) %}
    md5({% for col in columns %}cast(coalesce(cast({{ col }} as varchar), '') as varchar){% if not loop.last %} || '|' || {% endif %}{% endfor %})
{% endmacro %}
```

### Expected Functionality

- `dbt run` builds all models: staging views, ephemeral intermediates, core/finance tables.
- `dbt test` validates all column tests (unique, not_null, accepted_values, relationships, positive values).
- `dbt snapshot` captures product price changes as SCD Type 2 records.
- Incremental `fct_orders` only processes new orders on subsequent runs.
- `dbt docs generate && dbt docs serve` shows full lineage from sources through staging → intermediate → marts.

## Acceptance Criteria

- Project config sets staging as views, intermediate as ephemeral, marts as tables in separate schemas.
- Source definitions include freshness checks (12h warn, 24h error) with `loaded_at_field`.
- Staging models use CTE pattern (`source` → `renamed`), cast types, filter deleted/invalid records.
- `cents_to_dollars` macro converts integer cents to numeric(16,2) dollars.
- Intermediate models join across source systems (Stripe + Shopify + App DB) on customer email.
- `dim_customers` includes surrogate key, lifetime metrics, and CASE-based customer segmentation.
- `fct_orders` and `fct_revenue` use incremental materialization with `merge` strategy and timestamp-based filtering.
- `snap_products` implements SCD Type 2 via timestamp strategy tracking `updated_at`.
- Model YAML files include column-level tests: unique, not_null, accepted_values, expression_is_true, relationships.
- Custom singular test validates no negative revenue in `fct_revenue`.
- Seed file `country_codes.csv` provides country code to name mapping used in staging.
