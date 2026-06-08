"""
Test skill: bash-defensive-patterns
Verify that the Agent correctly implements defensive wrapper scripts
for the ShellCheck test harness.
"""

import os
import re
import subprocess
import pytest


class TestBashDefensivePatterns:
    REPO_DIR = "/workspace/shellcheck"

    # === File Path Checks ===

    def test_run_checks_exists(self):
        """Verify test/run_checks.sh was created"""
        path = os.path.join(self.REPO_DIR, "test/run_checks.sh")
        assert os.path.exists(path), "run_checks.sh not found"

    def test_format_results_exists(self):
        """Verify test/format_results.sh was created"""
        path = os.path.join(self.REPO_DIR, "test/format_results.sh")
        assert os.path.exists(path), "format_results.sh not found"

    def test_ci_setup_exists(self):
        """Verify test/ci_setup.sh was created"""
        path = os.path.join(self.REPO_DIR, "test/ci_setup.sh")
        assert os.path.exists(path), "ci_setup.sh not found"

    # === Semantic Checks: run_checks.sh ===

    def test_run_checks_shebang(self):
        """Verify shebang and set -Eeuo pipefail"""
        path = os.path.join(self.REPO_DIR, "test/run_checks.sh")
        with open(path) as f:
            content = f.read()
        assert content.startswith("#!/bin/bash"), "Should start with #!/bin/bash"
        assert "set -Eeuo pipefail" in content, "Should have set -Eeuo pipefail"

    def test_run_checks_err_trap(self):
        """Verify ERR trap is registered"""
        path = os.path.join(self.REPO_DIR, "test/run_checks.sh")
        with open(path) as f:
            content = f.read()
        assert "trap" in content and "ERR" in content, "Should register ERR trap"

    def test_run_checks_null_delimited_find(self):
        """Verify find with -print0 and read -d ''"""
        path = os.path.join(self.REPO_DIR, "test/run_checks.sh")
        with open(path) as f:
            content = f.read()
        assert "-print0" in content, "Should use find -print0"
        assert 'read -r -d' in content or "read -r -d ''" in content, (
            "Should use read -r -d '' for null-delimited"
        )

    def test_run_checks_validates_target_dir(self):
        """Verify TARGET_DIR validation"""
        path = os.path.join(self.REPO_DIR, "test/run_checks.sh")
        with open(path) as f:
            content = f.read()
        assert "Target directory" in content or "-d" in content, (
            "Should validate TARGET_DIR exists and is a directory"
        )

    def test_run_checks_summary_output(self):
        """Verify summary line format"""
        path = os.path.join(self.REPO_DIR, "test/run_checks.sh")
        with open(path) as f:
            content = f.read()
        assert "Checked" in content and "passed" in content and "failed" in content, (
            "Should print summary: Checked N files: P passed, F failed"
        )

    def test_run_checks_parallel_flag(self):
        """Verify -j flag for parallel jobs"""
        path = os.path.join(self.REPO_DIR, "test/run_checks.sh")
        with open(path) as f:
            content = f.read()
        assert "xargs" in content or "-j" in content, (
            "Should support -j flag for parallel execution"
        )

    # === Semantic Checks: format_results.sh ===

    def test_format_results_shebang(self):
        """Verify shebang and set -Eeuo pipefail"""
        path = os.path.join(self.REPO_DIR, "test/format_results.sh")
        with open(path) as f:
            content = f.read()
        assert content.startswith("#!/bin/bash"), "Should start with #!/bin/bash"
        assert "set -Eeuo pipefail" in content, "Should have set -Eeuo pipefail"

    def test_format_results_exit_trap(self):
        """Verify EXIT trap for cleanup"""
        path = os.path.join(self.REPO_DIR, "test/format_results.sh")
        with open(path) as f:
            content = f.read()
        assert "trap" in content and "EXIT" in content, "Should register EXIT trap"

    def test_format_results_severity_levels(self):
        """Verify parsing of error, warning, info, style severities"""
        path = os.path.join(self.REPO_DIR, "test/format_results.sh")
        with open(path) as f:
            content = f.read()
        for level in ["error", "warning", "info", "style"]:
            assert level in content, f"Should parse '{level}' severity"

    def test_format_results_empty_json(self):
        """Verify 'No issues found.' for empty JSON"""
        path = os.path.join(self.REPO_DIR, "test/format_results.sh")
        with open(path) as f:
            content = f.read()
        assert "No issues found" in content, (
            "Should print 'No issues found.' for empty JSON"
        )

    def test_format_results_invalid_json(self):
        """Verify error handling for invalid JSON"""
        path = os.path.join(self.REPO_DIR, "test/format_results.sh")
        with open(path) as f:
            content = f.read()
        assert "Invalid JSON" in content, (
            "Should print 'ERROR: Invalid JSON input'"
        )

    def test_format_results_stdin_check(self):
        """Verify terminal stdin detection"""
        path = os.path.join(self.REPO_DIR, "test/format_results.sh")
        with open(path) as f:
            content = f.read()
        assert "-t 0" in content or "-t 1" in content, (
            "Should check if stdin is a terminal"
        )

    # === Semantic Checks: ci_setup.sh ===

    def test_ci_setup_shebang(self):
        """Verify shebang and set -Eeuo pipefail"""
        path = os.path.join(self.REPO_DIR, "test/ci_setup.sh")
        with open(path) as f:
            content = f.read()
        assert content.startswith("#!/bin/bash"), "Should start with #!/bin/bash"
        assert "set -Eeuo pipefail" in content, "Should have set -Eeuo pipefail"

    def test_ci_setup_script_dir(self):
        """Verify SCRIPT_DIR definition"""
        path = os.path.join(self.REPO_DIR, "test/ci_setup.sh")
        with open(path) as f:
            content = f.read()
        assert "SCRIPT_DIR" in content, "Should define SCRIPT_DIR"
        assert "BASH_SOURCE" in content, "Should use BASH_SOURCE"

    def test_ci_setup_mktemp(self):
        """Verify mktemp -d for temporary directory"""
        path = os.path.join(self.REPO_DIR, "test/ci_setup.sh")
        with open(path) as f:
            content = f.read()
        assert "mktemp -d" in content, "Should use mktemp -d"

    def test_ci_setup_exit_trap_cleanup(self):
        """Verify EXIT trap removes temp directory"""
        path = os.path.join(self.REPO_DIR, "test/ci_setup.sh")
        with open(path) as f:
            content = f.read()
        assert "trap" in content and "EXIT" in content, "Should register EXIT trap"
        assert "rm -rf" in content, "Should cleanup temp dir with rm -rf"

    def test_ci_setup_command_v_checks(self):
        """Verify command -v checks for required commands"""
        path = os.path.join(self.REPO_DIR, "test/ci_setup.sh")
        with open(path) as f:
            content = f.read()
        assert "command -v" in content, "Should use command -v for validation"
        for cmd in ["shellcheck", "jq", "git"]:
            assert cmd in content, f"Should check for {cmd}"

    def test_ci_setup_fixtures_repo(self):
        """Verify --fixtures-repo argument handling"""
        path = os.path.join(self.REPO_DIR, "test/ci_setup.sh")
        with open(path) as f:
            content = f.read()
        assert "fixtures-repo" in content, "Should accept --fixtures-repo"

    def test_ci_setup_logging_functions(self):
        """Verify log_info, log_error, log_debug functions"""
        path = os.path.join(self.REPO_DIR, "test/ci_setup.sh")
        with open(path) as f:
            content = f.read()
        assert "log_info" in content, "Should define log_info"
        assert "log_error" in content, "Should define log_error"
        assert "log_debug" in content, "Should define log_debug"
        assert "DEBUG" in content, "log_debug should check DEBUG env var"

    def test_ci_setup_exports_test_dir(self):
        """Verify SHELLCHECK_TEST_DIR is exported"""
        path = os.path.join(self.REPO_DIR, "test/ci_setup.sh")
        with open(path) as f:
            content = f.read()
        assert "SHELLCHECK_TEST_DIR" in content, (
            "Should export SHELLCHECK_TEST_DIR"
        )

    # === Semantic Checks: Variable quoting ===

    def test_no_eval_usage(self):
        """Verify no eval in any script"""
        for script in ["test/run_checks.sh", "test/format_results.sh", "test/ci_setup.sh"]:
            path = os.path.join(self.REPO_DIR, script)
            with open(path) as f:
                content = f.read()
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                assert not re.search(r'\beval\b', stripped), (
                    f"{script} line {i}: should not use eval"
                )

    # === Functional Checks ===

    def test_scripts_are_executable_or_valid_bash(self):
        """Verify all scripts have valid bash syntax"""
        for script in ["test/run_checks.sh", "test/format_results.sh", "test/ci_setup.sh"]:
            path = os.path.join(self.REPO_DIR, script)
            result = subprocess.run(
                ["bash", "-n", path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0, (
                f"{script} has bash syntax error:\n{result.stderr}"
            )

    def test_run_checks_nonexistent_dir(self):
        """Verify run_checks.sh exits 1 for nonexistent directory"""
        path = os.path.join(self.REPO_DIR, "test/run_checks.sh")
        result = subprocess.run(
            ["bash", path, "/nonexistent_dir_xyz", "/tmp/output"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 1, (
            "Should exit 1 for nonexistent directory"
        )

    def test_format_results_empty_json(self):
        """Verify format_results.sh handles empty JSON array"""
        path = os.path.join(self.REPO_DIR, "test/format_results.sh")
        result = subprocess.run(
            ["bash", path],
            input="[]",
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, "Should exit 0 for empty JSON"
        assert "No issues found" in result.stdout, (
            "Should print 'No issues found.'"
        )

    def test_format_results_invalid_json(self):
        """Verify format_results.sh rejects invalid JSON"""
        path = os.path.join(self.REPO_DIR, "test/format_results.sh")
        result = subprocess.run(
            ["bash", path],
            input="not json",
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 1, "Should exit 1 for invalid JSON"
        assert "Invalid JSON" in result.stderr, (
            "Should print error about invalid JSON"
        )
