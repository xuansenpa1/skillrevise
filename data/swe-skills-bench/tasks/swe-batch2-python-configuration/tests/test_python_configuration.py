"""
Test skill: python-configuration
Verify that the Agent correctly implements type-safe configuration
management for FastAPI using pydantic-settings, including environment
variable reading, type validation, defaults, and FastAPI integration.
"""

import os
import re
import ast
import subprocess
import pytest


class TestPythonConfiguration:
    REPO_DIR = "/workspace/fastapi"

    # === File Path Checks ===

    def test_tutorial_file_exists(self):
        """Verify docs_src/settings/tutorial001.py exists"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/tutorial001.py")
        assert os.path.exists(path), f"tutorial001.py not found at {path}"

    # === Semantic Checks ===

    def test_settings_class_defined(self):
        """Verify a Settings class is defined that inherits from BaseSettings"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/tutorial001.py")
        with open(path) as f:
            content = f.read()

        assert re.search(r"class\s+\w*[Ss]ettings\w*", content), (
            "A Settings class should be defined"
        )
        assert "BaseSettings" in content, (
            "Settings class should inherit from BaseSettings (pydantic-settings)"
        )

    def test_imports_pydantic_settings(self):
        """Verify pydantic-settings is imported"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/tutorial001.py")
        with open(path) as f:
            content = f.read()

        indicators = [
            "pydantic_settings", "pydantic.settings",
            "BaseSettings",
        ]
        found = [ind for ind in indicators if ind in content]
        assert len(found) >= 1, (
            f"Should import from pydantic-settings. Found: {found}"
        )

    def test_database_url_field(self):
        """Verify settings include a database connection string field"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/tutorial001.py")
        with open(path) as f:
            content = f.read().lower()

        db_indicators = [
            "database_url", "database_uri", "db_url", "db_uri",
            "database", "sqlalchemy",
        ]
        found = [ind for ind in db_indicators if ind in content]
        assert len(found) >= 1, (
            f"Settings should include a database URL field. Found: {found}"
        )

    def test_api_key_field(self):
        """Verify settings include API key field(s)"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/tutorial001.py")
        with open(path) as f:
            content = f.read().lower()

        key_indicators = [
            "api_key", "secret_key", "api_token", "secret",
        ]
        found = [ind for ind in key_indicators if ind in content]
        assert len(found) >= 1, (
            f"Settings should include API key field(s). Found: {found}"
        )

    def test_debug_mode_field(self):
        """Verify settings include a debug mode toggle (boolean)"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/tutorial001.py")
        with open(path) as f:
            content = f.read()

        assert "debug" in content.lower(), (
            "Settings should include a debug mode toggle field"
        )
        # Should be typed as bool
        bool_indicators = ["bool", "True", "False"]
        found = [ind for ind in bool_indicators if ind in content]
        assert len(found) >= 1, (
            f"Debug field should be boolean typed. Found: {found}"
        )

    def test_host_port_fields(self):
        """Verify settings include host and port fields"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/tutorial001.py")
        with open(path) as f:
            content = f.read().lower()

        assert "host" in content, "Settings should include a host field"
        assert "port" in content, "Settings should include a port field"

    def test_cors_origins_field(self):
        """Verify settings include allowed CORS origins"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/tutorial001.py")
        with open(path) as f:
            content = f.read().lower()

        cors_indicators = [
            "cors", "origins", "allowed_origins", "allowed_hosts",
        ]
        found = [ind for ind in cors_indicators if ind in content]
        assert len(found) >= 1, (
            f"Settings should include CORS origins. Found: {found}"
        )

    def test_type_annotations_present(self):
        """Verify fields have proper type annotations"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/tutorial001.py")
        with open(path) as f:
            content = f.read()

        type_indicators = ["str", "int", "bool", "list", "List", "Optional"]
        found = [t for t in type_indicators if t in content]
        assert len(found) >= 3, (
            f"Settings fields should have type annotations. Found types: {found}"
        )

    def test_fastapi_integration(self):
        """Verify tutorial shows FastAPI app using the settings"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/tutorial001.py")
        with open(path) as f:
            content = f.read()

        assert "FastAPI" in content or "fastapi" in content.lower(), (
            "Tutorial should demonstrate FastAPI integration"
        )
        # Should instantiate settings and use in the app
        instance_indicators = [
            "Settings()", "settings =", "get_settings", "Depends(",
        ]
        found = [ind for ind in instance_indicators if ind in content]
        assert len(found) >= 1, (
            f"Tutorial should instantiate settings for FastAPI use. Found: {found}"
        )

    # === Functional Checks ===

    def test_tutorial_valid_python(self):
        """Verify tutorial001.py is valid Python syntax"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/tutorial001.py")
        with open(path) as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"tutorial001.py has syntax errors: {e}")

    def test_tutorial_importable(self):
        """Verify tutorial001.py can be imported"""
        import sys
        sys.path.insert(0, self.REPO_DIR)
        try:
            result = subprocess.run(
                [
                    "python", "-c",
                    "import sys; sys.path.insert(0, "
                    f"'{self.REPO_DIR}'); "
                    "from docs_src.settings.tutorial001 import *",
                ],
                capture_output=True, text=True, timeout=30,
                cwd=self.REPO_DIR,
            )
            # Allow import failure only if env vars are missing (expected)
            if result.returncode != 0:
                stderr = result.stderr.lower()
                acceptable_failures = [
                    "validationerror", "validation error",
                    "environment variable", "field required",
                    "missing", "pydantic",
                ]
                is_acceptable = any(f in stderr for f in acceptable_failures)
                assert is_acceptable, (
                    f"Import failed for unexpected reason: {result.stderr}"
                )
        finally:
            if self.REPO_DIR in sys.path:
                sys.path.remove(self.REPO_DIR)

    def test_no_hardcoded_secrets(self):
        """Verify no hardcoded production secrets in default values"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/tutorial001.py")
        with open(path) as f:
            content = f.read()

        # Sensitive fields should not have real default values
        tree = ast.parse(content)
        # Check for suspicious hardcoded strings
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                val = node.value.lower()
                suspicious = [
                    "sk-", "pk-", "bearer ", "password123",
                    "supersecret", "mysecretkey",
                ]
                for s in suspicious:
                    if s in val and len(node.value) > 10:
                        pytest.fail(
                            f"Possible hardcoded secret found: "
                            f"'{node.value[:30]}...'"
                        )

    def test_settings_class_has_defaults(self):
        """Verify settings fields have sensible default values"""
        path = os.path.join(self.REPO_DIR, "docs_src/settings/tutorial001.py")
        with open(path) as f:
            content = f.read()

        # Should have at least some defaults (= value or Field(default=...))
        default_indicators = [
            "= ", "Field(", "default=", ": str =", ": int =", ": bool =",
        ]
        found = [ind for ind in default_indicators if ind in content]
        assert len(found) >= 2, (
            f"Settings should have default values for some fields. Found: {found}"
        )
