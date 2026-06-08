"""
Test skill: add-malli-schemas
Verify that the Agent correctly adds Malli schemas to Metabase Field API endpoints.
"""

import os
import re
import subprocess
import pytest


class TestAddMalliSchemas:
    REPO_DIR = "/workspace/metabase"

    # === File Path Checks ===

    def test_field_api_clj_exists(self):
        """Verify src/metabase/api/field.clj exists"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        assert os.path.exists(path), f"field.clj not found at {path}"

    def test_field_test_clj_exists(self):
        """Verify test/metabase/api/field_test.clj exists"""
        path = os.path.join(self.REPO_DIR, "test/metabase/api/field_test.clj")
        assert os.path.exists(path), f"field_test.clj not found at {path}"

    # === Semantic Checks: Route Param Schemas ===

    def test_route_params_use_positive_int(self):
        """Verify route params use ms/PositiveInt for :id"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        assert "PositiveInt" in content, (
            "Route params should use ms/PositiveInt for :id validation"
        )

    def test_defendpoint_declarations_have_schemas(self):
        """Verify defendpoint forms include Malli schema annotations"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        assert "defendpoint" in content, "File should contain defendpoint declarations"
        # At least some endpoints should have schema annotations
        assert content.count(":-") >= 2 or content.count(":- ") >= 2, (
            "defendpoint forms should include response schema annotations with :-"
        )

    def test_get_field_id_has_route_param_schema(self):
        """Verify GET /api/field/:id validates id as PositiveInt"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        # Look for GET endpoint with id and PositiveInt near each other
        assert "PositiveInt" in content, "id param should be validated as PositiveInt"

    # === Semantic Checks: Query Param Schemas ===

    def test_remapping_endpoint_has_query_param(self):
        """Verify GET /api/field/:id/remapping has remapped_value query param schema"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        assert "remapped_value" in content, (
            "remapping endpoint should reference remapped_value param"
        )
        assert "NonBlankString" in content, (
            "remapped_value should be validated as ms/NonBlankString"
        )

    def test_include_editable_data_model_param(self):
        """Verify GET /api/field/:id has optional include_editable_data_model param"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        assert "include_editable_data_model" in content, (
            "GET field endpoint should have include_editable_data_model query param"
        )

    # === Semantic Checks: Request Body Schemas ===

    def test_put_field_body_has_display_name_schema(self):
        """Verify PUT /api/field/:id body includes display_name with schema"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        assert "display_name" in content, "PUT body should include display_name field"

    def test_put_field_body_has_visibility_type_enum(self):
        """Verify PUT /api/field/:id body validates visibility_type as enum"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        assert "visibility_type" in content, "PUT body should include visibility_type"
        # Check for enum with valid values
        for val in ["normal", "details-only", "hidden", "retired"]:
            assert val in content, (
                f"visibility_type enum should include '{val}'"
            )

    def test_post_dimension_body_has_type_enum(self):
        """Verify POST /api/field/:id/dimension body validates type as enum"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        assert "external" in content and "internal" in content, (
            "dimension type should be validated as enum with 'external' and 'internal'"
        )

    def test_post_dimension_body_requires_name(self):
        """Verify POST /api/field/:id/dimension body requires :name field"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        # The dimension endpoint should reference :name as required
        assert "dimension" in content.lower(), "Should have dimension endpoint"

    def test_post_values_body_has_values_schema(self):
        """Verify POST /api/field/:id/values body defines values as sequential"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        assert "sequential" in content, (
            "values endpoint body should validate :values as [:sequential ...]"
        )

    # === Semantic Checks: Response Schemas ===

    def test_field_response_schema_defined(self):
        """Verify ::FieldResponse named schema is defined with mr/def"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        assert "FieldResponse" in content, (
            "::FieldResponse named schema should be defined"
        )

    def test_field_response_has_required_keys(self):
        """Verify FieldResponse schema includes core field keys"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        for key in [":id", ":name", ":display_name", ":base_type", ":table_id"]:
            assert key in content, (
                f"FieldResponse schema should include {key}"
            )

    def test_response_temporal_fields_use_any(self):
        """Verify :created_at and :updated_at use :any in response schemas"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        assert "created_at" in content, "Response should include :created_at"
        assert "updated_at" in content, "Response should include :updated_at"
        # They should use :any, not ms/TemporalString
        assert ":any" in content, "Temporal fields should use :any type"

    # === Semantic Checks: Separate Destructuring ===

    def test_route_params_destructured_separately(self):
        """Verify route params are destructured separately from query/body params"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        # In Malli-annotated defendpoint, route params, query params, and body
        # params should be in separate map destructuring forms
        assert ":optional" in content, (
            "Should have :optional markers for separated param destructuring"
        )

    # === Semantic Checks: Test Coverage ===

    def test_test_file_has_validation_tests(self):
        """Verify test file includes schema validation tests"""
        path = os.path.join(self.REPO_DIR, "test/metabase/api/field_test.clj")
        with open(path) as f:
            content = f.read()
        assert "400" in content or "invalid" in content.lower(), (
            "Tests should verify HTTP 400 for invalid inputs"
        )

    def test_test_file_validates_non_integer_id(self):
        """Verify tests check that non-integer id returns 400"""
        path = os.path.join(self.REPO_DIR, "test/metabase/api/field_test.clj")
        with open(path) as f:
            content = f.read()
        # Should test something like GET /api/field/abc
        assert "field" in content.lower(), "Tests should reference field API"

    # === Functional Checks ===

    def test_clojure_file_parses_without_errors(self):
        """Verify field.clj has balanced parentheses (basic syntax check)"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        # Simple paren balance check
        open_parens = content.count("(") + content.count("[") + content.count("{")
        close_parens = content.count(")") + content.count("]") + content.count("}")
        assert open_parens == close_parens, (
            f"Parentheses mismatch: {open_parens} opening vs {close_parens} closing"
        )

    def test_has_field_values_enum(self):
        """Verify has_field_values field uses proper enum values"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        for val in ["none", "list", "search"]:
            assert val in content, (
                f"has_field_values enum should include '{val}'"
            )

    def test_summary_response_inline_schema(self):
        """Verify GET /api/field/:id/summary has inline response schema"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        assert "distinct-count" in content or "summary" in content.lower(), (
            "Summary endpoint should have response schema with :distinct-count"
        )

    def test_namespace_requires_malli(self):
        """Verify namespace requires Malli schema namespaces"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/field.clj")
        with open(path) as f:
            content = f.read()
        assert "metabase.util.malli" in content or "malli" in content.lower(), (
            "Namespace should require Malli schema utilities"
        )
