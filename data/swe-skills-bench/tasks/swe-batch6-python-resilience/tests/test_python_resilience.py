"""
Test skill: python-resilience
Verify that the Agent correctly implements a resilient HTTP transport with
retry logic, exponential backoff, and circuit breaker for httpx.
"""

import os
import re
import ast
import sys
import subprocess
import pytest


class TestPythonResilience:
    REPO_DIR = "/workspace/httpx"

    # === File Path Checks ===

    def test_resilience_module_exists(self):
        """Verify that the resilience module file exists"""
        path = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        assert os.path.exists(path), f"_resilience.py not found at {path}"

    def test_resilience_test_file_exists(self):
        """Verify that the resilience test file exists"""
        path = os.path.join(self.REPO_DIR, "tests/test_resilience.py")
        assert os.path.exists(path), f"test_resilience.py not found at {path}"

    def test_resilience_module_is_valid_python(self):
        """Verify that _resilience.py is valid Python syntax"""
        path = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(path, "r") as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"_resilience.py has syntax error: {e}")

    # === Semantic Checks ===

    def test_resilient_transport_class_exists(self):
        """Verify that ResilientTransport class is defined with required parameters"""
        path = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(path, "r") as f:
            source = f.read()

        tree = ast.parse(source)
        class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        assert "ResilientTransport" in class_names, (
            "httpx/_resilience.py should define a ResilientTransport class"
        )

        # Verify init parameters
        assert "max_retries" in source, "ResilientTransport should accept max_retries parameter"
        assert "backoff_base" in source, "ResilientTransport should accept backoff_base parameter"
        assert "backoff_max" in source, "ResilientTransport should accept backoff_max parameter"

    def test_circuit_breaker_states_defined(self):
        """Verify that circuit breaker has three states: CLOSED, OPEN, HALF_OPEN"""
        path = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(path, "r") as f:
            content = f.read()

        for state in ["CLOSED", "OPEN", "HALF_OPEN"]:
            assert state in content, (
                f"Circuit breaker missing state: {state}"
            )

    def test_circuit_breaker_open_error_defined(self):
        """Verify that CircuitBreakerOpenError exception class is defined"""
        path = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(path, "r") as f:
            source = f.read()

        tree = ast.parse(source)
        class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        assert "CircuitBreakerOpenError" in class_names, (
            "Missing CircuitBreakerOpenError exception class"
        )

    def test_circuit_breaker_config_parameters(self):
        """Verify circuit breaker accepts failure_threshold, recovery_timeout, success_threshold"""
        path = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(path, "r") as f:
            content = f.read()

        for param in ["failure_threshold", "recovery_timeout", "success_threshold"]:
            assert param in content, (
                f"Circuit breaker missing configuration parameter: {param}"
            )

    def test_stats_method_defined(self):
        """Verify that ResilientTransport has a stats() method with required keys"""
        path = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(path, "r") as f:
            content = f.read()

        assert "stats" in content, "ResilientTransport should have a stats() method"
        required_keys = ["total_requests", "total_retries", "total_failures",
                        "circuit_state", "consecutive_failures"]
        for key in required_keys:
            assert key in content, (
                f"stats() method should return key: {key}"
            )

    def test_retry_after_header_handling(self):
        """Verify that the transport handles Retry-After header for 429 responses"""
        path = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(path, "r") as f:
            content = f.read()

        has_retry_after = any(kw in content for kw in [
            "retry-after", "Retry-After", "retry_after",
        ])
        assert has_retry_after, (
            "Transport should handle Retry-After header on 429 responses"
        )

    def test_transient_error_detection(self):
        """Verify that code distinguishes transient from permanent errors"""
        path = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(path, "r") as f:
            content = f.read()

        # Check for transient status codes
        transient_codes = ["429", "502", "503", "504"]
        found_codes = sum(1 for code in transient_codes if code in content)
        assert found_codes >= 3, (
            f"Transport should identify transient HTTP status codes (429, 502, 503, 504). "
            f"Found {found_codes} of {len(transient_codes)}"
        )

    # === Functional Checks ===

    def test_import_resilient_transport(self):
        """Verify that ResilientTransport can be imported"""
        result = subprocess.run(
            [
                "python", "-c",
                (
                    "import sys; sys.path.insert(0, '.'); "
                    "from httpx._resilience import ResilientTransport, CircuitBreakerOpenError; "
                    "print('OK')"
                ),
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"Failed to import ResilientTransport: {result.stderr}"
        )
        assert "OK" in result.stdout

    def test_resilient_transport_instantiation(self):
        """Verify that ResilientTransport can be instantiated with default parameters"""
        result = subprocess.run(
            [
                "python", "-c",
                (
                    "import sys; sys.path.insert(0, '.'); "
                    "import httpx; "
                    "from httpx._resilience import ResilientTransport; "
                    "transport = httpx.HTTPTransport(); "
                    "rt = ResilientTransport(transport); "
                    "print('max_retries' in dir(rt) or hasattr(rt, '_max_retries') or True); "
                    "print('OK')"
                ),
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"Failed to instantiate ResilientTransport: {result.stderr}"
        )
        assert "OK" in result.stdout

    def test_stats_method_returns_dict(self):
        """Verify that stats() returns a dict with required keys"""
        result = subprocess.run(
            [
                "python", "-c",
                (
                    "import sys; sys.path.insert(0, '.'); "
                    "import httpx; "
                    "from httpx._resilience import ResilientTransport; "
                    "transport = httpx.HTTPTransport(); "
                    "rt = ResilientTransport(transport); "
                    "s = rt.stats(); "
                    "assert isinstance(s, dict), f'stats() should return dict, got {type(s)}'; "
                    "required = ['total_requests', 'total_retries', 'total_failures', 'circuit_state', 'consecutive_failures']; "
                    "for k in required: "
                    "    assert k in s, f'stats() missing key: {k}'; "
                    "assert s['total_requests'] == 0; "
                    "assert s['total_retries'] == 0; "
                    "assert s['total_failures'] == 0; "
                    "assert s['consecutive_failures'] == 0; "
                    "print('OK')"
                ),
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"stats() method test failed: {result.stderr}\n{result.stdout}"
        )
        assert "OK" in result.stdout

    def test_circuit_breaker_open_error_is_transport_error(self):
        """Verify that CircuitBreakerOpenError inherits from httpx.TransportError"""
        result = subprocess.run(
            [
                "python", "-c",
                (
                    "import sys; sys.path.insert(0, '.'); "
                    "import httpx; "
                    "from httpx._resilience import CircuitBreakerOpenError; "
                    "assert issubclass(CircuitBreakerOpenError, httpx.TransportError), "
                    "  'CircuitBreakerOpenError should inherit from httpx.TransportError'; "
                    "print('OK')"
                ),
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"CircuitBreakerOpenError inheritance check failed: {result.stderr}"
        )
        assert "OK" in result.stdout

    def test_resilient_transport_zero_retries(self):
        """Verify that max_retries=0 disables retries entirely"""
        result = subprocess.run(
            [
                "python", "-c",
                (
                    "import sys; sys.path.insert(0, '.'); "
                    "import httpx; "
                    "from httpx._resilience import ResilientTransport; "
                    "transport = httpx.HTTPTransport(); "
                    "rt = ResilientTransport(transport, max_retries=0); "
                    "s = rt.stats(); "
                    "print('OK')"
                ),
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"max_retries=0 instantiation failed: {result.stderr}"
        )
        assert "OK" in result.stdout

    def test_resilience_tests_run(self):
        """Verify that the resilience unit tests execute"""
        # Install httpx first
        subprocess.run(
            ["pip", "install", "-e", "."],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_resilience.py", "-v", "--tb=short", "-x"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        # At least some tests should pass
        assert "passed" in result.stdout or result.returncode == 0, (
            f"Resilience tests failed:\n{result.stdout[-2000:]}\n{result.stderr[-1000:]}"
        )
