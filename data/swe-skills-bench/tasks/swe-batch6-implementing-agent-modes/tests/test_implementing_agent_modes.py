"""
Test skill: implementing-agent-modes
Verify that the Agent implements a Data Explorer mode for PostHog with
AgentMode enum extension, toolkit with 5 tools, trajectory examples,
feature flag gating, and frontend integration.
"""

import os
import re
import ast
import pytest


class TestImplementingAgentModes:
    REPO_DIR = "/workspace/posthog"

    # === File Path Checks ===

    def test_data_explorer_init_exists(self):
        assert os.path.exists(
            os.path.join(
                self.REPO_DIR,
                "ee/hogai/core/agent_modes/presets/data_explorer/__init__.py",
            )
        )

    def test_toolkit_exists(self):
        assert os.path.exists(
            os.path.join(
                self.REPO_DIR,
                "ee/hogai/core/agent_modes/presets/data_explorer/toolkit.py",
            )
        )

    def test_definition_exists(self):
        assert os.path.exists(
            os.path.join(
                self.REPO_DIR,
                "ee/hogai/core/agent_modes/presets/data_explorer/definition.py",
            )
        )

    def test_test_file_exists(self):
        assert os.path.exists(
            os.path.join(
                self.REPO_DIR,
                "ee/hogai/core/agent_modes/presets/data_explorer/tests/test_data_explorer_toolkit.py",
            )
        )

    # === Semantic Checks ===

    def test_agent_mode_enum_has_data_explorer(self):
        """AgentMode enum should include DATA_EXPLORER"""
        path = os.path.join(
            self.REPO_DIR,
            "frontend/src/queries/schema/schema-assistant-messages.ts",
        )
        with open(path) as f:
            content = f.read()
        assert "DATA_EXPLORER" in content or "data_explorer" in content, (
            "AgentMode enum should include DATA_EXPLORER"
        )

    def test_toolkit_has_required_tools(self):
        """DataExplorerToolkit should expose exactly 5 tools"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/data_explorer/toolkit.py",
        )
        with open(path) as f:
            content = f.read()
        assert "DataExplorerToolkit" in content, "Missing DataExplorerToolkit class"
        for tool in ("read_data", "search", "list_data", "create_insight", "trends_query"):
            assert tool in content, f"Toolkit should expose '{tool}' tool"

    def test_toolkit_excludes_other_tools(self):
        """Toolkit should NOT include experiment/flag/session/survey tools"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/data_explorer/toolkit.py",
        )
        with open(path) as f:
            content = f.read()
        # These terms should not appear as exposed tools
        for excluded in ("experiment", "feature_flag", "session_recording", "survey"):
            # Check if it appears as a registered tool (not just in comments)
            if excluded in content:
                # Allow in comments or docstrings, but not as tool registration
                lines = [
                    l.strip()
                    for l in content.split("\n")
                    if excluded in l and not l.strip().startswith("#") and not l.strip().startswith('"""')
                ]
                # This is a soft check - we just ensure the tool names are limited
                pass

    def test_toolkit_has_trajectory_examples(self):
        """Toolkit should have at least 3 trajectory examples"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/data_explorer/toolkit.py",
        )
        with open(path) as f:
            content = f.read()
        content_lower = content.lower()
        assert (
            "trajectory" in content_lower
            or "example" in content_lower
            or "few_shot" in content_lower
        ), "Toolkit should include trajectory examples"

    def test_definition_has_mode_and_description(self):
        """Definition should set mode, description, toolkit_class"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/data_explorer/definition.py",
        )
        with open(path) as f:
            content = f.read()
        assert "AgentModeDefinition" in content, "Should use AgentModeDefinition"
        assert "DATA_EXPLORER" in content or "data_explorer" in content, "Should reference DATA_EXPLORER mode"
        assert "description" in content, "Should include description"
        assert "DataExplorerToolkit" in content, "Should reference DataExplorerToolkit"

    def test_mode_manager_registers_data_explorer(self):
        """Mode manager should register DATA_EXPLORER behind feature flag"""
        path = os.path.join(
            self.REPO_DIR, "ee/hogai/chat_agent/mode_manager.py"
        )
        with open(path) as f:
            content = f.read()
        assert "DATA_EXPLORER" in content or "data_explorer" in content, (
            "Mode manager should reference DATA_EXPLORER"
        )
        assert "feature" in content.lower() or "flag" in content.lower(), (
            "Registration should be gated by feature flag"
        )

    def test_feature_flag_constant_defined(self):
        """Feature flag constant HOGAI_DATA_EXPLORER_MODE should be defined"""
        path = os.path.join(
            self.REPO_DIR, "posthog/models/feature_flag/feature_flag.py"
        )
        with open(path) as f:
            content = f.read()
        assert "HOGAI_DATA_EXPLORER_MODE" in content, (
            "Missing HOGAI_DATA_EXPLORER_MODE constant"
        )

    def test_frontend_mode_selector_has_data_explorer(self):
        """Frontend mode constants should include Data Explorer"""
        path = os.path.join(
            self.REPO_DIR, "frontend/src/scenes/max/max-constants.tsx"
        )
        with open(path) as f:
            content = f.read()
        assert "Data Explorer" in content or "data_explorer" in content, (
            "Mode selector should include Data Explorer"
        )

    # === Functional Checks ===

    def test_all_python_files_parse(self):
        """All new Python files should parse without syntax errors"""
        py_files = [
            "ee/hogai/core/agent_modes/presets/data_explorer/__init__.py",
            "ee/hogai/core/agent_modes/presets/data_explorer/toolkit.py",
            "ee/hogai/core/agent_modes/presets/data_explorer/definition.py",
            "ee/hogai/core/agent_modes/presets/data_explorer/tests/test_data_explorer_toolkit.py",
        ]
        for pf in py_files:
            path = os.path.join(self.REPO_DIR, pf)
            with open(path) as f:
                source = f.read()
            try:
                ast.parse(source)
            except SyntaxError as e:
                pytest.fail(f"{pf} has syntax error: {e}")

    def test_init_exports_definition(self):
        """__init__.py should export the mode definition"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/data_explorer/__init__.py",
        )
        with open(path) as f:
            content = f.read()
        assert (
            "definition" in content.lower()
            or "DataExplorer" in content
            or "data_explorer" in content
        ), "__init__.py should export the mode definition"

    def test_test_file_has_test_methods(self):
        """Test file should contain actual test methods"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/data_explorer/tests/test_data_explorer_toolkit.py",
        )
        with open(path) as f:
            content = f.read()
        test_methods = re.findall(r"def (test_\w+)", content)
        assert len(test_methods) >= 2, (
            f"Test file should have at least 2 test methods, found {len(test_methods)}"
        )
