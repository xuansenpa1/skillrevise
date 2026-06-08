"""
Tests for the implementing-agent-modes skill.

Validates that an agent mode definition and toolkit system was implemented
for PostHog, including mode configuration, tool permissions, trajectory
tracking, and feature flag integration.

Repo: posthog (https://github.com/PostHog/posthog)
"""

import os
import re
import subprocess
import sys

REPO_DIR = "/workspace/posthog"


class TestFilePathCheck:
    """Verify all required files were created."""

    def test_mode_definition_exists(self):
        path = os.path.join(REPO_DIR, "posthog", "agent", "mode_definition.py")
        assert os.path.isfile(path), f"Expected mode_definition.py at {path}"

    def test_toolkit_exists(self):
        path = os.path.join(REPO_DIR, "posthog", "agent", "toolkit.py")
        assert os.path.isfile(path), f"Expected toolkit.py at {path}"

    def test_trajectory_exists(self):
        path = os.path.join(REPO_DIR, "posthog", "agent", "trajectory.py")
        assert os.path.isfile(path), f"Expected trajectory.py at {path}"

    def test_mode_definition_test_exists(self):
        path = os.path.join(
            REPO_DIR, "posthog", "agent", "tests", "test_mode_definition.py",
        )
        assert os.path.isfile(path), f"Expected test_mode_definition.py"

    def test_trajectory_test_exists(self):
        path = os.path.join(
            REPO_DIR, "posthog", "agent", "tests", "test_trajectory.py",
        )
        assert os.path.isfile(path), f"Expected test_trajectory.py"

    def test_init_exists(self):
        """Agent package should have __init__.py."""
        init_path = os.path.join(REPO_DIR, "posthog", "agent", "__init__.py")
        assert os.path.isfile(init_path), "Expected posthog/agent/__init__.py"


class TestSemanticModeDefinition:
    """Verify AgentModeDefinition class."""

    def _read(self):
        path = os.path.join(REPO_DIR, "posthog", "agent", "mode_definition.py")
        with open(path, "r") as f:
            return f.read()

    def test_class_definition(self):
        content = self._read()
        assert re.search(r"class\s+AgentModeDefinition", content), (
            "Expected AgentModeDefinition class"
        )

    def test_dataclass_or_init(self):
        content = self._read()
        assert re.search(r"@dataclass|dataclass|def __init__", content), (
            "Expected dataclass decorator or __init__"
        )

    def test_name_field(self):
        content = self._read()
        assert re.search(r"name.*str|name:", content), (
            "Expected name field (str)"
        )

    def test_allowed_tools_field(self):
        content = self._read()
        assert re.search(r"allowed_tools", content), (
            "Expected allowed_tools field (list of str)"
        )

    def test_max_iterations_field(self):
        content = self._read()
        assert re.search(r"max_iterations", content), (
            "Expected max_iterations field (default 10)"
        )

    def test_timeout_seconds_field(self):
        content = self._read()
        assert re.search(r"timeout_seconds", content), (
            "Expected timeout_seconds field (default 300)"
        )

    def test_feature_flags_field(self):
        content = self._read()
        assert re.search(r"feature_flags", content), (
            "Expected feature_flags field (dict)"
        )

    def test_constraints_field(self):
        content = self._read()
        assert re.search(r"constraints", content), (
            "Expected constraints field (dict with max_data_rows, allow_mutations, etc.)"
        )

    def test_is_tool_allowed(self):
        content = self._read()
        assert re.search(r"def\s+is_tool_allowed", content), (
            "Expected is_tool_allowed(tool_name) method"
        )

    def test_check_constraint(self):
        content = self._read()
        assert re.search(r"def\s+check_constraint", content), (
            "Expected check_constraint(key) method"
        )

    def test_merge_method(self):
        content = self._read()
        assert re.search(r"def\s+merge", content), (
            "Expected merge(overrides) method"
        )

    def test_name_validation(self):
        content = self._read()
        assert re.search(r"alphanumeric|[a-zA-Z0-9_]|isalnum|re\.match", content), (
            "Expected name validation (alphanumeric + underscores)"
        )

    def test_is_feature_enabled(self):
        content = self._read()
        assert re.search(r"def\s+is_feature_enabled", content), (
            "Expected is_feature_enabled(flag_name, default=False) method"
        )


class TestSemanticToolkit:
    """Verify AgentToolkit class."""

    def _read(self):
        path = os.path.join(REPO_DIR, "posthog", "agent", "toolkit.py")
        with open(path, "r") as f:
            return f.read()

    def test_class_definition(self):
        content = self._read()
        assert re.search(r"class\s+AgentToolkit", content), (
            "Expected AgentToolkit class"
        )

    def test_register_tool(self):
        content = self._read()
        assert re.search(r"def\s+register_tool", content), (
            "Expected register_tool method"
        )

    def test_get_tools(self):
        content = self._read()
        assert re.search(r"def\s+get_tools", content), (
            "Expected get_tools(mode) method"
        )

    def test_execute_tool(self):
        content = self._read()
        assert re.search(r"def\s+execute_tool", content), (
            "Expected execute_tool method"
        )

    def test_tool_not_allowed_error(self):
        content = self._read()
        assert re.search(r"ToolNotAllowedError|ToolNotAllowed", content), (
            "Expected ToolNotAllowedError exception"
        )

    def test_confirmation_required(self):
        content = self._read()
        assert re.search(r"ConfirmationRequired", content), (
            "Expected ConfirmationRequired exception"
        )

    def test_mutation_not_allowed(self):
        content = self._read()
        assert re.search(r"MutationNotAllowed", content), (
            "Expected MutationNotAllowedError exception"
        )

    def test_iteration_limit_exceeded(self):
        content = self._read()
        assert re.search(r"IterationLimit|iteration.*limit", content, re.IGNORECASE), (
            "Expected IterationLimitExceeded exception"
        )


class TestSemanticTrajectory:
    """Verify Trajectory tracking class."""

    def _read(self):
        path = os.path.join(REPO_DIR, "posthog", "agent", "trajectory.py")
        with open(path, "r") as f:
            return f.read()

    def test_class_definition(self):
        content = self._read()
        assert re.search(r"class\s+Trajectory", content), (
            "Expected Trajectory class"
        )

    def test_add_step(self):
        content = self._read()
        assert re.search(r"def\s+add_step", content), (
            "Expected add_step method"
        )

    def test_get_steps(self):
        content = self._read()
        assert re.search(r"def\s+get_steps", content), (
            "Expected get_steps method"
        )

    def test_summary(self):
        content = self._read()
        assert re.search(r"def\s+summary", content), (
            "Expected summary method"
        )

    def test_to_dict(self):
        content = self._read()
        assert re.search(r"def\s+to_dict", content), (
            "Expected to_dict serialization method"
        )

    def test_from_dict(self):
        content = self._read()
        assert re.search(r"def\s+from_dict|from_dict", content), (
            "Expected from_dict deserialization method"
        )

    def test_trajectory_step(self):
        content = self._read()
        assert re.search(r"TrajectoryStep|trajectory_step", content), (
            "Expected TrajectoryStep class/namedtuple"
        )

    def test_trajectory_summary(self):
        content = self._read()
        assert re.search(r"TrajectorySummary|summary", content), (
            "Expected TrajectorySummary with total/passed/failed/duration/tools_used"
        )

    def test_success_rate(self):
        content = self._read()
        assert re.search(r"success_rate", content), (
            "Expected success_rate in trajectory summary"
        )

    def test_replay(self):
        content = self._read()
        assert re.search(r"def\s+replay|replay", content), (
            "Expected replay function for determinism testing"
        )


class TestFunctionalPythonSyntax:
    """Validate Python files compile and agent tests pass."""

    def test_mode_definition_syntax(self):
        path = os.path.join(REPO_DIR, "posthog", "agent", "mode_definition.py")
        with open(path, "r") as f:
            content = f.read()
        compile(content, path, "exec")

    def test_toolkit_syntax(self):
        path = os.path.join(REPO_DIR, "posthog", "agent", "toolkit.py")
        with open(path, "r") as f:
            content = f.read()
        compile(content, path, "exec")

    def test_trajectory_syntax(self):
        path = os.path.join(REPO_DIR, "posthog", "agent", "trajectory.py")
        with open(path, "r") as f:
            content = f.read()
        compile(content, path, "exec")

    def test_agent_tests_pass(self):
        test_dir = os.path.join(REPO_DIR, "posthog", "agent", "tests")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_dir, "-v", "--tb=short"],
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"Agent tests failed:\n{result.stdout[-1000:]}\n{result.stderr[-500:]}"
        )
