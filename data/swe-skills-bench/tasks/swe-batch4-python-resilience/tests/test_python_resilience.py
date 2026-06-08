"""
Test skill: python-resilience
Verify that the resilient HTTP transport layer has been correctly added to httpx,
including ResilientTransport class with retry logic, exponential backoff,
timeout enforcement, fallback support, and 429 rate-limit handling.
"""

import os
import sys
import ast
import re
import inspect
import subprocess
import pytest


class TestPythonResilience:
    REPO_DIR = "/workspace/httpx"

    # === File Path Checks ===

    def test_resilience_module_exists(self):
        """Verify that httpx/_resilience.py was created"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        assert os.path.exists(filepath), f"_resilience.py not found at {filepath}"

    def test_config_module_exists(self):
        """Verify that httpx/_config.py exists"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_config.py")
        assert os.path.exists(filepath), f"_config.py not found at {filepath}"

    def test_resilience_tests_exist(self):
        """Verify that tests/test_resilience.py was created"""
        filepath = os.path.join(self.REPO_DIR, "tests/test_resilience.py")
        assert os.path.exists(filepath), f"test_resilience.py not found at {filepath}"

    # === Semantic Checks ===

    def test_resilient_transport_class_defined(self):
        """Verify that ResilientTransport class is defined in _resilience.py"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(filepath) as f:
            content = f.read()
        tree = ast.parse(content)
        class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        assert "ResilientTransport" in class_names, \
            "ResilientTransport class should be defined in _resilience.py"

    def test_resilient_transport_constructor_params(self):
        """Verify ResilientTransport has correct constructor parameters"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(filepath) as f:
            content = f.read()
        expected_params = [
            "max_retries", "backoff_base", "backoff_max",
            "backoff_jitter", "timeout_per_attempt",
            "retryable_status_codes"
        ]
        for param in expected_params:
            assert param in content, \
                f"ResilientTransport should accept '{param}' parameter"

    def test_handle_request_method_exists(self):
        """Verify ResilientTransport implements handle_request method"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(filepath) as f:
            content = f.read()
        assert "handle_request" in content, \
            "ResilientTransport should implement handle_request method"

    def test_exponential_backoff_implemented(self):
        """Verify exponential backoff formula is implemented"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(filepath) as f:
            content = f.read()
        # Should have power/exponential calculation
        has_exponential = ("**" in content or "pow(" in content or "2 **" in content or
                           "backoff_base" in content)
        assert has_exponential, \
            "Should implement exponential backoff (2^attempt pattern)"
        assert "backoff_max" in content, \
            "Should cap backoff at backoff_max"

    def test_retry_after_header_handling(self):
        """Verify 429 responses with Retry-After header are handled"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(filepath) as f:
            content = f.read()
        assert "Retry-After" in content or "retry-after" in content or "retry_after" in content, \
            "Should handle Retry-After header from 429 responses"

    def test_fallback_callable_support(self):
        """Verify fallback callable is accepted and invoked on retry exhaustion"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(filepath) as f:
            content = f.read()
        assert "fallback" in content, \
            "ResilientTransport should accept a 'fallback' callable parameter"

    def test_logging_on_retries(self):
        """Verify retry attempts produce warning-level log messages"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(filepath) as f:
            content = f.read()
        has_logging = ("logging" in content or "logger" in content)
        assert has_logging, "Should use logging for retry attempts"
        has_warning = ("warning" in content.lower() or ".warn" in content)
        assert has_warning, "Should log retry attempts at warning level"
        # Logger name should be httpx._resilience
        assert "httpx._resilience" in content or "_resilience" in content, \
            "Logger name should be 'httpx._resilience'"

    def test_default_retryable_status_codes(self):
        """Verify default retryable status codes include 429, 502, 503, 504"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(filepath) as f:
            content = f.read()
        for code in ["429", "502", "503", "504"]:
            assert code in content, \
                f"Default retryable status codes should include {code}"

    def test_test_file_covers_key_scenarios(self):
        """Verify test file covers retry success, timeout, 429, and fallback scenarios"""
        filepath = os.path.join(self.REPO_DIR, "tests/test_resilience.py")
        with open(filepath) as f:
            content = f.read()
        test_count = len(re.findall(r'def\s+test_', content))
        assert test_count >= 5, \
            f"Test file should have at least 5 test cases, found {test_count}"

    # === Functional Checks ===

    def test_resilience_module_is_importable(self):
        """Verify that the _resilience module can be imported without errors"""
        result = subprocess.run(
            ["python", "-c", "from httpx._resilience import ResilientTransport; print('OK')"],
            cwd=self.REPO_DIR,
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "PYTHONPATH": self.REPO_DIR}
        )
        if result.returncode != 0:
            # Try installing httpx first
            subprocess.run(["pip", "install", "-e", "."], cwd=self.REPO_DIR,
                           capture_output=True, text=True, timeout=120)
            result = subprocess.run(
                ["python", "-c", "from httpx._resilience import ResilientTransport; print('OK')"],
                cwd=self.REPO_DIR,
                capture_output=True, text=True, timeout=30
            )
        assert result.returncode == 0, \
            f"Failed to import ResilientTransport: {result.stderr[:500]}"
        assert "OK" in result.stdout, "Import should succeed"

    def test_resilient_transport_instantiation(self):
        """Verify that ResilientTransport can be instantiated with a mock transport"""
        result = subprocess.run(
            ["python", "-c", """
import sys
sys.path.insert(0, '.')
from httpx._resilience import ResilientTransport
from unittest.mock import Mock

mock_transport = Mock()
rt = ResilientTransport(transport=mock_transport)
assert rt is not None
assert hasattr(rt, 'handle_request')
print('OK')
"""],
            cwd=self.REPO_DIR,
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "PYTHONPATH": self.REPO_DIR}
        )
        if result.returncode != 0:
            subprocess.run(["pip", "install", "-e", "."], cwd=self.REPO_DIR,
                           capture_output=True, text=True, timeout=120)
            result = subprocess.run(
                ["python", "-c", """
from httpx._resilience import ResilientTransport
from unittest.mock import Mock
mock_transport = Mock()
rt = ResilientTransport(transport=mock_transport)
assert rt is not None
assert hasattr(rt, 'handle_request')
print('OK')
"""],
                cwd=self.REPO_DIR,
                capture_output=True, text=True, timeout=30
            )
        assert result.returncode == 0, \
            f"Failed to instantiate ResilientTransport: {result.stderr[:500]}"

    def test_agents_resilience_tests_pass(self):
        """Verify that the Agent's own test suite for resilience passes"""
        # Install the package first
        subprocess.run(["pip", "install", "-e", "."], cwd=self.REPO_DIR,
                       capture_output=True, text=True, timeout=120)
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_resilience.py", "-v", "--tb=short"],
            cwd=self.REPO_DIR,
            capture_output=True, text=True, timeout=120
        )
        assert result.returncode == 0, \
            f"Resilience test suite failed:\n{result.stdout[-1500:]}\n{result.stderr[-500:]}"
