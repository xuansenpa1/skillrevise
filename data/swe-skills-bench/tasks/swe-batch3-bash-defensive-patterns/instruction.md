# SWE-Skills-Bench: bash-defensive-patterns (batch3)

# Task: Create a Defensive Bash Test Runner Script for ShellCheck's CI Pipeline

## Background

ShellCheck (https://github.com/koalaman/shellcheck) is a static analysis tool for shell scripts, primarily written in Haskell. The project's build and test infrastructure uses simple shell scripts (`quickrun`, `quicktest`, `striptests`) for development convenience, but lacks a robust, production-grade CI test runner that can handle complex scenarios like parallel test execution, result aggregation, temporary workspace management, and graceful failure handling. A new comprehensive test orchestration script is needed to run ShellCheck's Cabal test suite alongside integration tests against sample shell scripts, with proper error handling, logging, and reporting.

## Files to Create/Modify

- `test/run_tests.sh` (create) — Main test orchestration script: argument parsing, environment validation, parallel test execution, result aggregation, and structured reporting
- `test/lib/common.sh` (create) — Shared library of utility functions: logging, temporary directory management, cleanup traps, dependency checking
- `test/lib/runner.sh` (create) — Test runner functions: execute individual test suites, capture output, handle timeouts, collect exit codes
- `test/integration/run_integration.sh` (create) — Integration test driver: runs ShellCheck binary against sample scripts in `test/integration/samples/` and validates expected output

## Requirements

### Main Test Script (`test/run_tests.sh`)

- Must start with `#!/bin/bash` and enable strict mode
- Accept command-line arguments: `--parallel` / `-p` (number of parallel jobs, default: number of CPU cores), `--timeout` / `-t` (per-test timeout in seconds, default: 300), `--output-dir` / `-o` (directory for test reports, default: `./test-results`), `--suite` / `-s` (which suite to run: `unit`, `integration`, `all`; default: `all`), `--verbose` / `-v` (enable debug logging), `--dry-run` / `-d` (print what would be executed without running), and `--help` / `-h`
- Validate all required external commands exist before starting (`cabal`, `shellcheck`, `timeout`, `mktemp`, `tee`, `date`) and exit with a clear error listing all missing dependencies
- Create a temporary workspace directory and register a cleanup trap that removes it on EXIT, SIGTERM, and SIGINT
- Detect the script's own directory reliably regardless of how the script is invoked (symlinks, relative paths, `source`)
- Generate a JUnit XML report in `--output-dir` containing one `<testsuite>` per suite and one `<testcase>` per individual test, with `<failure>` elements for failed tests including captured stderr
- Exit with code 0 if all tests pass, 1 if any test fails, and 2 if setup or infrastructure errors occur

### Shared Library (`test/lib/common.sh`)

- Provide logging functions (`log_info`, `log_warn`, `log_error`, `log_debug`) that write timestamped messages to stderr; `log_debug` should only produce output when `VERBOSE=1`
- Provide `check_dependencies()` that accepts an array of command names and returns a list of missing ones
- Provide `create_temp_workspace()` that creates a `mktemp -d` directory and echoes its path; the caller must register cleanup
- Provide `safe_rm()` that validates the path is under `/tmp` or the workspace before deleting, to prevent accidental deletion of system directories
- All functions must use `local` for variables and handle unset variables gracefully (no unbound variable errors in strict mode)

### Test Runner Functions (`test/lib/runner.sh`)

- Provide `run_with_timeout()` that wraps a command with the `timeout` utility, captures stdout and stderr to separate files, and returns the exit code
- Provide `run_parallel_tests()` that accepts an array of test commands and a job limit, executes them in parallel using background processes, tracks PIDs, waits for completion, and collects results
- If any background process is killed by a signal, record it as a failure with the signal name
- Provide `aggregate_results()` that reads individual test result files and produces a summary: total, passed, failed, errored, skipped, and wall-clock duration

### Integration Tests (`test/integration/run_integration.sh`)

- Scan `test/integration/samples/` for `.sh` files
- For each sample script, run `shellcheck --format=json` and compare the output against a corresponding `.expected` file in the same directory
- A test passes if the set of ShellCheck warning codes in the output matches the set in the expected file (order-independent comparison)
- Handle the case where the sample script does not exist, the expected file is missing, or ShellCheck produces no output
- Support a `--update-expected` flag that overwrites `.expected` files with actual output (for maintaining test fixtures)

### Expected Functionality

- Running `test/run_tests.sh --suite unit` executes only the Cabal test suite and produces a JUnit XML report with results
- Running `test/run_tests.sh --suite integration` runs only the integration tests against sample scripts
- Running `test/run_tests.sh --suite all --parallel 4` runs both suites, limiting parallel jobs to 4
- Running `test/run_tests.sh --dry-run` prints all commands that would be executed without actually running them
- If `cabal` is not installed, the script exits with code 2 and a message listing `cabal` as a missing dependency
- If a test hangs beyond `--timeout`, it is killed and reported as a failure with a timeout message
- If the user presses Ctrl+C during execution, all background test processes are terminated, temporary files are cleaned up, and a partial report is written
- A sample script with known ShellCheck warnings (e.g., unquoted variables, unused variables) produces the expected set of warning codes in integration tests

## Acceptance Criteria

- All four scripts are syntactically valid Bash that passes ShellCheck itself without errors at the default severity level
- `test/run_tests.sh` correctly parses all specified arguments and rejects unknown flags with a usage message
- Temporary directories are always cleaned up on normal exit, error exit, SIGTERM, and SIGINT
- Dependency checking detects and reports all missing commands before any test execution begins
- Parallel test execution respects the `--parallel` job limit and correctly collects results from all child processes
- The JUnit XML output is well-formed and contains accurate pass/fail/error counts
- Integration tests correctly compare ShellCheck output codes against expected files in an order-independent manner
- `--dry-run` mode produces no side effects (no files created, no commands executed)
- `safe_rm()` refuses to delete paths outside of `/tmp` or the designated workspace directory
