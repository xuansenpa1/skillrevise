"""
Test for 'implementing-agent-modes' skill — PostHog Agent Mode Implementation
Validates that the Agent implemented custom agent modes with proper state
management, transitions, and configuration.
"""

import os
import subprocess
import pytest


class TestImplementingAgentModes:
    """Verify agent mode implementation in PostHog."""

    REPO_DIR = "/workspace/posthog"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_agent_mode_file_exists(self):
        """An agent mode implementation file must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if (
                    ("agent" in f.lower() or "mode" in f.lower())
                    and f.endswith((".py", ".ts", ".tsx"))
                    and "node_modules" not in root
                    and "__pycache__" not in root
                ):
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, "r", errors="ignore") as fh:
                            content = fh.read()
                        if "mode" in content.lower() and "agent" in content.lower():
                            found.append(fpath)
                    except OSError:
                        pass
        assert len(found) >= 1, "No agent mode implementation file found"

    def test_test_file_exists(self):
        """Test file for agent modes must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if (
                    ("agent" in f.lower() or "mode" in f.lower())
                    and ("test" in f.lower() or "spec" in f.lower())
                    and f.endswith((".py", ".ts", ".tsx"))
                ):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No agent mode test file found"

    # ------------------------------------------------------------------
    # L2: content validation
    # ------------------------------------------------------------------

    def _find_mode_files(self):
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if (
                    ("agent" in f.lower() or "mode" in f.lower())
                    and f.endswith((".py", ".ts", ".tsx"))
                    and "node_modules" not in root
                    and "__pycache__" not in root
                ):
                    found.append(os.path.join(root, f))
        return found

    def _read_all_mode_files(self):
        content = ""
        for fpath in self._find_mode_files():
            try:
                with open(fpath, "r", errors="ignore") as f:
                    content += f.read() + "\n"
            except OSError:
                pass
        return content

    def test_mode_enum_or_constants(self):
        """Must define agent mode types/enum."""
        content = self._read_all_mode_files()
        enum_patterns = [
            "enum",
            "Enum",
            "MODE_",
            "AgentMode",
            "MODES",
            "mode_type",
            "class Mode",
        ]
        found = any(p in content for p in enum_patterns)
        assert found, "No agent mode enum/constants defined"

    def test_state_management(self):
        """Must implement state management for modes."""
        content = self._read_all_mode_files()
        state_patterns = [
            "state",
            "setState",
            "transition",
            "current_mode",
            "active_mode",
            "switch_mode",
            "change_mode",
        ]
        found = sum(1 for p in state_patterns if p in content)
        assert found >= 2, "Insufficient state management"

    def test_mode_transitions(self):
        """Must implement mode transition logic."""
        content = self._read_all_mode_files()
        transition_patterns = [
            "transition",
            "switch",
            "activate",
            "deactivate",
            "enter",
            "exit",
            "from_mode",
            "to_mode",
        ]
        found = sum(1 for p in transition_patterns if p in content)
        assert found >= 2, "No mode transition logic found"

    def test_mode_configuration(self):
        """Modes must be configurable."""
        content = self._read_all_mode_files()
        config_patterns = [
            "config",
            "settings",
            "options",
            "params",
            "properties",
            "attributes",
            "capabilities",
        ]
        found = any(p in content for p in config_patterns)
        assert found, "No mode configuration found"

    def test_at_least_3_modes(self):
        """Must define at least 3 distinct modes."""
        content = self._read_all_mode_files()
        import re

        # Look for mode name patterns
        mode_names = set()
        # String constants like "analysis", "generation", etc.
        strings = re.findall(r'["\']([a-z_]+_mode|[a-z_]+)["\']', content.lower())
        for s in strings:
            if "mode" in s or len(s) > 3:
                mode_names.add(s)
        # Also count enum-style definitions
        enum_values = re.findall(r'(\w+)\s*=\s*["\']', content)
        mode_names.update(enum_values)
        assert len(mode_names) >= 3, f"Only {len(mode_names)} mode definitions found"

    def test_error_handling_in_transitions(self):
        """Transition logic must handle errors."""
        content = self._read_all_mode_files()
        error_patterns = [
            "except",
            "catch",
            "Error",
            "raise",
            "throw",
            "invalid",
            "ValueError",
        ]
        found = any(p in content for p in error_patterns)
        assert found, "No error handling in mode transitions"

    def test_python_files_compile(self):
        """Python mode files must compile."""
        for fpath in self._find_mode_files():
            if fpath.endswith(".py"):
                result = subprocess.run(
                    ["python", "-m", "py_compile", fpath],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                assert (
                    result.returncode == 0
                ), f"{fpath} compile error:\n{result.stderr}"

    def test_api_or_interface(self):
        """Modes must expose an API or interface."""
        content = self._read_all_mode_files()
        api_patterns = [
            "def ",
            "function ",
            "class ",
            "interface ",
            "export ",
            "async def ",
            "@api",
            "@action",
        ]
        found = sum(1 for p in api_patterns if p in content)
        assert found >= 3, "Insufficient API surface for modes"
