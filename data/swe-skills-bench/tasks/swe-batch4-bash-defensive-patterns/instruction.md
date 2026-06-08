# SWE-Skills-Bench: bash-defensive-patterns (batch4)

# Task: Write a Defensive Bash Script Library for Safe File and Process Operations

## Background

The ShellCheck repository (https://github.com/koalaman/shellcheck) is a static analysis tool for shell scripts. A new example script library is needed that demonstrates production-grade defensive Bash programming: strict mode, error trapping with cleanup, safe temporary file/directory handling, argument validation, logging, retry logic, and safe file operations — serving as a reference for writing reliable shell scripts.

## Files to Create/Modify

- `examples/defensive-lib/lib/core.sh` (create) — Core library: strict mode initialization, error trap, cleanup handler, logging functions
- `examples/defensive-lib/lib/file_ops.sh` (create) — Safe file operation functions: atomic write, backup-and-replace, safe copy, locked operations
- `examples/defensive-lib/lib/process_ops.sh` (create) — Process management: retry with backoff, timeout execution, parallel job runner, PID file management
- `examples/defensive-lib/lib/validation.sh` (create) — Input validation: argument parser, type checkers, path validators, dependency checker
- `examples/defensive-lib/scripts/deploy.sh` (create) — Example deployment script that uses all library modules
- `tests/test_bash_defensive_patterns.py` (create) — Python tests that execute the Bash scripts and verify their behavior

## Requirements

### Core Library (core.sh)

- Must start with `#!/bin/bash` and `set -Eeuo pipefail`
- `init_strict_mode()` — sets all strict mode flags and configures ERR trap to print file, line number, and failed command
- `cleanup_handler()` — registered via `trap ... EXIT`; removes all temporary files/directories tracked in a global array `_CLEANUP_ITEMS`
- `register_cleanup(path)` — adds a path to the cleanup list
- `log_info(message)`, `log_warn(message)`, `log_error(message)` — structured log functions that output to stderr with ISO-8601 timestamp, level, and message
- `die(message, exit_code=1)` — log error and exit with the given code
- All log functions must include the calling function name and line number

### Safe File Operations (file_ops.sh)

- `safe_write(file, content)` — writes `content` to a temporary file in the same directory, then atomically moves (`mv`) it to `file`; ensures partial writes never corrupt the target
- `backup_and_replace(file, new_content)` — creates a `.bak` backup of the existing file, then atomically writes `new_content`; rolls back if the write fails
- `safe_copy(src, dest)` — validates both paths exist/are writable, copies via temp file, then moves
- `locked_operation(lock_file, command...)` — acquires an exclusive file lock (using `flock`), runs the command, releases the lock; times out after 30 seconds with an error
- All functions must validate their arguments: empty strings, nonexistent directories → error with descriptive message

### Process Operations (process_ops.sh)

- `retry_with_backoff(max_retries, initial_delay, command...)` — retries the command up to `max_retries` times with exponential backoff (delay doubles each attempt); logs each attempt and final failure
- `run_with_timeout(timeout_seconds, command...)` — runs the command with a timeout; returns 124 on timeout (matching standard `timeout` behavior)
- `run_parallel(max_jobs, commands...)` — runs commands in parallel with at most `max_jobs` concurrent; waits for all to complete; returns non-zero if any job failed
- `manage_pid_file(pid_file, action)` — `action` is `create` (write current PID, fail if stale PID file exists) or `remove` (clean up PID file); stale detection: check if PID in file is still running

### Input Validation (validation.sh)

- `parse_args(spec, "$@")` — parses command-line arguments against a specification; `spec` is a string like `"name:required,output:optional:default_value,verbose:flag"`; returns variables set in the caller's scope
- `require_commands(cmd1, cmd2, ...)` — checks that each command is available via `command -v`; dies with a list of missing commands if any are absent
- `validate_path(path, type)` — `type` is `file`, `dir`, or `writable`; returns 0 on success, 1 on failure with descriptive message
- `is_integer(value)`, `is_positive_integer(value)` — return 0/1
- Variables must always be quoted (`"$var"`) and references to potentially unset variables must use `"${var:-}"` syntax

### Example Deploy Script (deploy.sh)

- Sources all four library modules
- Accepts arguments: `--app` (required, app name), `--env` (required, one of `dev`, `staging`, `prod`), `--version` (required), `--dry-run` (flag)
- Validates that `docker`, `curl`, and `jq` are available
- Simulates a deployment: create temp dir → download artifact (simulated with a file write) → validate artifact → backup current version → deploy (copy to target dir) → verify → cleanup
- Uses `retry_with_backoff` for the download step and `locked_operation` for the deploy step
- `--dry-run` mode logs all steps but does not execute destructive operations

### Expected Functionality

- Running `deploy.sh --app myapp --env staging --version 1.2.3` completes all steps with log output
- Running `deploy.sh --app myapp --env staging --version 1.2.3 --dry-run` logs steps without modifying files
- Missing `--app` argument causes an error: "Required argument 'app' not provided"
- `retry_with_backoff 3 1 false` retries 3 times with delays 1s, 2s, 4s, then fails
- `safe_write` to a read-only directory produces a descriptive error, not a partial file
- A script interrupted mid-execution cleans up all temporary files via the EXIT trap

## Acceptance Criteria

- All scripts pass ShellCheck analysis without errors (may have intentional exclusions with `# shellcheck disable=`)
- Strict mode (`set -Eeuo pipefail`) is active in all scripts
- Error trapping logs the file, function, and line number of the failure
- EXIT trap cleans up all registered temporary files/directories
- Atomic file writes never leave partial content in the target file
- Retry logic correctly implements exponential backoff with configurable attempts
- Argument parsing validates required arguments and provides defaults for optional ones
- Deploy script uses all library modules and supports `--dry-run` mode
- Tests verify error handling, cleanup, retry behavior, and argument validation
