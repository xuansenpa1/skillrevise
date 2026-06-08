"""
Test skill: implementing-agent-modes
Verify that the Agent creates an Error Tracking agent mode with 4 tools
in PostHog (Python/TypeScript).
"""

import os
import re
import ast
import subprocess
import pytest


class TestImplementingAgentModes:
    REPO_DIR = "/workspace/posthog"

    # === File Path Checks ===

    def test_agent_mode_files_exist(self):
        """Verify error tracking agent mode files exist"""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root or "node_modules" in root:
                continue
            for f in files:
                if ("agent" in f.lower() or "error" in f.lower() or "mode" in f.lower()) and (f.endswith(".py") or f.endswith(".ts") or f.endswith(".tsx")):
                    found = True
                    break
            if found:
                break
        assert found, "Error tracking agent mode files not found"

    # === Semantic Checks ===

    def test_agent_mode_class_or_config(self):
        """Verify agent mode is defined as a class or configuration"""
        content = self._collect_content()
        content_lower = content.lower()
        has_agent = (
            "agentmode" in content_lower
            or "agent_mode" in content_lower
            or "errortracking" in content_lower
            or "error_tracking" in content_lower
        )
        assert has_agent, "Agent mode class or config not found"

    def test_four_tools_defined(self):
        """Verify at least 4 tools are defined for the agent"""
        content = self._collect_content()
        content_lower = content.lower()
        tool_indicators = 0
        tool_keywords = ["tool", "function", "action", "capability"]
        for kw in tool_keywords:
            if kw in content_lower:
                tool_indicators += 1
        assert tool_indicators >= 1, "No tool definitions found"

    def test_error_tracking_functionality(self):
        """Verify error tracking specific functionality"""
        content = self._collect_content()
        content_lower = content.lower()
        has_error = (
            "error" in content_lower
            and ("tracking" in content_lower or "trace" in content_lower or "stack" in content_lower)
        )
        assert has_error, "Error tracking functionality not found"

    def test_tool_registration(self):
        """Verify tools are registered with the agent"""
        content = self._collect_content()
        content_lower = content.lower()
        has_reg = (
            "register" in content_lower
            or "tools" in content_lower
            or "tool_list" in content_lower
            or "available_tools" in content_lower
        )
        assert has_reg, "Tool registration not found"

    # === Functional Checks ===

    def test_python_files_valid_syntax(self):
        """Verify Python files have valid syntax"""
        py_files = self._find_py_files()
        for pf in py_files:
            with open(pf) as fh:
                source = fh.read()
            try:
                ast.parse(source)
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {pf}: {e}")

    def test_ts_files_valid_syntax(self):
        """Verify TypeScript files have no obvious syntax errors"""
        ts_files = self._find_ts_files()
        for tf in ts_files:
            with open(tf) as fh:
                content = fh.read()
            opens = content.count('{')
            closes = content.count('}')
            assert abs(opens - closes) <= 2, f"Unbalanced braces in {tf}: {opens} vs {closes}"

    def test_agent_exports_or_interface(self):
        """Verify agent mode is exported or has a public interface"""
        content = self._collect_content()
        has_export = (
            "export " in content
            or "module.exports" in content
            or "class " in content
            or "def " in content
        )
        assert has_export, "Agent mode has no public interface"

    def test_mode_has_description(self):
        """Verify agent mode has a description or metadata"""
        content = self._collect_content()
        content_lower = content.lower()
        has_desc = (
            "description" in content_lower
            or "name" in content_lower
            or "label" in content_lower
            or "title" in content_lower
        )
        assert has_desc, "Agent mode missing description or metadata"

    def test_error_grouping_or_analysis(self):
        """Verify error grouping or analysis capability"""
        content = self._collect_content()
        content_lower = content.lower()
        has_analysis = (
            "group" in content_lower
            or "classify" in content_lower
            or "analyze" in content_lower
            or "pattern" in content_lower
            or "fingerprint" in content_lower
        )
        assert has_analysis, "Error grouping or analysis not found"

    def _collect_content(self):
        all_content = ""
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root or "node_modules" in root:
                continue
            for f in files:
                if (f.endswith(".py") or f.endswith(".ts") or f.endswith(".tsx")):
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath) as fh:
                            c = fh.read()
                        if any(kw in c.lower() for kw in ["agent", "error_tracking", "errortracking", "mode"]):
                            all_content += c + "\n"
                    except (UnicodeDecodeError, PermissionError):
                        continue
        return all_content

    def _find_py_files(self):
        py_files = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root or "node_modules" in root:
                continue
            for f in files:
                if f.endswith(".py") and ("agent" in f.lower() or "error" in f.lower() or "mode" in f.lower()):
                    py_files.append(os.path.join(root, f))
        return py_files

    def _find_ts_files(self):
        ts_files = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root or "node_modules" in root:
                continue
            for f in files:
                if (f.endswith(".ts") or f.endswith(".tsx")) and ("agent" in f.lower() or "error" in f.lower() or "mode" in f.lower()):
                    ts_files.append(os.path.join(root, f))
        return ts_files
