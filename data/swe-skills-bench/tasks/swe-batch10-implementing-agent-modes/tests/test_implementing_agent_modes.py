"""
Test skill: implementing-agent-modes
Verify that the Agent correctly implements a SQL query agent mode
with feature flag for PostHog.
"""

import os
import re
import ast
import subprocess
import pytest


class TestImplementingAgentModes:
    REPO_DIR = "/workspace/posthog"

    # === File Path Checks ===

    def test_sql_mode_exists(self):
        """Verify sql.py was created"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/sql.py",
        )
        assert os.path.exists(path), "sql.py not found"

    def test_sql_mode_test_exists(self):
        """Verify test_sql.py was created"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/tests/test_sql.py",
        )
        assert os.path.exists(path), "test_sql.py not found"

    # === Semantic Checks: SQLAgentToolkit ===

    def test_sql_agent_toolkit_class(self):
        """Verify SQLAgentToolkit class is defined"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/sql.py",
        )
        with open(path) as f:
            content = f.read()
        assert "class SQLAgentToolkit" in content, (
            "SQLAgentToolkit class should be defined"
        )

    def test_toolkit_subclasses_assistant_toolkit(self):
        """Verify SQLAgentToolkit subclasses AssistantToolkit"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/sql.py",
        )
        with open(path) as f:
            content = f.read()
        assert "AssistantToolkit" in content, (
            "Should subclass AssistantToolkit"
        )

    def test_toolkit_exposes_hogql_tool(self):
        """Verify execute_hogql_query tool is exposed"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/sql.py",
        )
        with open(path) as f:
            content = f.read()
        assert "execute_hogql_query" in content, (
            "Should expose execute_hogql_query tool"
        )

    def test_toolkit_exposes_read_data_tool(self):
        """Verify read_data tool is exposed"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/sql.py",
        )
        with open(path) as f:
            content = f.read()
        assert "read_data" in content, "Should expose read_data tool"

    def test_toolkit_excludes_feature_flag_tool(self):
        """Verify create_feature_flag is NOT imported"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/sql.py",
        )
        with open(path) as f:
            content = f.read()
        assert "create_feature_flag" not in content, (
            "Should NOT expose create_feature_flag tool"
        )

    def test_toolkit_excludes_experiment_tool(self):
        """Verify create_experiment is NOT imported"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/sql.py",
        )
        with open(path) as f:
            content = f.read()
        assert "create_experiment" not in content, (
            "Should NOT expose create_experiment tool"
        )

    def test_toolkit_no_feature_flags_import(self):
        """Verify no import from feature_flags module"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/sql.py",
        )
        with open(path) as f:
            content = f.read()
        assert "ee.hogai.tools.feature_flags" not in content and \
               "ee/hogai/tools/feature_flags" not in content, (
            "Should not import from feature_flags module"
        )

    def test_toolkit_trajectory_examples(self):
        """Verify trajectory_examples property"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/sql.py",
        )
        with open(path) as f:
            content = f.read()
        assert "trajectory_examples" in content, (
            "Should define trajectory_examples property"
        )

    # === Semantic Checks: AgentModeDefinition ===

    def test_sql_agent_mode_definition(self):
        """Verify sql_agent AgentModeDefinition variable"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/sql.py",
        )
        with open(path) as f:
            content = f.read()
        assert "sql_agent" in content, (
            "Should define sql_agent AgentModeDefinition"
        )
        assert "AgentModeDefinition" in content, (
            "Should use AgentModeDefinition"
        )

    def test_sql_agent_mode_value(self):
        """Verify mode set to AgentMode.SQL"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/sql.py",
        )
        with open(path) as f:
            content = f.read()
        assert "AgentMode.SQL" in content, (
            "Should set mode to AgentMode.SQL"
        )

    def test_sql_agent_toolkit_class_ref(self):
        """Verify toolkit_class set to SQLAgentToolkit"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/sql.py",
        )
        with open(path) as f:
            content = f.read()
        assert "toolkit_class" in content and "SQLAgentToolkit" in content, (
            "Should set toolkit_class to SQLAgentToolkit"
        )

    # === Semantic Checks: Feature Flag ===

    def test_flag_definition_constant(self):
        """Verify HOGAI_SQL_MODE constant in flag_definitions.py"""
        path = os.path.join(
            self.REPO_DIR,
            "posthog/models/feature_flag/flag_definitions.py",
        )
        with open(path) as f:
            content = f.read()
        assert 'HOGAI_SQL_MODE' in content, (
            "Should define HOGAI_SQL_MODE constant"
        )
        assert '"hogai-sql-mode"' in content, (
            "HOGAI_SQL_MODE should equal 'hogai-sql-mode'"
        )

    def test_has_hogai_sql_mode_function(self):
        """Verify has_hogai_sql_mode_feature_flag function"""
        path = os.path.join(
            self.REPO_DIR,
            "posthog/models/feature_flag/flag_definitions.py",
        )
        with open(path) as f:
            content = f.read()
        assert "has_hogai_sql_mode_feature_flag" in content, (
            "Should define has_hogai_sql_mode_feature_flag"
        )

    # === Semantic Checks: Mode Registration ===

    def test_mode_manager_registers_sql(self):
        """Verify mode_manager.py registers SQL mode"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/chat_agent/mode_manager.py",
        )
        with open(path) as f:
            content = f.read()
        assert "AgentMode.SQL" in content, (
            "Should register AgentMode.SQL in mode_manager"
        )

    def test_mode_manager_feature_flag_guard(self):
        """Verify SQL mode guarded by feature flag"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/chat_agent/mode_manager.py",
        )
        with open(path) as f:
            content = f.read()
        assert "has_hogai_sql_mode_feature_flag" in content, (
            "Should guard SQL mode with feature flag"
        )

    # === Semantic Checks: Schema ===

    def test_schema_has_sql_mode(self):
        """Verify AgentMode enum has SQL entry in schema"""
        path = os.path.join(
            self.REPO_DIR,
            "frontend/src/queries/schema/schema-assistant-messages.ts",
        )
        with open(path) as f:
            content = f.read()
        assert "SQL" in content, (
            "AgentMode enum should have SQL entry"
        )

    # === Semantic Checks: Tests ===

    def test_test_sql_toolkit_tools(self):
        """Verify TestSQLToolkitTools test class"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/tests/test_sql.py",
        )
        with open(path) as f:
            content = f.read()
        assert "TestSQLToolkitTools" in content, (
            "Should have TestSQLToolkitTools class"
        )

    def test_test_sql_mode_definition(self):
        """Verify TestSQLModeDefinition test class"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/tests/test_sql.py",
        )
        with open(path) as f:
            content = f.read()
        assert "TestSQLModeDefinition" in content, (
            "Should have TestSQLModeDefinition class"
        )

    def test_test_registration_enabled(self):
        """Verify TestSQLModeRegistrationEnabled test class"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/tests/test_sql.py",
        )
        with open(path) as f:
            content = f.read()
        assert "TestSQLModeRegistrationEnabled" in content, (
            "Should have TestSQLModeRegistrationEnabled class"
        )

    def test_test_registration_disabled(self):
        """Verify TestSQLModeRegistrationDisabled test class"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/tests/test_sql.py",
        )
        with open(path) as f:
            content = f.read()
        assert "TestSQLModeRegistrationDisabled" in content, (
            "Should have TestSQLModeRegistrationDisabled class"
        )

    # === Functional Checks ===

    def test_sql_py_parses(self):
        """Verify sql.py has valid Python syntax"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/sql.py",
        )
        with open(path) as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"sql.py has syntax error: {e}")

    def test_test_sql_parses(self):
        """Verify test_sql.py has valid Python syntax"""
        path = os.path.join(
            self.REPO_DIR,
            "ee/hogai/core/agent_modes/presets/tests/test_sql.py",
        )
        with open(path) as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"test_sql.py has syntax error: {e}")

    def test_sql_mode_tests_pass(self):
        """Verify test_sql.py tests pass"""
        result = subprocess.run(
            [
                "python", "-m", "pytest",
                "ee/hogai/core/agent_modes/presets/tests/test_sql.py",
                "-v", "--tb=short",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"Tests failed:\n{result.stdout}\n{result.stderr}"
        )
