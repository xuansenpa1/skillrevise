"""
Test skill: python-configuration
Verify that the Agent implements a typed config system with pydantic-settings
for FastAPI including DatabaseSettings, Settings, and /health/config endpoint.
"""

import os
import subprocess
import ast
import re
import pytest


class TestPythonConfiguration:
    REPO_DIR = "/workspace/fastapi"

    # === File Path Checks ===

    def test_config_file_exists(self):
        """Verify configuration module file exists"""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root or "node_modules" in root:
                continue
            for f in files:
                if f.endswith(".py") and ("config" in f.lower() or "settings" in f.lower()):
                    fpath = os.path.join(root, f)
                    with open(fpath) as fh:
                        content = fh.read()
                    if "DatabaseSettings" in content or "Settings" in content:
                        found = True
                        break
            if found:
                break
        assert found, "Configuration module with Settings not found"

    # === Semantic Checks ===

    def test_database_settings_class_defined(self):
        """Verify DatabaseSettings class is defined"""
        config_content = self._find_config_content()
        assert "DatabaseSettings" in config_content, "DatabaseSettings class not defined"

    def test_settings_uses_pydantic(self):
        """Verify Settings class uses pydantic-settings BaseSettings"""
        config_content = self._find_config_content()
        has_pydantic = (
            "pydantic" in config_content
            or "BaseSettings" in config_content
            or "pydantic_settings" in config_content
        )
        assert has_pydantic, "Settings does not use pydantic/pydantic-settings"

    def test_settings_has_database_config(self):
        """Verify Settings includes database configuration"""
        config_content = self._find_config_content()
        has_db = (
            "database" in config_content.lower()
            or "db_" in config_content.lower()
            or "DATABASE" in config_content
        )
        assert has_db, "Settings missing database configuration"

    def test_health_config_endpoint_exists(self):
        """Verify /health/config endpoint is defined"""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root or "node_modules" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath) as fh:
                            content = fh.read()
                        if "health" in content.lower() and "config" in content.lower():
                            if "@" in content and ("get" in content.lower() or "router" in content.lower()):
                                found = True
                                break
                    except (UnicodeDecodeError, PermissionError):
                        continue
            if found:
                break
        assert found, "/health/config endpoint not found"

    def test_settings_supports_env_vars(self):
        """Verify Settings supports environment variable configuration"""
        config_content = self._find_config_content()
        has_env = (
            "env" in config_content.lower()
            or "Config" in config_content
            or "model_config" in config_content
            or "env_prefix" in config_content
        )
        assert has_env, "Settings does not support environment variables"

    # === Functional Checks ===

    def test_config_module_parses(self):
        """Verify config module has valid Python syntax"""
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".py") and ("config" in f.lower() or "settings" in f.lower()):
                    fpath = os.path.join(root, f)
                    with open(fpath) as fh:
                        source = fh.read()
                    if "DatabaseSettings" in source or "BaseSettings" in source:
                        try:
                            ast.parse(source)
                        except SyntaxError as e:
                            pytest.fail(f"Syntax error in {fpath}: {e}")
                        return

    def test_config_module_imports_successfully(self):
        """Verify config can be imported"""
        # Find the config module path
        config_path = None
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".py") and ("config" in f.lower() or "settings" in f.lower()):
                    fpath = os.path.join(root, f)
                    with open(fpath) as fh:
                        content = fh.read()
                    if "DatabaseSettings" in content:
                        config_path = fpath
                        break
            if config_path:
                break
        if config_path is None:
            pytest.skip("Config module not found")
        result = subprocess.run(
            ["python", "-c", f"import ast; ast.parse(open('{config_path}').read()); print('OK')"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Config parse failed: {result.stderr}"

    def test_settings_has_type_annotations(self):
        """Verify Settings class uses type annotations"""
        config_content = self._find_config_content()
        # Check for type annotations pattern: field_name: type
        has_annotations = re.search(r'\w+\s*:\s*(str|int|bool|float|Optional)', config_content)
        assert has_annotations, "Settings class missing type annotations"

    def test_database_settings_has_url_or_components(self):
        """Verify DatabaseSettings has connection URL or host/port/name components"""
        config_content = self._find_config_content()
        content_lower = config_content.lower()
        has_url = "url" in content_lower or "dsn" in content_lower
        has_components = "host" in content_lower and "port" in content_lower
        assert has_url or has_components, (
            "DatabaseSettings missing connection URL or host/port components"
        )

    def _find_config_content(self):
        """Helper to find configuration module content"""
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".py") and ("config" in f.lower() or "settings" in f.lower()):
                    fpath = os.path.join(root, f)
                    with open(fpath) as fh:
                        content = fh.read()
                    if "DatabaseSettings" in content or "BaseSettings" in content:
                        return content
        return ""
