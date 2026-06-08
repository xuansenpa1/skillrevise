# SWE-Skills-Bench: implementing-agent-modes (batch7)

# Task: Implement a SQL Query Agent Mode for PostHog Max

## Background

PostHog (https://github.com/PostHog/posthog) includes an AI assistant called Max that operates in different modes, each scoping the available tools and prompts to a specific product area. The task is to implement a new `SQL` agent mode for Max that enables users to write HogQL/SQL queries through conversation, exposing database schema inspection tools and query execution in a backend-first manner.

## Files to Create/Modify

- `ee/hogai/core/agent_modes/presets/sql.py` (create) — `sql_agent` `AgentModeDefinition` and `SqlAgentToolkit` class
- `ee/hogai/tools/sql_tools.py` (create) — `InspectSchemaTool`, `ValidateQueryTool`, and `GetQueryExamplesTool` tool classes
- `frontend/src/queries/schema/schema-assistant-messages.ts` (modify) — Add `"sql"` to the `AgentMode` type union
- `ee/hogai/chat_agent/mode_manager.py` (modify) — Add `sql_agent` to the mode registry under the `hogai_sql_mode` feature flag
- `frontend/src/lib/ai/max-constants.tsx` (modify) — Register the SQL mode in the mode selector with label `"SQL Query"` and icon
- `ee/hogai/core/agent_modes/presets/tests/test_sql.py` (create) — Unit tests for the toolkit and agent mode definition

## Requirements

### `AgentMode` Update (`schema-assistant-messages.ts`)

Add `"sql"` to the `AgentMode` type:
```typescript
export type AgentMode = "trends" | "funnel" | "retention" | "sql"
```

### SQL Tools (`sql_tools.py`)

#### `InspectSchemaTool`

```python
class InspectSchemaTool(BaseTool):
    name: Literal["inspect_schema"] = "inspect_schema"
    description: str = "Inspect the HogQL database schema. Returns table names, column names, and types for the specified table or all tables if no table is specified."
    
    class InputSchema(BaseModel):
        table_name: Optional[str] = Field(
            default=None,
            description="The name of the table to inspect (e.g., 'events', 'persons'). If not provided, returns a summary of all available tables."
        )
    
    def _run(self, table_name: Optional[str] = None) -> str:
        # Query HogQL database metadata for the team
        # Return schema as a structured string: "table.column (type)"
        ...
```

Returns a string describing columns and types of the requested table(s). Uses the team's HogQL metadata API. Does not execute actual queries.

#### `ValidateQueryTool`

```python
class ValidateQueryTool(BaseTool):
    name: Literal["validate_query"] = "validate_query"
    description: str = "Validate a HogQL query for syntax and semantic correctness without executing it. Returns validation errors or confirms the query is valid."
    
    class InputSchema(BaseModel):
        query: str = Field(description="The HogQL SQL query to validate.")
    
    def _run(self, query: str) -> str:
        # Use HogQL parser to validate without executing
        # Return "Query is valid." or error descriptions
        ...
```

Uses the HogQL parser (`hogql.printer.prepare_ast_for_printing` or equivalent) to validate without running the query. Returns either `"Query is valid."` or a structured error message including the error position and description.

#### `GetQueryExamplesTool`

```python
class GetQueryExamplesTool(BaseTool):
    name: Literal["get_query_examples"] = "get_query_examples"
    description: str = "Get example HogQL queries for a given use case. Useful for finding the right syntax for common analytics patterns."
    
    class InputSchema(BaseModel):
        use_case: str = Field(
            description="The analytics use case (e.g., 'user retention', 'funnel analysis', 'event counts by day')."
        )
    
    def _run(self, use_case: str) -> str:
        # Return hardcoded or template-generated example queries for the use case
        ...
```

Returns 2-3 example HogQL queries relevant to the `use_case`. These are hardcoded or template-matched examples, not live queries. Must cover at minimum: event counts, user retention, funnel steps, and property filters.

### `SqlAgentToolkit` and Mode Definition (`sql.py`)

```python
from ee.hogai.core.toolkits import AgentToolkit, TrajectoryExample
from ee.hogai.core.agent_modes.presets.types import AgentModeDefinition
from ee.hogai.tools.sql_tools import InspectSchemaTool, ValidateQueryTool, GetQueryExamplesTool

class SqlAgentToolkit(AgentToolkit):
    tools = [InspectSchemaTool, ValidateQueryTool, GetQueryExamplesTool]
    
    def get_trajectory_examples(self) -> list[TrajectoryExample]:
        # Return JTBD-style trajectory examples
        ...

sql_agent = AgentModeDefinition(
    mode=AgentMode.SQL,
    description="...",
    toolkit_class=SqlAgentToolkit,
    executables=[],
)
```

#### Mode Description (injected into agent context)
```
You are a SQL query assistant for PostHog. Help users write, debug, and optimize HogQL queries.
HogQL is PostHog's SQL dialect based on ClickHouse SQL. Always validate queries before finalizing.
Available tables include: events, persons, sessions, and custom data tables.
Use inspect_schema to discover available columns before writing queries.
Use validate_query to check syntax before presenting a query to the user.
```

#### Trajectory Examples

Include at least two JTBD-style examples in `get_trajectory_examples()`:

1. **"Count events by type for the last 7 days"**:
   - Agent calls `inspect_schema(table_name="events")` to see available columns
   - Agent calls `validate_query(query="SELECT event, count() FROM events WHERE timestamp >= now() - INTERVAL 7 DAY GROUP BY event ORDER BY count() DESC")` 
   - Agent returns the validated query to the user

2. **"Find users who performed action A then action B"**:
   - Agent calls `get_query_examples(use_case="funnel analysis")`
   - Agent adapts the example to the user's specific events
   - Agent calls `validate_query(...)` on the adapted query

### Mode Manager (`mode_manager.py`)

Add the SQL mode to the registry under the `hogai_sql_mode` feature flag:

```python
if has_hogai_sql_mode_feature_flag(self._team, self._user):
    registry[AgentMode.SQL] = sql_agent
```

### Frontend Registration (`max-constants.tsx`)

Add to the mode selector configuration:
```typescript
{
  mode: AgentMode.SQL,
  label: "SQL Query",
  description: "Write and debug HogQL queries",
  icon: "IconCode",
}
```

## Expected Functionality

- The agent switches to SQL mode via `switch_mode(mode="sql")`
- In SQL mode, `inspect_schema()` returns tables and column types for the team's HogQL schema
- `validate_query("SELECT event FROM events LIMIT 10")` returns `"Query is valid."`
- `validate_query("SELECT nonexistent_col FROM events")` returns an error describing the invalid column
- `get_query_examples(use_case="event counts")` returns at least one example query with correct HogQL syntax
- The mode is only available when the `hogai_sql_mode` feature flag is active for the team

## Acceptance Criteria

- `AgentMode.SQL` is added to the TypeScript schema and Python enum
- All three tools (`InspectSchemaTool`, `ValidateQueryTool`, `GetQueryExamplesTool`) implement `_run` with correct behavior
- `ValidateQueryTool` uses HogQL's parser, not query execution, to validate syntax
- `sql_agent` mode definition includes the mode, toolkit, and mode description
- `SqlAgentToolkit` includes at least two JTBD trajectory examples
- The mode is registered under the `hogai_sql_mode` feature flag in `mode_manager.py`
- Frontend mode selector includes the SQL mode with correct label and icon
- All unit tests pass covering tool behavior, trajectory examples, and feature flag gating
