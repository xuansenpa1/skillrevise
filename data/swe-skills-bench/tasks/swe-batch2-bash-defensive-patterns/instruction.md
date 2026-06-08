# SWE-Skills-Bench: bash-defensive-patterns (batch2)

# Task: Create Defensive Bash Script Examples for ShellCheck

## Background

ShellCheck (https://github.com/koalaman/shellcheck) is a static analysis tool for shell scripts. New example scripts are needed under `test/` that demonstrate defensive Bash programming patterns — proper error handling, safe variable expansion, input validation, and portable command usage — and pass ShellCheck's analysis without warnings.

## Files to Create

- `test/defensive_example.sh` — Demonstrates error handling, safe variable expansion, and trap-based cleanup
- `test/safe_io.sh` — Demonstrates input validation, path sanitization, and portable command usage

## Requirements

### Error Handling

- Use `set -euo pipefail` for strict error modes
- Implement trap-based cleanup for temporary files and resources
- Handle command failures explicitly rather than relying solely on `set -e`

### Safe Variable Usage

- Quote all variable expansions to prevent word splitting and globbing
- Use `${var:-default}` for variables with fallback values
- Validate required variables early and exit with informative messages if missing

### Input Validation

- Validate command-line arguments (count, type, range) before use
- Sanitize file paths to prevent directory traversal
- Check file existence and permissions before operations

### Portability

- Avoid Bash-only features where POSIX alternatives exist, or explicitly declare `#!/bin/bash`
- Use portable command options and avoid undefined behavior

### ShellCheck Compliance

- All scripts must pass `shellcheck --severity=warning` without violations

## Expected Functionality

- Each script demonstrates one or more defensive patterns clearly
- Running the scripts with expected inputs succeeds
- Running the scripts with missing or invalid inputs produces helpful error messages and clean exits

## Acceptance Criteria

- The example scripts clearly demonstrate strict error handling, safe variable expansion, argument validation, and cleanup behavior.
- Running the scripts with valid inputs succeeds and performs the documented action.
- Running the scripts with invalid or missing inputs produces clear error messages and exits safely.
- File path handling and command usage avoid common shell safety problems such as unquoted expansions and unsafe path traversal.
- The scripts are written in a style that is compatible with ShellCheck's defensive scripting expectations.
