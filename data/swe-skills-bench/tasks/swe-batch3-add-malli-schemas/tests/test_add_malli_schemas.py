"""
Tests for the add-malli-schemas skill.

Validates that Malli validation schemas were correctly implemented for
Metabase Dashboard API endpoints, including dashboard CRUD schemas,
parameter validation, card layout constraints, and validation functions.

Repo: metabase (https://github.com/metabase/metabase)
"""

import os
import re
import subprocess

REPO_DIR = "/workspace/metabase"


class TestFilePathCheck:
    """Verify that all required files were created."""

    def test_dashboard_schema_file_exists(self):
        path = os.path.join(REPO_DIR, "src", "metabase", "api", "dashboard", "schema.clj")
        assert os.path.isfile(path), f"Expected schema file at {path}"

    def test_dashboard_validators_file_exists(self):
        path = os.path.join(REPO_DIR, "src", "metabase", "api", "dashboard", "validators.clj")
        assert os.path.isfile(path), f"Expected validators file at {path}"

    def test_dashboard_schema_test_file_exists(self):
        path = os.path.join(REPO_DIR, "test", "metabase", "api", "dashboard", "schema_test.clj")
        assert os.path.isfile(path), f"Expected schema test file at {path}"


class TestSemanticSchemaDefinitions:
    """Verify the Malli schemas are defined with correct types and constraints."""

    def _read_schema_file(self):
        path = os.path.join(REPO_DIR, "src", "metabase", "api", "dashboard", "schema.clj")
        with open(path, "r") as f:
            return f.read()

    def test_dashboard_schema_defined(self):
        content = self._read_schema_file()
        assert re.search(r":ms/Dashboard\b", content), (
            "Expected :ms/Dashboard schema to be defined in schema.clj"
        )

    def test_dashboard_create_request_schema_defined(self):
        content = self._read_schema_file()
        assert re.search(r":ms/DashboardCreateRequest\b", content), (
            "Expected :ms/DashboardCreateRequest schema to be defined"
        )

    def test_dashboard_update_request_schema_defined(self):
        content = self._read_schema_file()
        assert re.search(r":ms/DashboardUpdateRequest\b", content), (
            "Expected :ms/DashboardUpdateRequest schema to be defined"
        )

    def test_dashboard_parameter_schema_defined(self):
        content = self._read_schema_file()
        assert re.search(r":ms/DashboardParameter\b", content), (
            "Expected :ms/DashboardParameter schema to be defined"
        )

    def test_dashboard_card_schema_defined(self):
        content = self._read_schema_file()
        assert re.search(r":ms/DashboardCard\b", content), (
            "Expected :ms/DashboardCard schema to be defined"
        )

    def test_parameter_mapping_schema_defined(self):
        content = self._read_schema_file()
        assert re.search(r":ms/ParameterMapping\b", content), (
            "Expected :ms/ParameterMapping schema to be defined"
        )

    def test_dashboard_fields_present(self):
        """Check that key dashboard fields are referenced in the schema."""
        content = self._read_schema_file()
        for field in [":name", ":description", ":collection_id", ":parameters", ":cards"]:
            assert field in content, f"Expected field {field} in Dashboard schema"

    def test_parameter_type_enum_values(self):
        """Check that the parameter type enum includes required values."""
        content = self._read_schema_file()
        for ptype in ["date/single", "date/range", "string/=", "number/=", "category"]:
            assert ptype in content, (
                f"Expected parameter type enum value '{ptype}' in schema"
            )

    def test_grid_column_constraint(self):
        """Card col must be < 18 (0-17 for 18-column grid)."""
        content = self._read_schema_file()
        assert re.search(r"18|grid|col", content), (
            "Expected grid column constraint (col < 18 or size_x <= 18) in DashboardCard schema"
        )

    def test_card_grid_boundary_custom_validator(self):
        """col + size_x <= 18 custom validator must exist."""
        content = self._read_schema_file()
        assert re.search(r"grid.boundary|col.*size_x|extends.beyond", content, re.IGNORECASE), (
            "Expected custom validator for card grid boundary (col + size_x <= 18)"
        )


class TestSemanticValidatorFunctions:
    """Verify validation function definitions in validators.clj."""

    def _read_validators_file(self):
        path = os.path.join(REPO_DIR, "src", "metabase", "api", "dashboard", "validators.clj")
        with open(path, "r") as f:
            return f.read()

    def test_validate_create_request_function(self):
        content = self._read_validators_file()
        assert re.search(r"validate-create-request", content), (
            "Expected validate-create-request function in validators.clj"
        )

    def test_validate_update_request_function(self):
        content = self._read_validators_file()
        assert re.search(r"validate-update-request", content), (
            "Expected validate-update-request function in validators.clj"
        )

    def test_validate_card_layout_function(self):
        content = self._read_validators_file()
        assert re.search(r"validate-card-layout", content), (
            "Expected validate-card-layout function in validators.clj"
        )

    def test_validation_returns_structured_result(self):
        """Validation functions should return maps with :valid and :errors/:data keys."""
        content = self._read_validators_file()
        assert ":valid" in content, (
            "Expected :valid key in validation result structure"
        )
        assert re.search(r":errors|:data", content), (
            "Expected :errors or :data keys in validation result structure"
        )

    def test_coercion_logic_present(self):
        """Validators should include type coercion (string→int, string→inst)."""
        content = self._read_validators_file()
        assert re.search(r"coer|transform|decode", content, re.IGNORECASE), (
            "Expected type coercion logic in validators (coerce/transform/decode)"
        )


class TestSemanticCreateRequestExcludesServerFields:
    """Create/Update request schemas should exclude server-managed fields."""

    def _read_schema_file(self):
        path = os.path.join(REPO_DIR, "src", "metabase", "api", "dashboard", "schema.clj")
        with open(path, "r") as f:
            return f.read()

    def test_create_request_has_no_id_field(self):
        """The DashboardCreateRequest schema should not include :id as a required/accepted field.
        We check that :id is not associated with the create request definition."""
        content = self._read_schema_file()
        # Find the create request schema block and verify :id and timestamps are excluded
        # This is a heuristic check — :id should not appear between CreateRequest and the next schema
        create_match = re.search(
            r":ms/DashboardCreateRequest(.*?)(?=:ms/|$)", content, re.DOTALL
        )
        if create_match:
            block = create_match.group(1)
            # :id should not be a direct field in the create request
            # It may appear in nested schemas (DashboardCard), so check top level
            assert not re.search(r'^\s*:id\b', block, re.MULTILINE), (
                "DashboardCreateRequest should not include :id as a top-level field"
            )

    def test_namespace_declaration(self):
        content = self._read_schema_file()
        assert re.search(r"\(ns\s+metabase\.api\.dashboard\.schema", content), (
            "Expected proper namespace declaration for metabase.api.dashboard.schema"
        )


class TestSemanticOverlapDetection:
    """Card layout validation should detect overlapping positions."""

    def _read_validators_file(self):
        path = os.path.join(REPO_DIR, "src", "metabase", "api", "dashboard", "validators.clj")
        with open(path, "r") as f:
            return f.read()

    def test_overlap_detection_logic_present(self):
        content = self._read_validators_file()
        assert re.search(r"overlap|intersect|collision", content, re.IGNORECASE), (
            "Expected overlap/intersection detection logic in validate-card-layout"
        )

    def test_uses_malli_library(self):
        """Schema file should require/use malli."""
        path = os.path.join(REPO_DIR, "src", "metabase", "api", "dashboard", "schema.clj")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"malli", content, re.IGNORECASE), (
            "Expected malli library usage in schema.clj"
        )


class TestFunctionalClojureSyntax:
    """Validate Clojure files have valid syntax and can be parsed."""

    def test_schema_file_balanced_parens(self):
        path = os.path.join(REPO_DIR, "src", "metabase", "api", "dashboard", "schema.clj")
        with open(path, "r") as f:
            content = f.read()
        open_count = content.count("(") + content.count("[") + content.count("{")
        close_count = content.count(")") + content.count("]") + content.count("}")
        assert open_count == close_count, (
            f"Unbalanced delimiters in schema.clj: {open_count} opening vs {close_count} closing"
        )

    def test_validators_file_balanced_parens(self):
        path = os.path.join(REPO_DIR, "src", "metabase", "api", "dashboard", "validators.clj")
        with open(path, "r") as f:
            content = f.read()
        open_count = content.count("(") + content.count("[") + content.count("{")
        close_count = content.count(")") + content.count("]") + content.count("}")
        assert open_count == close_count, (
            f"Unbalanced delimiters in validators.clj: {open_count} opening vs {close_count} closing"
        )

    def test_test_file_balanced_parens(self):
        path = os.path.join(REPO_DIR, "test", "metabase", "api", "dashboard", "schema_test.clj")
        with open(path, "r") as f:
            content = f.read()
        open_count = content.count("(") + content.count("[") + content.count("{")
        close_count = content.count(")") + content.count("]") + content.count("}")
        assert open_count == close_count, (
            f"Unbalanced delimiters in schema_test.clj: {open_count} opening vs {close_count} closing"
        )

    def test_schema_test_uses_clojure_test(self):
        path = os.path.join(REPO_DIR, "test", "metabase", "api", "dashboard", "schema_test.clj")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"clojure\.test", content), (
            "Expected clojure.test to be required in schema_test.clj"
        )

    def test_schema_test_has_deftest(self):
        path = os.path.join(REPO_DIR, "test", "metabase", "api", "dashboard", "schema_test.clj")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"\(deftest\s+", content), (
            "Expected at least one deftest in schema_test.clj"
        )

    def test_schema_test_imports_schema_ns(self):
        """The test file should require the schema namespace."""
        path = os.path.join(REPO_DIR, "test", "metabase", "api", "dashboard", "schema_test.clj")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"metabase\.api\.dashboard\.schema", content), (
            "Expected schema_test.clj to require metabase.api.dashboard.schema"
        )

    def test_validators_namespace_declaration(self):
        path = os.path.join(REPO_DIR, "src", "metabase", "api", "dashboard", "validators.clj")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"\(ns\s+metabase\.api\.dashboard\.validators", content), (
            "Expected proper namespace declaration for metabase.api.dashboard.validators"
        )
