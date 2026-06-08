# SWE-Skills-Bench: implementing-agent-modes (batch8)

# Task: Implement a SQL Query Agent Mode for PostHog's AI Assistant

## Background

PostHog's AI assistant (Max) supports configurable agent modes that extend its capabilities through specialized tools. A new "SQL Query" agent mode is needed that allows Max to explore and query the PostHog database schema, write and execute read-only SQL queries, and format results for the user. The mode must include a toolkit with SQL-specific tools, a mode definition with prompt configuration, and integration into the existing agent mode registry.

## Files to Create/Modify

- `ee/hogai/tools/sql_query_tool.py` (new) — SQL query tool implementation with schema exploration and read-only query execution
- `ee/hogai/core/agent_modes/presets/sql_query_mode.py` (new) — Agent mode definition for SQL Query mode including prompt, tool bindings, and examples
- `ee/hogai/core/agent_modes/registry.py` (modify) — Register the new SQL Query agent mode in the mode registry
- `ee/hogai/tools/sql_query_tool_test.py` (new) — Unit tests for the SQL query tool validating query execution, schema exploration, and safety checks
- `ee/hogai/core/agent_modes/presets/sql_query_mode_test.py` (new) — Unit tests for the mode definition and prompt rendering

## Requirements

### SQL Query Tool

- Implement an `SQLQueryToolkit` class with two tools:
  - `explore_schema` — accepts an optional `table_name` parameter; if provided, returns column names, types, and nullable flags for that table; if omitted, returns a list of all available table names
  - `execute_query` — accepts a `query` string parameter and an optional `limit` integer (default: 100, max: 1000); executes the query and returns results as a list of row dictionaries
- `execute_query` must reject any query containing DDL or DML keywords (`CREATE`, `DROP`, `ALTER`, `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `GRANT`, `REVOKE`); if detected, return an error message "Only SELECT queries are allowed" without executing
- `execute_query` must automatically append `LIMIT {limit}` to queries that do not already contain a `LIMIT` clause
- If the query execution fails (e.g., syntax error), return the database error message prefixed with "Query error: " without raising an exception
- `explore_schema` must return results sorted alphabetically by table/column name

### Agent Mode Definition

- The mode must be registered with id `"sql_query"` and display name `"SQL Query Explorer"`
- The mode's system prompt must instruct the agent to: first explore the schema before writing queries, use column names exactly as returned by `explore_schema`, always use `execute_query` for data retrieval, and explain query results in natural language
- The mode must declare both `explore_schema` and `execute_query` as its available tools
- The mode must include at least 2 trajectory examples:
  - Example 1: User asks "How many events were recorded yesterday?" → agent explores schema → finds events table → writes and executes a count query with date filter → reports result
  - Example 2: User asks "What are the top 5 most active users?" → agent explores schema → finds relevant tables → writes a join/aggregate query → formats results as a ranked list

### Registry Integration

- The SQL Query mode must be added to the agent mode registry so it appears in the list of available modes
- The mode must be selectable by both its id (`"sql_query"`) and display name

### Expected Functionality

- `explore_schema()` with no arguments returns a sorted list of table names from the database
- `explore_schema("events")` returns column definitions for the `events` table including name, type, and nullable flag
- `explore_schema("nonexistent_table")` returns an error message "Table 'nonexistent_table' not found"
- `execute_query("SELECT count(*) FROM events")` returns `[{"count": <number>}]`
- `execute_query("DROP TABLE events")` returns "Only SELECT queries are allowed" without executing
- `execute_query("SELECT * FROM events")` without explicit limit appends `LIMIT 100` and returns at most 100 rows
- `execute_query("SELECT * FROM events LIMIT 50")` respects the existing limit and does not append another
- `execute_query("SELECT * FROM events", limit=2000)` caps the limit at 1000
- `execute_query("SELECT bad syntax")` returns "Query error: ..." with the database error message

## Acceptance Criteria

- The `SQLQueryToolkit` provides `explore_schema` and `execute_query` tools that correctly interact with the database
- DDL/DML queries are rejected before execution with the specified error message
- Queries without a LIMIT clause automatically receive a default limit; the limit is capped at 1000
- Schema exploration returns sorted results and handles missing tables with a clear error
- The agent mode is registered with id `"sql_query"` and includes a system prompt, tool declarations, and trajectory examples
- Unit tests cover query execution, DDL rejection, automatic limit injection, schema exploration, missing table handling, and mode registration
