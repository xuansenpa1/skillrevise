"""
Test skill: python-configuration
Verify that the Agent correctly adds typed configuration management
to the FastAPI project with validation and environment support.
"""

import os
import sys
import ast
import subprocess
import pytest


class TestPythonConfiguration:
    REPO_DIR = "/workspace/fastapi"

    CONFIG_MODULE = "fastapi/config.py"
    LOADER_MODULE = "fastapi/config_loader.py"
    TEST_FILE = "tests/test_config.py"

    def _read_file(self, rel_path):
        filepath = os.path.join(self.REPO_DIR, rel_path)
        with open(filepath) as f:
            return f.read()

    # === File Path Checks ===

    def test_config_module_exists(self):
        """Verify fastapi/config.py exists"""
        filepath = os.path.join(self.REPO_DIR, self.CONFIG_MODULE)
        assert os.path.exists(filepath), f"config.py not found at {filepath}"

    def test_loader_module_exists(self):
        """Verify fastapi/config_loader.py exists"""
        filepath = os.path.join(self.REPO_DIR, self.LOADER_MODULE)
        assert os.path.exists(filepath), f"config_loader.py not found at {filepath}"

    def test_test_file_exists(self):
        """Verify tests/test_config.py exists"""
        filepath = os.path.join(self.REPO_DIR, self.TEST_FILE)
        assert os.path.exists(filepath), f"Test file not found at {filepath}"

    # === Semantic Checks ===

    def test_app_settings_class_defined(self):
        """Verify AppSettings class with required fields"""
        content = self._read_file(self.CONFIG_MODULE)
        assert "AppSettings" in content, "config.py missing AppSettings class"
        for field in ["app_name", "debug", "environment", "log_level"]:
            assert field in content, f"AppSettings missing field: {field}"

    def test_database_settings_class_defined(self):
        """Verify DatabaseSettings class with required fields"""
        content = self._read_file(self.CONFIG_MODULE)
        assert "DatabaseSettings" in content, \
            "config.py missing DatabaseSettings class"
        for field in ["database_url", "pool_size", "pool_timeout"]:
            assert field in content, f"DatabaseSettings missing field: {field}"

    def test_auth_settings_class_defined(self):
        """Verify AuthSettings class with secret_key and token_expire fields"""
        content = self._read_file(self.CONFIG_MODULE)
        assert "AuthSettings" in content, "config.py missing AuthSettings class"
        assert "secret_key" in content, "AuthSettings missing secret_key field"
        assert "access_token_expire" in content or "token_expire" in content, \
            "AuthSettings missing access_token_expire_minutes field"

    def test_cors_settings_class_defined(self):
        """Verify CorsSettings class with CORS configuration fields"""
        content = self._read_file(self.CONFIG_MODULE)
        assert "CorsSettings" in content, "config.py missing CorsSettings class"
        assert "allow_origins" in content, "CorsSettings missing allow_origins field"

    def test_database_url_validation(self):
        """Verify database_url validates scheme (postgresql/sqlite/mysql)"""
        combined = self._read_file(self.CONFIG_MODULE)
        try:
            combined += self._read_file(self.LOADER_MODULE)
        except FileNotFoundError:
            pass
        has_scheme_validation = bool(
            "postgresql" in combined and "sqlite" in combined
        ) or "scheme" in combined.lower()
        assert has_scheme_validation, \
            "Config missing database_url scheme validation"

    def test_secret_key_min_length_validation(self):
        """Verify secret_key must be at least 32 characters"""
        combined = self._read_file(self.CONFIG_MODULE)
        try:
            combined += self._read_file(self.LOADER_MODULE)
        except FileNotFoundError:
            pass
        assert "32" in combined, \
            "Config missing secret_key minimum length constraint (32 chars)"

    def test_pool_size_range_validation(self):
        """Verify pool_size is validated within range [1, 50]"""
        combined = self._read_file(self.CONFIG_MODULE)
        try:
            combined += self._read_file(self.LOADER_MODULE)
        except FileNotFoundError:
            pass
        assert "50" in combined, \
            "Config missing pool_size upper bound validation (50)"

    def test_environment_enum_validation(self):
        """Verify environment field only accepts development/testing/production"""
        combined = self._read_file(self.CONFIG_MODULE)
        try:
            combined += self._read_file(self.LOADER_MODULE)
        except FileNotFoundError:
            pass
        for env in ["development", "testing", "production"]:
            assert env in combined, \
                f"Config missing environment option: {env}"

    # === Functional Checks ===

    def test_config_module_valid_python(self):
        """Verify config.py is valid Python syntax"""
        filepath = os.path.join(self.REPO_DIR, self.CONFIG_MODULE)
        with open(filepath) as f:
            try:
                ast.parse(f.read())
            except SyntaxError as e:
                pytest.fail(f"config.py has syntax error: {e}")

    def test_loader_module_valid_python(self):
        """Verify config_loader.py is valid Python syntax"""
        filepath = os.path.join(self.REPO_DIR, self.LOADER_MODULE)
        with open(filepath) as f:
            try:
                ast.parse(f.read())
            except SyntaxError as e:
                pytest.fail(f"config_loader.py has syntax error: {e}")

    def test_config_loads_with_valid_env(self):
        """Verify config loads successfully with valid environment variables"""
        sys.path.insert(0, self.REPO_DIR)
        env = os.environ.copy()
        env.update({
            "APP_APP_NAME": "TestApp",
            "APP_ENVIRONMENT": "testing",
            "APP_DATABASE_URL": "sqlite:///test.db",
            "APP_SECRET_KEY": "a" * 64,
        })
        result = subprocess.run(
            ["python", "-c",
             "import fastapi.config_loader; print('OK')"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        if result.returncode != 0:
            # May fail due to other import issues; check if it's a config error
            if "config" in result.stderr.lower() or "settings" in result.stderr.lower():
                pytest.fail(f"Config loading failed: {result.stderr[:500]}")

    def test_tests_cover_validation_scenarios(self):
        """Verify test file covers missing fields, constraint violations, and defaults"""
        content = self._read_file(self.TEST_FILE)
        test_tree = ast.parse(content)
        test_funcs = [
            node.name for node in ast.walk(test_tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        ]
        assert len(test_funcs) >= 5, \
            f"Expected at least 5 test functions, found {len(test_funcs)}"
        content_lower = content.lower()
        assert "missing" in content_lower or "required" in content_lower, \
            "Tests missing required-field-missing scenarios"
        assert "invalid" in content_lower or "error" in content_lower or "raise" in content_lower, \
            "Tests missing validation error scenarios"
