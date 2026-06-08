# SWE-Skills-Bench: bash-defensive-patterns (batch5)

# Task: Write Defensive Bash Scripts with ShellCheck Compliance

## Background

ShellCheck (https://github.com/koalaman/shellcheck) is a static analysis tool for shell scripts. This task requires writing a set of production deployment and maintenance Bash scripts that follow defensive programming patterns: strict mode, proper quoting, safe variable handling, error propagation, cleanup traps, and lock files. All scripts must pass ShellCheck with zero warnings.

## Files to Create/Modify

- `scripts/deploy.sh` (create) — Deployment script: pulls new Docker image, runs pre-deploy health check, swaps containers with zero-downtime rolling restart, runs post-deploy verification.
- `scripts/backup.sh` (create) — Database backup script: acquires a file lock (prevents concurrent runs), dumps PostgreSQL database, compresses with gzip, uploads to S3, rotates old backups (keep last 7), handles cleanup on failure.
- `scripts/healthcheck.sh` (create) — Health check script: checks multiple endpoints (HTTP status, response time, JSON response field matching), reports results in structured format, exits with appropriate code.
- `scripts/lib/common.sh` (create) — Shared library sourced by other scripts: logging functions (log_info, log_warn, log_error with timestamps), retry function with configurable attempts/delay, cleanup trap registration.
- `tests/test_bash_defensive_patterns.py` (create) — Tests that run ShellCheck on all scripts and verify they pass with zero warnings, plus tests for specific defensive patterns.

## Requirements

### Common Library (`lib/common.sh`)

- Starts with `#!/usr/bin/env bash` and `set -euo pipefail`.
- `log_info`, `log_warn`, `log_error` — print to stderr with ISO 8601 timestamp and severity tag: `[2024-01-15T10:30:00Z] [INFO] message`.
- `retry` — function: `retry <max_attempts> <delay_seconds> <command...>`. Retries the command, sleeping between attempts. Logs each retry attempt. Returns the exit code of the last attempt.
- `acquire_lock` — `flock`-based file locking using file descriptor 200. Lock file path passed as argument. Non-blocking: if lock cannot be acquired, log error and exit 1.
- `release_lock` — releases the lock file descriptor.
- `register_cleanup` — appends a cleanup command to a global `_CLEANUP_COMMANDS` array. Registers a trap on `EXIT` that executes all cleanup commands in reverse order.

### Deploy Script

- Sources `lib/common.sh`.
- Arguments: `--image <image:tag>` (required), `--service <name>` (required), `--timeout <seconds>` (default 120).
- Parse arguments using `getopts` or manual `while` loop with `shift`. Validate that required args are present.
- Steps:
  1. `docker pull "$IMAGE"` with retry (3 attempts, 5s delay).
  2. Pre-deploy health check: `healthcheck.sh --url "http://localhost:${PORT}/health"` → fail if unhealthy.
  3. Rolling restart: stop old container, start new container, wait for health check to pass within timeout.
  4. Post-deploy verification: check new container is running, health endpoint returns 200, log version from response.
- If any step fails, register cleanup to restart the old container. Use trap to ensure cleanup runs.
- All variables properly quoted: `"${IMAGE}"`, not `$IMAGE`.

### Backup Script

- Sources `lib/common.sh`.
- Arguments: `--db-name <name>`, `--s3-bucket <bucket>`, `--retention-days <n>` (default 7).
- Acquires file lock at `/var/lock/backup-${DB_NAME}.lock` — exits if another backup is running.
- Steps:
  1. `pg_dump -Fc "${DB_NAME}" > "${BACKUP_FILE}"` where `BACKUP_FILE="/tmp/backup-${DB_NAME}-$(date +%Y%m%d%H%M%S).dump"`.
  2. `gzip "${BACKUP_FILE}"`.
  3. `aws s3 cp "${BACKUP_FILE}.gz" "s3://${S3_BUCKET}/backups/"`.
  4. Rotate: `aws s3 ls "s3://${S3_BUCKET}/backups/"`, parse dates, delete backups older than retention days.
- Cleanup on failure: remove the local dump file if it exists. Use `register_cleanup` to register `rm -f "${BACKUP_FILE}" "${BACKUP_FILE}.gz"`.

### Health Check Script

- Arguments: `--url <url>` (repeatable for multiple endpoints), `--timeout <seconds>` (default 5), `--expected-status <code>` (default 200), `--json-field <field>` (optional, dot-notation path to check in JSON response).
- For each URL:
  - `curl -sf -o response.json -w "%{http_code}" --max-time "${TIMEOUT}" "${URL}"` — capture status and body.
  - Check HTTP status matches expected.
  - If `--json-field` specified, use `jq -r ".${FIELD}"` to extract and verify non-null.
  - Print result: `[PASS] url=<url> status=<code> latency=<ms>` or `[FAIL] url=<url> reason=<description>`.
- Exit 0 if all checks pass, exit 1 if any fail.
- Handles connection timeouts, refuse-to-connect, and non-JSON responses gracefully.

### ShellCheck Compliance

- All scripts must pass `shellcheck -s bash -S style` with zero warnings.
- No unquoted variables, no word splitting issues, no globbing risks.
- Use `[[ ]]` for conditionals (not `[ ]`), `$(command)` for substitution (not backticks).
- Use `local` for function-local variables.
- Use `readonly` for constants.

### Expected Functionality

- `./deploy.sh --image myapp:v1.2.3 --service webapp` → pulls image, health checks, rolling restart, verification.
- `./backup.sh --db-name myapp --s3-bucket my-backups --retention-days 7` → dump, compress, upload, rotate.
- `./healthcheck.sh --url http://localhost:8080/health --url http://localhost:8080/ready --json-field status` → checks both URLs and verifies JSON field.
- Running `shellcheck scripts/*.sh scripts/lib/*.sh` produces zero warnings.

## Acceptance Criteria

- All scripts start with `set -euo pipefail` and use proper Bash idioms.
- Variables are consistently quoted; no ShellCheck warnings on any script.
- `lib/common.sh` provides working logging, retry, lock, and cleanup functions.
- Deploy script handles argument parsing, retry on pull, and cleanup on failure.
- Backup script uses file locking, performs dump/compress/upload/rotate, and cleans up temp files.
- Health check script handles multiple URLs, timeout, HTTP status, and JSON field checking.
- Tests verify ShellCheck compliance and scan for defensive patterns (quoting, set -euo pipefail, trap usage).
