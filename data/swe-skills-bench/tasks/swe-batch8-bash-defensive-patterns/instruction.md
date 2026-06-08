# SWE-Skills-Bench: bash-defensive-patterns (batch8)

# Task: Build a Defensive Bash Script Library for ShellCheck

## Background

ShellCheck (https://github.com/koalaman/shellcheck) is a static analysis tool for shell scripts. The project needs a collection of production-grade Bash utility scripts that demonstrate defensive programming patterns: strict mode, error trapping, safe variable handling, atomic file operations, lock management, and structured logging. These scripts serve as both a reference library and test fixtures for validating ShellCheck compliance.

## Files to Create/Modify

- `test/scripts/lib/defensive_utils.sh` (create) — Core utility library with strict mode initialization, error trap handler, cleanup management, structured logging (with levels and timestamps), and safe temporary directory creation
- `test/scripts/lib/file_ops.sh` (create) — Atomic file operation functions: safe file write (write to temp then mv), directory creation with validation, safe file removal with confirmation, and backup-before-modify pattern
- `test/scripts/lib/lock_manager.sh` (create) — File-based lock management: acquire lock (with timeout and retry), release lock, check lock staleness (detect and clean up locks from dead processes), and flock-based concurrent execution guard
- `test/scripts/lib/input_validator.sh` (create) — Input validation functions: validate non-empty string, validate integer range, validate file path exists, validate URL format, validate IP address, and sanitize input for shell safety (reject shell metacharacters)
- `test/scripts/deploy.sh` (create) — Example deployment script using all library functions: parse arguments, validate inputs, acquire deployment lock, backup current version, deploy new version atomically, health check, rollback on failure, release lock
- `tests/test_bash_defensive_patterns.py` (create) — Python test suite that runs the Bash scripts, validates their behavior, and checks ShellCheck compliance

## Requirements

### Defensive Utils (`defensive_utils.sh`)

- `init_strict_mode()` — Set `set -Eeuo pipefail`, configure `IFS=$'\n\t'`
- `setup_error_trap()` — Register ERR trap that logs the failed command, line number, and function name: `"ERROR: Command '${BASH_COMMAND}' failed at line ${LINENO} in function ${FUNCNAME[1]:-main}"`
- `setup_cleanup_trap()` — Register EXIT trap that runs a list of cleanup functions in LIFO order; functions added via `register_cleanup "function_name"`
- `log()` — Accept level and message: `log "INFO" "Starting deployment"` → `"[2024-01-15T10:30:00Z] [INFO] [deploy.sh:42] Starting deployment"`; levels: `DEBUG`, `INFO`, `WARN`, `ERROR`
- `create_temp_dir()` — Create a temporary directory with `mktemp -d`, register its removal in cleanup, return the path
- `require_commands()` — Accept a list of command names, check each with `command -v`, exit with error listing missing commands
- All functions must be ShellCheck-clean (no warnings with `shellcheck -S warning`)

### File Operations (`file_ops.sh`)

- `atomic_write "target_path" "content"` — Write content to a temp file in the same directory, then `mv` to target; ensures no partial writes
- `atomic_write_file "target_path" "source_path"` — Copy source to temp in target directory, then `mv` to target
- `safe_mkdir "path"` — Create directory only if it doesn't exist; validate path doesn't contain `..`; set permissions to 755
- `safe_remove "path"` — Remove file/directory only if it exists and is within an allowed base directory (configurable via `SAFE_REMOVE_BASE`); refuse to remove `/`, `/etc`, `/usr`, `/var`, `/home`
- `backup_file "path"` — Copy file to `{path}.bak.{timestamp}`, return the backup path; limit to 5 backups (remove oldest)
- All operations must check return codes and log errors

### Lock Manager (`lock_manager.sh`)

- `acquire_lock "lock_file" [timeout_seconds]` — Create a lock file with PID content; if lock exists, check if PID is alive; if dead process, remove stale lock and acquire; retry every 1 second up to timeout (default 30); return 0 on success, 1 on timeout
- `release_lock "lock_file"` — Remove lock file only if current process owns it (PID matches); log warning if lock owned by different PID
- `with_lock "lock_file" "command" [args...]` — Acquire lock, run command, release lock regardless of command success/failure (use trap); propagate command exit code
- `check_stale_lock "lock_file"` — Return 0 if lock is stale (PID not running), 1 if active, 2 if no lock exists
- Lock files must contain: PID on line 1, hostname on line 2, timestamp on line 3

### Input Validator (`input_validator.sh`)

- `validate_not_empty "value" "field_name"` — Exit with error if value is empty: `"Validation failed: {field_name} must not be empty"`
- `validate_integer "value" "field_name" [min] [max]` — Check value is an integer within optional range; exit on failure
- `validate_file_exists "path" "field_name"` — Check file exists and is readable
- `validate_url "value" "field_name"` — Check value matches `https?://[a-zA-Z0-9.-]+(/.*)?` pattern
- `validate_ip "value" "field_name"` — Validate IPv4 format (4 octets, each 0-255)
- `sanitize_input "value"` — Remove shell metacharacters (`` ` ``, `$`, `;`, `|`, `&`, `>`, `<`, `(`, `)`, `{`, `}`); return sanitized string; if value changes after sanitization, log a warning

### Deploy Script (`deploy.sh`)

- Parse arguments: `--app-name` (required), `--version` (required), `--target-dir` (required), `--health-url` (optional), `--rollback` (flag)
- Validation: app name non-empty, version matches semver pattern `[0-9]+\.[0-9]+\.[0-9]+`, target dir exists
- Lock: acquire deployment lock at `/tmp/deploy-{app_name}.lock` with 60-second timeout
- Backup: backup current `{target_dir}/{app_name}` directory
- Deploy: atomically write version file, create/update symlink to new version
- Health check: if URL provided, curl with 30-second timeout and 3 retries, 5 seconds between retries
- Rollback: on health check failure, restore from backup, log rollback event
- Cleanup: release lock on exit (regardless of success/failure)

### Edge Cases

- `atomic_write` with target on a different filesystem than `/tmp`: detect cross-device and fall back to `cp` + `rm`
- Lock file with PID that has been recycled (different process): lock is only stale if the PID does not exist; if PID exists but is a different command, still treat as active (conservative approach)
- `safe_remove` called with path containing symlinks: resolve symlinks before checking base directory
- Empty arguments to validation functions: treated as validation failure, not a script error
- `deploy.sh` invoked with `--rollback` flag: skip deployment, restore most recent backup, and exit

## Expected Functionality

- Sourcing `defensive_utils.sh` and calling `init_strict_mode` enables all defensive settings in the calling script
- `atomic_write "/etc/myapp/config.json" '{"key": "value"}'` writes safely even if the script is interrupted mid-write
- `acquire_lock "/tmp/deploy.lock" 10` retries for 10 seconds before giving up on a held lock
- `validate_ip "256.1.2.3" "server_ip"` exits with error `"Validation failed: server_ip must be a valid IPv4 address"`
- Running `deploy.sh --app-name myapp --version 1.2.3 --target-dir /opt/apps --health-url http://localhost:8080/health` performs a complete deployment cycle with backup and health check

## Acceptance Criteria

- All `.sh` files pass `shellcheck -S warning` with no warnings
- Strict mode catches unset variables, pipe failures, and command errors
- Error traps log the specific command, line number, and function name
- Atomic file operations never leave partial files on interruption
- Lock manager handles stale locks from dead processes and supports timeout
- Input validators reject invalid formats and sanitize shell metacharacters
- Deploy script performs backup, atomic deploy, health check, and rollback on failure
- All tests pass with `pytest`
