"""
Test skill: python-configuration
Verify that the Agent correctly implements typed configuration management
for a FastAPI application using pydantic-settings, with validation,
fail-fast behavior, and secure endpoint exposure.
"""

import os
import re
import ast
import subprocess
import pytest


class TestPythonConfiguration:
    REPO_DIR = "/workspace/fastapi"

    # === File Path Checks ===

    def test_app_config_file_exists(self):
        """Verify app_config.py exists"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/app_config.py")
        assert os.path.exists(path), f"app_config.py not found at {path}"

    def test_main_file_exists(self):
        """Verify main.py exists"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/main.py")
        assert os.path.exists(path), f"main.py not found at {path}"

    def test_env_example_exists(self):
        """Verify .env.example exists"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/.env.example")
        assert os.path.exists(path), f".env.example not found at {path}"

    def test_test_settings_file_exists(self):
        """Verify test_settings.py exists"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/test_settings.py")
        assert os.path.exists(path), f"test_settings.py not found at {path}"

    # === Semantic Checks ===

    def test_settings_class_inherits_base_settings(self):
        """Verify Settings class inherits from BaseSettings"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/app_config.py")
        with open(path, "r") as f:
            content = f.read()

        assert "BaseSettings" in content, (
            "Settings class must inherit from pydantic_settings.BaseSettings"
        )
        assert re.search(r"class\s+Settings.*BaseSettings", content), (
            "Settings class definition not found"
        )

    def test_required_fields_defined(self):
        """Verify required fields database_url and secret_key are defined"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/app_config.py")
        with open(path, "r") as f:
            content = f.read()

        assert "database_url" in content, "Settings must define database_url field"
        assert "secret_key" in content, "Settings must define secret_key field"

    def test_all_settings_fields_present(self):
        """Verify all specified settings fields are defined"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/app_config.py")
        with open(path, "r") as f:
            content = f.read()

        expected_fields = [
            "database_url", "database_pool_size", "database_pool_overflow",
            "secret_key", "access_token_expire_minutes", "cors_origins",
            "debug", "log_level", "redis_url", "enable_signup"
        ]
        for field in expected_fields:
            assert field in content, f"Settings missing field: {field}"

    def test_database_url_validation(self):
        """Verify database_url validates postgresql:// prefix"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/app_config.py")
        with open(path, "r") as f:
            content = f.read()

        assert "postgresql" in content, (
            "Should validate that database_url starts with postgresql://"
        )
        has_validation = (
            "validator" in content
            or "field_validator" in content
            or "model_validator" in content
            or "@validator" in content
            or "startswith" in content
        )
        assert has_validation, (
            "database_url should have a validator checking the postgresql:// prefix"
        )

    def test_log_level_enum_validation(self):
        """Verify log_level is validated against allowed values"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/app_config.py")
        with open(path, "r") as f:
            content = f.read()

        assert "DEBUG" in content and "INFO" in content and "WARNING" in content and "ERROR" in content, (
            "log_level should validate against DEBUG, INFO, WARNING, ERROR"
        )

    def test_cors_origins_parsing(self):
        """Verify cors_origins supports comma-separated string parsing"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/app_config.py")
        with open(path, "r") as f:
            content = f.read()

        has_parsing = (
            "split" in content
            or "validator" in content
            or "parse" in content.lower()
            or "list[str]" in content.lower()
            or "List[str]" in content
        )
        assert has_parsing, (
            "cors_origins should support comma-separated string parsing"
        )

    def test_pool_size_range_validation(self):
        """Verify database_pool_size validates range 1-100"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/app_config.py")
        with open(path, "r") as f:
            content = f.read()

        assert "100" in content, (
            "database_pool_size should validate max value of 100"
        )

    def test_singleton_settings_instance(self):
        """Verify a module-level singleton settings instance is created"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/app_config.py")
        with open(path, "r") as f:
            content = f.read()

        assert re.search(r"^settings\s*=\s*Settings\(", content, re.MULTILINE) or \
               re.search(r"^settings\s*=\s*get_settings\(", content, re.MULTILINE) or \
               "settings" in content, (
            "Should create a module-level settings singleton"
        )

    def test_main_uses_cors_middleware(self):
        """Verify FastAPI app configures CORS middleware using settings"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/main.py")
        with open(path, "r") as f:
            content = f.read()

        assert "CORSMiddleware" in content or "cors" in content.lower(), (
            "FastAPI app should configure CORS middleware"
        )
        assert "cors_origins" in content or "settings" in content, (
            "CORS should use settings.cors_origins"
        )

    def test_health_endpoint_defined(self):
        """Verify /health endpoint returns status and debug flag"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/main.py")
        with open(path, "r") as f:
            content = f.read()

        assert "health" in content, "Must define /health endpoint"
        assert "debug" in content, "/health should return debug flag"

    def test_config_public_endpoint_no_secrets(self):
        """Verify /config/public endpoint exists and does NOT expose secrets"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/main.py")
        with open(path, "r") as f:
            content = f.read()

        assert "config/public" in content or "config_public" in content, (
            "Must define /config/public endpoint"
        )

        # The endpoint should not return sensitive values
        # Check that the response construction doesn't include secret_key, database_url, redis_url
        # Find the endpoint definition block
        endpoint_match = re.search(
            r"(config.public|config_public).*?\n((?:[ \t]+.*\n){1,20})",
            content
        )
        if endpoint_match:
            block = endpoint_match.group(2)
            assert "secret_key" not in block and "database_url" not in block, (
                "/config/public should NOT expose secret_key or database_url"
            )

    def test_depends_injection(self):
        """Verify settings are injectable via Depends()"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/main.py")
        with open(path, "r") as f:
            content = f.read()

        assert "Depends" in content, (
            "Settings should be injectable via FastAPI's Depends()"
        )
        assert "get_settings" in content, (
            "Should define get_settings function for dependency injection"
        )

    # === Functional Checks ===

    def test_all_python_files_parse(self):
        """Verify all Python files parse without syntax errors"""
        files = [
            "docs_src/settings/app_config.py",
            "docs_src/settings/main.py",
            "docs_src/settings/test_settings.py",
        ]
        for filename in files:
            path = os.path.join(self.REPO_DIR, filename)
            with open(path, "r") as f:
                source = f.read()
            try:
                ast.parse(source)
            except SyntaxError as e:
                pytest.fail(f"{filename} has syntax error: {e}")

    def test_env_example_documents_all_vars(self):
        """Verify .env.example lists all configuration variables"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/.env.example")
        with open(path, "r") as f:
            content = f.read()

        expected_vars = [
            "DATABASE_URL", "SECRET_KEY", "DEBUG", "LOG_LEVEL",
            "CORS_ORIGINS", "REDIS_URL"
        ]
        for var in expected_vars:
            assert var in content, f".env.example missing variable: {var}"

    def test_env_example_marks_required(self):
        """Verify .env.example distinguishes required vs optional"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/.env.example")
        with open(path, "r") as f:
            content = f.read()

        assert "required" in content.lower() or "REQUIRED" in content, (
            ".env.example should mark which variables are required"
        )

    def test_settings_import_with_valid_env(self):
        """Verify Settings can be instantiated with valid environment"""
        result = subprocess.run(
            [
                "python", "-c",
                "import os; "
                "os.environ['DATABASE_URL'] = 'postgresql://localhost/testdb'; "
                "os.environ['SECRET_KEY'] = 'test-secret-key-123'; "
                "import sys; sys.path.insert(0, 'docs_src/settings'); "
                "from app_config import Settings; "
                "s = Settings(); "
                "print(s.database_url); print(s.debug)"
            ],
            capture_output=True, text=True, timeout=30,
            cwd=self.REPO_DIR,
        )
        assert result.returncode == 0, (
            f"Failed to instantiate Settings:\n{result.stderr[:1000]}"
        )
        assert "postgresql" in result.stdout, (
            f"Unexpected output: {result.stdout}"
        )
