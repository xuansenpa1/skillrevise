"""
Test skill: python-resilience
Verify that the Agent correctly adds a resilient retry and timeout layer
to the httpx transport in the httpx repository.
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

    def test_resilience_module_exists(self):
        """Verify httpx/_resilience.py was created"""
        path = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        assert os.path.exists(path), f"_resilience.py not found at {path}"

    def test_resilience_module_is_valid_python(self):
        """Verify _resilience.py is syntactically valid"""
        path = os.path.join(self.REPO_DIR, "httpx/_resilience.py")
        with open(path) as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"_resilience.py has syntax errors: {e}")

    def test_resilience_tests_exist(self):
        """Verify tests/test_resilience.py was created"""
        path = os.path.join(self.REPO_DIR, "tests/test_resilience.py")
        assert os.path.exists(path), f"test_resilience.py not found at {path}"

    # === Semantic Checks ===

    def test_resilient_transport_class_defined(self):
        """Verify ResilientTransport class is defined in _resilience.py"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import ResilientTransport
            assert ResilientTransport is not None
        finally:
            sys.path.pop(0)

    def test_async_resilient_transport_class_defined(self):
        """Verify AsyncResilientTransport class is defined in _resilience.py"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import AsyncResilientTransport
            assert AsyncResilientTransport is not None
        finally:
            sys.path.pop(0)

    def test_resilient_transport_constructor_params(self):
        """Verify ResilientTransport constructor accepts required parameters"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import ResilientTransport
            sig = inspect.signature(ResilientTransport.__init__)
            params = list(sig.parameters.keys())
            assert "transport" in params, "Missing 'transport' parameter"
            assert "max_retries" in params, "Missing 'max_retries' parameter"
            # Check defaults
            max_retries_default = sig.parameters["max_retries"].default
            assert max_retries_default == 3, (
                f"max_retries default should be 3, got {max_retries_default}"
            )
        finally:
            sys.path.pop(0)

    def test_resilient_transport_has_handle_request(self):
        """Verify ResilientTransport implements handle_request method"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import ResilientTransport
            assert hasattr(ResilientTransport, "handle_request"), (
                "ResilientTransport missing handle_request method"
            )
        finally:
            sys.path.pop(0)

    def test_async_transport_has_handle_async_request(self):
        """Verify AsyncResilientTransport implements handle_async_request method"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import AsyncResilientTransport
            assert hasattr(AsyncResilientTransport, "handle_async_request"), (
                "AsyncResilientTransport missing handle_async_request method"
            )
        finally:
            sys.path.pop(0)

    def test_default_retryable_status_codes(self):
        """Verify default retryable_status_codes includes 429, 502, 503, 504"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import ResilientTransport
            sig = inspect.signature(ResilientTransport.__init__)
            if "retryable_status_codes" in sig.parameters:
                default = sig.parameters["retryable_status_codes"].default
                if default is not inspect.Parameter.empty and default is not None:
                    expected = {429, 502, 503, 504}
                    assert expected.issubset(set(default)), (
                        f"Default retryable_status_codes should include {expected}, got {default}"
                    )
        finally:
            sys.path.pop(0)

    # === Functional Checks ===

    def test_retry_on_transient_status_code(self):
        """Verify ResilientTransport retries on 503 and returns 200 on success"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import ResilientTransport
            from unittest.mock import Mock, MagicMock
            import httpx

            call_count = 0

            class MockTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    nonlocal call_count
                    call_count += 1
                    if call_count < 3:
                        return httpx.Response(503, request=request)
                    return httpx.Response(200, request=request, content=b"ok")

            transport = ResilientTransport(
                transport=MockTransport(),
                max_retries=5,
                initial_delay=0.01,
                max_retry_delay=0.05,
            )
            request = httpx.Request("GET", "http://example.com")
            response = transport.handle_request(request)
            assert response.status_code == 200, (
                f"Expected 200 after retries, got {response.status_code}"
            )
            assert call_count == 3, f"Expected 3 attempts, got {call_count}"
        finally:
            sys.path.pop(0)

    def test_retry_exhaustion_returns_last_response(self):
        """Verify exhausting retries returns the last error response"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import ResilientTransport
            import httpx

            class AlwaysFailTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    return httpx.Response(503, request=request)

            transport = ResilientTransport(
                transport=AlwaysFailTransport(),
                max_retries=2,
                initial_delay=0.01,
                max_retry_delay=0.05,
            )
            request = httpx.Request("GET", "http://example.com")
            response = transport.handle_request(request)
            assert response.status_code == 503, (
                f"Expected final 503 after exhausting retries, got {response.status_code}"
            )
        finally:
            sys.path.pop(0)

    def test_no_retry_on_non_retryable_exception(self):
        """Verify non-retryable exceptions propagate immediately"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import ResilientTransport
            import httpx

            call_count = 0

            class BadTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    nonlocal call_count
                    call_count += 1
                    raise ValueError("bad input")

            transport = ResilientTransport(
                transport=BadTransport(),
                max_retries=3,
                initial_delay=0.01,
            )
            request = httpx.Request("GET", "http://example.com")
            with pytest.raises(ValueError, match="bad input"):
                transport.handle_request(request)
            assert call_count == 1, (
                f"Expected exactly 1 call (no retry on ValueError), got {call_count}"
            )
        finally:
            sys.path.pop(0)

    def test_zero_retries_returns_first_response(self):
        """Verify max_retries=0 returns first response without retry"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import ResilientTransport
            import httpx

            call_count = 0

            class FailOnceTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    nonlocal call_count
                    call_count += 1
                    return httpx.Response(503, request=request)

            transport = ResilientTransport(
                transport=FailOnceTransport(),
                max_retries=0,
                initial_delay=0.01,
            )
            request = httpx.Request("GET", "http://example.com")
            response = transport.handle_request(request)
            assert response.status_code == 503
            assert call_count == 1, f"Expected 1 call with max_retries=0, got {call_count}"
        finally:
            sys.path.pop(0)

    def test_on_retry_callback_invoked(self):
        """Verify on_retry callback is called with correct arguments"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import ResilientTransport
            import httpx

            callback_calls = []

            def on_retry_cb(attempt, sleep_duration, error_or_response):
                callback_calls.append((attempt, sleep_duration, error_or_response))

            call_count = 0

            class RetryTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    nonlocal call_count
                    call_count += 1
                    if call_count < 3:
                        return httpx.Response(503, request=request)
                    return httpx.Response(200, request=request, content=b"ok")

            transport = ResilientTransport(
                transport=RetryTransport(),
                max_retries=5,
                initial_delay=0.01,
                max_retry_delay=0.05,
                on_retry=on_retry_cb,
            )
            request = httpx.Request("GET", "http://example.com")
            response = transport.handle_request(request)
            assert response.status_code == 200
            assert len(callback_calls) == 2, (
                f"Expected 2 callback invocations (2 retries), got {len(callback_calls)}"
            )
            # First callback should have attempt 1
            assert callback_calls[0][0] in (1, 2), (
                f"First callback attempt should be 1 or 2, got {callback_calls[0][0]}"
            )
        finally:
            sys.path.pop(0)

    def test_retry_on_connect_error(self):
        """Verify connection errors trigger retries"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._resilience import ResilientTransport
            import httpx

            call_count = 0

            class ConnErrTransport(httpx.BaseTransport):
                def handle_request(self, request):
                    nonlocal call_count
                    call_count += 1
                    if call_count < 3:
                        raise httpx.ConnectError("Connection refused")
                    return httpx.Response(200, request=request, content=b"ok")

            transport = ResilientTransport(
                transport=ConnErrTransport(),
                max_retries=5,
                initial_delay=0.01,
                max_retry_delay=0.05,
            )
            request = httpx.Request("GET", "http://example.com")
            response = transport.handle_request(request)
            assert response.status_code == 200, (
                f"Expected 200 after retrying ConnectError, got {response.status_code}"
            )
            assert call_count == 3, f"Expected 3 attempts, got {call_count}"
        finally:
            sys.path.pop(0)

    def test_agent_tests_pass(self):
        """Verify the agent's own test suite passes"""
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_resilience.py", "-v", "--tb=short"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"Agent test suite failed:\n{result.stdout[-1000:]}\n{result.stderr[-500:]}"
        )
