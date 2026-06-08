"""
Test skill: dbt-transformation-patterns
Verify that the Agent creates a dbt project with staging, intermediate,
and marts models following best practices.
"""

import os
import re
import subprocess
import pytest


class TestDbtTransformationPatterns:
    REPO_DIR = "/workspace/dbt-core"

    # === File Path Checks ===

    def test_dbt_project_yml_exists(self):
        """Verify dbt_project.yml exists"""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root or "node_modules" in root:
                continue
            if "dbt_project.yml" in files:
                found = True
                break
        assert found, "dbt_project.yml not found"

    def test_staging_models_exist(self):
        """Verify staging model files exist"""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            if "staging" in root.lower():
                for f in files:
                    if f.endswith(".sql"):
                        found = True
                        break
            if found:
                break
        assert found, "Staging model SQL files not found"

    # === Semantic Checks ===

    def test_intermediate_models_exist(self):
        """Verify intermediate model files exist"""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            if "intermediate" in root.lower() or "int_" in str(files).lower():
                for f in files:
                    if f.endswith(".sql"):
                        found = True
                        break
            if found:
                break
        assert found, "Intermediate model SQL files not found"

    def test_marts_models_exist(self):
        """Verify marts model files exist"""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            if "marts" in root.lower() or "mart" in root.lower():
                for f in files:
                    if f.endswith(".sql"):
                        found = True
                        break
            if found:
                break
        assert found, "Marts model SQL files not found"

    def test_schema_yml_exists(self):
        """Verify schema.yml files exist for documentation"""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f in ("schema.yml", "_schema.yml", "models.yml") or (f.endswith(".yml") and "schema" in f.lower()):
                    found = True
                    break
            if found:
                break
        assert found, "schema.yml files not found"

    def test_ref_function_used(self):
        """Verify ref() function is used for model dependencies"""
        sql_content = self._collect_sql_content()
        has_ref = "{{ ref(" in sql_content or "{{ref(" in sql_content
        assert has_ref, "ref() function not used in SQL models"

    def test_source_function_used(self):
        """Verify source() function is used for raw data references"""
        sql_content = self._collect_sql_content()
        has_source = "{{ source(" in sql_content or "{{source(" in sql_content
        assert has_source, "source() function not used in SQL models"

    # === Functional Checks ===

    def test_sql_files_valid_syntax(self):
        """Verify SQL files have basic valid syntax"""
        sql_files = self._find_sql_files()
        assert len(sql_files) > 0, "No SQL model files found"
        for sf in sql_files:
            with open(sf) as fh:
                content = fh.read()
            content_upper = content.upper()
            has_sql = "SELECT" in content_upper or "WITH" in content_upper or "{{" in content
            assert has_sql, f"Invalid SQL in {sf}"

    def test_dbt_project_yml_valid(self):
        """Verify dbt_project.yml is valid YAML"""
        import yaml
        yml_path = None
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            if "dbt_project.yml" in files:
                yml_path = os.path.join(root, "dbt_project.yml")
                break
        assert yml_path is not None, "dbt_project.yml not found"
        with open(yml_path) as fh:
            data = yaml.safe_load(fh)
        assert isinstance(data, dict), "dbt_project.yml is not a YAML mapping"
        assert "name" in data, "dbt_project.yml missing project name"

    def test_naming_conventions(self):
        """Verify models follow naming conventions"""
        sql_files = self._find_sql_files()
        staging_files = [f for f in sql_files if "staging" in f.lower()]
        for sf in staging_files:
            basename = os.path.basename(sf)
            assert basename.startswith("stg_") or "staging" in basename.lower(), \
                f"Staging model {basename} doesn't follow stg_ naming convention"

    def _collect_sql_content(self):
        all_content = ""
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".sql"):
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath) as fh:
                            all_content += fh.read() + "\n"
                    except (UnicodeDecodeError, PermissionError):
                        continue
        return all_content

    def _find_sql_files(self):
        result = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".sql"):
                    result.append(os.path.join(root, f))
        return result
