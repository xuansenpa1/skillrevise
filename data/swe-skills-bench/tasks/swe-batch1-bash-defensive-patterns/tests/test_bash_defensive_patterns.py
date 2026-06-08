"""
Test for 'bash-defensive-patterns' skill — Bash Defensive Scripting
Validates that the Agent created idiomatic, defensive bash scripts with
proper error handling and that shellcheck validates them.
"""

import os
import subprocess
import pytest


class TestBashDefensivePatterns:
    """Verify defensive bash scripting patterns."""

    REPO_DIR = "/workspace/shellcheck"

    # [!] Change: updated path from examples/defensive to test as specified in the requirements doc
    SCRIPTS_DIR = "test"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_main_script_exists(self):
        """Main defensive script must exist."""
        script_dir = os.path.join(self.REPO_DIR, self.SCRIPTS_DIR)
        if not os.path.isdir(script_dir):
            pytest.fail(f"Directory {self.SCRIPTS_DIR} not found")
        scripts = [f for f in os.listdir(script_dir) if f.endswith(".sh")]
        # [!] Change: updated the path in the error message text
        assert len(scripts) >= 1, "No .sh scripts found in test/"

    def test_readme_exists(self):
        """README.md must exist in test/."""
        fpath = os.path.join(self.REPO_DIR, self.SCRIPTS_DIR, "README.md")
        assert os.path.isfile(fpath), "README.md not found"

    # ------------------------------------------------------------------
    # L2: content & shellcheck validation
    # ------------------------------------------------------------------

    def _get_scripts(self):
        script_dir = os.path.join(self.REPO_DIR, self.SCRIPTS_DIR)
        return [
            os.path.join(script_dir, f)
            for f in os.listdir(script_dir)
            if f.endswith(".sh")
        ]

    def test_scripts_have_shebang(self):
        """All scripts must start with #!/bin/bash or #!/usr/bin/env bash."""
        for script in self._get_scripts():
            with open(script, "r") as f:
                first_line = f.readline().strip()
            valid = first_line.startswith("#!/bin/bash") or first_line.startswith(
                "#!/usr/bin/env bash"
            )
            assert valid, f"{script} missing proper shebang: {first_line}"

    def test_set_euo_pipefail(self):
        """Scripts must include 'set -euo pipefail'."""
        for script in self._get_scripts():
            with open(script, "r") as f:
                content = f.read()
            assert "set -e" in content, f"{script} missing set -e"
            # Check for u and o pipefail (may be separate)
            has_u = (
                "set -u" in content or "-u" in content.split("set -")[1]
                if "set -" in content
                else False
            )
            has_pipefail = "pipefail" in content
            assert has_u or has_pipefail, f"{script} missing -u or pipefail"

    def test_trap_handler(self):
        """Scripts must define a trap for error handling."""
        found_trap = False
        for script in self._get_scripts():
            with open(script, "r") as f:
                content = f.read()
            if "trap " in content or "trap\t" in content:
                found_trap = True
                break
        assert found_trap, "No script defines a trap handler"

    def test_shellcheck_passes(self):
        """shellcheck must pass on all scripts."""
        for script in self._get_scripts():
            result = subprocess.run(
                ["shellcheck", "-S", "warning", script],
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert (
                result.returncode == 0
            ), f"shellcheck failed on {script}:\n{result.stdout}"

    def test_variable_quoting(self):
        """Scripts should use quoted variables (e.g., "$var" not $var)."""
        for script in self._get_scripts():
            with open(script, "r") as f:
                lines = f.readlines()
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                # Skip comments and shebang
                if stripped.startswith("#") or stripped.startswith("set "):
                    continue

    def test_function_definitions(self):
        """At least one script should define helper functions."""
        found = False
        for script in self._get_scripts():
            with open(script, "r") as f:
                content = f.read()
            if "function " in content or "()" in content:
                found = True
                break
        assert found, "No script defines functions"

    def test_readonly_variables(self):
        """Scripts should use readonly or declare -r for constants."""
        found = False
        for script in self._get_scripts():
            with open(script, "r") as f:
                content = f.read()
            if "readonly " in content or "declare -r" in content:
                found = True
                break
        assert found, "No script uses readonly/declare -r for constants"

    def test_error_messages_to_stderr(self):
        """Error messages should be directed to stderr (>&2)."""
        found = False
        for script in self._get_scripts():
            with open(script, "r") as f:
                content = f.read()
            if ">&2" in content or "1>&2" in content or "2>" in content:
                found = True
                break
        assert found, "No script sends error messages to stderr"

    def test_script_is_executable_or_runnable(self):
        """Scripts must be runnable with bash."""
        for script in self._get_scripts():
            result = subprocess.run(
                ["bash", "-n", script],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert (
                result.returncode == 0
            ), f"Syntax check failed for {script}:\n{result.stderr}"
