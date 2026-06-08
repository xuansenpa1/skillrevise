"""
Test skill: python-resilience
Verify that the Agent correctly implements a resilient HTTP transport layer
for HTTPX with retry, backoff, jitter, Retry-After handling, and logging.
"""

import os
import sys
import ast
import inspect
import subprocess
import pytest


class TestPythonResilience:
    REPO_DIR = "/workspace/httpx"

    # === File Path Checks ===

    def test_resilient_transport_file_exists(self):
        """Verify the resilient transport module was created"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        assert os.path.exists(path), f"resilient.py not found at {path}"
        with open(path) as f:
            ast.parse(f.read())

    def test_resilient_tests_file_exists(self):
        """Verify the resilient transport test file was created"""
        path = os.path.join(self.REPO_DIR, "tests/test_resilient_transport.py")
        assert os.path.exists(path), f"test_resilient_transport.py not found at {path}"
        with open(path) as f:
            ast.parse(f.read())

    # === Semantic Checks ===

    def test_resilient_transport_class_exists(self):
        """Verify ResilientTransport class is defined with correct parameters"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._transports.resilient import ResilientTransport
            assert callable(ResilientTransport), "ResilientTransport should be a class"
            sig = inspect.signature(ResilientTransport.__init__)
            params = list(sig.parameters.keys())
            # Check for key config parameters
            expected_params = ["max_retries", "initial_backoff", "max_backoff"]
            for param in expected_params:
                assert param in params, \
                    f"ResilientTransport.__init__ missing parameter: {param}"
        finally:
            sys.path.pop(0)
            for m in list(sys.modules.keys()):
                if "httpx" in m:
                    del sys.modules[m]

    def test_resilient_transport_has_handle_request(self):
        """Verify ResilientTransport implements handle_request method"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            content = f.read()
        assert "handle_request" in content, \
            "ResilientTransport should implement handle_request"

    def test_resilient_transport_has_async_variant(self):
        """Verify async transport handling is implemented"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            content = f.read()
        has_async = (
            "handle_async_request" in content or
            "AsyncResilientTransport" in content or
            "async def" in content
        )
        assert has_async, \
            "Should implement async transport handling"

    def test_failure_classification_logic(self):
        """Verify transport distinguishes transient vs permanent failures"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            content = f.read()
        # Should reference retryable status codes
        retryable_codes = ["429", "502", "503", "504"]
        found_codes = sum(1 for code in retryable_codes if code in content)
        assert found_codes >= 3, \
            f"Should define retryable status codes (429, 502, 503, 504). Found {found_codes} codes"
        # Should handle ConnectionError/TimeoutError
        has_error_handling = (
            "ConnectionError" in content or
            "TimeoutError" in content or
            "ConnectError" in content
        )
        assert has_error_handling, \
            "Should handle transient connection/timeout errors"

    def test_backoff_and_jitter_implemented(self):
        """Verify exponential backoff with jitter is implemented"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            content = f.read()
        # Should have exponential backoff logic
        has_backoff = (
            "exponential" in content.lower() or
            "backoff" in content.lower() or
            "**" in content or
            "pow" in content
        )
        assert has_backoff, "Should implement exponential backoff"
        # Should have jitter
        has_jitter = (
            "jitter" in content.lower() or
            "random" in content.lower() or
            "uniform" in content.lower()
        )
        assert has_jitter, "Should add random jitter to backoff delays"

    def test_retry_after_header_handling(self):
        """Verify Retry-After header is honored"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            content = f.read()
        assert "retry-after" in content.lower() or "Retry-After" in content, \
            "Should handle Retry-After header"

    def test_logging_configured(self):
        """Verify logging is set up with correct logger name"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            content = f.read()
        assert "logging" in content, "Should use Python's logging module"
        assert "httpx._transports.resilient" in content or "getLogger" in content, \
            "Should configure logger with appropriate name"

    # === Functional Checks ===

    def _install_httpx(self):
        """Helper: install httpx in development mode"""
        result = subprocess.run(
            ["pip", "install", "-e", "."],
            cwd=self.REPO_DIR,
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            pytest.skip(f"Failed to install httpx: {result.stderr[:500]}")

    def test_resilient_transport_instantiation(self):
        """Verify ResilientTransport can be instantiated with default params"""
        self._install_httpx()
        result = subprocess.run(
            ["python", "-c",
             "from httpx._transports.resilient import ResilientTransport; "
             "from unittest.mock import Mock; "
             "mock_transport = Mock(); "
             "rt = ResilientTransport(transport=mock_transport); "
             "assert rt is not None; "
             "print('PASS')"],
            cwd=self.REPO_DIR,
            capture_output=True, text=True, timeout=30
        )
        assert "PASS" in result.stdout, \
            f"Failed to instantiate ResilientTransport: {result.stderr[:500]}"

    def test_client_resilient_parameter(self):
        """Verify Client accepts resilient parameter"""
        self._install_httpx()
        path = os.path.join(self.REPO_DIR, "httpx/_client.py")
        with open(path) as f:
            content = f.read()
        assert "resilient" in content, \
            "Client.__init__ should accept a 'resilient' parameter"

    def test_agent_tests_pass(self):
        """Verify the Agent's own resilient transport tests pass"""
        test_path = os.path.join(self.REPO_DIR, "tests/test_resilient_transport.py")
        if not os.path.exists(test_path):
            pytest.skip("Agent test file not found")
        self._install_httpx()
        result = subprocess.run(
            ["python", "-m", "pytest", test_path, "-v", "--tb=short", "-x"],
            cwd=self.REPO_DIR,
            capture_output=True, text=True, timeout=120
        )
        assert result.returncode == 0, \
            f"Agent's tests failed:\n{result.stdout[:2000]}\n{result.stderr[:500]}"

    def test_retry_on_503_with_mock(self):
        """Verify ResilientTransport retries on 503 and succeeds when server recovers"""
        self._install_httpx()
        test_code = '''
import sys
sys.path.insert(0, ".")
from unittest.mock import Mock, MagicMock, patch
from httpx._transports.resilient import ResilientTransport

# Create a mock transport that fails twice with 503 then succeeds
mock_transport = Mock()
call_count = [0]

def mock_handle(*args, **kwargs):
    call_count[0] += 1
    if call_count[0] <= 2:
        # Return a 503 response
        resp = Mock()
        resp.status = 503
        resp.headers = {}
        # Support different response formats
        try:
            resp.stream = Mock()
            resp.extensions = {}
        except:
            pass
        return resp
    # Return 200 on third call
    resp = Mock()
    resp.status = 200
    resp.headers = {}
    try:
        resp.stream = Mock()
        resp.extensions = {}
    except:
        pass
    return resp

mock_transport.handle_request = mock_handle

rt = ResilientTransport(
    transport=mock_transport,
    max_retries=3,
    initial_backoff=0.01,
    max_backoff=0.05,
)

# Make request
try:
    request = Mock()
    request.method = b"GET"
    request.url = Mock()
    request.url.raw = (b"https", b"example.com", 443, b"/test")
    request.headers = []
    request.stream = Mock()
    resp = rt.handle_request(request)
    assert resp.status == 200, f"Expected 200 after retries, got {resp.status}"
    assert call_count[0] == 3, f"Expected 3 calls (2 retries + 1 success), got {call_count[0]}"
    print("PASS")
except Exception as e:
    print(f"FAIL: {e}")
'''
        result = subprocess.run(
            ["python", "-c", test_code],
            cwd=self.REPO_DIR,
            capture_output=True, text=True, timeout=30
        )
        assert "PASS" in result.stdout, \
            f"Retry on 503 test failed: stdout={result.stdout[:500]}, stderr={result.stderr[:500]}"
