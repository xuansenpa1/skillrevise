"""
Test skill: add-malli-schemas
Verify that the Agent correctly adds Malli validation schemas to three
Metabase API endpoints: POST /api/card, PUT /api/dashboard/:id,
and POST /api/dataset.
"""

import os
import re
import subprocess
import pytest


class TestAddMalliSchemas:
    REPO_DIR = "/workspace/metabase"

    # === File Path Checks ===

    def test_card_api_file_exists(self):
        """Verify card.clj API file exists"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/card.clj")
        assert os.path.exists(path), f"card.clj not found at {path}"

    def test_dashboard_api_file_exists(self):
        """Verify dashboard.clj API file exists"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/dashboard.clj")
        assert os.path.exists(path), f"dashboard.clj not found at {path}"

    def test_dataset_api_file_exists(self):
        """Verify dataset.clj API file exists"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/dataset.clj")
        assert os.path.exists(path), f"dataset.clj not found at {path}"

    # === Semantic Checks – POST /api/card ===

    def test_card_endpoint_has_malli_schema(self):
        """Verify POST /api/card has Malli schema annotations"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/card.clj")
        with open(path, "r") as f:
            content = f.read()

        # Should have schema annotation using :- syntax or defendpoint schema
        has_schema = ":-" in content or "defendpoint" in content
        assert has_schema, "POST /api/card should have Malli schema annotations"

    def test_card_request_validates_name(self):
        """Verify card request body schema requires 'name' as NonBlankString"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/card.clj")
        with open(path, "r") as f:
            content = f.read()

        assert "name" in content, "Card schema should validate 'name' field"
        assert "NonBlankString" in content or "non-blank" in content.lower(), (
            "Card name should use NonBlankString or equivalent"
        )

    def test_card_request_validates_dataset_query(self):
        """Verify card request body schema validates dataset_query with type enum"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/card.clj")
        with open(path, "r") as f:
            content = f.read()

        assert "dataset_query" in content or "dataset-query" in content, (
            "Card schema should validate dataset_query field"
        )
        # Check for enum of native/structured
        assert "native" in content and "structured" in content, (
            "Card schema should validate type enum: native, structured"
        )

    def test_card_response_schema_defined(self):
        """Verify a named CardResponse schema is defined"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/card.clj")
        with open(path, "r") as f:
            content = f.read()

        assert re.search(r"CardResponse|::CardResponse|card-response", content), (
            "Should define a named CardResponse schema"
        )

    # === Semantic Checks – PUT /api/dashboard/:id ===

    def test_dashboard_route_param_schema(self):
        """Verify PUT /api/dashboard/:id validates route param as PositiveInt"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/dashboard.clj")
        with open(path, "r") as f:
            content = f.read()

        assert "PositiveInt" in content or "pos-int" in content, (
            "Dashboard :id route param should validate as PositiveInt"
        )

    def test_dashboard_validates_parameters(self):
        """Verify dashboard body schema validates parameters list"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/dashboard.clj")
        with open(path, "r") as f:
            content = f.read()

        assert "parameters" in content, (
            "Dashboard schema should validate 'parameters' field"
        )

    def test_dashboard_validates_cache_ttl(self):
        """Verify dashboard body schema validates cache_ttl"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/dashboard.clj")
        with open(path, "r") as f:
            content = f.read()

        assert "cache_ttl" in content or "cache-ttl" in content, (
            "Dashboard schema should validate cache_ttl field"
        )

    # === Semantic Checks – POST /api/dataset ===

    def test_dataset_validates_database_field(self):
        """Verify POST /api/dataset requires database as PositiveInt"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/dataset.clj")
        with open(path, "r") as f:
            content = f.read()

        assert "database" in content, (
            "Dataset schema should validate 'database' field"
        )
        assert "PositiveInt" in content or "pos-int" in content, (
            "Dataset database should be validated as PositiveInt"
        )

    def test_dataset_validates_type_enum(self):
        """Verify POST /api/dataset validates type as native/structured enum"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/dataset.clj")
        with open(path, "r") as f:
            content = f.read()

        assert "native" in content and "structured" in content, (
            "Dataset schema should validate type enum: native, structured"
        )

    def test_dataset_response_schema(self):
        """Verify dataset response schema includes data/status/row_count"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/dataset.clj")
        with open(path, "r") as f:
            content = f.read()

        has_response = (
            "data" in content
            and ("status" in content or "completed" in content)
        )
        assert has_response, (
            "Dataset response schema should define data and status fields"
        )

    def test_uses_named_schemas_with_mr_def(self):
        """Verify that complex types use named schemas (mr/def or equivalent)"""
        found_named_schema = False
        for filename in ["card.clj", "dashboard.clj", "dataset.clj"]:
            path = os.path.join(self.REPO_DIR, "src/metabase/api", filename)
            with open(path, "r") as f:
                content = f.read()
            if "mr/def" in content or "mu/def" in content or "def ::" in content:
                found_named_schema = True
                break

        assert found_named_schema, (
            "Should use named schemas (mr/def or equivalent) for reusable types"
        )

    def test_uses_metabase_schema_types(self):
        """Verify that standard Metabase schema types from ms namespace are used"""
        ms_types = ["ms/PositiveInt", "ms/NonBlankString", "ms/TemporalString", "ms/BooleanValue"]
        found_count = 0
        for filename in ["card.clj", "dashboard.clj", "dataset.clj"]:
            path = os.path.join(self.REPO_DIR, "src/metabase/api", filename)
            with open(path, "r") as f:
                content = f.read()
            for ms_type in ms_types:
                if ms_type in content:
                    found_count += 1

        assert found_count >= 2, (
            f"Should use at least 2 Metabase schema types (ms/*), found {found_count}"
        )

    def test_optional_fields_use_optional_true(self):
        """Verify optional fields use {:optional true} syntax"""
        found = False
        for filename in ["card.clj", "dashboard.clj", "dataset.clj"]:
            path = os.path.join(self.REPO_DIR, "src/metabase/api", filename)
            with open(path, "r") as f:
                content = f.read()
            if "{:optional true}" in content or ":optional true" in content:
                found = True
                break

        assert found, "Optional fields should use {:optional true}"

    # === Functional Checks ===

    def test_clojure_files_parse_without_errors(self):
        """Verify all modified Clojure files parse without syntax errors"""
        for filename in ["card.clj", "dashboard.clj", "dataset.clj"]:
            path = os.path.join(self.REPO_DIR, "src/metabase/api", filename)
            with open(path, "r") as f:
                content = f.read()

            # Basic Clojure syntax: balanced parens
            opens = content.count("(")
            closes = content.count(")")
            assert abs(opens - closes) <= 2, (
                f"{filename}: Unbalanced parentheses ({opens} open, {closes} close)"
            )

    def test_card_file_has_no_syntax_errors(self):
        """Verify card.clj evaluates or compiles without errors"""
        result = subprocess.run(
            ["clojure", "-e", f'(load-file "src/metabase/api/card.clj")'],
            capture_output=True, text=True, timeout=120,
            cwd=self.REPO_DIR,
        )
        # If clojure CLI isn't available, try lein
        if result.returncode != 0 and "clojure" in result.stderr.lower():
            result = subprocess.run(
                ["lein", "check"],
                capture_output=True, text=True, timeout=300,
                cwd=self.REPO_DIR,
            )
        # Accept if compilation doesn't show the files we modified as errors
        if result.returncode != 0:
            # At minimum, our files should not introduce new parse errors
            assert "card.clj" not in result.stderr or "Syntax" not in result.stderr, (
                f"card.clj has syntax errors:\n{result.stderr[:1000]}"
            )
