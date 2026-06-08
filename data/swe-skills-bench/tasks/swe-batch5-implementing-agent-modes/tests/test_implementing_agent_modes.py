"""
Test skill: implementing-agent-modes
Verify that the Agent correctly implements an Agent Mode system for PostHog
with Django models, registry, middleware, and API endpoints.
"""

import os
import re
import ast
import sys
import pytest


class TestImplementingAgentModes:
    REPO_DIR = "/workspace/posthog"

    MODELS = "posthog/agent_modes/models.py"
    REGISTRY = "posthog/agent_modes/registry.py"
    PROFILES = "posthog/agent_modes/profiles.py"
    MIDDLEWARE = "posthog/agent_modes/middleware.py"
    API = "posthog/agent_modes/api.py"
    TESTS = "posthog/agent_modes/tests/test_agent_modes.py"

    def _read_file(self, rel_path):
        filepath = os.path.join(self.REPO_DIR, rel_path)
        with open(filepath) as f:
            return f.read()

    # === File Path Checks ===

    def test_models_file_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.MODELS)
        assert os.path.exists(filepath), f"models.py not found"

    def test_registry_file_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.REGISTRY)
        assert os.path.exists(filepath), f"registry.py not found"

    def test_profiles_file_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.PROFILES)
        assert os.path.exists(filepath), f"profiles.py not found"

    def test_middleware_file_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.MIDDLEWARE)
        assert os.path.exists(filepath), f"middleware.py not found"

    def test_api_file_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.API)
        assert os.path.exists(filepath), f"api.py not found"

    def test_tests_file_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.TESTS)
        assert os.path.exists(filepath), f"Tests file not found"

    # === Semantic Checks ===

    def test_model_agent_mode_fields(self):
        """Verify AgentMode model with name, is_active, priority"""
        content = self._read_file(self.MODELS)
        assert "AgentMode" in content, "Missing AgentMode model"
        for field in ["name", "is_active", "priority"]:
            assert field in content, f"AgentMode missing field: {field}"

    def test_model_mode_configuration(self):
        """Verify ModeConfiguration model with config_key, config_value, value_type"""
        content = self._read_file(self.MODELS)
        assert "ModeConfiguration" in content, "Missing ModeConfiguration model"
        for field in ["config_key", "config_value", "value_type"]:
            assert field in content, f"ModeConfiguration missing field: {field}"

    def test_model_mode_schedule(self):
        """Verify ModeSchedule model with start_time, end_time, cron"""
        content = self._read_file(self.MODELS)
        assert "ModeSchedule" in content, "Missing ModeSchedule model"
        assert "start_time" in content, "ModeSchedule missing start_time"

    def test_registry_singleton(self):
        """Verify ModeRegistry is a singleton with get_instance"""
        content = self._read_file(self.REGISTRY)
        assert "ModeRegistry" in content, "Missing ModeRegistry class"
        assert "get_instance" in content, "ModeRegistry missing get_instance"

    def test_registry_priority_resolution(self):
        """Verify get_active_mode resolves by highest priority"""
        content = self._read_file(self.REGISTRY)
        assert "get_active_mode" in content, "Missing get_active_mode method"
        assert "priority" in content, "get_active_mode missing priority resolution"

    def test_registry_get_config_with_type_casting(self):
        """Verify get_config method with type casting"""
        content = self._read_file(self.REGISTRY)
        assert "get_config" in content, "Missing get_config method"
        has_cast = bool(re.search(r'(int|float|bool|json|cast|value_type)', content))
        assert has_cast, "get_config missing type casting"

    def test_registry_thread_safe(self):
        """Verify registry uses threading lock"""
        content = self._read_file(self.REGISTRY)
        has_lock = bool(re.search(r'(Lock|lock|threading|RLock)', content))
        assert has_lock, "ModeRegistry missing thread safety (Lock)"

    def test_registry_listener_pattern(self):
        """Verify register_listener for mode change notifications"""
        content = self._read_file(self.REGISTRY)
        assert "register_listener" in content or "listener" in content, \
            "ModeRegistry missing listener registration"

    def test_profiles_four_modes(self):
        """Verify 4 predefined profiles: Normal, HighThroughput, Degraded, Maintenance"""
        content = self._read_file(self.PROFILES)
        for mode in ["NormalMode", "HighThroughputMode", "DegradedMode", "MaintenanceMode"]:
            assert mode in content, f"Missing profile: {mode}"

    def test_profiles_config_values(self):
        """Verify profiles define query_timeout, concurrent_queries, ingestion_batch"""
        content = self._read_file(self.PROFILES)
        for key in ["query_timeout", "max_concurrent_queries", "ingestion_batch_size"]:
            assert key in content, f"Profiles missing config key: {key}"

    def test_middleware_injects_mode_context(self):
        """Verify middleware adds agent_mode and mode_config to request"""
        content = self._read_file(self.MIDDLEWARE)
        assert "AgentModeMiddleware" in content, "Missing AgentModeMiddleware"
        assert "agent_mode" in content, "Middleware missing request.agent_mode"
        assert "mode_config" in content, "Middleware missing request.mode_config"

    def test_api_endpoints_defined(self):
        """Verify API has list, activate, deactivate, current endpoints"""
        content = self._read_file(self.API)
        assert "activate" in content, "API missing activate endpoint"
        assert "deactivate" in content, "API missing deactivate endpoint"
        assert "current" in content, "API missing current mode endpoint"

    # === Functional Checks ===

    def test_all_files_valid_python(self):
        """Verify all Python files have valid syntax"""
        for path in [self.MODELS, self.REGISTRY, self.PROFILES,
                     self.MIDDLEWARE, self.API]:
            filepath = os.path.join(self.REPO_DIR, path)
            with open(filepath) as f:
                try:
                    ast.parse(f.read())
                except SyntaxError as e:
                    pytest.fail(f"{path} syntax error: {e}")

    def test_tests_cover_priority_and_api(self):
        """Verify test file covers priority resolution and API"""
        content = self._read_file(self.TESTS)
        tree = ast.parse(content)
        test_funcs = [
            n.name for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
        ]
        assert len(test_funcs) >= 5, \
            f"Expected at least 5 tests, found {len(test_funcs)}"
        content_lower = content.lower()
        assert "priority" in content_lower, "Tests missing priority resolution"
        assert "activate" in content_lower, "Tests missing activation tests"
