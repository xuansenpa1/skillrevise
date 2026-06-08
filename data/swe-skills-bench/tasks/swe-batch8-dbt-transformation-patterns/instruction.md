# SWE-Skills-Bench: dbt-transformation-patterns (batch8)

# Task: Implement a dbt Model Generator for E-Commerce Order Analytics

## Background

dbt-core provides the framework for building data transformation pipelines using SQL models organized into layers. A new set of dbt models is needed to transform raw e-commerce order data through the staging, intermediate, and marts layers, producing analytics-ready tables for order metrics, customer lifetime value, and product performance. The models must follow dbt conventions for naming, materialization, testing, and documentation.

## Files to Create/Modify

- `models/staging/ecommerce/_ecommerce__sources.yml` (new) — Source definitions for raw e-commerce tables (raw_orders, raw_order_items, raw_customers, raw_products)
- `models/staging/ecommerce/_ecommerce__models.yml` (new) — Model documentation and tests for staging models
- `models/staging/ecommerce/stg_ecommerce__orders.sql` (new) — Staging model for orders: rename columns, cast types, filter test orders
- `models/staging/ecommerce/stg_ecommerce__order_items.sql` (new) — Staging model for order line items: rename columns, compute line total
- `models/staging/ecommerce/stg_ecommerce__customers.sql` (new) — Staging model for customers: standardize names, parse registration date
- `models/staging/ecommerce/stg_ecommerce__products.sql` (new) — Staging model for products: standardize category names, handle null prices
- `models/intermediate/int_order_items_enriched.sql` (new) — Join order items with products and orders to create an enriched line-item model
- `models/intermediate/int_customer_orders.sql` (new) — Aggregate orders per customer: order count, total spend, first/last order dates
- `models/marts/fct_orders.sql` (new) — Fact table with one row per order: order total, item count, discount amount, net revenue, order status
- `models/marts/dim_customers.sql` (new) — Customer dimension with lifetime value, order frequency, average order value, customer segment
- `models/marts/dim_products.sql` (new) — Product dimension with total units sold, revenue generated, average order quantity
- `models/marts/_marts__models.yml` (new) — Documentation and tests for marts models
- `dbt_project.yml` (modify) — Add model configuration for materialization per layer (staging: view, intermediate: ephemeral, marts: table)

## Requirements

### Source Definitions

- Define source `ecommerce` with tables: `raw_orders` (columns: `id`, `customer_id`, `order_date`, `status`, `discount_code`, `is_test`), `raw_order_items` (columns: `id`, `order_id`, `product_id`, `quantity`, `unit_price`), `raw_customers` (columns: `id`, `name`, `email`, `created_at`), `raw_products` (columns: `id`, `name`, `category`, `price`, `is_active`)
- Add `loaded_at_field` and `freshness` checks on `raw_orders` with `warn_after: {count: 12, period: hour}` and `error_after: {count: 24, period: hour}`

### Staging Models

- `stg_ecommerce__orders`: Rename `id` → `order_id`, cast `order_date` to date type, filter out rows where `is_test = true`, map `status` values ("P" → "pending", "S" → "shipped", "D" → "delivered", "C" → "cancelled", "R" → "refunded")
- `stg_ecommerce__order_items`: Rename `id` → `order_item_id`, compute `line_total` as `quantity * unit_price`
- `stg_ecommerce__customers`: Rename `id` → `customer_id`, trim whitespace from `name`, extract `registration_date` from `created_at` (date only)
- `stg_ecommerce__products`: Rename `id` → `product_id`, lowercase `category`, replace null `price` with 0.00

### Intermediate Models

- `int_order_items_enriched`: Join order items with products (product name, category) and orders (order_date, status); exclude items from cancelled or refunded orders
- `int_customer_orders`: Group by customer, compute `total_orders`, `total_spend` (sum of line totals), `first_order_date`, `last_order_date`, `avg_order_value`

### Marts Models

- `fct_orders`: One row per order; columns: `order_id`, `customer_id`, `order_date`, `status`, `item_count`, `gross_total` (sum of line totals), `discount_amount` (10% if discount_code is not null, else 0), `net_revenue` (gross_total - discount_amount), `is_first_order` (boolean, true if this is the customer's earliest order)
- `dim_customers`: One row per customer; columns: `customer_id`, `customer_name`, `email`, `registration_date`, `lifetime_value` (sum of net_revenue across all orders), `total_orders`, `avg_order_value`, `days_since_last_order`, `segment` ("vip" if lifetime_value > 1000 and total_orders > 10, "regular" if total_orders > 3, "new" otherwise)
- `dim_products`: One row per product; columns: `product_id`, `product_name`, `category`, `unit_price`, `total_units_sold`, `total_revenue`, `avg_order_quantity`, `is_active`

### Testing and Documentation

- Staging models: `unique` and `not_null` tests on all primary key columns; `accepted_values` test on `stg_ecommerce__orders.status` for the five mapped values
- Marts models: `unique` and `not_null` on primary keys; `relationships` test linking `fct_orders.customer_id` to `dim_customers.customer_id`; `accepted_values` on `dim_customers.segment` for ["vip", "regular", "new"]
- All models must have `description` entries in their YAML documentation files

### Expected Functionality

- Raw order with `is_test = true` does not appear in `stg_ecommerce__orders` or any downstream model
- Raw order with `status = "S"` appears as `status = "shipped"` in staging
- An order with 3 line items (quantities 2, 1, 3 at unit prices 10, 20, 5) and a discount code → `gross_total = 55`, `discount_amount = 5.50`, `net_revenue = 49.50`
- A customer with 15 orders and lifetime value $1500 → segment "vip"
- A customer with 2 orders → segment "new"
- A product with null price in raw data → `unit_price = 0.00` in staging and downstream
- `dbt build` runs staging views, skips intermediate (ephemeral), and materializes marts as tables

## Acceptance Criteria

- All staging models correctly rename columns, cast types, filter test records, and map status values
- Intermediate models correctly join and aggregate data, excluding cancelled/refunded orders from enriched items
- `fct_orders` computes item count, gross total, discount amount, net revenue, and first-order flag correctly
- `dim_customers` computes lifetime value, order frequency, and segment classification according to the defined rules
- `dim_products` aggregates sales metrics across all non-cancelled orders
- dbt tests pass: primary key uniqueness, not-null constraints, accepted values, and relationship integrity
- Model materialization follows the layer convention (staging: view, intermediate: ephemeral, marts: table)
- All models have documentation entries with descriptions in their respective YAML files
