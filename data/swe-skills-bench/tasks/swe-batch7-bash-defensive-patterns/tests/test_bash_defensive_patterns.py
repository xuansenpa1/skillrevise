"""
Test skill: bash-defensive-patterns
Verify that the Agent implements three new ShellCheck rules:
SC2326 (unsafe temp file creation without mktemp),
SC2327 (missing cleanup trap for temp resources),
SC2328 (unquoted command substitution in test expressions).
"""

import os
import re
import subprocess
import pytest


class TestBashDefensivePatterns:
    REPO_DIR = "/workspace/shellcheck"

    # ────── helpers ──────

    def _read(self, rel_path):
        fpath = os.path.join(self.REPO_DIR, rel_path)
        with open(fpath, "r") as f:
            return f.read()

    def _exists(self, rel_path):
        return os.path.isfile(os.path.join(self.REPO_DIR, rel_path))

    # === File Path Checks ===

    def test_commands_hs_exists(self):
        """Commands.hs must exist"""
        assert self._exists("src/ShellCheck/Checks/Commands.hs")

    def test_shell_support_hs_exists(self):
        """ShellSupport.hs must exist"""
        assert self._exists("src/ShellCheck/Checks/ShellSupport.hs")

    def test_commands_test_exists(self):
        """CommandsTest.hs must exist"""
        assert self._exists("tests/ShellCheck/Checks/CommandsTest.hs")

    def test_shell_support_test_exists(self):
        """ShellSupportTest.hs must exist"""
        assert self._exists("tests/ShellCheck/Checks/ShellSupportTest.hs")

    # === Semantic Checks — SC2326 (unsafe temp file) ===

    def test_sc2326_rule_id(self):
        """SC2326 rule ID referenced in Commands.hs"""
        src = self._read("src/ShellCheck/Checks/Commands.hs")
        assert "2326" in src, "SC2326 rule ID not found in Commands.hs"

    def test_sc2326_tmp_detection(self):
        """SC2326 must detect /tmp/ path patterns"""
        src = self._read("src/ShellCheck/Checks/Commands.hs")
        assert "/tmp/" in src or "tmp" in src.lower(), (
            "SC2326 /tmp/ pattern detection not found"
        )

    def test_sc2326_mktemp_reference(self):
        """SC2326 must reference mktemp as the correct alternative"""
        src = self._read("src/ShellCheck/Checks/Commands.hs")
        assert "mktemp" in src, "SC2326 mktemp reference not found"

    def test_sc2326_message(self):
        """SC2326 must include warning message about symlink attacks"""
        src = self._read("src/ShellCheck/Checks/Commands.hs")
        lower = src.lower()
        assert "symlink" in lower or "race condition" in lower or "mktemp" in lower, (
            "SC2326 warning message not found"
        )

    # === Semantic Checks — SC2327 (missing cleanup trap) ===

    def test_sc2327_rule_id(self):
        """SC2327 rule ID referenced in ShellSupport.hs"""
        src = self._read("src/ShellCheck/Checks/ShellSupport.hs")
        assert "2327" in src, "SC2327 rule ID not found in ShellSupport.hs"

    def test_sc2327_trap_detection(self):
        """SC2327 must check for trap command"""
        src = self._read("src/ShellCheck/Checks/ShellSupport.hs")
        lower = src.lower()
        assert "trap" in lower, "SC2327 trap detection not found"

    def test_sc2327_exit_signal(self):
        """SC2327 must reference EXIT signal"""
        src = self._read("src/ShellCheck/Checks/ShellSupport.hs")
        assert "EXIT" in src or "exit" in src.lower(), (
            "SC2327 EXIT signal reference not found"
        )

    def test_sc2327_severity_info(self):
        """SC2327 should be Info/style severity"""
        src = self._read("src/ShellCheck/Checks/ShellSupport.hs")
        lower = src.lower()
        assert "info" in lower or "style" in lower, (
            "SC2327 should be Info/style severity"
        )

    # === Semantic Checks — SC2328 (unquoted cmd substitution in test) ===

    def test_sc2328_rule_id(self):
        """SC2328 rule ID referenced in Commands.hs"""
        src = self._read("src/ShellCheck/Checks/Commands.hs")
        assert "2328" in src, "SC2328 rule ID not found in Commands.hs"

    def test_sc2328_command_substitution(self):
        """SC2328 must detect command substitution patterns"""
        src = self._read("src/ShellCheck/Checks/Commands.hs")
        lower = src.lower()
        assert "substitution" in lower or "$(" in src or "backtick" in lower, (
            "SC2328 command substitution detection not found"
        )

    def test_sc2328_test_expression_context(self):
        """SC2328 must be scoped to test expressions"""
        src = self._read("src/ShellCheck/Checks/Commands.hs")
        assert "test" in src.lower() or "[" in src or "T_Condition" in src, (
            "SC2328 test expression context not found"
        )

    def test_sc2328_quote_message(self):
        """SC2328 must advise quoting"""
        src = self._read("src/ShellCheck/Checks/Commands.hs")
        lower = src.lower()
        assert "quote" in lower or "word splitting" in lower, (
            "SC2328 quoting advice not found"
        )

    # === Semantic Checks — Tests ===

    def test_sc2326_test_cases(self):
        """CommandsTest.hs must have SC2326 test cases"""
        src = self._read("tests/ShellCheck/Checks/CommandsTest.hs")
        assert "2326" in src, "SC2326 test cases not found"

    def test_sc2327_test_cases(self):
        """ShellSupportTest.hs must have SC2327 test cases"""
        src = self._read("tests/ShellCheck/Checks/ShellSupportTest.hs")
        assert "2327" in src, "SC2327 test cases not found"

    def test_sc2328_test_cases(self):
        """CommandsTest.hs must have SC2328 test cases"""
        src = self._read("tests/ShellCheck/Checks/CommandsTest.hs")
        assert "2328" in src, "SC2328 test cases not found"

    # === Functional Checks ===

    def test_cabal_build(self):
        """Project must build with cabal or stack"""
        # Try cabal first
        result = subprocess.run(
            ["cabal", "build"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=600,
        )
        if result.returncode != 0:
            result = subprocess.run(
                ["stack", "build"],
                capture_output=True, text=True, cwd=self.REPO_DIR, timeout=600,
            )
        assert result.returncode == 0, (
            f"Build failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_run_tests(self):
        """Tests must pass"""
        result = subprocess.run(
            ["cabal", "test"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=600,
        )
        if result.returncode != 0:
            result = subprocess.run(
                ["stack", "test"],
                capture_output=True, text=True, cwd=self.REPO_DIR, timeout=600,
            )
        assert result.returncode == 0, (
            f"Tests failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_shellcheck_binary_runs(self):
        """Built shellcheck binary should execute"""
        # Try to find the built binary
        result = subprocess.run(
            ["cabal", "exec", "shellcheck", "--", "--version"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=60,
        )
        if result.returncode != 0:
            result = subprocess.run(
                ["stack", "exec", "shellcheck", "--", "--version"],
                capture_output=True, text=True, cwd=self.REPO_DIR, timeout=60,
            )
        assert result.returncode == 0, (
            f"Binary execution failed:\n{result.stdout}\n{result.stderr}"
        )
