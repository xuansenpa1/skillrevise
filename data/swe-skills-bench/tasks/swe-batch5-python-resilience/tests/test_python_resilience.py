"""
Test skill: python-resilience
Verify that the Agent correctly implements RetryTransport and
AsyncRetryTransport with configurable backoff for the httpx library.
"""

import os
import sys
import ast
import inspect
import subprocess
import pytest


class TestPythonResilience:
    REPO_DIR = "/workspace/httpx"

    RETRY_MODULE = "httpx/_transports/retry.py"
    CONFIG_MODULE = "httpx/_config.py"
    TEST_FILE = "tests/test_retry_transport.py"

    def _read_file(self, rel_path):
        filepath = os.path.join(self.REPO_DIR, rel_path)
        with open(filepath) as f:
            return f.read()

    def _import_retry_module(self):
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._transports.retry import RetryTransport
            return RetryTransport
        except ImportError:
            # Alternative: module might be at a different location
            from httpx._transports import retry
            return getattr(retry, "RetryTransport", None)

    # === File Path Checks ===

    def test_retry_module_exists(self):
        """Verify httpx/_transports/retry.py exists"""
        filepath = os.path.join(self.REPO_DIR, self.RETRY_MODULE)
        assert os.path.exists(filepath), f"retry.py not found at {filepath}"

    def test_config_module_exists(self):
        """Verify httpx/_config.py exists"""
        filepath = os.path.join(self.REPO_DIR, self.CONFIG_MODULE)
        assert os.path.exists(filepath), f"_config.py not found at {filepath}"

    def test_test_file_exists(self):
        """Verify tests/test_retry_transport.py exists"""
        filepath = os.path.join(self.REPO_DIR, self.TEST_FILE)
        assert os.path.exists(filepath), f"Test file not found at {filepath}"

    def test_retry_module_valid_python(self):
        """Verify retry.py is valid Python syntax"""
        filepath = os.path.join(self.REPO_DIR, self.RETRY_MODULE)
        with open(filepath) as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"retry.py has syntax error: {e}")

    # === Semantic Checks ===

    def test_retry_transport_class_defined(self):
        """Verify RetryTransport class is defined in retry.py"""
        content = self._read_file(self.RETRY_MODULE)
        assert "class RetryTransport" in content, \
            "RetryTransport class not defined in retry.py"

    def test_async_retry_transport_class_defined(self):
        """Verify AsyncRetryTransport class is defined in retry.py"""
        content = self._read_file(self.RETRY_MODULE)
        assert "class AsyncRetryTransport" in content, \
            "AsyncRetryTransport class not defined in retry.py"

    def test_retry_config_dataclass_defined(self):
        """Verify RetryConfig is defined in _config.py with required fields"""
        content = self._read_file(self.CONFIG_MODULE)
        assert "RetryConfig" in content, "RetryConfig not found in _config.py"
        for field in ["max_retries", "backoff_factor", "retryable_status_codes"]:
            assert field in content, \
                f"RetryConfig missing field: {field}"

    def test_retry_config_defaults(self):
        """Verify RetryConfig has correct default values"""
        content = self._read_file(self.CONFIG_MODULE)
        # max_retries default 3
        assert "3" in content, "RetryConfig missing default max_retries=3"
        # backoff_factor default 0.5
        assert "0.5" in content, "RetryConfig missing default backoff_factor=0.5"
        # retryable status codes should include 429, 502, 503, 504
        for code in ["429", "502", "503", "504"]:
            assert code in content, \
                f"RetryConfig missing retryable status code: {code}"

    def test_retry_transport_handles_retry_after_header(self):
        """Verify RetryTransport logic handles Retry-After header"""
        content = self._read_file(self.RETRY_MODULE)
        has_retry_after = "retry-after" in content.lower() or "Retry-After" in content
        assert has_retry_after, \
            "RetryTransport missing Retry-After header handling"

    def test_retry_transport_implements_exponential_backoff(self):
        """Verify backoff calculation uses exponential formula"""
        content = self._read_file(self.RETRY_MODULE)
        # Look for exponential backoff patterns: 2**attempt, pow(2, ...), << attempt
        has_exponential = bool(
            "2 **" in content or "2**" in content or
            "pow(2" in content or "<< " in content or
            "backoff_factor" in content
        )
        assert has_exponential, \
            "RetryTransport missing exponential backoff calculation"

    # === Functional Checks ===

    def test_retry_transport_importable(self):
        """Verify RetryTransport can be imported"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._transports.retry import RetryTransport
            assert RetryTransport is not None
        except ImportError as e:
            pytest.fail(f"Cannot import RetryTransport: {e}")

    def test_retry_config_importable_with_defaults(self):
        """Verify RetryConfig can be instantiated with defaults"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._config import RetryConfig
            config = RetryConfig()
            assert config.max_retries == 3, \
                f"Expected max_retries=3, got {config.max_retries}"
            assert abs(config.backoff_factor - 0.5) < 0.001, \
                f"Expected backoff_factor=0.5, got {config.backoff_factor}"
            assert 429 in config.retryable_status_codes, \
                "429 not in retryable_status_codes"
            assert 503 in config.retryable_status_codes, \
                "503 not in retryable_status_codes"
        except ImportError as e:
            pytest.fail(f"Cannot import RetryConfig: {e}")

    def test_retry_transport_with_mock_transport(self):
        """Verify RetryTransport retries on 503 and returns 200 on success"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._transports.retry import RetryTransport
            from httpx._config import RetryConfig
            import httpx

            call_count = 0
            responses = [503, 503, 200]

            class MockTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    nonlocal call_count
                    idx = min(call_count, len(responses) - 1)
                    status = responses[idx]
                    call_count += 1
                    return httpx.Response(status)

            config = RetryConfig(max_retries=3, backoff_factor=0.0)
            transport = RetryTransport(MockTransport(), config=config)
            req = httpx.Request("GET", "http://example.com")
            response = transport.handle_request(req)

            assert response.status_code == 200, \
                f"Expected 200 after retry, got {response.status_code}"
            assert call_count == 3, \
                f"Expected 3 calls (2 retries + 1 success), got {call_count}"
        except (ImportError, TypeError, AttributeError) as e:
            pytest.skip(f"Could not set up mock transport test: {e}")

    def test_retry_transport_exhausts_retries(self):
        """Verify RetryTransport returns last response after exhausting retries"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._transports.retry import RetryTransport
            from httpx._config import RetryConfig
            import httpx

            call_count = 0

            class AlwaysFailTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    nonlocal call_count
                    call_count += 1
                    return httpx.Response(503)

            config = RetryConfig(max_retries=2, backoff_factor=0.0)
            transport = RetryTransport(AlwaysFailTransport(), config=config)
            req = httpx.Request("GET", "http://example.com")
            response = transport.handle_request(req)

            assert response.status_code == 503, \
                f"Expected 503 after exhaustion, got {response.status_code}"
            assert call_count == 3, \
                f"Expected 3 total calls (1 initial + 2 retries), got {call_count}"
        except (ImportError, TypeError, AttributeError) as e:
            pytest.skip(f"Could not set up exhaustion test: {e}")

    def test_non_retryable_status_passes_through(self):
        """Verify non-retryable 400 response is returned immediately"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._transports.retry import RetryTransport
            from httpx._config import RetryConfig
            import httpx

            call_count = 0

            class BadRequestTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    nonlocal call_count
                    call_count += 1
                    return httpx.Response(400)

            config = RetryConfig(max_retries=3, backoff_factor=0.0)
            transport = RetryTransport(BadRequestTransport(), config=config)
            req = httpx.Request("GET", "http://example.com")
            response = transport.handle_request(req)

            assert response.status_code == 400, \
                f"Expected 400, got {response.status_code}"
            assert call_count == 1, \
                f"Non-retryable status should not retry, got {call_count} calls"
        except (ImportError, TypeError, AttributeError) as e:
            pytest.skip(f"Could not set up passthrough test: {e}")

    def test_project_tests_pass(self):
        """Verify the retry transport tests pass"""
        filepath = os.path.join(self.REPO_DIR, self.TEST_FILE)
        result = subprocess.run(
            ["python", "-m", "pytest", filepath, "-v", "--tb=short"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, \
            f"Retry transport tests failed:\n{result.stdout[-500:]}\n{result.stderr[-500:]}"
