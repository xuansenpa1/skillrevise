# SWE-Skills-Bench: dbt-transformation-patterns (batch2)

# Task: Add Incremental Model Materialization to dbt Core

## Background

dbt (https://github.com/dbt-labs/dbt-core) transforms data in warehouses using SQL models. A new materialization strategy is needed in the core engine that supports efficient incremental loads with merge semantics — inserting new rows and updating existing rows based on a configurable unique key.

## Files to Create

- `core/dbt/materializations/incremental_merge.py` — Incremental merge materialization strategy (full load + merge logic)
- `core/dbt/materializations/schema_evolution.py` — Schema evolution detection and `on_schema_change` handling

## Requirements

### Materialization Strategy

- Implement an incremental materialization that:
  - On first run, performs a full table creation from the model query
  - On subsequent runs, identifies new and changed rows using a configurable `updated_at` column
  - Merges changes into the target table using the unique key for matching

### Unique Key Handling

- Accept a single column or composite key as the merge key
- When a matching row exists, update all non-key columns
- When no match exists, insert the new row

### Schema Evolution

- Detect when the model query adds new columns not present in the target table
- Support an `on_schema_change` configuration with options: `ignore`, `append_new_columns`, `fail`
- When `append_new_columns` is set, alter the target table to add missing columns

### Error Handling

- Raise clear errors when the unique key is not specified for incremental models
- Handle the case where the target table was dropped externally (fall back to full refresh)

## Expected Functionality

- First run creates the target table
- Subsequent runs efficiently merge only changed data
- New columns are handled according to the `on_schema_change` setting
- Missing tables trigger automatic full refresh

## Acceptance Criteria

- The incremental materialization performs a full table build on the first run and a merge-style incremental update on subsequent runs.
- New rows are inserted and existing rows are updated according to the configured unique key.
- Missing unique-key configuration for incremental models produces a clear error instead of silently proceeding.
- Schema changes are handled according to the configured `on_schema_change` behavior.
- If the target table is missing, the materialization falls back to a safe full refresh flow.
