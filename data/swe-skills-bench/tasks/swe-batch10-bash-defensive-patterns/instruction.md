# SWE-Skills-Bench: bash-defensive-patterns (batch10)

# Task: Add Defensive Wrapper Scripts to the ShellCheck Test Harness

## Background

ShellCheck (`koalaman/shellcheck`) is a static analysis tool for shell scripts. The project's test infrastructure under `test/` runs shell-based integration tests to verify ShellCheck's behavior. Three new Bash utility scripts are needed in `test/`: a test runner that orchestrates parallel ShellCheck invocations across sample files, a result formatter that parses ShellCheck JSON output into a summary report, and a CI bootstrap script that sets up the test environment. All three scripts must follow strict defensive programming practices to handle missing files, broken pipes, signal interrupts, and malformed input without silent failures.

## Files to Create/Modify

- `test/run_checks.sh` (new) — Orchestrates parallel ShellCheck runs across all `.sh` files in a target directory, collects exit codes, and produces a pass/fail summary
- `test/format_results.sh` (new) — Reads ShellCheck JSON output from stdin or a file argument, extracts error counts per severity level, and prints a formatted summary table
- `test/ci_setup.sh` (new) — Bootstraps the CI test environment: validates prerequisites, creates a temporary workspace, clones test fixtures, and registers cleanup on exit
- `tests/test_bash_defensive_patterns.py` (new) — Unit tests validating script behavior under normal, error, and edge-case conditions

## Requirements

### Test Runner — `test/run_checks.sh`

- Must begin with `#!/bin/bash` followed by `set -Eeuo pipefail`
- Register an ERR trap that prints the failing line number and script name to stderr in the format `ERROR: run_checks.sh line <N>`
- Accept two positional arguments: `TARGET_DIR` (directory of `.sh` files) and `OUTPUT_DIR` (directory for result files)
- Validate that `TARGET_DIR` exists and is a directory; if not, print `ERROR: Target directory does not exist: <path>` to stderr and exit 1
- Create `OUTPUT_DIR` with `mkdir -p`; if creation fails, exit 1 with a descriptive message
- Use `find ... -print0` and `while IFS= read -r -d ''` to iterate over `.sh` files safely (handling filenames with spaces and special characters)
- For each file, run `shellcheck --format=json` and write output to `OUTPUT_DIR/<basename>.json`
- Track the count of files checked, files with errors, and files passing; print a summary line to stdout: `Checked <N> files: <P> passed, <F> failed`
- If any file check fails, exit with code 1 after processing all files (do not abort on first failure)
- Accept an optional `-j <N>` flag to set the number of parallel jobs (default: 4); use `xargs -0 -P` for parallelization

### Result Formatter — `test/format_results.sh`

- Must begin with `#!/bin/bash` followed by `set -Eeuo pipefail`
- Register an EXIT trap that removes any temporary files created during execution
- Accept input from either stdin (piped) or a single file path argument
- If a file path is given, validate it exists and is readable; if not, print `ERROR: Cannot read file: <path>` to stderr and exit 1
- If no argument is provided and stdin is a terminal (not piped), print a usage message to stderr and exit 1
- Parse ShellCheck JSON output to count findings per severity level: `error`, `warning`, `info`, `style`
- Print a formatted table to stdout with columns `Severity` and `Count`, plus a `Total` row
- If the JSON input is empty (`[]`), print `No issues found.` and exit 0
- If the input is not valid JSON, print `ERROR: Invalid JSON input` to stderr and exit 1

### CI Bootstrap — `test/ci_setup.sh`

- Must begin with `#!/bin/bash` followed by `set -Eeuo pipefail`
- Define a `SCRIPT_DIR` variable using `"$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"`
- Create a temporary working directory using `mktemp -d`; register an EXIT trap that removes this directory with `rm -rf`
- Validate required commands exist (`shellcheck`, `jq`, `git`) using `command -v`; for each missing command, print `ERROR: Required command not found: <cmd>` to stderr and exit 1
- Accept a `--fixtures-repo <URL>` argument for cloning test fixtures into the temp directory; validate the URL is non-empty
- Accept a `--branch <name>` argument (default: `main`) for the fixtures branch
- Clone the repository with `git clone --depth 1 --branch "$BRANCH"` into `$TMPDIR/fixtures`
- Export `SHELLCHECK_TEST_DIR="$TMPDIR/fixtures"` for downstream scripts
- Print `Environment ready: $TMPDIR` to stdout on success
- Implement structured logging functions (`log_info`, `log_error`, `log_debug`) that write timestamps and levels to stderr; `log_debug` must only output when environment variable `DEBUG=1` is set

### Variable and Quoting Safety

- Every variable expansion must be double-quoted (e.g., `"$var"`, `"${array[@]}"`)
- Required variables must be validated at script start using `: "${VAR:?message}"` syntax where applicable
- No use of `eval` or unquoted `$()` in any script
- All `local` variable declarations must use `local -r` for read-only where the value does not change

### Expected Functionality

- `run_checks.sh ./samples ./output` with 5 clean `.sh` files → prints `Checked 5 files: 5 passed, 0 failed`, exit code 0
- `run_checks.sh ./samples ./output` with 2 of 5 files having ShellCheck errors → prints `Checked 5 files: 3 passed, 2 failed`, exit code 1
- `run_checks.sh /nonexistent ./output` → prints error to stderr, exit code 1
- `run_checks.sh ./samples ./output` with a file named `my file (copy).sh` → processes without error
- `echo '[]' | format_results.sh` → prints `No issues found.`
- `echo 'not json' | format_results.sh` → prints `ERROR: Invalid JSON input` to stderr, exit code 1
- `format_results.sh` with no stdin pipe and no argument → prints usage to stderr, exit code 1
- `ci_setup.sh --fixtures-repo https://example.com/repo.git` on a system missing `jq` → prints `ERROR: Required command not found: jq`, exit code 1
- Sending SIGTERM to `ci_setup.sh` mid-execution → temporary directory is cleaned up, no orphaned files remain

## Acceptance Criteria

- All three scripts begin with `#!/bin/bash` and `set -Eeuo pipefail`
- `run_checks.sh` uses null-delimited `find`/`read` for safe filename iteration and does not abort on the first failed check
- `format_results.sh` handles empty JSON arrays, invalid JSON, missing files, and terminal stdin without crashing
- `ci_setup.sh` validates all prerequisites before proceeding, creates and cleans up temp directories via EXIT trap, and exports the fixture path
- Every variable expansion in all scripts is double-quoted
- No script uses `eval` or unquoted command substitution
- Tests in `tests/test_bash_defensive_patterns.py` pass, validating script outputs and exit codes under normal and error scenarios
