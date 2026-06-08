# SWE-Skills-Bench: bash-defensive-patterns (batch7)

# Task: Implement New ShellCheck Rules for Common Bash Anti-Patterns

## Background

ShellCheck (https://github.com/koalaman/shellcheck) is a static analysis tool for shell scripts, written in Haskell. The task is to add three new analysis rules that detect common defensive programming anti-patterns: unsafe temporary file creation without `mktemp`, missing cleanup traps for temporary resources, and unquoted command substitutions in conditional expressions.

## Files to Create/Modify

- `src/ShellCheck/Checks/Commands.hs` (modify) — Add rule SC2326: detect `tempfile=$(echo /tmp/myfile_$$)` or direct `/tmp/name` assignments instead of `mktemp`
- `src/ShellCheck/Checks/ShellSupport.hs` (modify) — Add rule SC2327: detect scripts that create temporary files/directories but never set a `trap` for cleanup on EXIT/ERR
- `src/ShellCheck/Checks/Commands.hs` (modify) — Add rule SC2328: detect unquoted `$(command)` inside `[[ ]]` or `[ ]` test expressions where word splitting could cause incorrect behavior
- `tests/ShellCheck/Checks/CommandsTest.hs` (modify) — Unit tests for SC2326 and SC2328
- `tests/ShellCheck/Checks/ShellSupportTest.hs` (modify) — Unit tests for SC2327

## Requirements

### SC2326: Unsafe Temporary File Creation

#### Detection Pattern
Trigger when a variable assignment uses any of these patterns for temporary file paths:
- Direct `/tmp/` path: `tmpfile=/tmp/myfile_$$` or `tmpfile="/tmp/script.$$"`
- Using `echo`: `tmpfile=$(echo /tmp/myfile)`
- Using string concatenation with `$RANDOM` or `$$`: `tmpfile="/tmp/data_${RANDOM}"`

#### Correct Alternative
The fix is to use `mktemp`: `tmpfile=$(mktemp)` or `tmpdir=$(mktemp -d)`

#### Message
`"SC2326: Use mktemp instead of manual /tmp paths to avoid symlink attacks and race conditions."`

#### Severity
Warning

#### Specifics
- Match variable assignments where the RHS contains a literal `/tmp/` path
- Do not trigger if the variable is being used to check existence (`[ -f /tmp/something ]`)
- Do not trigger if `mktemp` is already being used in the assignment
- Handle both `VAR=value` and `local VAR=value` and `export VAR=value` forms

### SC2327: Missing Cleanup Trap

#### Detection Pattern
Trigger when a script:
1. Creates a temporary file (via `mktemp` or `/tmp/` assignment) AND
2. Does NOT have a `trap` command that references EXIT, ERR, or RETURN signals anywhere in the script

#### Conditions
- Only trigger at the function or script scope level where the temp file is created
- If a `trap` is set before the `mktemp` call, do not trigger
- If a `trap` is set after the `mktemp` call in the same scope, do not trigger (order within same scope is acceptable)
- If the temp file variable is used in a subshell `()`, the trap in the parent shell counts

#### Message
`"SC2327: Temporary file created without a cleanup trap. Add 'trap cleanup EXIT' to ensure removal on script exit."`

#### Severity
Info (style suggestion)

### SC2328: Unquoted Command Substitution in Test

#### Detection Pattern
Trigger when a command substitution `$(...)` or `` `...` `` appears unquoted inside a test expression:
- Inside `[ ... ]`: `[ $(wc -l < file) -gt 10 ]`
- Inside `[[ ... ]]`: `[[ $(cat file) == "expected" ]]`

#### Why It Matters
In `[ ]`, unquoted command substitution is subject to word splitting and globbing. If the command output contains spaces or glob characters, the test breaks. In `[[ ]]`, it's safer but still a best practice to quote.

#### Correct Alternative
- `[ "$(wc -l < file)" -gt 10 ]`
- `[[ "$(cat file)" == "expected" ]]`

#### Message
`"SC2328: Quote command substitution in test expressions to prevent word splitting: \"$(...)\" instead of $(...)."`

#### Severity
Warning (in `[ ]` tests), Info (in `[[ ]]` tests — less dangerous but still recommended)

#### Specifics
- Detect both `$(...)` and backtick forms
- Only trigger inside test expressions (`[ ]` or `[[ ]]`)
- Do not trigger if the substitution is already quoted: `"$(...)"`
- Do not trigger for arithmetic contexts: `$(( ... ))`
- Do not trigger inside `[[ ]]` for `=~` regex matching (right side intentionally unquoted sometimes)

### Implementation Notes

- Each rule follows ShellCheck's existing pattern: a check function that traverses the AST, detects the pattern, and calls `warn` or `info` or `style` with the rule ID and message
- Rules must be registered in the appropriate check module's rule list
- Use ShellCheck's existing AST types (`Token`, `InnerToken`) for pattern matching
- Follow the existing coding conventions in each `.hs` file

## Expected Functionality

- `tmpfile=/tmp/myapp_$$` triggers SC2326 with the unsafe temp file warning
- `tmpfile=$(mktemp)` followed by operations without any `trap` triggers SC2327
- `tmpfile=$(mktemp); trap "rm -f $tmpfile" EXIT` does NOT trigger SC2327
- `[ $(wc -l < file) -gt 10 ]` triggers SC2328; `[ "$(wc -l < file)" -gt 10 ]` does not
- `[[ $(cat file) == "hello" ]]` triggers SC2328 with Info severity

## Acceptance Criteria

- SC2326 detects all forms of manual `/tmp/` path assignment and does not false-positive on `mktemp` usage
- SC2327 correctly identifies scripts that create temp files without setting cleanup traps
- SC2327 does not trigger when a trap is already present in the same scope
- SC2328 detects unquoted command substitutions inside both `[ ]` and `[[ ]]` test expressions
- SC2328 does not trigger for already-quoted substitutions or arithmetic contexts
- Each rule produces the specified message and severity
- All new and existing tests pass after the changes
- Rules are properly registered and run as part of ShellCheck's analysis pipeline
