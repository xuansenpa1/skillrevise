"""
Test for 'add-malli-schemas' skill — Malli Schema Validation in Metabase
Validates that the Agent added Malli schemas for API request/response
validation in the Metabase Clojure codebase.
"""

import os
import subprocess
import pytest


class TestAddMalliSchemas:
    """Verify Malli schema implementation in Metabase."""

    REPO_DIR = "/workspace/metabase"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_schema_file_exists(self):
        """A Malli schema definition file must exist."""
        src_dir = os.path.join(self.REPO_DIR, "src")
        found = []
        for root, dirs, files in os.walk(src_dir):
            for f in files:
                if f.endswith(".clj") and "schema" in f.lower():
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No schema-related .clj file found in src/"

    def test_test_file_exists(self):
        """Test file for schema validation must exist."""
        test_dir = os.path.join(self.REPO_DIR, "test")
        found = []
        for root, dirs, files in os.walk(test_dir):
            for f in files:
                if f.endswith(".clj") and "schema" in f.lower():
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No schema test .clj file found in test/"

    # ------------------------------------------------------------------
    # L2: content validation
    # ------------------------------------------------------------------

    def _find_schema_files(self):
        """Find all Clojure files referencing malli."""
        result = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".clj"):
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read()
                        if "malli" in content:
                            result.append(fpath)
                    except OSError:
                        pass
        return result

    def test_malli_dependency_used(self):
        """Project must use malli library (referenced in source)."""
        files = self._find_schema_files()
        assert len(files) >= 1, "No .clj file references malli"

    def test_schema_has_map_definition(self):
        """Schema file must define :map or [:map ...] schemas."""
        files = self._find_schema_files()
        for fpath in files:
            with open(fpath, "r") as f:
                content = f.read()
            if ":map" in content or "[:map" in content:
                return
        pytest.fail("No :map schema definition found")

    def test_schema_has_required_fields(self):
        """Schema must define required fields (card, dashboard, etc.)."""
        files = self._find_schema_files()
        field_patterns = [
            ":name",
            ":id",
            ":description",
            ":type",
            ":email",
            ":string",
            ":int",
        ]
        for fpath in files:
            with open(fpath, "r") as f:
                content = f.read()
            found = sum(1 for p in field_patterns if p in content)
            if found >= 3:
                return
        pytest.fail("Schema files don't define enough typed fields")

    def test_schema_uses_malli_core(self):
        """Files must require malli.core."""
        files = self._find_schema_files()
        for fpath in files:
            with open(fpath, "r") as f:
                content = f.read()
            if "malli.core" in content or "m/schema" in content or "[m " in content:
                return
        pytest.fail("No file requires malli.core")

    def test_validation_function_exists(self):
        """Must define validation functions (m/validate, m/explain, etc.)."""
        files = self._find_schema_files()
        validators = [
            "m/validate",
            "m/explain",
            "m/decode",
            "m/encode",
            "validate",
            "explain",
            "coerce",
        ]
        for fpath in files:
            with open(fpath, "r") as f:
                content = f.read()
            found = any(v in content for v in validators)
            if found:
                return
        pytest.fail("No validation function (m/validate etc.) found")

    def test_error_handling(self):
        """Schema validation must include error handling."""
        files = self._find_schema_files()
        error_patterns = [
            "m/explain",
            "humanize",
            "error",
            "invalid",
            "throw",
            "ex-info",
            "assert",
        ]
        for fpath in files:
            with open(fpath, "r") as f:
                content = f.read()
            found = any(p in content for p in error_patterns)
            if found:
                return
        pytest.fail("No error handling found in schema validation")

    def test_clojure_syntax_check(self):
        """Clojure files must be parseable (basic bracket matching)."""
        files = self._find_schema_files()
        for fpath in files:
            with open(fpath, "r") as f:
                content = f.read()
            opens = content.count("(") + content.count("[") + content.count("{")
            closes = content.count(")") + content.count("]") + content.count("}")
            # Allow small imbalance from strings/comments but not large
            diff = abs(opens - closes)
            assert (
                diff <= 5
            ), f"{fpath} has {diff} bracket imbalance (opens={opens}, closes={closes})"

    def test_api_endpoint_integration(self):
        """Schema should be integrated with API endpoints (compojure/reitit)."""
        files = self._find_schema_files()
        api_patterns = [
            "defendpoint",
            "compojure",
            "reitit",
            "api/",
            "middleware",
            "coercion",
            "ring",
        ]
        for fpath in files:
            with open(fpath, "r") as f:
                content = f.read()
            found = any(p in content.lower() for p in api_patterns)
            if found:
                return
        # Check broader source
        src_dir = os.path.join(self.REPO_DIR, "src")
        for root, dirs, files_list in os.walk(src_dir):
            for fname in files_list:
                if fname.endswith(".clj"):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", errors="ignore") as f:
                            content = f.read()
                        if "malli" in content and any(
                            p in content.lower() for p in api_patterns
                        ):
                            return
                    except OSError:
                        pass
        pytest.fail("No API endpoint integration with malli schemas found")
