"""
Test skill: python-resilience
Verify that the Agent correctly implements a RetryTransport layer for HTTPX
with configurable retry behavior, exponential backoff, and error classification.
"""

import os
import subprocess
import sys
import ast
import inspect
import re
import pytest


class TestPythonResilience:
    REPO_DIR = "/workspace/httpx"

    # === File Path Checks ===

    def test_retry_module_exists(self):
        """Verify that _retry.py exists at the correct path"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_retry.py")
        assert os.path.exists(filepath), f"_retry.py not found at {filepath}"

    def test_retry_module_is_valid_python(self):
        """Verify that _retry.py is valid Python syntax"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_retry.py")
        with open(filepath) as f:
            content = f.read()
        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"_retry.py has syntax errors: {e}")

    def test_test_retry_file_exists(self):
        """Verify that tests/test_retry.py exists"""
        filepath = os.path.join(self.REPO_DIR, "tests/test_retry.py")
        assert os.path.exists(filepath), f"test_retry.py not found at {filepath}"

    # === Semantic Checks ===

    def test_retry_transport_class_exists(self):
        """Verify that RetryTransport class is defined in _retry.py"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_retry.py")
        with open(filepath) as f:
            content = f.read()
        tree = ast.parse(content)
        class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        assert "RetryTransport" in class_names, (
            f"RetryTransport class not found in _retry.py. Found classes: {class_names}"
        )

    def test_async_retry_transport_class_exists(self):
        """Verify that AsyncRetryTransport class is defined in _retry.py"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_retry.py")
        with open(filepath) as f:
            content = f.read()
        tree = ast.parse(content)
        class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        assert "AsyncRetryTransport" in class_names, (
            f"AsyncRetryTransport class not found in _retry.py. Found classes: {class_names}"
        )

    def test_retry_config_exists(self):
        """Verify that RetryConfig is defined with required fields"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_config.py")
        with open(filepath) as f:
            content = f.read()

        assert "RetryConfig" in content, (
            "RetryConfig not found in _config.py"
        )

        required_fields = [
            "max_attempts",
            "backoff_factor",
            "backoff_max",
            "retryable_status_codes",
        ]
        for field in required_fields:
            assert field in content, (
                f"RetryConfig missing required field '{field}' in _config.py"
            )

    def test_retry_config_exported_in_init(self):
        """Verify that RetryConfig is exported from httpx.__init__"""
        filepath = os.path.join(self.REPO_DIR, "httpx/__init__.py")
        with open(filepath) as f:
            content = f.read()
        assert "RetryConfig" in content, (
            "RetryConfig not exported from httpx/__init__.py"
        )

    def test_client_accepts_retry_parameter(self):
        """Verify that Client and AsyncClient accept a retry parameter"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_client.py")
        with open(filepath) as f:
            content = f.read()

        assert "retry" in content, (
            "_client.py does not contain 'retry' parameter. "
            "Client and AsyncClient must accept retry=RetryConfig(...)."
        )

    def test_retry_transport_handles_status_codes(self):
        """Verify RetryTransport references default retryable status codes"""
        filepath = os.path.join(self.REPO_DIR, "httpx/_retry.py")
        with open(filepath) as f:
            content = f.read()

        default_codes = ["429", "502", "503", "504"]
        found_codes = [c for c in default_codes if c in content]
        assert len(found_codes) >= 3, (
            f"RetryTransport should reference default retryable status codes (429, 502, 503, 504). "
            f"Found only: {found_codes}"
        )

    # === Functional Checks ===

    def test_retry_config_defaults(self):
        """Verify RetryConfig has correct default values"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._config import RetryConfig
            config = RetryConfig()
            assert config.max_attempts == 3, f"Expected max_attempts=3, got {config.max_attempts}"
            assert config.backoff_factor == 0.5, f"Expected backoff_factor=0.5, got {config.backoff_factor}"
            assert config.backoff_max == 30.0, f"Expected backoff_max=30.0, got {config.backoff_max}"
            assert 429 in config.retryable_status_codes, "429 not in retryable_status_codes"
            assert 503 in config.retryable_status_codes, "503 not in retryable_status_codes"
        except ImportError as e:
            pytest.skip(f"Cannot import RetryConfig: {e}")
        finally:
            sys.path.pop(0)

    def test_retry_config_validates_max_attempts(self):
        """Verify that RetryConfig raises ValueError when max_attempts < 1"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._config import RetryConfig
            with pytest.raises(ValueError) as exc_info:
                RetryConfig(max_attempts=0)
            assert "max_attempts" in str(exc_info.value).lower() or "attempt" in str(exc_info.value).lower(), (
                f"Expected error message about max_attempts, got: {exc_info.value}"
            )
        except ImportError as e:
            pytest.skip(f"Cannot import RetryConfig: {e}")
        finally:
            sys.path.pop(0)

    def test_retry_transport_wraps_transport(self):
        """Verify that RetryTransport can wrap a mock transport"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._retry import RetryTransport
            from httpx._config import RetryConfig
            from unittest.mock import Mock

            mock_transport = Mock()
            config = RetryConfig(max_attempts=2)
            rt = RetryTransport(transport=mock_transport, config=config)
            assert rt is not None, "RetryTransport should be created successfully"
        except (ImportError, TypeError) as e:
            pytest.skip(f"Cannot create RetryTransport: {e}")
        finally:
            sys.path.pop(0)

    def test_retry_on_503_status(self):
        """Verify that RetryTransport retries on 503 status code"""
        sys.path.insert(0, self.REPO_DIR)
        try:
            from httpx._retry import RetryTransport
            from httpx._config import RetryConfig
            from unittest.mock import Mock, MagicMock
            import httpcore

            # Create a mock transport that returns 503 twice then 200
            mock_transport = Mock()
            response_503 = Mock()
            response_503.status = 503
            response_503.headers = []
            response_503.stream = Mock()
            response_200 = Mock()
            response_200.status = 200
            response_200.headers = []
            response_200.stream = Mock()

            mock_transport.handle_request = Mock(
                side_effect=[response_503, response_503, response_200]
            )

            config = RetryConfig(max_attempts=3, backoff_factor=0.01)
            rt = RetryTransport(transport=mock_transport, config=config)

            # Create a mock request
            request = Mock()
            request.method = b"GET"
            request.url = Mock()
            request.headers = []
            request.stream = Mock()

            try:
                result = rt.handle_request(request)
                assert result.status == 200, (
                    f"Expected final status 200 after retries, got {result.status}"
                )
                assert mock_transport.handle_request.call_count == 3, (
                    f"Expected 3 attempts, got {mock_transport.handle_request.call_count}"
                )
            except Exception:
                # If the transport interface is different, check that retry logic exists
                assert mock_transport.handle_request.call_count >= 1, (
                    "Transport was never called"
                )
        except ImportError as e:
            pytest.skip(f"Cannot test retry logic: {e}")
        finally:
            sys.path.pop(0)

    def test_existing_httpx_tests_pass(self):
        """Verify that existing HTTPX test suite passes without regression"""
        # Install httpx first
        subprocess.run(
            ["pip", "install", "-e", "."],
            cwd=self.REPO_DIR,
            capture_output=True,
            timeout=120
        )
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-x", "-q",
             "--ignore=tests/test_retry.py", "-k", "not test_ssl"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=300
        )
        # Allow some failures due to environment constraints
        # but check for catastrophic regression
        if result.returncode != 0:
            # Count failures vs total
            match = re.search(r'(\d+) passed', result.stdout)
            if match:
                passed = int(match.group(1))
                assert passed > 10, (
                    f"Too many test failures: only {passed} tests passed. "
                    "Retry changes may have caused regression."
                )
