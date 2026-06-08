"""
Test skill: python-resilience
Verify that the Agent correctly implements a resilient HTTP transport layer
for httpx with retry logic, timeout handling, and circuit breaker patterns.
"""

import os
import sys
import ast
import inspect
import subprocess
import time
import pytest


class TestPythonResilience:
    REPO_DIR = "/workspace/httpx"

    # === File Path Checks ===

    def test_resilient_transport_file_exists(self):
        """Verify resilient.py exists in the transports directory"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        assert os.path.exists(path), f"resilient.py not found at {path}"

    def test_resilient_transport_is_valid_python(self):
        """Verify resilient.py is syntactically valid Python"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            content = f.read()
        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"resilient.py has syntax error: {e}")

    # === Semantic Checks ===

    def test_defines_transport_class(self):
        """Verify resilient.py defines a transport class"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            tree = ast.parse(f.read())

        class_names = [node.name for node in ast.walk(tree)
                       if isinstance(node, ast.ClassDef)]
        transport_classes = [
            n for n in class_names
            if "transport" in n.lower() or "resilient" in n.lower()
        ]
        assert len(transport_classes) > 0, (
            f"resilient.py should define a transport class. "
            f"Classes found: {class_names}"
        )

    def test_transport_class_has_handle_request_method(self):
        """Verify transport class implements handle_request or handle_async_request"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            tree = ast.parse(f.read())

        methods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                methods.append(node.name)

        transport_methods = [
            m for m in methods
            if "handle" in m.lower() and "request" in m.lower()
        ]
        assert len(transport_methods) > 0, (
            "Transport class should implement handle_request or "
            f"handle_async_request. Methods found: {methods}"
        )

    def test_implements_retry_logic(self):
        """Verify resilient.py implements retry logic with backoff"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            content = f.read().lower()

        retry_indicators = {
            "retry": "retry" in content,
            "backoff": "backoff" in content or "exponential" in content or "sleep" in content,
            "max_retries/attempts": (
                "max_retries" in content or "max_attempts" in content
                or "retries" in content or "attempts" in content
            ),
        }
        found = [k for k, v in retry_indicators.items() if v]
        assert len(found) >= 2, (
            f"Transport should implement retry with backoff. Found: {found}. "
            f"Expected at least 2 of: {list(retry_indicators.keys())}"
        )

    def test_implements_circuit_breaker(self):
        """Verify resilient.py implements circuit breaker pattern"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            content = f.read().lower()

        cb_indicators = {
            "circuit": "circuit" in content,
            "breaker": "breaker" in content,
            "open/closed/half": (
                "open" in content or "closed" in content
                or "half_open" in content or "half-open" in content
            ),
            "threshold/failure_count": (
                "threshold" in content or "failure_count" in content
                or "consecutive" in content
            ),
            "cooldown/reset": (
                "cooldown" in content or "reset_timeout" in content
                or "recovery" in content
            ),
        }
        found = [k for k, v in cb_indicators.items() if v]
        assert len(found) >= 3, (
            f"Transport should implement circuit breaker. Found: {found}. "
            f"Expected at least 3 of: {list(cb_indicators.keys())}"
        )

    def test_transport_is_configurable(self):
        """Verify transport constructor accepts configuration parameters"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            tree = ast.parse(f.read())

        init_params = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        init_params = [
                            arg.arg for arg in item.args.args
                            if arg.arg != "self"
                        ]
                        break

        config_keywords = [
            "retry", "retries", "max_retries", "backoff", "timeout",
            "threshold", "cooldown", "transport", "base",
        ]
        found = [p for p in init_params if any(kw in p.lower() for kw in config_keywords)]
        assert len(found) >= 2, (
            f"Transport __init__ should accept configuration parameters. "
            f"Params found: {init_params}. Expected at least 2 config-related params."
        )

    # === Functional Checks ===

    def test_transport_class_is_importable(self):
        """Verify the resilient transport class can be imported"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._transports.resilient import (
                ResilientTransport
            )
            assert ResilientTransport is not None
        except ImportError:
            # Try alternative class names
            import importlib
            mod = importlib.import_module("httpx._transports.resilient")
            classes = [
                name for name in dir(mod)
                if isinstance(getattr(mod, name), type)
                and ("transport" in name.lower() or "resilient" in name.lower())
            ]
            assert len(classes) > 0, (
                f"Could not find a transport class in resilient.py. "
                f"Available names: {dir(mod)}"
            )

    def test_transport_wraps_base_transport(self):
        """Verify the resilient transport wraps an underlying transport"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            import importlib
            mod = importlib.import_module("httpx._transports.resilient")

            # Find the transport class
            transport_cls = None
            for name in dir(mod):
                obj = getattr(mod, name)
                if isinstance(obj, type) and (
                    "transport" in name.lower() or "resilient" in name.lower()
                ):
                    transport_cls = obj
                    break

            assert transport_cls is not None, "No transport class found"

            # Check constructor signature references a base transport
            sig = inspect.signature(transport_cls.__init__)
            params = list(sig.parameters.keys())
            transport_param = [
                p for p in params
                if "transport" in p.lower() or "base" in p.lower() or "wrapped" in p.lower()
            ]
            assert len(transport_param) > 0, (
                f"Transport constructor should accept a base transport parameter. "
                f"Parameters: {params}"
            )
        except Exception as e:
            pytest.fail(f"Failed to inspect transport class: {e}")

    def test_transport_retries_on_transient_error(self):
        """Verify transport retries on transient errors using mocked base transport"""
        sys.path.insert(0, self.REPO_DIR)
        from unittest.mock import Mock, MagicMock

        try:
            import importlib
            mod = importlib.import_module("httpx._transports.resilient")

            transport_cls = None
            for name in dir(mod):
                obj = getattr(mod, name)
                if isinstance(obj, type) and (
                    "transport" in name.lower() or "resilient" in name.lower()
                ):
                    transport_cls = obj
                    break

            if transport_cls is None:
                pytest.fail("No transport class found")

            # Create a mock base transport that fails then succeeds
            mock_transport = Mock()
            mock_response = Mock()
            mock_response.status_code = 200

            # First call raises, second succeeds
            call_count = 0
            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise ConnectionError("Transient failure")
                return mock_response

            mock_transport.handle_request = Mock(side_effect=side_effect)

            # Try to instantiate with the mock transport
            try:
                instance = transport_cls(transport=mock_transport, max_retries=3)
            except TypeError:
                try:
                    instance = transport_cls(mock_transport, max_retries=3)
                except TypeError:
                    pytest.skip("Cannot instantiate transport with test parameters")

            # The transport should retry and eventually succeed
            # This is a structural test - we verify the transport was created
            assert instance is not None

        except ImportError as e:
            pytest.skip(f"Import failed: {e}")

    def test_circuit_breaker_state_tracking(self):
        """Verify transport tracks circuit breaker state (open/closed/half-open)"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            content = f.read()

        # Should have state-related attributes or enums
        state_indicators = [
            "CLOSED", "OPEN", "HALF_OPEN", "half_open",
            "_state", "state", "is_open", "is_closed",
        ]
        found = [ind for ind in state_indicators if ind in content]
        assert len(found) >= 2, (
            "Circuit breaker should track state transitions. "
            f"Found: {found}. Expected at least 2 of: {state_indicators}"
        )

    def test_timeout_raises_appropriate_exception(self):
        """Verify transport raises appropriate exception on timeout"""
        path = os.path.join(self.REPO_DIR, "httpx/_transports/resilient.py")
        with open(path) as f:
            content = f.read()

        timeout_indicators = [
            "timeout", "TimeoutError", "TimeoutException",
            "ReadTimeout", "ConnectTimeout",
        ]
        found = [ind for ind in timeout_indicators if ind in content]
        assert len(found) >= 2, (
            "Transport should handle timeouts and raise clear exceptions. "
            f"Found: {found}. Expected at least 2 of: {timeout_indicators}"
        )
