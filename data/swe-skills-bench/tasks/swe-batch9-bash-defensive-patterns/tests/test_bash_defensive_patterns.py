"""
Test skill: bash-defensive-patterns
Verify that the Agent creates a Bash library with strict mode, logging,
validation, retry, and other defensive patterns.
"""

import os
import re
import subprocess
import pytest


class TestBashDefensivePatterns:
    REPO_DIR = "/workspace/shellcheck"

    # === File Path Checks ===

    def test_bash_library_files_exist(self):
        """Verify Bash library files exist"""
        expected_names = ["strict", "logging", "validation", "retry"]
        found = 0
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".sh"):
                    for name in expected_names:
                        if name in f.lower():
                            found += 1
                            break
        assert found >= 2, f"Expected at least 2 of the Bash library files, found {found}"

    # === Semantic Checks ===

    def test_strict_mode_enabled(self):
        """Verify strict mode (set -euo pipefail) is used"""
        content = self._collect_sh_content()
        has_strict = "set -euo pipefail" in content or ("set -e" in content and "set -u" in content)
        assert has_strict, "Strict mode (set -euo pipefail) not found"

    def test_logging_functions_defined(self):
        """Verify logging functions are defined"""
        content = self._collect_sh_content()
        content_lower = content.lower()
        has_logging = (
            "log_info" in content_lower
            or "log_error" in content_lower
            or "log_warn" in content_lower
            or "log()" in content
            or "function log" in content
        )
        assert has_logging, "Logging functions not defined"

    def test_validation_functions_defined(self):
        """Verify input validation functions are defined"""
        content = self._collect_sh_content()
        content_lower = content.lower()
        has_validation = (
            "validate" in content_lower
            or "is_valid" in content_lower
            or "check_" in content_lower
            or "assert_" in content_lower
            or "require" in content_lower
        )
        assert has_validation, "Validation functions not defined"

    def test_retry_logic_defined(self):
        """Verify retry/backoff logic is defined"""
        content = self._collect_sh_content()
        content_lower = content.lower()
        has_retry = "retry" in content_lower or "backoff" in content_lower or "attempt" in content_lower
        assert has_retry, "Retry logic not defined"

    def test_error_handling_patterns(self):
        """Verify trap-based error handling is used"""
        content = self._collect_sh_content()
        has_trap = "trap " in content or "trap '" in content or 'trap "' in content
        assert has_trap, "trap-based error handling not found"

    # === Functional Checks ===

    def test_sh_files_valid_syntax(self):
        """Verify Bash files pass syntax check"""
        sh_files = self._find_sh_files()
        assert len(sh_files) > 0, "No relevant Bash files found"
        for sf in sh_files:
            result = subprocess.run(
                ["bash", "-n", sf],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0, f"Syntax error in {sf}: {result.stderr}"

    def test_sh_files_have_shebang(self):
        """Verify Bash files have a shebang line"""
        sh_files = self._find_sh_files()
        for sf in sh_files:
            with open(sf) as fh:
                first_line = fh.readline().strip()
            assert first_line.startswith("#!"), f"{sf} missing shebang line"

    def test_shellcheck_passes(self):
        """Verify Bash files pass shellcheck"""
        sh_files = self._find_sh_files()
        for sf in sh_files:
            result = subprocess.run(
                ["shellcheck", "-S", "warning", sf],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                errors = [l for l in result.stdout.splitlines() if "error" in l.lower() or "warning" in l.lower()]
                assert len(errors) == 0, f"shellcheck issues in {sf}: {errors[:5]}"

    def test_cleanup_on_exit(self):
        """Verify cleanup/exit handler is defined"""
        content = self._collect_sh_content()
        content_lower = content.lower()
        has_cleanup = (
            "cleanup" in content_lower
            or "on_exit" in content_lower
            or "trap.*exit" in content_lower
            or "atexit" in content_lower
        )
        assert has_cleanup, "Cleanup/exit handler not defined"

    def _collect_sh_content(self):
        all_content = ""
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".sh"):
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath) as fh:
                            all_content += fh.read() + "\n"
                    except (UnicodeDecodeError, PermissionError):
                        continue
        return all_content

    def _find_sh_files(self):
        sh_files = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".sh") and any(kw in f.lower() for kw in ["strict", "logging", "validation", "retry", "cleanup", "util", "lib", "common"]):
                    sh_files.append(os.path.join(root, f))
        return sh_files
