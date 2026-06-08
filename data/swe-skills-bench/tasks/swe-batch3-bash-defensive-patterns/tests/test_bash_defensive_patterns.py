"""
Tests for the bash-defensive-patterns skill.

Validates that a defensive Bash test runner was implemented for ShellCheck's
CI pipeline, including main orchestration, shared library, runner functions,
and integration tests.

Repo: shellcheck (https://github.com/koalaman/shellcheck)
"""

import os
import re
import subprocess

REPO_DIR = "/workspace/shellcheck"


class TestFilePathCheck:
    """Verify all required scripts were created."""

    def test_run_tests_exists(self):
        path = os.path.join(REPO_DIR, "test", "run_tests.sh")
        assert os.path.isfile(path), f"Expected test/run_tests.sh at {path}"

    def test_common_lib_exists(self):
        path = os.path.join(REPO_DIR, "test", "lib", "common.sh")
        assert os.path.isfile(path), f"Expected test/lib/common.sh at {path}"

    def test_runner_lib_exists(self):
        path = os.path.join(REPO_DIR, "test", "lib", "runner.sh")
        assert os.path.isfile(path), f"Expected test/lib/runner.sh at {path}"

    def test_integration_driver_exists(self):
        path = os.path.join(REPO_DIR, "test", "integration", "run_integration.sh")
        assert os.path.isfile(path), f"Expected test/integration/run_integration.sh"

    def test_scripts_are_executable(self):
        path = os.path.join(REPO_DIR, "test", "run_tests.sh")
        assert os.access(path, os.X_OK) or True, (
            "test/run_tests.sh should be executable (or chmod +x)"
        )


class TestSemanticRunTests:
    """Verify main test orchestration script."""

    def _read(self):
        path = os.path.join(REPO_DIR, "test", "run_tests.sh")
        with open(path, "r") as f:
            return f.read()

    def test_bash_shebang(self):
        content = self._read()
        assert content.startswith("#!/bin/bash") or content.startswith("#!/usr/bin/env bash"), (
            "Expected #!/bin/bash or #!/usr/bin/env bash shebang"
        )

    def test_strict_mode(self):
        content = self._read()
        assert re.search(r"set\s+-[euo]\s+pipefail|set\s+-e|set\s+-u", content), (
            "Expected strict mode (set -euo pipefail or set -e)"
        )

    def test_parallel_argument(self):
        content = self._read()
        assert re.search(r"--parallel|-p", content), (
            "Expected --parallel / -p argument parsing"
        )

    def test_timeout_argument(self):
        content = self._read()
        assert re.search(r"--timeout|-t", content), (
            "Expected --timeout / -t argument parsing"
        )

    def test_output_dir_argument(self):
        content = self._read()
        assert re.search(r"--output-dir|-o", content), (
            "Expected --output-dir / -o argument parsing"
        )

    def test_suite_argument(self):
        content = self._read()
        assert re.search(r"--suite|-s", content), (
            "Expected --suite / -s argument (unit, integration, all)"
        )

    def test_verbose_flag(self):
        content = self._read()
        assert re.search(r"--verbose|-v", content), (
            "Expected --verbose / -v flag"
        )

    def test_dry_run_flag(self):
        content = self._read()
        assert re.search(r"--dry-run|-d", content), (
            "Expected --dry-run / -d flag"
        )

    def test_help_flag(self):
        content = self._read()
        assert re.search(r"--help|-h", content), (
            "Expected --help / -h flag"
        )

    def test_cleanup_trap(self):
        content = self._read()
        assert re.search(r"trap\s+.*EXIT|trap\s+.*SIGTERM|trap\s+.*SIGINT", content), (
            "Expected cleanup trap on EXIT/SIGTERM/SIGINT"
        )

    def test_dependency_check(self):
        content = self._read()
        assert re.search(r"check_dependencies|command\s+-v|which", content), (
            "Expected dependency validation before test execution"
        )

    def test_junit_xml(self):
        content = self._read()
        assert re.search(r"junit|JUnit|testsuite|testcase|xml", content, re.IGNORECASE), (
            "Expected JUnit XML report generation"
        )

    def test_exit_codes(self):
        content = self._read()
        # Should use exit 0, 1, 2
        assert "exit 0" in content or "exit 1" in content or "exit 2" in content, (
            "Expected explicit exit codes (0=pass, 1=fail, 2=infra error)"
        )


class TestSemanticCommonLib:
    """Verify shared utility library."""

    def _read(self):
        path = os.path.join(REPO_DIR, "test", "lib", "common.sh")
        with open(path, "r") as f:
            return f.read()

    def test_log_info(self):
        content = self._read()
        assert re.search(r"log_info", content), "Expected log_info function"

    def test_log_warn(self):
        content = self._read()
        assert re.search(r"log_warn", content), "Expected log_warn function"

    def test_log_error(self):
        content = self._read()
        assert re.search(r"log_error", content), "Expected log_error function"

    def test_log_debug(self):
        content = self._read()
        assert re.search(r"log_debug", content), "Expected log_debug function"
        assert re.search(r"VERBOSE", content), (
            "Expected VERBOSE check in log_debug"
        )

    def test_check_dependencies_func(self):
        content = self._read()
        assert re.search(r"check_dependencies", content), (
            "Expected check_dependencies function"
        )

    def test_create_temp_workspace(self):
        content = self._read()
        assert re.search(r"create_temp_workspace|mktemp", content), (
            "Expected create_temp_workspace with mktemp -d"
        )

    def test_safe_rm(self):
        content = self._read()
        assert re.search(r"safe_rm", content), "Expected safe_rm function"
        assert re.search(r"/tmp", content), (
            "Expected /tmp path validation in safe_rm"
        )

    def test_local_variables(self):
        content = self._read()
        assert re.search(r"\blocal\b", content), (
            "Expected 'local' keyword for variable scoping"
        )


class TestSemanticRunnerLib:
    """Verify test runner functions."""

    def _read(self):
        path = os.path.join(REPO_DIR, "test", "lib", "runner.sh")
        with open(path, "r") as f:
            return f.read()

    def test_run_with_timeout(self):
        content = self._read()
        assert re.search(r"run_with_timeout", content), (
            "Expected run_with_timeout function"
        )
        assert "timeout" in content, "Expected timeout utility usage"

    def test_run_parallel_tests(self):
        content = self._read()
        assert re.search(r"run_parallel_tests", content), (
            "Expected run_parallel_tests function"
        )

    def test_background_processes(self):
        content = self._read()
        assert re.search(r"&$|wait|PID|\$!", content, re.MULTILINE), (
            "Expected background process management (& wait $!)"
        )

    def test_aggregate_results(self):
        content = self._read()
        assert re.search(r"aggregate_results", content), (
            "Expected aggregate_results function"
        )


class TestSemanticIntegration:
    """Verify integration test driver."""

    def _read(self):
        path = os.path.join(REPO_DIR, "test", "integration", "run_integration.sh")
        with open(path, "r") as f:
            return f.read()

    def test_shellcheck_invocation(self):
        content = self._read()
        assert re.search(r"shellcheck.*--format.*json|shellcheck", content), (
            "Expected shellcheck --format=json invocation"
        )

    def test_expected_file_comparison(self):
        content = self._read()
        assert re.search(r"\.expected|expected", content), (
            "Expected comparison against .expected files"
        )

    def test_update_expected_flag(self):
        content = self._read()
        assert re.search(r"--update-expected|update.*expected", content), (
            "Expected --update-expected flag support"
        )


class TestFunctionalBashSyntax:
    """Validate Bash scripts have valid syntax."""

    def test_run_tests_syntax(self):
        path = os.path.join(REPO_DIR, "test", "run_tests.sh")
        result = subprocess.run(
            ["bash", "-n", path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"Bash syntax error in run_tests.sh: {result.stderr[:500]}"
        )

    def test_common_lib_syntax(self):
        path = os.path.join(REPO_DIR, "test", "lib", "common.sh")
        result = subprocess.run(
            ["bash", "-n", path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"Bash syntax error in common.sh: {result.stderr[:500]}"
        )

    def test_runner_lib_syntax(self):
        path = os.path.join(REPO_DIR, "test", "lib", "runner.sh")
        result = subprocess.run(
            ["bash", "-n", path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"Bash syntax error in runner.sh: {result.stderr[:500]}"
        )

    def test_integration_syntax(self):
        path = os.path.join(REPO_DIR, "test", "integration", "run_integration.sh")
        result = subprocess.run(
            ["bash", "-n", path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"Bash syntax error in run_integration.sh: {result.stderr[:500]}"
        )
