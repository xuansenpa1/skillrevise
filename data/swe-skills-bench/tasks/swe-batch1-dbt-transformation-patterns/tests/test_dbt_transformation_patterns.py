"""
Test for 'dbt-transformation-patterns' skill — dbt Transformation Patterns
Validates that the Agent created dbt model files with proper SQL
transformations, tests, and documentation.
"""

import os
import pytest


class TestDbtTransformationPatterns:
    """Verify dbt model and transformation setup."""

    REPO_DIR = "/workspace/dbt-core"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_model_sql_exists(self):
        """At least one .sql model file must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".sql") and "model" in root.lower():
                    found.append(os.path.join(root, f))
        if not found:
            for root, dirs, files in os.walk(self.REPO_DIR):
                for f in files:
                    if f.endswith(".sql"):
                        found.append(os.path.join(root, f))
        assert len(found) >= 1, "No .sql model files found"

    def test_schema_yml_exists(self):
        """A schema.yml or _schema.yml must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if "schema" in f.lower() and f.endswith((".yml", ".yaml")):
                    found = True
                    break
            if found:
                break
        assert found, "No schema.yml found"

    def test_dbt_project_yml_exists(self):
        """dbt_project.yml must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "dbt_project.yml" in files:
                found = True
                break
        assert found, "dbt_project.yml not found"

    # ------------------------------------------------------------------
    # L2: content validation
    # ------------------------------------------------------------------

    def _find_sql_models(self):
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".sql"):
                    found.append(os.path.join(root, f))
        return found

    def test_models_use_ref(self):
        """SQL models should use {{ ref('...') }} for dependencies."""
        found = False
        for fpath in self._find_sql_models():
            with open(fpath, "r", errors="ignore") as f:
                content = f.read()
            if "ref(" in content or "{{ ref" in content:
                found = True
                break
        assert found, "No model uses {{ ref() }}"

    def test_models_use_source(self):
        """SQL models should use {{ source('...') }} for raw data."""
        found = False
        for fpath in self._find_sql_models():
            with open(fpath, "r", errors="ignore") as f:
                content = f.read()
            if "source(" in content or "{{ source" in content:
                found = True
                break
        assert found, "No model uses {{ source() }}"

    def test_staging_model_pattern(self):
        """Should follow staging/marts layer pattern."""
        dirs_found = set()
        for root, dirs, files in os.walk(self.REPO_DIR):
            for d in dirs:
                if d.lower() in (
                    "staging",
                    "marts",
                    "intermediate",
                    "raw",
                    "transform",
                ):
                    dirs_found.add(d.lower())
        if not dirs_found:
            # Check SQL file prefixes
            for fpath in self._find_sql_models():
                fname = os.path.basename(fpath).lower()
                if (
                    fname.startswith("stg_")
                    or fname.startswith("fct_")
                    or fname.startswith("dim_")
                ):
                    dirs_found.add(fname[:3])
        assert len(dirs_found) >= 1, "No staging/marts layer pattern found"

    def test_schema_has_tests(self):
        """schema.yml must define column tests."""
        import yaml

        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if "schema" in f.lower() and f.endswith((".yml", ".yaml")):
                    fpath = os.path.join(root, f)
                    with open(fpath, "r") as fh:
                        doc = yaml.safe_load(fh)
                    if doc and isinstance(doc, dict):
                        content = str(doc)
                        test_patterns = [
                            "tests:",
                            "not_null",
                            "unique",
                            "accepted_values",
                            "relationships",
                        ]
                        if any(p in content for p in test_patterns):
                            return
        pytest.fail("No column tests in schema.yml")

    def test_schema_has_descriptions(self):
        """schema.yml must include model/column descriptions."""
        import yaml

        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if "schema" in f.lower() and f.endswith((".yml", ".yaml")):
                    fpath = os.path.join(root, f)
                    with open(fpath, "r") as fh:
                        content = fh.read()
                    if "description:" in content:
                        return
        pytest.fail("No descriptions in schema.yml")

    def test_cte_pattern(self):
        """SQL models should use CTE (WITH ... AS) pattern."""
        found = False
        for fpath in self._find_sql_models():
            with open(fpath, "r", errors="ignore") as f:
                content = f.read().upper()
            if "WITH " in content and " AS " in content:
                found = True
                break
        assert found, "No CTE pattern (WITH ... AS) in SQL models"

    def test_incremental_or_materialized(self):
        """At least one model should use config with materialization."""
        found = False
        for fpath in self._find_sql_models():
            with open(fpath, "r", errors="ignore") as f:
                content = f.read()
            if "materialized" in content or "config(" in content:
                found = True
                break
        assert found, "No materialization config in models"
