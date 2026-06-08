"""
Test skill: python-configuration
Verify that the Agent adds a typed configuration system to FastAPI's tutorial
examples — Pydantic settings with nested groups, validators, env-var loading,
fail-fast behaviour, and dependency injection via endpoints.
"""

import os
import re
import ast
import subprocess
import pytest


class TestPythonConfiguration:
    REPO_DIR = "/workspace/fastapi"

    # ────────────────── helpers ──────────────────

    def _read(self, rel_path):
        fpath = os.path.join(self.REPO_DIR, rel_path)
        with open(fpath, "r") as f:
            return f.read()

    def _exists(self, rel_path):
        return os.path.isfile(os.path.join(self.REPO_DIR, rel_path))

    def _parse(self, rel_path):
        fpath = os.path.join(self.REPO_DIR, rel_path)
        with open(fpath, "r") as f:
            return ast.parse(f.read())

    # === File Path Checks ===

    def test_config_module_exists(self):
        """docs_src/settings/config.py must exist"""
        assert self._exists("docs_src/settings/config.py")

    def test_tutorial_app_exists(self):
        """docs_src/settings/tutorial001.py must exist"""
        assert self._exists("docs_src/settings/tutorial001.py")

    def test_test_file_exists(self):
        """tests/test_tutorial/test_settings/test_tutorial001.py must exist"""
        assert self._exists("tests/test_tutorial/test_settings/test_tutorial001.py")

    def test_test_init_exists(self):
        """tests/test_tutorial/test_settings/__init__.py must exist"""
        assert self._exists("tests/test_tutorial/test_settings/__init__.py")

    # === Semantic Checks — Settings Classes ===

    def test_database_settings_class(self):
        """DatabaseSettings class must be defined in config.py"""
        src = self._read("docs_src/settings/config.py")
        assert re.search(r'class\s+DatabaseSettings\b', src), (
            "DatabaseSettings class not found"
        )

    def test_redis_settings_class(self):
        """RedisSettings class must be defined in config.py"""
        src = self._read("docs_src/settings/config.py")
        assert re.search(r'class\s+RedisSettings\b', src), (
            "RedisSettings class not found"
        )

    def test_auth_settings_class(self):
        """AuthSettings class must be defined in config.py"""
        src = self._read("docs_src/settings/config.py")
        assert re.search(r'class\s+AuthSettings\b', src), (
            "AuthSettings class not found"
        )

    def test_app_settings_class(self):
        """AppSettings (root) class must be defined in config.py"""
        src = self._read("docs_src/settings/config.py")
        assert re.search(r'class\s+AppSettings\b', src), (
            "AppSettings class not found"
        )

    # === Semantic Checks — DatabaseSettings Fields ===

    def test_database_fields(self):
        """DatabaseSettings must have host, port, name, user, password, pool_size"""
        src = self._read("docs_src/settings/config.py")
        for field in ["host", "port", "name", "user", "password", "pool_size"]:
            assert re.search(rf'{field}\s*[=:]', src), (
                f"DatabaseSettings missing field: {field}"
            )

    def test_database_url_property(self):
        """DatabaseSettings must have a computed url property"""
        src = self._read("docs_src/settings/config.py")
        assert "url" in src, "DatabaseSettings missing url property"
        assert "postgresql://" in src, (
            "Database url should produce a postgresql:// connection string"
        )

    # === Semantic Checks — AppSettings ===

    def test_app_settings_nested_groups(self):
        """AppSettings must include database, redis, auth as nested settings"""
        src = self._read("docs_src/settings/config.py")
        for group in ["database", "redis", "auth"]:
            assert group in src, f"AppSettings missing nested group: {group}"

    def test_env_nested_delimiter(self):
        """AppSettings model config must use env_nested_delimiter = '__'"""
        src = self._read("docs_src/settings/config.py")
        assert "env_nested_delimiter" in src, (
            "env_nested_delimiter not configured in AppSettings"
        )

    def test_environment_literal_type(self):
        """environment field must be a Literal with local, staging, production"""
        src = self._read("docs_src/settings/config.py")
        assert "Literal" in src, "Literal type not used for environment field"
        for env in ["local", "staging", "production"]:
            assert f'"{env}"' in src or f"'{env}'" in src, (
                f"Environment Literal missing value: {env}"
            )

    def test_allowed_hosts_validator(self):
        """allowed_hosts must have a validator that splits comma-separated strings"""
        src = self._read("docs_src/settings/config.py")
        assert "allowed_hosts" in src, "allowed_hosts field not found"
        # Should have a validator or field_validator for splitting
        assert "validator" in src.lower() or "split" in src, (
            "allowed_hosts needs a validator to split comma-separated strings"
        )

    def test_production_debug_validation(self):
        """In production, debug must be False — a validator must enforce this"""
        src = self._read("docs_src/settings/config.py")
        assert "production" in src and "debug" in src, (
            "Production + debug validation logic not found"
        )

    def test_production_secret_key_length_validation(self):
        """In production, auth.secret_key must be >= 32 chars"""
        src = self._read("docs_src/settings/config.py")
        assert "32" in src or "secret_key" in src, (
            "Secret key length validation for production not found"
        )

    def test_is_production_property(self):
        """AppSettings must have an is_production computed property"""
        src = self._read("docs_src/settings/config.py")
        assert "is_production" in src, "is_production property not found"

    # === Semantic Checks — FastAPI App ===

    def test_fastapi_app_created(self):
        """tutorial001.py must create a FastAPI app instance"""
        src = self._read("docs_src/settings/tutorial001.py")
        assert "FastAPI" in src, "FastAPI app not found in tutorial001.py"

    def test_get_settings_dependency(self):
        """get_settings() dependency function must be defined"""
        src = self._read("docs_src/settings/tutorial001.py")
        assert re.search(r'def\s+get_settings\s*\(', src), (
            "get_settings dependency not found"
        )

    def test_lru_cache_used(self):
        """get_settings must use @lru_cache for singleton caching"""
        src = self._read("docs_src/settings/tutorial001.py")
        assert "lru_cache" in src, "lru_cache not used for settings caching"

    def test_info_endpoint(self):
        """GET /info endpoint must be defined"""
        src = self._read("docs_src/settings/tutorial001.py")
        assert re.search(r'["\'/]info["\']', src) or "/info" in src, (
            "GET /info endpoint not found"
        )

    def test_health_endpoint(self):
        """GET /health endpoint must be defined"""
        src = self._read("docs_src/settings/tutorial001.py")
        assert re.search(r'["\'/]health["\']', src) or "/health" in src, (
            "GET /health endpoint not found"
        )

    def test_health_redacts_password(self):
        """GET /health must redact the database password"""
        src = self._read("docs_src/settings/tutorial001.py")
        assert '***' in src or 'redact' in src.lower() or 'replace' in src.lower(), (
            "/health should redact the database password with '***'"
        )

    def test_validate_endpoint(self):
        """GET /settings/validate endpoint must be defined"""
        src = self._read("docs_src/settings/tutorial001.py")
        assert "validate" in src, "GET /settings/validate endpoint not found"

    # === Functional Checks ===

    def test_config_module_importable(self):
        """config.py must be importable"""
        result = subprocess.run(
            ["python", "-c",
             "import sys; sys.path.insert(0, '.'); "
             "from docs_src.settings.config import AppSettings, DatabaseSettings, "
             "RedisSettings, AuthSettings; print('OK')"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=30,
        )
        assert "OK" in result.stdout, (
            f"Import failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_settings_loads_with_env_vars(self):
        """AppSettings must load successfully when all required env vars are set"""
        env = {
            **os.environ,
            "DATABASE_NAME": "testdb",
            "DATABASE_USER": "testuser",
            "DATABASE_PASSWORD": "testpass",
            "AUTH_SECRET_KEY": "super-long-secret-key-for-testing-32ch",
        }
        result = subprocess.run(
            ["python", "-c",
             "import sys; sys.path.insert(0, '.'); "
             "from docs_src.settings.config import AppSettings; "
             "s = AppSettings(); "
             "assert s.database.name == 'testdb'; "
             "assert s.database.user == 'testuser'; "
             "print('OK')"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=30,
            env=env,
        )
        assert "OK" in result.stdout, (
            f"Settings load failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_missing_required_env_raises(self):
        """Missing required env vars must raise a ValidationError"""
        # Remove all DATABASE_* and AUTH_* vars to trigger validation
        clean_env = {
            k: v for k, v in os.environ.items()
            if not k.startswith(("DATABASE_", "AUTH_"))
        }
        result = subprocess.run(
            ["python", "-c",
             "import sys; sys.path.insert(0, '.'); "
             "from docs_src.settings.config import AppSettings; "
             "try:\n"
             "    AppSettings()\n"
             "    print('NO_ERROR')\n"
             "except Exception as e:\n"
             "    print('VALIDATION_ERROR')"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=30,
            env=clean_env,
        )
        assert "VALIDATION_ERROR" in result.stdout, (
            "Missing required env vars should raise ValidationError"
        )

    def test_tests_pass(self):
        """The tutorial test file must pass"""
        result = subprocess.run(
            ["python", "-m", "pytest",
             "tests/test_tutorial/test_settings/test_tutorial001.py",
             "-v", "--tb=short"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, (
            f"Tests failed:\n{result.stdout}\n{result.stderr}"
        )
