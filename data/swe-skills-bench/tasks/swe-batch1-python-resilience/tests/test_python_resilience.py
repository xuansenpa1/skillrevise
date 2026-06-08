"""
Test for 'python-resilience' skill — Resilient Transport Layer for httpx
Validates that the Agent implemented ResilientTransport with retry and
circuit-breaker logic in httpx/_transports/resilient.py.
"""

import os
import sys
import ast
import subprocess
import importlib
import pytest


class TestPythonResilience:
    """Verify resilient transport implementation for httpx."""

    REPO_DIR = "/workspace/httpx"

    @classmethod
    def setup_class(cls):
        if cls.REPO_DIR not in sys.path:
            sys.path.insert(0, cls.REPO_DIR)

    # ------------------------------------------------------------------
    # L1: file & syntax
    # ------------------------------------------------------------------

    def test_resilient_module_exists(self):
        """httpx/_transports/resilient.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "httpx", "_transports", "resilient.py")
        assert os.path.isfile(fpath), "resilient.py not found"

    def test_resilient_compiles(self):
        """resilient.py must compile without syntax errors."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "httpx/_transports/resilient.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: structural & functional verification
    # ------------------------------------------------------------------

    def _load_source(self):
        fpath = os.path.join(self.REPO_DIR, "httpx", "_transports", "resilient.py")
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_classes(self):
        source = self._load_source()
        tree = ast.parse(source)
        return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}

    def test_resilient_transport_class_exists(self):
        """ResilientTransport class must be defined."""
        classes = self._parse_classes()
        assert (
            "ResilientTransport" in classes
        ), f"ResilientTransport not found; classes: {list(classes.keys())}"

    def test_circuit_open_error_defined(self):
        """CircuitOpenError exception class must be defined."""
        classes = self._parse_classes()
        assert (
            "CircuitOpenError" in classes
        ), f"CircuitOpenError not found; classes: {list(classes.keys())}"

    def test_retry_max_attempts_configured(self):
        """Retry logic must define maximum 3 attempts."""
        source = self._load_source()
        assert "3" in source, "No mention of 3 retry attempts in source"
        # Verify there's a retry-related constant or parameter
        retry_keywords = ["max_retries", "max_attempts", "retry", "retries"]
        assert any(
            kw in source.lower() for kw in retry_keywords
        ), "No retry configuration found in source"

    def test_exponential_backoff_defined(self):
        """Exponential backoff (1s, 2s, 4s or similar) must be implemented."""
        source = self._load_source()
        backoff_indicators = ["backoff", "exponential", "sleep", "**", "pow"]
        found = sum(1 for ind in backoff_indicators if ind in source.lower())
        assert found >= 1, "No exponential backoff logic found"

    def test_circuit_breaker_states(self):
        """Circuit breaker must define CLOSED, OPEN, HALF_OPEN states."""
        source = self._load_source()
        for state in ["CLOSED", "OPEN", "HALF_OPEN"]:
            assert state in source, f"Circuit breaker state '{state}' not found"

    def test_circuit_breaker_failure_threshold(self):
        """Circuit should open after 5 consecutive failures."""
        source = self._load_source()
        assert "5" in source, "Failure threshold of 5 not found in source"
        threshold_keywords = [
            "threshold",
            "failure_count",
            "consecutive",
            "max_failures",
        ]
        assert any(
            kw in source.lower() for kw in threshold_keywords
        ), "No failure threshold configuration found"

    def test_circuit_breaker_cooldown(self):
        """30-second cooldown before HALF_OPEN transition."""
        source = self._load_source()
        assert "30" in source, "30-second cooldown not found in source"

    def test_no_retry_on_4xx(self):
        """4xx errors must NOT be retried — only 5xx and connection errors."""
        source = self._load_source()
        # Source should distinguish between 4xx (client error) and 5xx (server error)
        if "4" in source and ("5" in source or "500" in source):
            pass  # basic sanity
        status_patterns = [
            "status_code",
            "response.status",
            "5xx",
            "500",
            ">=500",
            "> 499",
        ]
        found = any(p in source.lower() for p in status_patterns)
        assert found, "No HTTP status code handling found for retry logic"

    def test_import_resilient_transport(self):
        """ResilientTransport should be importable at runtime."""
        result = subprocess.run(
            [
                "python",
                "-c",
                "from httpx._transports.resilient import ResilientTransport; print('OK')",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Import failed:\n{result.stderr}"
        assert "OK" in result.stdout

    def test_import_circuit_open_error(self):
        """CircuitOpenError should be importable."""
        result = subprocess.run(
            [
                "python",
                "-c",
                "from httpx._transports.resilient import CircuitOpenError; print('OK')",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Import failed:\n{result.stderr}"
        assert "OK" in result.stdout
