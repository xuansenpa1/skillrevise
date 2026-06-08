# SWE-Skills-Bench: dbt-transformation-patterns (batch1)

# Task: Add dbt Model Transformation Tests for dbt-core

## Background

Add comprehensive transformation test coverage for dbt-core's model compilation and execution, including staging model examples and custom test definitions.

## Files to Create/Modify

- `tests/functional/staging/test_stg_orders.py` - Python test for model compilation
- `tests/functional/staging/fixtures.py` - Test fixtures with model SQL and schema YAML
- `core/dbt/tests/staging/stg_orders.sql` - Example staging model (optional fixture)
- `core/dbt/tests/staging/schema.yml` - Model documentation and tests (optional fixture)

## Requirements

### Staging Model Definition (stg_orders.sql)
- Source reference using `{{ source() }}` macro
- Column transformations (renaming, type casting)
- Appropriate materialization config block (`{{ config(materialized='view') }}`)

### Schema Documentation (schema.yml)
- Model description
- Column-level descriptions
- Built-in tests: `unique`, `not_null` on key columns
- Custom test reference for positive amount validation

### Custom Test
- SQL-based test that returns rows that fail the condition
- `assert_positive_amounts` test on the amount column

### Python Test (test_stg_orders.py)
- Verify model SQL compiles without errors
- Verify schema.yml contains model description
- Verify custom test file exists with valid SQL

## Acceptance Criteria

- `core/dbt/*.py` compiles without syntax errors
- schema.yml contains model descriptions and test definitions
- Custom test SQL file validates positive amounts
