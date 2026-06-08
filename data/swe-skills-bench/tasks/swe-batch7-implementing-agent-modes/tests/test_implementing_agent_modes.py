"""
Test skill: implementing-agent-modes
Verify that the Agent implements a SQL Query Agent Mode for PostHog Max —
SqlAgentToolkit, InspectSchemaTool, ValidateQueryTool, GetQueryExamplesTool,
sql_agent AgentModeDefinition, mode manager registration, and frontend enum update.
"""

import os
import re
import subprocess
import pytest


class TestImplementingAgentModes:
    REPO_DIR = "/workspace/posthog"

    # ────── helpers ──────

    def _read(self, rel_path):
        fpath = os.path.join(self.REPO_DIR, rel_path)
        with open(fpath, "r") as f:
            return f.read()

    def _exists(self, rel_path):
        return os.path.isfile(os.path.join(self.REPO_DIR, rel_path))

    # === File Path Checks ===

    def test_sql_agent_mode_exists(self):
        """sql.py agent mode file must exist"""
        assert self._exists("ee/hogai/core/agent_modes/presets/sql.py")

    def test_sql_tools_exists(self):
        """sql_tools.py must exist"""
        assert self._exists("ee/hogai/tools/sql_tools.py")

    def test_sql_test_exists(self):
        """test_sql.py must exist"""
        assert self._exists("ee/hogai/core/agent_modes/presets/tests/test_sql.py")

    # === Semantic Checks — sql_tools.py ===

    def test_inspect_schema_tool(self):
        """InspectSchemaTool class must be defined"""
        src = self._read("ee/hogai/tools/sql_tools.py")
        assert re.search(r'class\s+InspectSchemaTool', src)

    def test_validate_query_tool(self):
        """ValidateQueryTool class must be defined"""
        src = self._read("ee/hogai/tools/sql_tools.py")
        assert re.search(r'class\s+ValidateQueryTool', src)

    def test_get_query_examples_tool(self):
        """GetQueryExamplesTool class must be defined"""
        src = self._read("ee/hogai/tools/sql_tools.py")
        assert re.search(r'class\s+GetQueryExamplesTool', src)

    def test_inspect_schema_name(self):
        """InspectSchemaTool must have name='inspect_schema'"""
        src = self._read("ee/hogai/tools/sql_tools.py")
        assert "inspect_schema" in src

    def test_validate_query_name(self):
        """ValidateQueryTool must have name='validate_query'"""
        src = self._read("ee/hogai/tools/sql_tools.py")
        assert "validate_query" in src

    def test_get_query_examples_name(self):
        """GetQueryExamplesTool must have name='get_query_examples'"""
        src = self._read("ee/hogai/tools/sql_tools.py")
        assert "get_query_examples" in src

    def test_tool_run_methods(self):
        """Each tool must implement _run"""
        src = self._read("ee/hogai/tools/sql_tools.py")
        run_count = len(re.findall(r'def\s+_run\b', src))
        assert run_count >= 3, f"Expected at least 3 _run methods, found {run_count}"

    def test_validate_uses_hogql_parser(self):
        """ValidateQueryTool must use HogQL parser, not query execution"""
        src = self._read("ee/hogai/tools/sql_tools.py")
        lower = src.lower()
        assert "hogql" in lower or "parse" in lower, (
            "ValidateQueryTool should use HogQL parser for validation"
        )

    def test_inspect_schema_optional_table(self):
        """InspectSchemaTool must accept optional table_name"""
        src = self._read("ee/hogai/tools/sql_tools.py")
        assert "table_name" in src
        assert "Optional" in src or "None" in src

    # === Semantic Checks — sql.py (agent mode) ===

    def test_sql_agent_toolkit_class(self):
        """SqlAgentToolkit class must be defined"""
        src = self._read("ee/hogai/core/agent_modes/presets/sql.py")
        assert re.search(r'class\s+SqlAgentToolkit', src)

    def test_sql_agent_definition(self):
        """sql_agent AgentModeDefinition must exist"""
        src = self._read("ee/hogai/core/agent_modes/presets/sql.py")
        assert "sql_agent" in src
        assert "AgentModeDefinition" in src

    def test_toolkit_tools_list(self):
        """Toolkit must reference all three tools"""
        src = self._read("ee/hogai/core/agent_modes/presets/sql.py")
        assert "InspectSchemaTool" in src
        assert "ValidateQueryTool" in src
        assert "GetQueryExamplesTool" in src

    def test_trajectory_examples(self):
        """Must have trajectory examples"""
        src = self._read("ee/hogai/core/agent_modes/presets/sql.py")
        assert "get_trajectory_examples" in src or "trajectory" in src.lower()

    # === Semantic Checks — Frontend ===

    def test_agent_mode_type_union(self):
        """schema-assistant-messages.ts must include 'sql' in AgentMode"""
        src = self._read("frontend/src/queries/schema/schema-assistant-messages.ts")
        assert '"sql"' in src or "'sql'" in src, (
            "'sql' not added to AgentMode type union"
        )

    def test_max_constants_sql_mode(self):
        """max-constants.tsx must register SQL mode"""
        src = self._read("frontend/src/lib/ai/max-constants.tsx")
        assert "sql" in src.lower() and "SQL Query" in src

    # === Semantic Checks — Mode Manager ===

    def test_mode_manager_sql_registration(self):
        """mode_manager.py must register sql_agent"""
        src = self._read("ee/hogai/chat_agent/mode_manager.py")
        assert "sql_agent" in src or "SQL" in src

    def test_feature_flag_gating(self):
        """SQL mode gated by hogai_sql_mode feature flag"""
        src = self._read("ee/hogai/chat_agent/mode_manager.py")
        assert "hogai_sql_mode" in src

    # === Functional Checks ===

    def test_python_syntax_sql_tools(self):
        """sql_tools.py must have valid Python syntax"""
        result = subprocess.run(
            ["python", "-c",
             "import py_compile; py_compile.compile('ee/hogai/tools/sql_tools.py', doraise=True)"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=30,
        )
        assert result.returncode == 0, (
            f"Syntax error in sql_tools.py:\n{result.stderr}"
        )

    def test_python_syntax_sql_agent(self):
        """sql.py must have valid Python syntax"""
        result = subprocess.run(
            ["python", "-c",
             "import py_compile; py_compile.compile('ee/hogai/core/agent_modes/presets/sql.py', doraise=True)"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=30,
        )
        assert result.returncode == 0, (
            f"Syntax error in sql.py:\n{result.stderr}"
        )

    def test_unit_tests_pass(self):
        """test_sql.py tests must pass"""
        result = subprocess.run(
            ["python", "-m", "pytest",
             "ee/hogai/core/agent_modes/presets/tests/test_sql.py",
             "-v", "--tb=short"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, (
            f"Tests failed:\n{result.stdout}\n{result.stderr}"
        )
