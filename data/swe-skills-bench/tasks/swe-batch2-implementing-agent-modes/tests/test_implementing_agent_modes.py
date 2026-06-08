"""
Test skill: implementing-agent-modes
Verify that the Agent extends the PostHog capture endpoint with agent
mode detection, metadata validation, backward compatibility, and
proper storage of agent event properties.
"""

import os
import re
import ast
import subprocess
import pytest


class TestImplementingAgentModes:
    REPO_DIR = "/workspace/posthog"

    # === File Path Checks ===

    def test_capture_py_exists(self):
        """Verify posthog/api/capture.py exists"""
        path = os.path.join(self.REPO_DIR, "posthog/api/capture.py")
        assert os.path.exists(path), f"capture.py not found at {path}"

    # === Semantic Checks ===

    def test_agent_mode_detection(self):
        """Verify agent mode detection from payload or header"""
        path = os.path.join(self.REPO_DIR, "posthog/api/capture.py")
        with open(path) as f:
            content = f.read()

        detection_indicators = [
            "agent_mode", "X-Agent-Mode", "x-agent-mode",
            "HTTP_X_AGENT_MODE",
        ]
        found = [ind for ind in detection_indicators if ind in content]
        assert len(found) >= 1, (
            f"Should detect agent mode. Found: {found}"
        )

    def test_agent_id_field(self):
        """Verify agent_id metadata field is handled"""
        path = os.path.join(self.REPO_DIR, "posthog/api/capture.py")
        with open(path) as f:
            content = f.read()

        assert "agent_id" in content, (
            "Should handle agent_id metadata field"
        )

    def test_agent_session_id_field(self):
        """Verify agent_session_id metadata field is handled"""
        path = os.path.join(self.REPO_DIR, "posthog/api/capture.py")
        with open(path) as f:
            content = f.read()

        assert "agent_session_id" in content, (
            "Should handle agent_session_id metadata field"
        )

    def test_agent_action_field(self):
        """Verify agent_action metadata field is handled"""
        path = os.path.join(self.REPO_DIR, "posthog/api/capture.py")
        with open(path) as f:
            content = f.read()

        assert "agent_action" in content, (
            "Should handle agent_action metadata field"
        )

    def test_required_field_validation(self):
        """Verify agent_id and agent_action are required for agent mode"""
        path = os.path.join(self.REPO_DIR, "posthog/api/capture.py")
        with open(path) as f:
            content = f.read()

        validation_indicators = [
            "required", "missing", "error", "400",
            "validation", "reject", "raise",
        ]
        found = [ind for ind in validation_indicators if ind in content.lower()]
        assert len(found) >= 1, (
            f"Should validate required agent fields. Found: {found}"
        )

    def test_backward_compatibility(self):
        """Verify non-agent events are processed unchanged"""
        path = os.path.join(self.REPO_DIR, "posthog/api/capture.py")
        with open(path) as f:
            content = f.read()

        # Agent mode should be conditional, not breaking existing flow
        conditional_indicators = [
            "if ", "else", "agent_mode", "not agent",
        ]
        found = [ind for ind in conditional_indicators if ind in content]
        assert len(found) >= 2, (
            f"Should conditionally apply agent processing. Found: {found}"
        )

    def test_metadata_stored_as_properties(self):
        """Verify agent metadata is stored as event properties"""
        path = os.path.join(self.REPO_DIR, "posthog/api/capture.py")
        with open(path) as f:
            content = f.read()

        property_indicators = [
            "properties", "props", "event_data",
            "update(", "[\"agent",
        ]
        found = [ind for ind in property_indicators if ind in content]
        assert len(found) >= 1, (
            f"Agent metadata should be stored as properties. Found: {found}"
        )

    def test_header_and_payload_detection(self):
        """Verify agent mode detectable via both header and payload"""
        path = os.path.join(self.REPO_DIR, "posthog/api/capture.py")
        with open(path) as f:
            content = f.read()

        # Should check both request header and event payload
        header_indicators = [
            "META", "headers", "HTTP_", "request.",
        ]
        payload_indicators = [
            "data", "payload", "body", "event",
        ]
        header_found = [ind for ind in header_indicators if ind in content]
        payload_found = [ind for ind in payload_indicators if ind in content]

        assert len(header_found) >= 1, (
            f"Should check request headers. Found: {header_found}"
        )
        assert len(payload_found) >= 1, (
            f"Should check event payload. Found: {payload_found}"
        )

    # === Functional Checks ===

    def test_capture_py_valid_python(self):
        """Verify capture.py is valid Python"""
        path = os.path.join(self.REPO_DIR, "posthog/api/capture.py")
        with open(path) as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"capture.py has syntax errors: {e}")

    def test_capture_py_importable(self):
        """Verify capture.py can be parsed and key constructs exist"""
        path = os.path.join(self.REPO_DIR, "posthog/api/capture.py")
        with open(path) as f:
            source = f.read()

        tree = ast.parse(source)
        func_names = [
            node.name for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]
        assert len(func_names) >= 1, (
            f"capture.py should define functions. Found: {func_names}"
        )

    def test_error_response_format(self):
        """Verify validation errors return proper response format"""
        path = os.path.join(self.REPO_DIR, "posthog/api/capture.py")
        with open(path) as f:
            content = f.read()

        response_indicators = [
            "JsonResponse", "Response", "status",
            "400", "error", "message",
        ]
        found = [ind for ind in response_indicators if ind in content]
        assert len(found) >= 2, (
            f"Should return proper error responses. Found: {found}"
        )
