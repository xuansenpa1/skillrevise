"""
Tests for the implementing-agent-modes skill.
Validates a SQL Query agent mode for PostHog's AI assistant with
schema exploration, read-only query execution, and mode registration.
"""

import os
import re
import ast

REPO_DIR = "/workspace/posthog"
TOOLS_DIR = os.path.join(REPO_DIR, "ee", "hogai", "tools")
MODES_DIR = os.path.join(REPO_DIR, "ee", "hogai", "core", "agent_modes")
PRESETS_DIR = os.path.join(MODES_DIR, "presets")


class TestImplementingAgentModes:
    """Tests for the PostHog SQL Query agent mode."""

    # ── file_path_check ──────────────────────────────────────────────

    def test_sql_query_tool_exists(self):
        """SQL query tool module must exist."""
        path = os.path.join(TOOLS_DIR, "sql_query_tool.py")
        assert os.path.isfile(path), f"Missing {path}"

    def test_sql_query_mode_exists(self):
        """SQL query mode definition must exist."""
        path = os.path.join(PRESETS_DIR, "sql_query_mode.py")
        assert os.path.isfile(path), f"Missing {path}"

    def test_registry_exists(self):
        """Agent mode registry must exist."""
        path = os.path.join(MODES_DIR, "registry.py")
        assert os.path.isfile(path), f"Missing {path}"

    def test_tool_test_exists(self):
        """SQL query tool test file must exist."""
        path = os.path.join(TOOLS_DIR, "sql_query_tool_test.py")
        assert os.path.isfile(path), f"Missing {path}"

    def test_mode_test_exists(self):
        """SQL query mode test file must exist."""
        path = os.path.join(PRESETS_DIR, "sql_query_mode_test.py")
        assert os.path.isfile(path), f"Missing {path}"

    # ── semantic_check ───────────────────────────────────────────────

    def _read(self, path):
        if not os.path.isfile(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_sql_toolkit_class(self):
        """SQLQueryToolkit must define explore_schema and execute_query."""
        content = self._read(os.path.join(TOOLS_DIR, "sql_query_tool.py"))
        assert re.search(r"class\s+SQLQueryToolkit", content), (
            "SQLQueryToolkit class not defined"
        )
        assert re.search(r"def\s+explore_schema\b", content), "explore_schema not defined"
        assert re.search(r"def\s+execute_query\b", content), "execute_query not defined"

    def test_ddl_dml_rejection(self):
        """execute_query must reject DDL/DML keywords."""
        content = self._read(os.path.join(TOOLS_DIR, "sql_query_tool.py"))
        for keyword in ["CREATE", "DROP", "ALTER", "INSERT", "UPDATE", "DELETE", "TRUNCATE"]:
            assert keyword in content or keyword.lower() in content, (
                f"DDL/DML keyword '{keyword}' not checked"
            )
        assert re.search(r"Only SELECT queries are allowed", content), (
            "DDL rejection error message not found"
        )

    def test_auto_limit_injection(self):
        """execute_query must auto-append LIMIT to queries without one."""
        content = self._read(os.path.join(TOOLS_DIR, "sql_query_tool.py"))
        assert re.search(r"LIMIT|limit", content), "LIMIT handling not found"
        assert "1000" in content, "Max limit of 1000 not found"

    def test_mode_id_and_name(self):
        """SQL query mode must be registered with id 'sql_query'."""
        content = self._read(os.path.join(PRESETS_DIR, "sql_query_mode.py"))
        assert "sql_query" in content, "Mode id 'sql_query' not found"
        assert re.search(r"SQL Query Explorer|SQL Query", content), (
            "Mode display name not found"
        )

    def test_mode_system_prompt(self):
        """SQL query mode must include system prompt with schema exploration guidance."""
        content = self._read(os.path.join(PRESETS_DIR, "sql_query_mode.py"))
        assert re.search(r"schema|explore.*schema|column.*name", content, re.IGNORECASE), (
            "System prompt schema guidance not found"
        )

    def test_trajectory_examples(self):
        """SQL query mode must include at least 2 trajectory examples."""
        content = self._read(os.path.join(PRESETS_DIR, "sql_query_mode.py"))
        example_count = len(re.findall(r"example|trajectory|Example", content, re.IGNORECASE))
        assert example_count >= 2, f"Found {example_count} example references, expected ≥ 2"

    def test_registry_contains_sql_query(self):
        """Registry must include the sql_query mode."""
        content = self._read(os.path.join(MODES_DIR, "registry.py"))
        assert "sql_query" in content, "sql_query mode not registered in registry"

    # ── functional_check ─────────────────────────────────────────────

    def test_tool_file_valid_python(self):
        """SQL query tool must have valid Python syntax."""
        content = self._read(os.path.join(TOOLS_DIR, "sql_query_tool.py"))
        if content:
            ast.parse(content)

    def test_mode_file_valid_python(self):
        """SQL query mode definition must have valid Python syntax."""
        content = self._read(os.path.join(PRESETS_DIR, "sql_query_mode.py"))
        if content:
            ast.parse(content)

    def test_registry_valid_python(self):
        """Registry must have valid Python syntax."""
        content = self._read(os.path.join(MODES_DIR, "registry.py"))
        if content:
            ast.parse(content)

    def test_query_error_prefix(self):
        """Failed queries must return error message prefixed with 'Query error:'."""
        content = self._read(os.path.join(TOOLS_DIR, "sql_query_tool.py"))
        assert re.search(r"Query error:", content), "Query error prefix not found"

    def test_table_not_found_message(self):
        """explore_schema must return error for nonexistent table."""
        content = self._read(os.path.join(TOOLS_DIR, "sql_query_tool.py"))
        assert re.search(r"not found|Table.*not found", content, re.IGNORECASE), (
            "Table not found error message not found"
        )

    def test_tool_tests_exist(self):
        """Tool test file must contain actual test methods."""
        content = self._read(os.path.join(TOOLS_DIR, "sql_query_tool_test.py"))
        test_count = len(re.findall(r"def\s+test_", content))
        assert test_count >= 3, f"Found {test_count} test methods, expected ≥ 3"
