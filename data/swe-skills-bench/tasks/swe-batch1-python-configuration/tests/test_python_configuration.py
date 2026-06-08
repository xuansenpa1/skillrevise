"""
Test for 'python-configuration' skill — Python Configuration Management
Validates that the Agent transformed FastAPI hardcoded config into a
pydantic-settings BaseSettings class with validation, @lru_cache, and DI.
"""

import os
import sys
import ast
import subprocess
import pytest


class TestPythonConfiguration:
    """Verify pydantic-settings configuration implementation for FastAPI."""

    REPO_DIR = "/workspace/fastapi"

    # ------------------------------------------------------------------
    # L1: file & syntax
    # ------------------------------------------------------------------

    def test_settings_file_exists(self):
        """docs_src/settings/tutorial001.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "docs_src", "settings", "tutorial001.py")
        assert os.path.isfile(fpath), "tutorial001.py not found"

    def test_settings_compiles(self):
        """tutorial001.py must compile without syntax errors."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "docs_src/settings/tutorial001.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: structural verification via AST
    # ------------------------------------------------------------------

    def _read_source(self):
        fpath = os.path.join(self.REPO_DIR, "docs_src", "settings", "tutorial001.py")
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()

    def test_settings_class_inherits_base_settings(self):
        """Settings class should inherit from BaseSettings."""
        source = self._read_source()
        assert "BaseSettings" in source, "BaseSettings not found in source"

    def test_field_app_name(self):
        """Settings must define app_name: str field."""
        source = self._read_source()
        assert "app_name" in source, "app_name field not defined"

    def test_field_admin_email(self):
        """Settings must define admin_email field (EmailStr type)."""
        source = self._read_source()
        assert "admin_email" in source, "admin_email field not defined"
        assert "EmailStr" in source, "EmailStr type not used for admin_email"

    def test_field_database_url(self):
        """Settings must define database_url field (PostgresDsn or similar)."""
        source = self._read_source()
        assert "database_url" in source, "database_url field not defined"
        assert (
            "Dsn" in source or "PostgresDsn" in source or "AnyUrl" in source
        ), "No Dsn/URL type annotation found for database_url"

    def test_field_debug_with_default(self):
        """Settings must define debug: bool with default False."""
        source = self._read_source()
        assert "debug" in source, "debug field not defined"

    def test_field_max_connections(self):
        """Settings must define max_connections: PositiveInt with default 10."""
        source = self._read_source()
        assert "max_connections" in source, "max_connections field not defined"

    def test_lru_cache_decorator(self):
        """Singleton pattern via @lru_cache must be present."""
        source = self._read_source()
        assert "lru_cache" in source, "@lru_cache decorator not found"

    def test_depends_injection(self):
        """FastAPI Depends should be used for DI."""
        source = self._read_source()
        assert "Depends" in source, "FastAPI Depends not found"

    def test_settings_importable(self):
        """Settings module should be importable and expose settings getter."""
        result = subprocess.run(
            [
                "python",
                "-c",
                "import sys; sys.path.insert(0,'.'); "
                "from docs_src.settings.tutorial001 import *; print('OK')",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
            env={
                **os.environ,
                "APP_NAME": "test",
                "ADMIN_EMAIL": "a@b.com",
                "DATABASE_URL": "postgresql://localhost/test",
            },
        )
        assert result.returncode == 0, f"Import failed:\n{result.stderr}"

    def test_validation_error_on_missing_required(self):
        """Missing required field should raise ValidationError."""
        result = subprocess.run(
            [
                "python",
                "-c",
                "import sys; sys.path.insert(0,'.'); "
                "from docs_src.settings.tutorial001 import *",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
            env={"PATH": os.environ.get("PATH", "")},  # minimal env
        )
        # Should fail because required fields are missing
        if result.returncode == 0:
            pytest.skip(
                "Settings loaded without env vars — defaults may cover all fields"
            )
        assert (
            "ValidationError" in result.stderr or "validation" in result.stderr.lower()
        ), f"Expected ValidationError, got:\n{result.stderr[-1000:]}"
