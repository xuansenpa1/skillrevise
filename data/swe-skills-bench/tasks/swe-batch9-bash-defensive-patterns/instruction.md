# SWE-Skills-Bench: bash-defensive-patterns (batch9)

# Task: Create a Production-Grade Bash Script Library with Defensive Patterns

## Background

ShellCheck (https://github.com/koalaman/shellcheck) enforces Bash best practices. A comprehensive Bash script library is needed that implements production-grade defensive patterns: strict mode, error trapping with stack traces, safe temporary file handling, a logging framework, input validation, a retry mechanism with exponential backoff, a configuration parser, and a deployment script that ties all patterns together.

## Files to Create/Modify

- `scripts/lib/strict.sh` (create) — Strict mode initialization with `set -Eeuo pipefail`, ERR trap that prints file, line number, and function call stack, EXIT trap for cleanup of temporary resources
- `scripts/lib/logging.sh` (create) — Logging framework with levels (DEBUG, INFO, WARN, ERROR, FATAL), colored output, timestamps, log-to-file support, and structured context fields
- `scripts/lib/validation.sh` (create) — Input validation functions: `require_var`, `require_file`, `require_command`, `validate_ip`, `validate_port`, `validate_url`, `validate_semver`
- `scripts/lib/retry.sh` (create) — Retry mechanism with configurable max attempts, exponential backoff with jitter, and success/failure callbacks
- `scripts/lib/tempfiles.sh` (create) — Safe temporary file/directory management with automatic cleanup on EXIT, trap-safe creation, and secure permissions (mode 0600/0700)
- `scripts/lib/config.sh` (create) — Configuration file parser supporting KEY=VALUE format, environment variable interpolation, default values, and type coercion
- `scripts/deploy.sh` (create) — Deployment script using all library modules: validates environment, reads config, creates temp staging area, deploys with retry, and logs all operations
- `scripts/tests/test_library.sh` (create) — Test harness that validates each library module's behavior

## Requirements

### Strict Mode (`strict.sh`)

- `set -Eeuo pipefail` at the top
- ERR trap function `_trap_err()`:
  - Captures `$LINENO`, `$BASH_COMMAND`, `$?` (exit code)
  - Prints stack trace using `FUNCNAME[@]`, `BASH_SOURCE[@]`, `BASH_LINENO[@]` arrays
  - Format: `ERROR: Command '<command>' failed with exit code <N> at <file>:<line> in <function>`
  - Walks the full call stack (all frames) for nested function errors
- EXIT trap function `_trap_exit()`:
  - Calls registered cleanup functions in LIFO order
  - Never fails (uses `|| true` for each cleanup step)
- Function `register_cleanup <function_name>` — Adds a cleanup function to the EXIT trap stack
- All trap functions must be safe to call multiple times (idempotent)

### Logging (`logging.sh`)

- Variable `LOG_LEVEL` (default: `INFO`) — Controls minimum output level
- Variable `LOG_FILE` (optional) — When set, also writes to this file (without colors)
- Function `log_debug <message>`, `log_info <message>`, `log_warn <message>`, `log_error <message>`, `log_fatal <message>`
- Output format: `[2024-01-15T10:30:45Z] [LEVEL] [script:line] message`
- Colors: DEBUG=cyan, INFO=green, WARN=yellow, ERROR=red, FATAL=red+bold
- `log_fatal` must call `exit 1` after logging
- Function `log_context <key> <value>` — Sets context pairs that appear in subsequent log lines as `[key=value]`
- All log output goes to stderr (not stdout) to avoid polluting command output

### Validation (`validation.sh`)

- `require_var <var_name>` — Checks if variable is set and non-empty; prints error and returns 1 if not
- `require_file <path>` — Checks if file exists and is readable; returns 1 with message if not
- `require_command <cmd>` — Checks if command is available in PATH; returns 1 with message if not
- `validate_ip <value>` — Returns 0 for valid IPv4 addresses (4 octets, 0-255 each), 1 otherwise
- `validate_port <value>` — Returns 0 for integers 1-65535, 1 otherwise
- `validate_url <value>` — Returns 0 for http:// or https:// URLs, 1 otherwise
- `validate_semver <value>` — Returns 0 for valid semver (MAJOR.MINOR.PATCH with optional pre-release), 1 otherwise
- All validation functions print a descriptive error message on failure
- No `eval` usage anywhere for safety

### Retry (`retry.sh`)

- Function `retry <max_attempts> <initial_delay> <command...>`:
  - Executes `command` up to `max_attempts` times
  - On failure, waits with exponential backoff: `delay = initial_delay * 2^attempt`
  - Adds jitter: `actual_delay = delay + random(0, delay/2)`
  - Returns the exit code of the last attempt if all fail
  - Logs each attempt number and wait duration
- Function `retry_with_callback <max_attempts> <delay> <on_success_fn> <on_failure_fn> <command...>`:
  - Same retry logic, but calls `on_success_fn` on success and `on_failure_fn` on final failure
- Maximum backoff cap: 300 seconds (never wait longer regardless of attempt count)

### Temporary Files (`tempfiles.sh`)

- Function `create_temp_file [prefix]` — Creates a temp file with `mktemp`, mode 0600, registers it for cleanup, echoes the path
- Function `create_temp_dir [prefix]` — Creates a temp directory with `mktemp -d`, mode 0700, registers it for cleanup, echoes the path
- All created paths are stored in array `_TEMP_RESOURCES`
- Cleanup function `_cleanup_temps()` registered via `register_cleanup`:
  - Removes all entries in `_TEMP_RESOURCES` using `rm -rf`
  - Handles already-deleted paths gracefully
- Function `secure_write <file> <content>` — Writes content to file atomically (write to temp, then `mv`) to prevent partial writes

### Configuration Parser (`config.sh`)

- Function `load_config <file>`:
  - Reads KEY=VALUE lines (ignoring comments `#` and blank lines)
  - Strips inline comments
  - Handles quoted values (single and double quotes)
  - Performs environment variable interpolation: `${VAR}` and `$VAR` are expanded
  - Stores values in associative array `CONFIG`
- Function `config_get <key> [default]` — Returns value for key, or default if not set
- Function `config_require <key>` — Returns value or exits with error if key is missing
- Function `config_get_int <key> [default]` — Returns integer value; exits with error if value is not numeric
- Function `config_get_bool <key> [default]` — Returns `true`/`false`; accepts `true/false/yes/no/1/0`
- No `eval` or `source` on config values to prevent code injection

### Deployment Script (`deploy.sh`)

- Sources all library modules from `scripts/lib/`
- Loads config from `scripts/deploy.conf`
- Validates required variables: `DEPLOY_TARGET`, `DEPLOY_VERSION`, `DEPLOY_USER`
- Creates a temp staging directory
- Simulates a deployment: copies files to staging, validates, then "deploys" (moves to target)
- Uses `retry 3 5 deploy_step` for the deployment step
- Logs all operations at INFO level with timing information
- Cleans up temp resources on exit (even on failure)

### Expected Functionality

- An ERR trap catches a failing command in a nested function and prints the full call stack with file, line, and function names
- `retry 3 2 false` attempts 3 times with backoff delays of ~2s, ~4s, then fails with exit code 1
- `validate_ip "256.1.1.1"` returns 1; `validate_ip "192.168.1.1"` returns 0
- `load_config` ignores comments, handles quotes, and interpolates environment variables
- `create_temp_file` returns a path that exists with mode 0600 and is automatically deleted on EXIT

## Acceptance Criteria

- All scripts pass ShellCheck (`shellcheck -x scripts/**/*.sh`) with no errors
- Strict mode catches undefined variables and pipe failures
- ERR trap prints function call stack for nested function errors
- Logging respects LOG_LEVEL filtering and outputs timestamps to stderr
- All validation functions correctly accept valid and reject invalid inputs
- Retry implements exponential backoff with jitter capped at 300s
- Temp files have secure permissions and are cleaned up on EXIT
- Config parser handles quotes, comments, and env var interpolation without using eval
- `python -m pytest /workspace/tests/test_bash_defensive_patterns.py -v --tb=short` passes
