"""
Test skill: python-configuration
Verify that the Agent correctly implements a typed configuration system
for a FastAPI application using pydantic-settings.
"""

import os
import re
import ast
import subprocess
import pytest


class TestPythonConfiguration:
    REPO_DIR = "/workspace/fastapi"

    # === File Path Checks ===

    def test_config_module_exists(self):
        """Verify fastapi/config.py was created"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        assert os.path.exists(path), f"config.py not found at {path}"

    def test_config_test_file_exists(self):
        """Verify tests/test_config.py was created"""
        path = os.path.join(self.REPO_DIR, "tests/test_config.py")
        assert os.path.exists(path), f"test_config.py not found at {path}"

    # === Semantic Checks: Settings Class ===

    def test_settings_uses_base_settings(self):
        """Verify Settings class uses pydantic_settings.BaseSettings"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "BaseSettings" in content, (
            "Settings should inherit from BaseSettings"
        )
        assert "pydantic_settings" in content or "pydantic" in content, (
            "Should import from pydantic_settings"
        )

    def test_settings_has_db_fields(self):
        """Verify Settings has all database-related fields"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        for field in ["db_host", "db_port", "db_name", "db_user", "db_password"]:
            assert field in content, f"Settings should have '{field}' field"

    def test_settings_has_redis_fields(self):
        """Verify Settings has Redis-related fields"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "redis_url" in content, "Settings should have redis_url field"
        assert "redis_max_connections" in content, (
            "Settings should have redis_max_connections field"
        )

    def test_settings_has_api_secret_key(self):
        """Verify Settings has required api_secret_key field"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "api_secret_key" in content, (
            "Settings should have api_secret_key field"
        )

    def test_settings_has_debug_field(self):
        """Verify Settings has debug bool field"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "debug" in content, "Settings should have debug field"

    def test_settings_has_environment_field(self):
        """Verify Settings has environment field with validation"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "environment" in content, "Settings should have environment field"
        for env in ["local", "staging", "production"]:
            assert env in content, (
                f"Environment validation should include '{env}'"
            )

    def test_settings_has_allowed_hosts(self):
        """Verify Settings has allowed_hosts as list[str]"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "allowed_hosts" in content, "Settings should have allowed_hosts field"

    def test_settings_has_feature_flags(self):
        """Verify Settings has feature_beta_ui flag"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "feature_beta_ui" in content, (
            "Settings should have feature_beta_ui field"
        )

    def test_settings_has_log_level(self):
        """Verify Settings has log_level with validation"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "log_level" in content, "Settings should have log_level field"

    def test_settings_has_auth_token_expiry(self):
        """Verify Settings has auth_token_expiry_seconds"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "auth_token_expiry_seconds" in content, (
            "Settings should have auth_token_expiry_seconds field"
        )

    # === Semantic Checks: Nested Configuration ===

    def test_nested_settings_class(self):
        """Verify NestedSettings class with env_nested_delimiter='__'"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "NestedSettings" in content, (
            "Should define NestedSettings class"
        )
        assert "__" in content, (
            "NestedSettings should use '__' as env_nested_delimiter"
        )

    def test_database_settings_submodel(self):
        """Verify DatabaseSettings submodel is defined"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "DatabaseSettings" in content, (
            "Should define DatabaseSettings submodel"
        )

    def test_redis_settings_submodel(self):
        """Verify RedisSettings submodel is defined"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "RedisSettings" in content, (
            "Should define RedisSettings submodel"
        )

    # === Semantic Checks: Computed Properties ===

    def test_is_production_property(self):
        """Verify is_production computed property"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "is_production" in content, (
            "Settings should have is_production property"
        )

    def test_is_local_property(self):
        """Verify is_local computed property"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "is_local" in content, "Settings should have is_local property"

    def test_database_url_property(self):
        """Verify database_url computed property"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "database_url" in content, (
            "Settings should have database_url property"
        )
        assert "postgresql://" in content, (
            "database_url should construct postgresql:// URL"
        )

    # === Semantic Checks: Validation Rules ===

    def test_log_level_validation(self):
        """Verify log_level is validated against valid levels"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            assert level in content, (
                f"log_level validation should include '{level}'"
            )

    def test_db_port_validation(self):
        """Verify db_port is validated for range 1-65535"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "65535" in content, "db_port should be validated with max 65535"

    # === Semantic Checks: Fail-Fast Behavior ===

    def test_fail_fast_on_missing_required(self):
        """Verify module calls sys.exit(1) when required fields are missing"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "sys.exit" in content, (
            "Module should call sys.exit(1) on missing required vars"
        )

    def test_configuration_error_message(self):
        """Verify error output includes 'CONFIGURATION ERROR' text"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert "CONFIGURATION ERROR" in content, (
            "Error output should include 'CONFIGURATION ERROR'"
        )

    # === Semantic Checks: Model Config ===

    def test_env_file_config(self):
        """Verify model_config includes env_file='.env'"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            content = f.read()
        assert ".env" in content, (
            "model_config should reference .env file for environment loading"
        )

    # === Semantic Checks: Test File ===

    def test_test_covers_missing_required(self):
        """Verify test file tests missing required fields"""
        path = os.path.join(self.REPO_DIR, "tests/test_config.py")
        with open(path) as f:
            content = f.read()
        assert "missing" in content.lower() or "required" in content.lower() or "ValidationError" in content, (
            "Tests should cover missing required field scenarios"
        )

    def test_test_covers_type_coercion(self):
        """Verify test file tests type coercion"""
        path = os.path.join(self.REPO_DIR, "tests/test_config.py")
        with open(path) as f:
            content = f.read()
        assert "True" in content or "bool" in content.lower(), (
            "Tests should cover type coercion scenarios"
        )

    def test_test_covers_invalid_environment(self):
        """Verify test file tests invalid environment value"""
        path = os.path.join(self.REPO_DIR, "tests/test_config.py")
        with open(path) as f:
            content = f.read()
        assert "invalid" in content.lower() or "ValidationError" in content, (
            "Tests should cover invalid environment value"
        )

    # === Functional Checks ===

    def test_config_module_parses(self):
        """Verify config.py has valid Python syntax"""
        path = os.path.join(self.REPO_DIR, "fastapi/config.py")
        with open(path) as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"config.py has syntax error: {e}")

    def test_test_file_parses(self):
        """Verify test_config.py has valid Python syntax"""
        path = os.path.join(self.REPO_DIR, "tests/test_config.py")
        with open(path) as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"test_config.py has syntax error: {e}")

    def test_config_tests_pass(self):
        """Verify config tests pass"""
        result = subprocess.run(
            [
                "python", "-m", "pytest",
                "tests/test_config.py",
                "-v", "--tb=short",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"Config tests failed:\n{result.stdout}\n{result.stderr}"
        )
