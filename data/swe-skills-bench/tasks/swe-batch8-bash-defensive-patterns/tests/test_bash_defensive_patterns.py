"""
Tests for the bash-defensive-patterns skill.
Validates a defensive Bash script library with strict mode, error trapping,
atomic file operations, lock management, input validation, and deploy script.
"""

import os
import re
import subprocess

REPO_DIR = "/workspace/shellcheck"
LIB_DIR = os.path.join(REPO_DIR, "test", "scripts", "lib")


class TestBashDefensivePatterns:
    """Tests for the defensive Bash script library."""

    # ── file_path_check ──────────────────────────────────────────────

    def test_defensive_utils_exists(self):
        """Core defensive_utils.sh library must exist."""
        path = os.path.join(LIB_DIR, "defensive_utils.sh")
        assert os.path.isfile(path), f"Missing {path}"

    def test_file_ops_exists(self):
        """File operations library must exist."""
        path = os.path.join(LIB_DIR, "file_ops.sh")
        assert os.path.isfile(path), f"Missing {path}"

    def test_lock_manager_exists(self):
        """Lock manager library must exist."""
        path = os.path.join(LIB_DIR, "lock_manager.sh")
        assert os.path.isfile(path), f"Missing {path}"

    def test_input_validator_exists(self):
        """Input validator library must exist."""
        path = os.path.join(LIB_DIR, "input_validator.sh")
        assert os.path.isfile(path), f"Missing {path}"

    def test_deploy_script_exists(self):
        """Deploy script must exist."""
        path = os.path.join(REPO_DIR, "test", "scripts", "deploy.sh")
        assert os.path.isfile(path), f"Missing {path}"

    # ── semantic_check ───────────────────────────────────────────────

    def _read(self, rel_path):
        path = os.path.join(REPO_DIR, "test", "scripts", rel_path)
        if not os.path.isfile(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_strict_mode(self):
        """defensive_utils.sh must set strict mode with -Eeuo pipefail."""
        content = self._read("lib/defensive_utils.sh")
        assert re.search(r"set\s+-[Eeuo]+\s*pipefail|set\s+-E.*-e.*-u.*-o\s*pipefail", content), (
            "Strict mode (set -Eeuo pipefail) not found"
        )

    def test_error_trap(self):
        """defensive_utils.sh must set up ERR trap with BASH_COMMAND and LINENO."""
        content = self._read("lib/defensive_utils.sh")
        assert re.search(r"trap\s+.*ERR", content), "ERR trap not found"
        assert "BASH_COMMAND" in content, "BASH_COMMAND not referenced in error trap"
        assert "LINENO" in content, "LINENO not referenced in error trap"

    def test_cleanup_trap(self):
        """defensive_utils.sh must register EXIT trap for cleanup."""
        content = self._read("lib/defensive_utils.sh")
        assert re.search(r"trap\s+.*EXIT", content), "EXIT trap not found"
        assert re.search(r"register_cleanup|cleanup", content), "Cleanup registration not found"

    def test_atomic_write_function(self):
        """file_ops.sh must define atomic_write using temp file + mv."""
        content = self._read("lib/file_ops.sh")
        assert re.search(r"atomic_write", content), "atomic_write function not found"
        assert re.search(r"mktemp|tmp", content, re.IGNORECASE), "Temp file usage not found"
        assert re.search(r"\bmv\b", content), "mv command not found (needed for atomic write)"

    def test_safe_remove_protection(self):
        """file_ops.sh must protect dangerous paths from removal."""
        content = self._read("lib/file_ops.sh")
        assert "safe_remove" in content, "safe_remove function not found"
        for path in ["/etc", "/usr", "/var"]:
            assert path in content, f"Protected path '{path}' not listed in safe_remove"

    def test_lock_acquire_and_release(self):
        """lock_manager.sh must define acquire_lock and release_lock."""
        content = self._read("lib/lock_manager.sh")
        assert re.search(r"acquire_lock", content), "acquire_lock function not found"
        assert re.search(r"release_lock", content), "release_lock function not found"

    def test_stale_lock_detection(self):
        """lock_manager.sh must detect stale locks from dead processes."""
        content = self._read("lib/lock_manager.sh")
        assert re.search(r"stale|kill\s+-0|/proc/", content, re.IGNORECASE), (
            "Stale lock detection not found"
        )

    def test_input_validation_functions(self):
        """input_validator.sh must define validation functions."""
        content = self._read("lib/input_validator.sh")
        for func in ["validate_not_empty", "validate_integer", "validate_ip", "sanitize_input"]:
            assert func in content, f"{func} function not found"

    def test_deploy_argument_parsing(self):
        """deploy.sh must parse --app-name, --version, --target-dir arguments."""
        content = self._read("deploy.sh")
        for arg in ["--app-name", "--version", "--target-dir"]:
            assert arg in content, f"Argument '{arg}' not handled in deploy.sh"

    # ── functional_check ─────────────────────────────────────────────

    def test_bash_syntax_valid(self):
        """All shell scripts must have valid bash syntax."""
        scripts = [
            os.path.join(LIB_DIR, "defensive_utils.sh"),
            os.path.join(LIB_DIR, "file_ops.sh"),
            os.path.join(LIB_DIR, "lock_manager.sh"),
            os.path.join(LIB_DIR, "input_validator.sh"),
            os.path.join(REPO_DIR, "test", "scripts", "deploy.sh"),
        ]
        errors = []
        for script in scripts:
            if not os.path.isfile(script):
                continue
            result = subprocess.run(
                ["bash", "-n", script],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                errors.append(f"{script}: {result.stderr.strip()}")
        assert not errors, "Bash syntax errors:\n" + "\n".join(errors)

    def test_ip_validation_regex(self):
        """input_validator.sh must validate IPv4 format with octet range check."""
        content = self._read("lib/input_validator.sh")
        assert re.search(r"[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+|25[0-5]|2[0-4]|[01]?[0-9]", content), (
            "IPv4 validation regex not found"
        )

    def test_semver_validation_in_deploy(self):
        """deploy.sh must validate version matches semver pattern."""
        content = self._read("deploy.sh")
        assert re.search(r"[0-9]+\.[0-9]+\.[0-9]+|semver", content, re.IGNORECASE), (
            "Semver validation not found in deploy.sh"
        )

    def test_health_check_in_deploy(self):
        """deploy.sh must perform health check with curl."""
        content = self._read("deploy.sh")
        assert re.search(r"curl|health|health.url", content, re.IGNORECASE), (
            "Health check (curl) not found in deploy.sh"
        )

    def test_rollback_in_deploy(self):
        """deploy.sh must support rollback on failure."""
        content = self._read("deploy.sh")
        assert re.search(r"rollback|restore|backup", content, re.IGNORECASE), (
            "Rollback support not found in deploy.sh"
        )
