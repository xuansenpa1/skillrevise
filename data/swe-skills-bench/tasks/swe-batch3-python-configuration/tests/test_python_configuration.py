"""
Tests for the python-configuration skill.

Validates that typed configuration management with validation,
environment-specific defaults, and secret masking was implemented
for a FastAPI test application.

Repo: fastapi (https://github.com/fastapi/fastapi)
"""

import ast
import os
import re
import subprocess
import sys

REPO_DIR = "/workspace/fastapi"


class TestFilePathCheck:
    """Verify that all required files were created or modified."""

    def test_config_file_exists(self):
        path = os.path.join(REPO_DIR, "tests", "test_app", "config.py")
        assert os.path.isfile(path), f"Expected config.py at {path}"

    def test_app_file_exists(self):
        path = os.path.join(REPO_DIR, "tests", "test_app", "app.py")
        assert os.path.isfile(path), f"Expected app.py at {path}"

    def test_test_config_file_exists(self):
        path = os.path.join(REPO_DIR, "tests", "test_app", "test_config.py")
        assert os.path.isfile(path), f"Expected test_config.py at {path}"


class TestSemanticSettingsClasses:
    """Verify the settings classes are properly defined."""

    def _read_config(self):
        path = os.path.join(REPO_DIR, "tests", "test_app", "config.py")
        with open(path, "r") as f:
            return f.read()

    def test_database_settings_class(self):
        content = self._read_config()
        assert re.search(r"class\s+DatabaseSettings", content), (
            "Expected DatabaseSettings class in config.py"
        )

    def test_redis_settings_class(self):
        content = self._read_config()
        assert re.search(r"class\s+RedisSettings", content), (
            "Expected RedisSettings class in config.py"
        )

    def test_app_settings_class(self):
        content = self._read_config()
        assert re.search(r"class\s+AppSettings", content), (
            "Expected AppSettings class in config.py"
        )

    def test_database_host_field(self):
        content = self._read_config()
        assert re.search(r"host", content), (
            "Expected 'host' field in DatabaseSettings"
        )

    def test_database_port_field_with_default(self):
        content = self._read_config()
        assert re.search(r"port.*5432|5432.*port", content), (
            "Expected port field with default 5432 in DatabaseSettings"
        )

    def test_database_pool_size_field(self):
        content = self._read_config()
        assert re.search(r"pool_size", content), (
            "Expected pool_size field in DatabaseSettings"
        )

    def test_database_ssl_mode_field(self):
        content = self._read_config()
        assert re.search(r"ssl_mode", content), (
            "Expected ssl_mode field in DatabaseSettings"
        )

    def test_ssl_mode_valid_values(self):
        content = self._read_config()
        for mode in ["disable", "require", "verify-ca", "verify-full"]:
            assert mode in content, f"Expected ssl_mode value '{mode}' in config"

    def test_redis_url_field(self):
        content = self._read_config()
        assert re.search(r"redis://|rediss://", content), (
            "Expected redis:// or rediss:// URL validation in RedisSettings"
        )

    def test_environment_choices(self):
        content = self._read_config()
        for env in ["development", "staging", "production"]:
            assert env in content, f"Expected environment choice '{env}' in AppSettings"

    def test_secret_key_min_length(self):
        content = self._read_config()
        assert "32" in content, (
            "Expected minimum secret_key length of 32 in AppSettings validation"
        )


class TestSemanticValidationRules:
    """Verify validation rules are enforced at construction time."""

    def _read_config(self):
        path = os.path.join(REPO_DIR, "tests", "test_app", "config.py")
        with open(path, "r") as f:
            return f.read()

    def test_production_debug_conflict_check(self):
        """production + debug=True must raise ValueError."""
        content = self._read_config()
        assert re.search(r"production.*debug|debug.*production|ValueError", content, re.IGNORECASE), (
            "Expected validation: production environment rejects debug=True"
        )

    def test_production_allowed_hosts_wildcard_check(self):
        """production + allowed_hosts=['*'] must raise ValueError."""
        content = self._read_config()
        assert re.search(r"allowed_hosts|allowed.hosts|\"\*\"", content), (
            "Expected allowed_hosts wildcard validation for production"
        )

    def test_port_range_validation(self):
        """database.port must be 1–65535."""
        content = self._read_config()
        assert "65535" in content, (
            "Expected port range validation up to 65535"
        )

    def test_redis_url_validation(self):
        """redis.url must start with redis:// or rediss://."""
        content = self._read_config()
        assert re.search(r"redis://|rediss://|startswith", content), (
            "Expected redis URL prefix validation"
        )


class TestSemanticSecretMasking:
    """Verify that secret fields are masked in repr/str."""

    def _read_config(self):
        path = os.path.join(REPO_DIR, "tests", "test_app", "config.py")
        with open(path, "r") as f:
            return f.read()

    def test_repr_masking(self):
        content = self._read_config()
        assert re.search(r"__repr__|repr|SecretStr|\*\*\*|masked|hidden", content, re.IGNORECASE), (
            "Expected __repr__ masking or SecretStr usage for sensitive fields"
        )

    def test_password_field_protected(self):
        content = self._read_config()
        assert re.search(r"password", content, re.IGNORECASE), (
            "Expected password field in DatabaseSettings"
        )

    def test_secret_key_field_protected(self):
        content = self._read_config()
        assert re.search(r"secret_key", content), (
            "Expected secret_key field in AppSettings"
        )


class TestSemanticEnvironmentDefaults:
    """Verify environment-specific defaults."""

    def _read_config(self):
        path = os.path.join(REPO_DIR, "tests", "test_app", "config.py")
        with open(path, "r") as f:
            return f.read()

    def test_log_level_defaults(self):
        """development → DEBUG, production → WARNING."""
        content = self._read_config()
        assert "DEBUG" in content and "WARNING" in content, (
            "Expected DEBUG and WARNING log level defaults for different environments"
        )

    def test_env_variable_prefix(self):
        """Settings should load from APP_ prefixed env vars."""
        content = self._read_config()
        assert re.search(r"APP_|env_prefix|model_config", content), (
            "Expected APP_ environment variable prefix configuration"
        )


class TestSemanticAppIntegration:
    """Verify configuration is wired into the FastAPI app."""

    def _read_app(self):
        path = os.path.join(REPO_DIR, "tests", "test_app", "app.py")
        with open(path, "r") as f:
            return f.read()

    def test_get_settings_dependency(self):
        """App should have a get_settings() dependency function."""
        content = self._read_app()
        assert re.search(r"get_settings", content), (
            "Expected get_settings dependency function in app.py"
        )

    def test_startup_validation(self):
        """Settings should be validated on application startup."""
        content = self._read_app()
        assert re.search(r"startup|lifespan|on_event|AppSettings", content, re.IGNORECASE), (
            "Expected startup validation or lifespan hook in app.py"
        )


class TestFunctionalPythonSyntax:
    """Validate Python syntax of all created/modified files."""

    def _check_syntax(self, filepath):
        with open(filepath, "r") as f:
            source = f.read()
        ast.parse(source)

    def test_config_syntax(self):
        self._check_syntax(os.path.join(REPO_DIR, "tests", "test_app", "config.py"))

    def test_app_syntax(self):
        self._check_syntax(os.path.join(REPO_DIR, "tests", "test_app", "app.py"))

    def test_test_config_syntax(self):
        self._check_syntax(os.path.join(REPO_DIR, "tests", "test_app", "test_config.py"))


class TestFunctionalTestCoverage:
    """Verify the agent's own tests are well-structured and pass."""

    def _read_test_file(self):
        path = os.path.join(REPO_DIR, "tests", "test_app", "test_config.py")
        with open(path, "r") as f:
            return f.read()

    def test_sufficient_test_count(self):
        content = self._read_test_file()
        test_count = len(re.findall(r"def\s+test_", content))
        assert test_count >= 5, (
            f"Expected at least 5 test functions in test_config.py, found {test_count}"
        )

    def test_covers_validation_errors(self):
        content = self._read_test_file()
        assert re.search(r"ValueError|ValidationError|raises|invalid", content, re.IGNORECASE), (
            "Expected tests covering validation error scenarios"
        )

    def test_covers_environment_switching(self):
        content = self._read_test_file()
        assert re.search(r"development|production|staging|environment", content, re.IGNORECASE), (
            "Expected tests covering environment switching"
        )

    def test_agent_tests_pass(self):
        """Run the agent's own configuration tests."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest",
             "tests/test_app/test_config.py", "-v", "--tb=short"],
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"Agent's own config tests failed:\n{result.stdout[-1000:]}\n{result.stderr[-500:]}"
        )
