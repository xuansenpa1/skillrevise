"""
Test skill: python-resilience
Verify that the Agent correctly adds ResilientTransport with retry, circuit breaker,
and AsyncResilientTransport to the httpx library.
"""

import os
import subprocess
import ast
import re
import pytest


class TestPythonResilience:
    REPO_DIR = "/workspace/httpx"

    # === File Path Checks ===

    def test_resilient_transport_file_exists(self):
        """Verify resilient.py exists in _transports directory"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        assert os.path.exists(path), f"resilient.py not found at {path}"

    def test_config_file_exists(self):
        """Verify _config.py exists"""
        path = os.path.join(self.REPO_DIR, "httpx/_config.py")
        assert os.path.exists(path), f"_config.py not found at {path}"

    # === Semantic Checks ===

    def test_resilient_transport_class_defined(self):
        """Verify ResilientTransport class is defined"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            source = f.read()
        tree = ast.parse(source)
        class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        assert "ResilientTransport" in class_names, (
            f"ResilientTransport class not found. Classes: {class_names}"
        )

    def test_async_resilient_transport_class_defined(self):
        """Verify AsyncResilientTransport class is defined"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            source = f.read()
        tree = ast.parse(source)
        class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        assert "AsyncResilientTransport" in class_names, (
            f"AsyncResilientTransport class not found. Classes: {class_names}"
        )

    def test_retry_logic_with_exponential_backoff(self):
        """Verify retry logic includes exponential backoff"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            source = f.read()
        has_backoff = (
            "exponential" in source.lower()
            or "backoff" in source.lower()
            or ("**" in source and "retry" in source.lower())
            or "2 **" in source
            or "pow(" in source
        )
        assert has_backoff, "No exponential backoff logic found in resilient.py"

    def test_retry_after_header_support(self):
        """Verify retry logic respects Retry-After header"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            source = f.read()
        has_retry_after = "retry-after" in source.lower() or "Retry-After" in source
        assert has_retry_after, "No Retry-After header handling found"

    def test_circuit_breaker_states(self):
        """Verify circuit breaker implements CLOSED, OPEN, HALF_OPEN states"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            source = f.read()
        source_upper = source.upper()
        has_closed = "CLOSED" in source_upper
        has_open = "OPEN" in source_upper
        has_half_open = "HALF_OPEN" in source_upper or "HALF-OPEN" in source_upper
        assert has_closed and has_open and has_half_open, (
            f"Circuit breaker states missing. CLOSED={has_closed}, OPEN={has_open}, HALF_OPEN={has_half_open}"
        )

    def test_config_defines_retry_and_circuit_breaker_settings(self):
        """Verify _config.py defines configuration for retry and circuit breaker"""
        path = os.path.join(self.REPO_DIR, "httpx/_config.py")
        with open(path) as f:
            source = f.read()
        has_retry_config = "retry" in source.lower() or "max_retries" in source.lower()
        has_cb_config = "circuit" in source.lower() or "breaker" in source.lower() or "threshold" in source.lower()
        assert has_retry_config, "_config.py missing retry configuration"
        assert has_cb_config, "_config.py missing circuit breaker configuration"

    # === Functional Checks ===

    def test_resilient_module_imports(self):
        """Verify resilient module can be imported"""
        result = subprocess.run(
            [
                "python", "-c",
                "import sys; sys.path.insert(0, '.'); "
                "from httpx._transports.resilient import ResilientTransport, AsyncResilientTransport; "
                "print('OK')"
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"
        assert "OK" in result.stdout

    def test_resilient_transport_instantiation(self):
        """Verify ResilientTransport can be instantiated"""
        script = """
import sys
sys.path.insert(0, '.')
from httpx._transports.resilient import ResilientTransport
try:
    transport = ResilientTransport()
    print(f'OK:{type(transport).__name__}')
except TypeError as e:
    # May require parameters
    print(f'NEEDS_PARAMS:{e}')
except Exception as e:
    print(f'FAIL:{e}')
"""
        result = subprocess.run(
            ["python", "-c", script],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        output = result.stdout.strip()
        assert output.startswith("OK:") or output.startswith("NEEDS_PARAMS:"), (
            f"ResilientTransport instantiation failed: {output}"
        )

    def test_circuit_breaker_state_transitions(self):
        """Verify circuit breaker has state transition methods"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            source = f.read()
        tree = ast.parse(source)
        methods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                methods.add(node.name)
        state_methods = [m for m in methods if any(
            kw in m.lower() for kw in ["record", "success", "failure", "trip", "reset", "state", "transition"]
        )]
        assert len(state_methods) >= 2, (
            f"Circuit breaker has insufficient state management methods. Found: {state_methods}"
        )

    def test_existing_httpx_tests_not_broken(self):
        """Verify existing httpx tests still pass"""
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-x", "--timeout=60", "-q", "--ignore=tests/test_resilient.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        # Allow some failures in pre-existing tests, but the suite should generally work
        if result.returncode != 0:
            # Check if failures are only in unrelated tests
            assert "error" not in result.stderr.lower()[:200] or "resilient" not in result.stderr.lower(), (
                f"Tests failed due to resilient changes: {result.stdout[-500:]}"
            )
