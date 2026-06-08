# SWE-Skills-Bench: bash-defensive-patterns (batch6)

# Task: Write a Defensive Bash Deployment Script Suite for a Multi-Service Application

## Background

A multi-service application (frontend, backend API, worker) deployed on Linux VMs needs a set of defensive Bash scripts for zero-downtime deployments, health checking, log rotation, and rollback. Each script must use strict mode, proper error trapping, safe variable handling, and atomic operations. The scripts must work on both Ubuntu 22.04 and Amazon Linux 2023.

## Files to Create/Modify

- `scripts/deploy.sh` (create) — Main deployment orchestrator: pulls artifacts, stops old service, installs new version, starts service, verifies health, rolls back on failure
- `scripts/health-check.sh` (create) — Health check script with configurable retries, timeout, and endpoint validation for HTTP services
- `scripts/rollback.sh` (create) — Rollback to previous version: restores symlink, restarts services, verifies health
- `scripts/log-rotate.sh` (create) — Log rotation: compress old logs, enforce retention policy, handle concurrent access safely
- `scripts/lib/common.sh` (create) — Shared library: logging functions, lock file management, cleanup traps, variable validation

## Requirements

### Shared Library (`scripts/lib/common.sh`)

- Strict mode header: `set -Eeuo pipefail`.
- `SCRIPT_DIR` detection using `${BASH_SOURCE[0]}`.
- Logging functions: `log_info`, `log_warn`, `log_error`, `log_debug`. Format: `[YYYY-MM-DDTHH:MM:SS] [LEVEL] [script_name] message`. `log_error` writes to stderr. `log_debug` only outputs when `DEBUG=1`.
- `require_var VAR_NAME` — check that variable is set and non-empty; exit 1 with message `"Required variable VAR_NAME is not set"` if missing.
- `require_command CMD_NAME` — check that command exists in PATH; exit 1 with message `"Required command CMD_NAME not found"` if missing.
- `acquire_lock LOCK_FILE` — create lock file with PID using `flock` or manual atomic creation (`set -o noclobber; echo $$ > "$LOCK_FILE"`). If lock exists and PID is still alive, exit 1 with message `"Another instance is running (PID: XXXX)"`. Stale lock (PID not running) is removed and re-acquired.
- `release_lock LOCK_FILE` — remove lock file if it contains current PID.
- `setup_cleanup` — register EXIT trap that calls `release_lock` and removes temp directory.
- `create_temp_dir` — create temp directory with `mktemp -d`, register for cleanup.

### Deploy Script (`scripts/deploy.sh`)

- Usage: `./deploy.sh --service <frontend|api|worker> --version <semver> [--skip-health-check] [--dry-run]`.
- Parse arguments with `getopts` or manual loop. Validate that `--service` and `--version` are provided.
- Required environment variables (validated via `require_var`): `DEPLOY_USER`, `DEPLOY_DIR`, `ARTIFACT_URL`.
- Required commands (validated via `require_command`): `curl`, `tar`, `systemctl`, `jq`.
- Deployment steps:
  1. Acquire lock file `/var/run/deploy-${SERVICE}.lock`.
  2. Create temp directory for download.
  3. Download artifact: `curl -fSL --retry 3 --retry-delay 5 "${ARTIFACT_URL}/${SERVICE}-${VERSION}.tar.gz" -o "$TMPDIR/artifact.tar.gz"`. Verify download with SHA256 checksum from `${ARTIFACT_URL}/${SERVICE}-${VERSION}.sha256`.
  4. Extract to versioned directory: `${DEPLOY_DIR}/${SERVICE}/releases/${VERSION}/`.
  5. Run pre-deploy hook if `${DEPLOY_DIR}/${SERVICE}/hooks/pre-deploy.sh` exists (source it).
  6. Update symlink atomically: `ln -sfn "${DEPLOY_DIR}/${SERVICE}/releases/${VERSION}" "${DEPLOY_DIR}/${SERVICE}/current.tmp" && mv -Tf "${DEPLOY_DIR}/${SERVICE}/current.tmp" "${DEPLOY_DIR}/${SERVICE}/current"`.
  7. Restart service: `systemctl restart "${SERVICE}.service"`.
  8. Run health check (unless `--skip-health-check`): call `health-check.sh` for the service.
  9. If health check fails: call `rollback.sh` for the service, exit 1.
  10. Run post-deploy hook if `${DEPLOY_DIR}/${SERVICE}/hooks/post-deploy.sh` exists.
  11. Clean up old releases: keep only the 5 most recent in `releases/`, delete older ones.
  12. Release lock, exit 0.
- Dry-run mode: log all steps without executing destructive operations (no downloads, no symlink changes, no restarts).
- All file operations must use quoted variables. All pipes must be checked (pipefail).

### Health Check Script (`scripts/health-check.sh`)

- Usage: `./health-check.sh --service <name> --port <port> [--path /health] [--retries 10] [--interval 3] [--timeout 5]`.
- Default values: `--path /health`, `--retries 10`, `--interval 3` (seconds), `--timeout 5` (seconds per request).
- For each retry attempt:
  1. `curl -sf --max-time "${TIMEOUT}" "http://localhost:${PORT}${PATH}"` — check HTTP 200.
  2. Parse JSON response: verify `{"status": "healthy"}` using `jq -e '.status == "healthy"'`.
  3. If success: log `"Health check passed on attempt N/${RETRIES}"`, exit 0.
  4. If failure: log warning, sleep `${INTERVAL}` seconds.
- After all retries exhausted: log error `"Health check failed after ${RETRIES} attempts for service ${SERVICE}"`, exit 1.
- Handle cases: service not yet listening (connection refused), timeout, invalid JSON response, non-200 status.

### Rollback Script (`scripts/rollback.sh`)

- Usage: `./rollback.sh --service <name> [--version <specific_version>]`.
- If `--version` not specified: read symlink at `${DEPLOY_DIR}/${SERVICE}/current`, list `releases/` directory, find the release immediately before current (sorted by semver).
- Acquire lock, update symlink to previous version, restart service, run health check.
- If rollback health check also fails: log `"CRITICAL: Rollback also failed for ${SERVICE}. Manual intervention required."`, exit 2.
- Keep the failed release directory (don't delete) for debugging.

### Log Rotation Script (`scripts/log-rotate.sh`)

- Usage: `./log-rotate.sh --log-dir <path> [--max-age 30] [--max-size 100M] [--compress]`.
- Find log files matching `*.log` in `--log-dir`.
- For files exceeding `--max-size`: rotate by renaming `app.log` → `app.log.1` (shift existing numbered files up), truncate original using `cp /dev/null`.
- For files older than `--max-age` days: delete.
- If `--compress`: gzip rotated files (`app.log.1` → `app.log.1.gz`), skip already compressed files.
- Use `flock` on each log file during rotation to prevent concurrent access issues.
- Log summary: `"Rotated N files, compressed M files, deleted K files"`.

### Expected Functionality

- `./deploy.sh --service api --version 2.1.0` → downloads artifact, verifies checksum, creates release directory, atomically updates symlink, restarts service, verifies health.
- `./deploy.sh --service api --version 2.1.0 --dry-run` → logs all steps without executing them.
- `./health-check.sh --service api --port 8080 --retries 5` → polls `http://localhost:8080/health` up to 5 times.
- `./rollback.sh --service api` → finds previous release, reverts symlink, restarts, verifies health.
- `./deploy.sh --service api --version 2.1.0` while another deploy is running → exits with "Another instance is running (PID: XXXX)".
- Running `deploy.sh` without `DEPLOY_USER` set → exits with "Required variable DEPLOY_USER is not set".

## Acceptance Criteria

- All scripts begin with `set -Eeuo pipefail` and use ERR/EXIT traps for cleanup.
- All variable references are double-quoted to prevent word splitting and globbing.
- Lock file mechanism prevents concurrent deployments of the same service and handles stale locks.
- Symlink update is atomic using `ln -sfn` + `mv -Tf` pattern.
- Health check implements retry loop with configurable attempts, interval, and per-request timeout.
- Rollback determines previous version from release directory listing when no explicit version is given.
- Rollback failure (health check fails after reverting) exits with code 2 and a CRITICAL log message.
- Log rotation handles concurrent access with `flock`, compresses rotated files, and enforces retention by age and count.
- All scripts validate required variables and commands before starting destructive operations.
- Dry-run mode logs intended actions without side effects.
