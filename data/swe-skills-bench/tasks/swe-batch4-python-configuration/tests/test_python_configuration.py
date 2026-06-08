"""
Tests for skill: python-configuration
Repo: fastapi/fastapi
Image: zhangyiiiiii/swe-skills-bench-python
Task: Implement a typed configuration system for a FastAPI application with
      environment profiles, fail-fast validation, and dependency injection.
"""

import ast
import os
import re
import subprocess
import sys

import pytest

REPO_DIR = "/workspace/fastapi"
APP_DIR = os.path.join(REPO_DIR, "docs_src", "advanced_settings", "app")
TESTS_DIR = os.path.join(REPO_DIR, "docs_src", "advanced_settings", "tests")

CONFIG_FILE = os.path.join(APP_DIR, "config.py")
MAIN_FILE = os.path.join(APP_DIR, "main.py")
DEPS_FILE = os.path.join(APP_DIR, "dependencies.py")
ENV_EXAMPLE = os.path.join(REPO_DIR, "docs_src", "advanced_settings", ".env.example")
TEST_CONFIG_FILE = os.path.join(TESTS_DIR, "test_config.py")


# ---------------------------------------------------------------------------
# Layer 1 — file_path_check
# ---------------------------------------------------------------------------

class TestFilePathCheck:
    """Verify all expected files are created."""

    def test_config_file_exists(self):
        assert os.path.isfile(CONFIG_FILE), f"Expected {CONFIG_FILE}"

    def test_main_file_exists(self):
        assert os.path.isfile(MAIN_FILE), f"Expected {MAIN_FILE}"

    def test_dependencies_file_exists(self):
        assert os.path.isfile(DEPS_FILE), f"Expected {DEPS_FILE}"

    def test_env_example_exists(self):
        assert os.path.isfile(ENV_EXAMPLE), f"Expected {ENV_EXAMPLE}"

    def test_test_config_file_exists(self):
        assert os.path.isfile(TEST_CONFIG_FILE), f"Expected {TEST_CONFIG_FILE}"


# ---------------------------------------------------------------------------
# Layer 2 — semantic_check
# ---------------------------------------------------------------------------

class TestSemanticConfig:
    """Verify Settings class structure and validation."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()
        self.tree = ast.parse(self.src)

    def test_settings_class_defined(self):
        classes = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.ClassDef)]
        assert "Settings" in classes, (
            f"Expected Settings class in config.py; found: {classes}"
        )

    def test_required_fields_declared(self):
        """DATABASE_URL, SECRET_KEY, API_KEY must be declared without defaults."""
        for field in ["DATABASE_URL", "SECRET_KEY", "API_KEY"]:
            assert field in self.src, (
                f"Expected required field '{field}' in Settings class"
            )

    def test_optional_fields_with_defaults(self):
        """DEBUG, LOG_LEVEL, DB_POOL_SIZE, REDIS_URL must have defaults."""
        optional_fields = ["DEBUG", "LOG_LEVEL", "DB_POOL_SIZE", "REDIS_URL"]
        found = [f for f in optional_fields if f in self.src]
        assert len(found) >= 3, (
            f"Expected at least 3 optional fields with defaults; found: {found}"
        )

    def test_environment_field(self):
        """ENVIRONMENT field with enum of development/staging/production."""
        assert "ENVIRONMENT" in self.src, "Expected ENVIRONMENT field"
        for env in ["development", "staging", "production"]:
            assert env in self.src, (
                f"Expected environment value '{env}' in config"
            )

    def test_database_url_masked_property(self):
        """Computed property database_url_masked must exist."""
        assert "database_url_masked" in self.src, (
            "Expected database_url_masked computed property"
        )

    def test_production_debug_validation(self):
        """Production must reject DEBUG=True."""
        has_prod_debug = (
            "production" in self.src
            and ("DEBUG" in self.src)
            and ("raise" in self.src or "ValueError" in self.src
                 or "ValidationError" in self.src or "validator" in self.src)
        )
        assert has_prod_debug, (
            "Expected production validation rejecting DEBUG=True"
        )

    def test_production_cors_validation(self):
        """Production must reject localhost CORS origins."""
        has_cors_check = (
            "CORS_ORIGINS" in self.src
            and "localhost" in self.src
        )
        assert has_cors_check, (
            "Expected production validation rejecting localhost CORS origins"
        )

    def test_model_config_env_loading(self):
        """Settings must have model_config for .env file loading."""
        has_config = (
            "model_config" in self.src
            or "Config" in self.src
            or "env_file" in self.src
        )
        assert has_config, (
            "Expected model_config or Config class for .env file loading"
        )


class TestSemanticDependencies:
    """Verify dependency providers."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        with open(DEPS_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()
        self.tree = ast.parse(self.src)

    def test_get_settings_function(self):
        funcs = [n.name for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]
        assert "get_settings" in funcs, (
            f"Expected get_settings dependency; found: {funcs}"
        )

    def test_get_db_pool_function(self):
        funcs = [n.name for n in ast.walk(self.tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        assert "get_db_pool" in funcs, (
            f"Expected get_db_pool dependency; found: {funcs}"
        )

    def test_get_redis_function(self):
        funcs = [n.name for n in ast.walk(self.tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        assert "get_redis" in funcs, (
            f"Expected get_redis dependency; found: {funcs}"
        )


class TestSemanticMain:
    """Verify FastAPI application wiring."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        with open(MAIN_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()

    def test_fastapi_app_created(self):
        assert "FastAPI" in self.src, "Expected FastAPI app in main.py"

    def test_depends_used(self):
        """Settings dependency must be injected via Depends."""
        assert "Depends" in self.src, (
            "Expected Depends() for dependency injection in main.py"
        )


class TestSemanticEnvExample:
    """Verify .env.example file content."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        with open(ENV_EXAMPLE, "r", encoding="utf-8") as f:
            self.src = f.read()

    def test_required_vars_documented(self):
        for var in ["DATABASE_URL", "SECRET_KEY", "API_KEY"]:
            assert var in self.src, (
                f"Expected {var} in .env.example"
            )

    def test_required_marker(self):
        """Required variables must be marked with REQUIRED."""
        assert "REQUIRED" in self.src.upper(), (
            "Expected # REQUIRED markers for required variables"
        )

    def test_sensitive_marker(self):
        """Sensitive variables must have SENSITIVE warning."""
        assert "SENSITIVE" in self.src.upper(), (
            "Expected # SENSITIVE warning for sensitive variables"
        )

    def test_all_optional_vars_documented(self):
        """Optional fields should appear in the env example."""
        optional = ["DEBUG", "LOG_LEVEL", "DB_POOL_SIZE", "REDIS_URL",
                     "CORS_ORIGINS", "ENVIRONMENT"]
        found = [v for v in optional if v in self.src]
        assert len(found) >= 4, (
            f"Expected at least 4 optional vars documented; found: {found}"
        )


# ---------------------------------------------------------------------------
# Layer 3 — functional_check
# ---------------------------------------------------------------------------

class TestFunctionalConfiguration:
    """Functional checks — syntax, validation, and import tests."""

    def _parse_file(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            src = f.read()
        try:
            ast.parse(src)
            return True, None
        except SyntaxError as e:
            return False, str(e)

    def test_config_valid_python(self):
        ok, err = self._parse_file(CONFIG_FILE)
        assert ok, f"config.py syntax error: {err}"

    def test_main_valid_python(self):
        ok, err = self._parse_file(MAIN_FILE)
        assert ok, f"main.py syntax error: {err}"

    def test_dependencies_valid_python(self):
        ok, err = self._parse_file(DEPS_FILE)
        assert ok, f"dependencies.py syntax error: {err}"

    def test_test_config_valid_python(self):
        ok, err = self._parse_file(TEST_CONFIG_FILE)
        assert ok, f"test_config.py syntax error: {err}"

    def test_pydantic_settings_used(self):
        """Settings class should inherit from Pydantic BaseSettings."""
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            src = f.read()
        has_pydantic = (
            "BaseSettings" in src
            or "pydantic_settings" in src
            or "pydantic" in src
        )
        assert has_pydantic, (
            "Expected Pydantic BaseSettings for typed configuration"
        )

    def test_password_masking_logic(self):
        """database_url_masked must replace password portion with ***."""
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            src = f.read()
        has_masking = (
            "***" in src
            or "replace" in src
            or "urlparse" in src
            or "_replace" in src
            or "mask" in src.lower()
        )
        assert has_masking, (
            "Expected password masking logic (*** replacement) in database_url_masked"
        )

    def test_log_level_constrained(self):
        """LOG_LEVEL must be constrained to DEBUG/INFO/WARNING/ERROR."""
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            src = f.read()
        levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        found = [l for l in levels if f'"{l}"' in src or f"'{l}'" in src]
        assert len(found) >= 3, (
            f"Expected at least 3 log level options; found: {found}"
        )

    def test_db_pool_size_range_validation(self):
        """DB_POOL_SIZE must be constrained to range 1-50."""
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            src = f.read()
        has_range = (
            "ge=1" in src or "gt=0" in src or "ge = 1" in src
            or "le=50" in src or "le = 50" in src
            or "Field(" in src or "validator" in src
        )
        assert has_range, (
            "Expected DB_POOL_SIZE range validation (1-50)"
        )

    def test_secret_key_min_length(self):
        """SECRET_KEY must have minimum length validation (32+ chars)."""
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            src = f.read()
        has_min_len = (
            "min_length" in src
            or "32" in src
            or "len(" in src
        )
        assert has_min_len, (
            "Expected SECRET_KEY minimum length validation (32 chars)"
        )

    def test_dependency_override_pattern_in_tests(self):
        """Test file must demonstrate FastAPI dependency override."""
        with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            src = f.read()
        has_override = (
            "dependency_overrides" in src
            or "override" in src.lower()
            or "app.dependency_overrides" in src
        )
        assert has_override, (
            "Expected FastAPI dependency_overrides pattern in test file"
        )
