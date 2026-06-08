# SWE-Skills-Bench: dbt-transformation-patterns (batch7)

# Task: Add a Custom Generic Test Macro for dbt-core

## Background

dbt-core (https://github.com/dbt-labs/dbt-core) supports generic data tests that can be applied to any model column using a Jinja macro. The task is to implement a new built-in generic test macro `accepted_range` (similar to the existing `accepted_values` test) that validates a numeric column falls within a specified min/max range, with support for inclusive/exclusive bounds, null handling, and row-level failure reporting.

## Files to Create/Modify

- `core/dbt/include/global_project/macros/generic_test_templates/accepted_range.sql` (create) — Jinja/SQL macro definition for the `accepted_range` generic test
- `core/dbt/contracts/test.py` (modify) — Add `AcceptedRangeConfig` dataclass for the test's parameters
- `tests/unit/test_accepted_range_macro.py` (create) — Unit tests that compile the macro and verify the generated SQL

## Requirements

### `accepted_range` Macro (`accepted_range.sql`)

The macro must be a generic test that accepts these parameters:

| Parameter | Type | Required | Description |
|---|---|---|---|
| `min_value` | numeric | No | Minimum allowed value (inclusive by default) |
| `max_value` | numeric | No | Maximum allowed value (inclusive by default) |
| `inclusive` | boolean | Yes (default: `true`) | If `true`, bounds are inclusive (`>=`/`<=`); if `false`, exclusive (`>`/`<`) |
| `where` | string | No | Optional SQL filter predicate added as `WHERE <where>` |

At least one of `min_value` or `max_value` must be provided. If neither is provided, the macro must raise a compilation error.

#### Generated SQL Structure

```sql
-- For model "orders", column "amount", min_value=0, max_value=1000, inclusive=true
with validation as (
    select
        amount as value_field
    from {{ model }}
    {% if where %}where {{ where }}{% endif %}
),

validation_errors as (
    select
        value_field
    from validation
    where
        value_field is not null
        {% if min_value is not none %}
        and value_field {% if inclusive %}>= {{ min_value }}{% else %}> {{ min_value }}{% endif %}
        {% endif %}
        {% if max_value is not none %}
        and value_field {% if inclusive %}<= {{ max_value }}{% else %}< {{ max_value }}{% endif %}
        {% endif %}
)

select count(*) from validation_errors
```

Wait — the errors are violations, so the `where` clause in `validation_errors` must select rows that are OUT OF RANGE (i.e., violations). Correct logic:

```sql
validation_errors as (
    select value_field
    from validation
    where
        value_field is not null
        and (
            {% if min_value is not none %}
            value_field {% if inclusive %}< {{ min_value }}{% else %}<= {{ min_value }}{% endif %}
            {% if max_value is not none %}or{% endif %}
            {% endif %}
            {% if max_value is not none %}
            value_field {% if inclusive %}> {{ max_value }}{% else %}>= {{ max_value }}{% endif %}
            {% endif %}
        )
)
```

#### Null Handling
- By default, `NULL` values are excluded from the violation count (not flagged as failures)
- This is because `value_field is not null` is always applied before the range check

#### Compilation Error
If neither `min_value` nor `max_value` is provided:
```jinja
{% if min_value is none and max_value is none %}
    {{ exceptions.raise_compiler_error("accepted_range test requires at least one of min_value or max_value") }}
{% endif %}
```

#### Macro Registration

The macro must be named `test_accepted_range` (dbt prepends `test_` to identify generic test macros):
```jinja
{% test accepted_range(model, column_name, min_value=none, max_value=none, inclusive=true, where=none) %}
```

### `AcceptedRangeConfig` (`test.py`)

Add a dataclass for the test parameters:

```python
@dataclass
class AcceptedRangeConfig:
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    inclusive: bool = True
    where: Optional[str] = None
    
    def __post_init__(self):
        if self.min_value is None and self.max_value is None:
            raise ValueError("accepted_range test requires at least one of min_value or max_value")
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError(f"min_value ({self.min_value}) must be <= max_value ({self.max_value})")
```

### Unit Tests (`test_accepted_range_macro.py`)

Test cases must verify the compiled SQL output (not run against a real database):

1. **`test_min_only`**: `accepted_range(column_name='price', min_value=0)` — generated SQL contains `< 0` (violation condition for inclusive lower bound)

2. **`test_max_only`**: `accepted_range(column_name='price', max_value=100)` — generated SQL contains `> 100`

3. **`test_both_bounds_inclusive`**: `accepted_range(column_name='score', min_value=0, max_value=100, inclusive=true)` — violations are `< 0 or > 100`

4. **`test_exclusive_bounds`**: `accepted_range(column_name='score', min_value=0, max_value=100, inclusive=false)` — violations are `<= 0 or >= 100`

5. **`test_where_clause`**: When `where='is_active = true'` is passed — generated SQL contains `where is_active = true` in the `validation` CTE

6. **`test_no_bounds_raises`**: `AcceptedRangeConfig()` raises `ValueError`

7. **`test_inverted_bounds_raises`**: `AcceptedRangeConfig(min_value=100, max_value=0)` raises `ValueError`

## Expected Functionality

- Applying `accepted_range` in a `schema.yml`:
  ```yaml
  columns:
    - name: amount
      tests:
        - accepted_range:
            min_value: 0
            max_value: 10000
  ```
  generates SQL that returns 0 for a passing column and non-zero for rows where `amount < 0 or amount > 10000`

- With `inclusive: false` and `min_value: 0`: a row with `amount = 0` is flagged as a violation (`<= 0` condition)

- With only `max_value: 100`: rows where `amount > 100` are violations; rows below 100 pass

## Acceptance Criteria

- The `test_accepted_range` macro is syntactically valid Jinja2/SQL
- Generated SQL correctly inverts the comparison to find violation rows (out-of-range values)
- `inclusive=true` uses `<` / `>` for violation conditions; `inclusive=false` uses `<=` / `>=`
- `NULL` values are never counted as violations
- `where` parameter is correctly applied as a filter in the `validation` CTE
- When neither `min_value` nor `max_value` is provided: `exceptions.raise_compiler_error` is called in the macro
- `AcceptedRangeConfig.__post_init__` raises `ValueError` for missing bounds and inverted bounds
- All unit tests pass correctly verifying the compiled SQL structure
