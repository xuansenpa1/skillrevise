# SWE-Skills-Bench: bash-defensive-patterns (batch1)

# Task: Add Defensive Bash Scripts to ShellCheck Test Suite

## Background

Add example shell scripts to the ShellCheck repository's `test/` directory that demonstrate robust, production-quality Bash patterns and pass ShellCheck analysis without warnings.

## Files to Create/Modify

- `test/safe_backup.sh` - Backup script demonstrating defensive coding
- `test/common_utils.sh` - Reusable utility functions library
- `test/test_scripts.bats` - BATS test suite for the scripts (optional)

## Requirements

### safe_backup.sh
- `set -euo pipefail` at script start
- Proper quoting of all variable expansions
- `trap` for cleanup on `EXIT` / `ERR`
- Input validation for directory arguments
- Meaningful exit codes on errors

### common_utils.sh
- Logging functions (info, warn, error)
- Error handling helpers
- Argument parsing template using `getopts` or manual parsing

### Static Analysis
- Both `.sh` files must pass `shellcheck --severity=warning` with exit code 0
- Consistent formatting (shfmt-compatible)

## Acceptance Criteria

- `shellcheck --severity=warning test/*.sh` exits with code 0
- Scripts demonstrate defensive coding patterns
- Utility functions are reusable and well-structured
