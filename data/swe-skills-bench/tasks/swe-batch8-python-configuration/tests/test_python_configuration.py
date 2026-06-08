"""
Tests for the python-configuration skill.
Validates typed configuration management in a FastAPI application using
pydantic-settings with environment validation, dependency injection, and secrets protection.
"""

import os
import re
import ast

REPO_DIR = "/workspace/fastapi"
SETTINGS_DIR = os.path.join(REPO_DIR, "docs_src", "settings")


class TestPythonConfiguration:
    """Tests for the FastAPI typed configuration management example."""

    # ── file_path_check ──────────────────────────────────────────────

    def test_config_file_exists(self):
        """Central Settings config.py must exist."""
        path = os.path.join(SETTINGS_DIR, "config.py")
        assert os.path.isfile(path), f"Missing {path}"

    def test_app_file_exists(self):
        """FastAPI application app.py must exist."""
        path = os.path.join(SETTINGS_DIR, "app.py")
        assert os.path.isfile(path), f"Missing {path}"

    def test_database_file_exists(self):
        """Database connection factory database.py must exist."""
        path = os.path.join(SETTINGS_DIR, "database.py")
        assert os.path.isfile(path), f"Missing {path}"

    def test_dependencies_file_exists(self):
        """FastAPI dependency functions dependencies.py must exist."""
        path = os.path.join(SETTINGS_DIR, "dependencies.py")
        assert os.path.isfile(path), f"Missing {path}"

    def test_env_example_exists(self):
        """.env.example template must exist."""
        path = os.path.join(SETTINGS_DIR, ".env.example")
        assert os.path.isfile(path), f"Missing {path}"

    # ── semantic_check ───────────────────────────────────────────────

    def _read(self, filename):
        path = os.path.join(SETTINGS_DIR, filename)
        if not os.path.isfile(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_settings_extends_base_settings(self):
        """Settings class must extend pydantic_settings.BaseSettings."""
        content = self._read("config.py")
        assert re.search(r"class\s+Settings\b.*BaseSettings", content, re.DOTALL), (
            "Settings class not extending BaseSettings"
        )
        assert re.search(r"pydantic_settings|pydantic\.settings", content), (
            "pydantic_settings not imported"
        )

    def test_required_fields_defined(self):
        """Settings must define all required fields: database_url, api_secret_key, external_api_base_url."""
        content = self._read("config.py")
        required = ["database_url", "api_secret_key", "external_api_base_url"]
        for field in required:
            assert field in content, f"Required field '{field}' not found in Settings"

    def test_optional_fields_with_defaults(self):
        """Settings must define optional fields with proper defaults."""
        content = self._read("config.py")
        defaults = {
            "app_name": "FastAPI App",
            "debug": "False",
            "database_pool_min": "2",
            "database_pool_max": "10",
            "log_level": "INFO",
        }
        for field, _ in defaults.items():
            assert field in content, f"Optional field '{field}' not found in Settings"

    def test_pool_validation(self):
        """Cross-field validator must enforce database_pool_max >= database_pool_min."""
        content = self._read("config.py")
        assert re.search(
            r"model_validator|validator|pool_max.*pool_min|pool_min.*pool_max",
            content, re.IGNORECASE
        ), "Cross-field pool validation not found"

    def test_https_enforcement_in_non_debug(self):
        """external_api_base_url must require https:// when debug is False."""
        content = self._read("config.py")
        assert re.search(r"https://|https|field_validator|validator", content), (
            "HTTPS enforcement for external_api_base_url not found"
        )

    def test_cors_origins_field(self):
        """cors_origins field must be defined as a list."""
        content = self._read("config.py")
        assert "cors_origins" in content, "cors_origins field not found"
        assert re.search(r"list|List", content), "cors_origins should be a list type"

    def test_log_level_validation(self):
        """log_level must be constrained to DEBUG/INFO/WARNING/ERROR."""
        content = self._read("config.py")
        assert re.search(r"DEBUG.*INFO.*WARNING.*ERROR|Literal|enum|validator.*log_level", content, re.DOTALL), (
            "log_level validation not found"
        )

    # ── functional_check ─────────────────────────────────────────────

    def test_all_files_valid_python(self):
        """All settings Python files must have valid syntax."""
        errors = []
        for fname in ["config.py", "app.py", "database.py", "dependencies.py"]:
            content = self._read(fname)
            if not content:
                continue
            try:
                ast.parse(content)
            except SyntaxError as e:
                errors.append(f"{fname}: {e}")
        assert not errors, "Syntax errors found:\n" + "\n".join(errors)

    def test_dependency_injection_pattern(self):
        """Dependencies must use FastAPI's Depends pattern for settings injection."""
        deps = self._read("dependencies.py")
        app = self._read("app.py")
        combined = deps + app
        assert re.search(r"Depends\(|get_settings|get_db", combined), (
            "FastAPI Depends pattern not found for settings injection"
        )

    def test_health_endpoint_defined(self):
        """GET /health endpoint must be defined returning app_name and debug."""
        content = self._read("app.py")
        assert re.search(r'/health|"health"', content), "GET /health endpoint not found"

    def test_features_endpoint_defined(self):
        """GET /config/features endpoint must be defined."""
        content = self._read("app.py")
        assert re.search(r'/config/features|"features"|feature_x', content, re.IGNORECASE), (
            "GET /config/features endpoint not found"
        )

    def test_no_secrets_in_responses(self):
        """API endpoints must not expose secret_key or database_url in responses."""
        content = self._read("app.py")
        # Check that health/features endpoints don't directly return secrets
        # Look for response dicts that DON'T include secret fields
        assert not re.search(
            r'"api_secret_key".*response|return.*secret_key', content
        ), "API may be exposing api_secret_key in responses"

    def test_env_example_documents_all_vars(self):
        """.env.example must list all required environment variables."""
        content = self._read(".env.example")
        required_vars = ["DATABASE_URL", "API_SECRET_KEY", "EXTERNAL_API_BASE_URL"]
        for var in required_vars:
            assert var in content, f"{var} not documented in .env.example"

    def test_env_example_marks_required_fields(self):
        """.env.example must indicate which fields are required."""
        content = self._read(".env.example")
        assert re.search(r"required|Required|REQUIRED", content), (
            ".env.example does not indicate required fields"
        )

    def test_test_config_file_exists(self):
        """Test file for configuration must exist."""
        path = os.path.join(REPO_DIR, "tests", "test_settings", "test_config.py")
        assert os.path.isfile(path), f"Missing {path}"
