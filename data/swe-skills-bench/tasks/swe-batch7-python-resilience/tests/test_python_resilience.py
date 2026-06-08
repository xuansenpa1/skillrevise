"""
Test skill: python-resilience
Verify that the Agent correctly implements a resilient HTTP client wrapper
with retry, exponential backoff, timeout, and circuit breaker for httpx.
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
        """Verify _resilience.py exists in httpx directory"""
        fpath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        assert os.path.isfile(fpath), f"_resilience.py not found at {fpath}"

    def test_resilience_test_file_exists(self):
        """Verify test_resilience.py exists in tests directory"""
        fpath = os.path.join(self.REPO_DIR, "tests/test_resilience.py")
        assert os.path.isfile(fpath), f"test_resilience.py not found at {fpath}"

    def test_resilience_module_is_valid_python(self):
        """Verify _resilience.py is syntactically valid Python"""
        fpath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(fpath, "r") as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"_resilience.py has syntax error: {e}")

    # === Semantic Checks ===

    def test_resilient_async_client_class_exists(self):
        """Verify ResilientAsyncClient class is defined"""
        fpath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(fpath, "r") as f:
            tree = ast.parse(f.read())
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        assert "ResilientAsyncClient" in classes, (
            f"ResilientAsyncClient class not found. Found classes: {classes}"
        )

    def test_resilient_client_has_http_methods(self):
        """Verify ResilientAsyncClient has get, post, put, patch, delete methods"""
        fpath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(fpath, "r") as f:
            content = f.read()
        required_methods = ["get", "post", "put", "patch", "delete"]
        for method in required_methods:
            pattern = rf'(async\s+)?def\s+{method}\s*\('
            assert re.search(pattern, content), (
                f"ResilientAsyncClient missing '{method}' method"
            )

    def test_circuit_breaker_states_defined(self):
        """Verify circuit breaker defines CLOSED, OPEN, HALF_OPEN states"""
        fpath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(fpath, "r") as f:
            content = f.read()
        for state in ["CLOSED", "OPEN", "HALF_OPEN"]:
            assert state in content, (
                f"Circuit breaker missing state: '{state}'"
            )

    def test_circuit_breaker_open_error_defined(self):
        """Verify CircuitBreakerOpenError exception class is defined"""
        fpath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(fpath, "r") as f:
            content = f.read()
        has_error = bool(re.search(r'class\s+CircuitBreakerOpenError', content))
        assert has_error, "CircuitBreakerOpenError exception class not found"

    def test_exponential_backoff_formula(self):
        """Verify exponential backoff implementation with base * 2^attempt pattern"""
        fpath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(fpath, "r") as f:
            content = f.read()
        has_exp = bool(re.search(r'(\*\*|pow|2\s*\*\*)', content))
        has_min = bool(re.search(r'min\(', content))
        has_jitter = bool(re.search(r'(jitter|random)', content, re.IGNORECASE))
        assert has_exp, "Backoff should use exponential formula (2**attempt)"
        assert has_min, "Backoff should cap delay with min()"
        assert has_jitter, "Backoff should include jitter"

    def test_retryable_status_codes_defined(self):
        """Verify retryable status codes include 429, 502, 503, 504"""
        fpath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(fpath, "r") as f:
            content = f.read()
        for code in [429, 502, 503, 504]:
            assert str(code) in content, (
                f"Retryable status codes should include {code}"
            )

    def test_non_retryable_4xx_handling(self):
        """Verify 4xx errors (except 429) are not retried"""
        fpath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(fpath, "r") as f:
            content = f.read()
        # Should have logic excluding general 4xx from retry
        has_4xx_check = bool(re.search(r'(4\d\d|status_code.*4|not.*retry|raise.*immediately)', content, re.IGNORECASE))
        assert has_4xx_check, "Code should handle non-retryable 4xx errors"

    # === Functional Checks ===

    def test_import_resilient_async_client(self):
        """Verify ResilientAsyncClient can be imported"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import ResilientAsyncClient
            assert ResilientAsyncClient is not None
        except ImportError as e:
            pytest.fail(f"Cannot import ResilientAsyncClient: {e}")

    def test_import_circuit_breaker_open_error(self):
        """Verify CircuitBreakerOpenError can be imported"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import CircuitBreakerOpenError
            assert issubclass(CircuitBreakerOpenError, Exception), (
                "CircuitBreakerOpenError should be an Exception subclass"
            )
        except ImportError as e:
            pytest.fail(f"Cannot import CircuitBreakerOpenError: {e}")

    def test_client_constructor_accepts_config(self):
        """Verify ResilientAsyncClient constructor accepts retry and circuit breaker config"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import ResilientAsyncClient
            import inspect
            sig = inspect.signature(ResilientAsyncClient.__init__)
            params = list(sig.parameters.keys())
            # Should have parameters for retry and circuit breaker configuration
            has_retry_config = any("retry" in p.lower() for p in params)
            has_cb_config = any("circuit" in p.lower() or "breaker" in p.lower() for p in params)
            # Or it could accept them as keyword arguments
            assert has_retry_config or has_cb_config or len(params) >= 2, (
                f"Constructor should accept retry/circuit breaker config. Params: {params}"
            )
        except ImportError:
            pytest.skip("Cannot import ResilientAsyncClient")

    def test_circuit_breaker_state_machine(self):
        """Verify circuit breaker starts in CLOSED state and transitions correctly"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import ResilientAsyncClient
            client = ResilientAsyncClient()
            # Check initial state
            if hasattr(client, '_circuit_breaker'):
                cb = client._circuit_breaker
                state = getattr(cb, 'state', getattr(cb, '_state', None))
                if state is not None:
                    state_str = str(state).upper()
                    assert "CLOSED" in state_str, (
                        f"Circuit breaker should start CLOSED, got {state_str}"
                    )
            elif hasattr(client, 'circuit_breaker'):
                cb = client.circuit_breaker
                state = getattr(cb, 'state', getattr(cb, '_state', None))
                if state is not None:
                    state_str = str(state).upper()
                    assert "CLOSED" in state_str, (
                        f"Circuit breaker should start CLOSED, got {state_str}"
                    )
        except Exception as e:
            pytest.fail(f"Error testing circuit breaker state: {e}")

    def test_resilience_tests_pass(self):
        """Verify the project's resilience tests pass"""
        test_path = os.path.join(self.REPO_DIR, "tests/test_resilience.py")
        if not os.path.isfile(test_path):
            pytest.skip("test_resilience.py not found")
        result = subprocess.run(
            ["python", "-m", "pytest", test_path, "-v", "--tb=short", "-x"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        assert result.returncode == 0, (
            f"Resilience tests failed:\n{result.stdout[-1000:]}\n{result.stderr[-500:]}"
        )

    def test_default_config_values(self):
        """Verify default configuration values for retry and backoff"""
        fpath = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(fpath, "r") as f:
            content = f.read()
        # Check default values mentioned in requirements
        has_max_retries_3 = bool(re.search(r'(max_retries|MAX_RETRIES)\s*[=:]\s*3', content))
        has_backoff_base = bool(re.search(r'(backoff_base|BACKOFF_BASE)\s*[=:]\s*0\.5', content))
        has_backoff_max = bool(re.search(r'(backoff_max|BACKOFF_MAX)\s*[=:]\s*30', content))
        has_failure_threshold = bool(re.search(r'(failure_threshold|FAILURE_THRESHOLD)\s*[=:]\s*5', content))
        assert has_max_retries_3 or has_backoff_base or has_backoff_max, (
            "Module should define default retry config values (max_retries=3, backoff_base=0.5, backoff_max=30)"
        )
        assert has_failure_threshold, (
            "Module should define default circuit breaker failure_threshold=5"
        )
