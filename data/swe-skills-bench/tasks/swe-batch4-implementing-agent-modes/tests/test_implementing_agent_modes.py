"""
Tests for skill: implementing-agent-modes
Repo: PostHog/posthog
Image: zhangyiiiiii/swe-skills-bench-python
Task: Implement a new Error Tracking agent mode for PostHog with
      toolkit, mode definition, tools, and feature flag gating.
"""

import ast
import os
import re

import pytest

REPO_DIR = "/workspace/posthog"
MODE_DIR = os.path.join(
    REPO_DIR, "ee", "hogai", "core", "agent_modes", "presets", "error_tracking"
)
TOOLS_FILE = os.path.join(REPO_DIR, "ee", "hogai", "tools", "error_tracking_tools.py")
MODE_MANAGER_FILE = os.path.join(REPO_DIR, "ee", "hogai", "chat_agent", "mode_manager.py")
SCHEMA_FILE = os.path.join(
    REPO_DIR, "frontend", "src", "queries", "schema", "schema-assistant-messages.ts"
)

INIT_FILE = os.path.join(MODE_DIR, "__init__.py")
TOOLKIT_FILE = os.path.join(MODE_DIR, "toolkit.py")
MODE_DEF_FILE = os.path.join(MODE_DIR, "mode_definition.py")


# ---------------------------------------------------------------------------
# Layer 1 — file_path_check
# ---------------------------------------------------------------------------

class TestFilePathCheck:
    """Verify all required agent mode files exist."""

    def test_mode_init_exists(self):
        assert os.path.isfile(INIT_FILE), f"Missing {INIT_FILE}"

    def test_toolkit_exists(self):
        assert os.path.isfile(TOOLKIT_FILE), f"Missing {TOOLKIT_FILE}"

    def test_mode_definition_exists(self):
        assert os.path.isfile(MODE_DEF_FILE), f"Missing {MODE_DEF_FILE}"

    def test_tools_file_exists(self):
        assert os.path.isfile(TOOLS_FILE), f"Missing {TOOLS_FILE}"

    def test_mode_manager_exists(self):
        assert os.path.isfile(MODE_MANAGER_FILE), f"Missing {MODE_MANAGER_FILE}"

    def test_schema_file_exists(self):
        assert os.path.isfile(SCHEMA_FILE), f"Missing {SCHEMA_FILE}"


# ---------------------------------------------------------------------------
# Layer 2 — semantic_check
# ---------------------------------------------------------------------------

class TestSemanticSchema:
    """Verify AgentMode enum includes ERROR_TRACKING."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()

    def test_error_tracking_in_enum(self):
        assert "ERROR_TRACKING" in self.src or "error_tracking" in self.src, (
            "AgentMode enum must include ERROR_TRACKING"
        )


class TestSemanticToolkit:
    """Verify ErrorTrackingToolkit structure."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open(TOOLKIT_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()
        self.tree = ast.parse(self.src)

    def test_toolkit_class(self):
        classes = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.ClassDef)]
        assert "ErrorTrackingToolkit" in classes, (
            f"Expected ErrorTrackingToolkit class; found {classes}"
        )

    def test_list_issues_method(self):
        funcs = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]
        assert "list_issues" in funcs, f"Expected list_issues; found {funcs}"

    def test_search_issues_method(self):
        funcs = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]
        assert "search_issues" in funcs, f"Expected search_issues; found {funcs}"

    def test_get_issue_details_method(self):
        funcs = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]
        assert "get_issue_details" in funcs, f"Expected get_issue_details; found {funcs}"

    def test_analyze_issue_method(self):
        funcs = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]
        assert "analyze_issue" in funcs, f"Expected analyze_issue; found {funcs}"

    def test_status_filtering(self):
        assert "active" in self.src and "resolved" in self.src, (
            "list_issues should support active/resolved status filtering"
        )

    def test_trajectory_examples(self):
        assert "trajectory" in self.src.lower() or "example" in self.src.lower(), (
            "Toolkit should include trajectory examples"
        )


class TestSemanticModeDefinition:
    """Verify mode definition structure."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open(MODE_DEF_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()
        self.tree = ast.parse(self.src)

    def test_agent_mode_reference(self):
        assert "ERROR_TRACKING" in self.src, (
            "Mode definition must reference AgentMode.ERROR_TRACKING"
        )

    def test_mode_definition_class_or_instance(self):
        assert "AgentModeDefinition" in self.src or "ModeDefinition" in self.src, (
            "Mode definition should use AgentModeDefinition"
        )

    def test_description_provided(self):
        assert "description" in self.src, (
            "Mode definition must include a description"
        )

    def test_toolkit_class_binding(self):
        assert "ErrorTrackingToolkit" in self.src, (
            "Mode definition should bind ErrorTrackingToolkit"
        )


class TestSemanticTools:
    """Verify backend tool implementations."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open(TOOLS_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()
        self.tree = ast.parse(self.src)

    def test_list_function(self):
        funcs = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]
        assert any("list" in f.lower() and "error" in f.lower() for f in funcs) or \
               "list_error_tracking_issues" in funcs, (
            f"Expected list_error_tracking_issues tool; found {funcs}"
        )

    def test_search_function(self):
        funcs = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]
        assert any("search" in f.lower() and "error" in f.lower() for f in funcs) or \
               "search_error_tracking_issues" in funcs, (
            f"Expected search_error_tracking_issues tool; found {funcs}"
        )

    def test_get_details_function(self):
        funcs = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]
        assert any("get" in f.lower() and "detail" in f.lower() for f in funcs), (
            f"Expected get_error_tracking_issue_details tool; found {funcs}"
        )

    def test_team_id_validation(self):
        assert "team_id" in self.src, "Tools must accept team_id parameter"

    def test_query_model(self):
        assert "ErrorTrackingIssue" in self.src or "error_tracking" in self.src.lower(), (
            "Tools should query the ErrorTrackingIssue model"
        )


class TestSemanticModeManager:
    """Verify mode manager registers error tracking mode."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open(MODE_MANAGER_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()

    def test_error_tracking_registered(self):
        assert "error_tracking" in self.src.lower() or "ERROR_TRACKING" in self.src, (
            "Mode manager must register the ERROR_TRACKING mode"
        )

    def test_feature_flag_check(self):
        assert "feature_flag" in self.src.lower() or "feature" in self.src.lower(), (
            "Mode registration must check a feature flag"
        )


# ---------------------------------------------------------------------------
# Layer 3 — functional_check
# ---------------------------------------------------------------------------

class TestFunctionalToolkitFields:
    """Verify toolkit issue dict fields via source analysis."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open(TOOLKIT_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()

    def test_issue_dict_has_id(self):
        assert '"id"' in self.src or "'id'" in self.src, (
            "Issue dict must include 'id' field"
        )

    def test_issue_dict_has_title(self):
        assert '"title"' in self.src or "'title'" in self.src, (
            "Issue dict must include 'title' field"
        )

    def test_issue_dict_has_status(self):
        assert '"status"' in self.src or "'status'" in self.src, (
            "Issue dict must include 'status' field"
        )

    def test_issue_dict_has_event_count(self):
        assert "event_count" in self.src, "Issue dict must include 'event_count' field"

    def test_issue_dict_has_first_seen(self):
        assert "first_seen" in self.src, "Issue dict must include 'first_seen' field"

    def test_issue_dict_has_last_seen(self):
        assert "last_seen" in self.src, "Issue dict must include 'last_seen' field"


class TestFunctionalFeatureFlagGating:
    """Verify feature flag gating behavior via source analysis."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open(MODE_MANAGER_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()

    def test_conditional_registration(self):
        """Mode registration should be conditional on feature flag."""
        has_if = re.search(
            r"if\s+.*(?:feature_flag|has_error_tracking)",
            self.src,
            re.IGNORECASE,
        )
        assert has_if, (
            "Mode manager should conditionally register error tracking based on flag"
        )

    def test_flag_function_or_check(self):
        """There should be a dedicated function or check for the flag."""
        assert "has_error_tracking" in self.src or "error_tracking" in self.src.lower(), (
            "Expected a feature flag check for error tracking mode"
        )


class TestFunctionalTrajectoryExamples:
    """Verify trajectory examples cover the three main journeys."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open(TOOLKIT_FILE, "r", encoding="utf-8") as f:
            self.src = f.read().lower()

    def test_list_trajectory(self):
        assert "list" in self.src and "active" in self.src, (
            "Should have trajectory example for listing active errors"
        )

    def test_search_trajectory(self):
        assert "search" in self.src and "query" in self.src, (
            "Should have trajectory example for searching issues"
        )

    def test_analyze_trajectory(self):
        assert "analyze" in self.src and "issue" in self.src, (
            "Should have trajectory example for analyzing an issue"
        )


class TestFunctionalToolsValidation:
    """Verify tool implementations validate input."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open(TOOLS_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()

    def test_team_id_required(self):
        """Tools must validate team_id is provided."""
        assert "team_id" in self.src, "Tools must require team_id"
        # Check for some form of validation
        has_validation = (
            "if not team_id" in self.src or
            "team_id is None" in self.src or
            "raise" in self.src or
            "ValueError" in self.src
        )
        assert has_validation, "Tools should validate team_id input"

    def test_empty_result_handling(self):
        """Tools should handle not-found cases gracefully."""
        assert "[]" in self.src or "None" in self.src or "{}" in self.src, (
            "Tools should return empty list or None for not-found cases"
        )

    def test_ordering_by_last_seen(self):
        """list_issues should order by last_seen."""
        assert "last_seen" in self.src, (
            "list_error_tracking_issues should order by last_seen"
        )
        assert "desc" in self.src.lower() or "order_by" in self.src or "-last_seen" in self.src, (
            "list_issues should sort by last_seen descending"
        )
