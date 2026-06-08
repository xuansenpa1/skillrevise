"""
Test skill: bash-defensive-patterns
Verify that the Agent creates defensive Bash script examples with
strict error modes, trap cleanup, safe variable expansion, input
validation, and ShellCheck compliance.
"""

import os
import re
import subprocess
import pytest


class TestBashDefensivePatterns:
    REPO_DIR = "/workspace/shellcheck"

    # === File Path Checks ===

    def test_defensive_example_exists(self):
        """Verify test/defensive_example.sh exists"""
        path = os.path.join(self.REPO_DIR, "test/defensive_example.sh")
        assert os.path.exists(path), (
            f"defensive_example.sh not found at {path}"
        )

    def test_safe_io_exists(self):
        """Verify test/safe_io.sh exists"""
        path = os.path.join(self.REPO_DIR, "test/safe_io.sh")
        assert os.path.exists(path), f"safe_io.sh not found at {path}"

    # === Semantic Checks ===

    def test_strict_error_modes(self):
        """Verify set -euo pipefail is used"""
        path = os.path.join(self.REPO_DIR, "test/defensive_example.sh")
        with open(path) as f:
            content = f.read()

        strict_indicators = [
            "set -e", "set -u", "set -o pipefail", "set -euo pipefail",
        ]
        found = [ind for ind in strict_indicators if ind in content]
        assert len(found) >= 1, (
            f"Should use strict error modes. Found: {found}"
        )

    def test_trap_cleanup(self):
        """Verify trap-based cleanup is implemented"""
        path = os.path.join(self.REPO_DIR, "test/defensive_example.sh")
        with open(path) as f:
            content = f.read()

        assert "trap" in content, (
            "Should implement trap-based cleanup"
        )
        trap_indicators = ["EXIT", "ERR", "INT", "TERM", "cleanup"]
        found = [ind for ind in trap_indicators if ind in content]
        assert len(found) >= 1, (
            f"Trap should handle signals. Found: {found}"
        )

    def test_quoted_variable_expansions(self):
        """Verify variables are properly quoted"""
        for fname in ["defensive_example.sh", "safe_io.sh"]:
            path = os.path.join(self.REPO_DIR, f"test/{fname}")
            with open(path) as f:
                content = f.read()

            # Count unquoted vs quoted variable references
            quoted = len(re.findall(r'"[^"]*\$\{?\w+', content))
            assert quoted >= 2, (
                f"{fname} should quote variable expansions. "
                f"Found {quoted} quoted references"
            )

    def test_default_values(self):
        """Verify ${var:-default} pattern for fallback values"""
        combined = ""
        for fname in ["defensive_example.sh", "safe_io.sh"]:
            path = os.path.join(self.REPO_DIR, f"test/{fname}")
            with open(path) as f:
                combined += f.read()

        default_pattern = re.findall(r"\$\{[^}]+:-[^}]+\}", combined)
        assert len(default_pattern) >= 1, (
            "Should use ${var:-default} for fallback values"
        )

    def test_argument_validation(self):
        """Verify command-line argument validation"""
        path = os.path.join(self.REPO_DIR, "test/safe_io.sh")
        with open(path) as f:
            content = f.read()

        validation_indicators = [
            "$#", "argc", "args", "-z", "-n", "usage",
            "if [", "test ", "exit 1",
        ]
        found = [ind for ind in validation_indicators if ind in content]
        assert len(found) >= 2, (
            f"Should validate arguments. Found: {found}"
        )

    def test_path_sanitization(self):
        """Verify file path sanitization"""
        path = os.path.join(self.REPO_DIR, "test/safe_io.sh")
        with open(path) as f:
            content = f.read()

        sanitize_indicators = [
            "realpath", "readlink", "basename", "dirname",
            "..", "traversal", "sanitiz", "canonical",
        ]
        found = [ind for ind in sanitize_indicators if ind in content.lower()]
        assert len(found) >= 1, (
            f"Should sanitize file paths. Found: {found}"
        )

    def test_file_existence_checks(self):
        """Verify file existence and permission checks before operations"""
        path = os.path.join(self.REPO_DIR, "test/safe_io.sh")
        with open(path) as f:
            content = f.read()

        check_indicators = [
            "-f ", "-d ", "-e ", "-r ", "-w ", "-x ",
            "test -", "[ -",
        ]
        found = [ind for ind in check_indicators if ind in content]
        assert len(found) >= 2, (
            f"Should check file existence/permissions. Found: {found}"
        )

    def test_shebang_line(self):
        """Verify both scripts have a shebang line"""
        for fname in ["defensive_example.sh", "safe_io.sh"]:
            path = os.path.join(self.REPO_DIR, f"test/{fname}")
            with open(path) as f:
                first_line = f.readline()

            assert first_line.startswith("#!"), (
                f"{fname} should have a shebang line"
            )

    # === Functional Checks ===

    def test_shellcheck_defensive_example(self):
        """Verify defensive_example.sh passes ShellCheck"""
        path = os.path.join(self.REPO_DIR, "test/defensive_example.sh")
        result = subprocess.run(
            ["shellcheck", "--severity=warning", path],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            # Only fail if shellcheck is available
            if "not found" not in result.stderr.lower():
                pytest.fail(
                    f"ShellCheck warnings in defensive_example.sh: "
                    f"{result.stdout[:500]}"
                )

    def test_shellcheck_safe_io(self):
        """Verify safe_io.sh passes ShellCheck"""
        path = os.path.join(self.REPO_DIR, "test/safe_io.sh")
        result = subprocess.run(
            ["shellcheck", "--severity=warning", path],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            if "not found" not in result.stderr.lower():
                pytest.fail(
                    f"ShellCheck warnings in safe_io.sh: "
                    f"{result.stdout[:500]}"
                )

    def test_bash_syntax_valid(self):
        """Verify scripts pass bash -n syntax check"""
        for fname in ["defensive_example.sh", "safe_io.sh"]:
            path = os.path.join(self.REPO_DIR, f"test/{fname}")
            result = subprocess.run(
                ["bash", "-n", path],
                capture_output=True, text=True, timeout=15,
            )
            assert result.returncode == 0, (
                f"{fname} has syntax errors: {result.stderr}"
            )
