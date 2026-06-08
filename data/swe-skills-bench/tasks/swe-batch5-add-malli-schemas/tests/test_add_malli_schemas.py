"""
Test skill: add-malli-schemas
Verify that the Agent correctly defines Malli schemas for Metabase
Dashboard and Card entities in Clojure.
"""

import os
import re
import subprocess
import pytest


class TestAddMalliSchemas:
    REPO_DIR = "/workspace/metabase"

    DASHBOARD_SCHEMA = "src/metabase/models/dashboard/schema.clj"
    CARD_SCHEMA = "src/metabase/models/card/schema.clj"
    SCHEMA_REGISTRY = "src/metabase/models/schema_registry.clj"
    DASHBOARD_TEST = "test/metabase/models/dashboard/schema_test.clj"
    CARD_TEST = "test/metabase/models/card/schema_test.clj"

    def _read_file(self, rel_path):
        filepath = os.path.join(self.REPO_DIR, rel_path)
        with open(filepath) as f:
            return f.read()

    # === File Path Checks ===

    def test_dashboard_schema_exists(self):
        """Verify dashboard/schema.clj exists"""
        filepath = os.path.join(self.REPO_DIR, self.DASHBOARD_SCHEMA)
        assert os.path.exists(filepath), f"Dashboard schema not found at {filepath}"

    def test_card_schema_exists(self):
        """Verify card/schema.clj exists"""
        filepath = os.path.join(self.REPO_DIR, self.CARD_SCHEMA)
        assert os.path.exists(filepath), f"Card schema not found at {filepath}"

    def test_schema_registry_exists(self):
        """Verify schema_registry.clj exists"""
        filepath = os.path.join(self.REPO_DIR, self.SCHEMA_REGISTRY)
        assert os.path.exists(filepath), f"Schema registry not found at {filepath}"

    def test_test_files_exist(self):
        """Verify test files for dashboard and card schemas exist"""
        for path in [self.DASHBOARD_TEST, self.CARD_TEST]:
            filepath = os.path.join(self.REPO_DIR, path)
            assert os.path.exists(filepath), f"Test file not found: {filepath}"

    # === Semantic Checks ===

    def test_dashboard_schema_defines_dashboard(self):
        """Verify Dashboard schema definition with required fields"""
        content = self._read_file(self.DASHBOARD_SCHEMA)
        assert "Dashboard" in content, "Dashboard schema not defined"
        for field in [":name", ":dashcards", ":parameters"]:
            assert field in content, \
                f"Dashboard schema missing field: {field}"

    def test_dashboard_schema_defines_dashboardcard(self):
        """Verify DashboardCard schema with position and size fields"""
        content = self._read_file(self.DASHBOARD_SCHEMA)
        assert "DashboardCard" in content, "DashboardCard schema not defined"
        for field in [":card_id", ":row", ":col", ":size_x", ":size_y"]:
            assert field in content, \
                f"DashboardCard missing field: {field}"

    def test_dashboard_schema_defines_parameter_mapping(self):
        """Verify ParameterMapping schema definition"""
        content = self._read_file(self.DASHBOARD_SCHEMA)
        assert "ParameterMapping" in content, "ParameterMapping not defined"
        assert ":parameter_id" in content, "ParameterMapping missing :parameter_id"

    def test_card_schema_defines_card_with_display_enum(self):
        """Verify Card schema has display field with enum of visualization types"""
        content = self._read_file(self.CARD_SCHEMA)
        assert "Card" in content, "Card schema not defined"
        assert ":display" in content, "Card schema missing :display field"
        # Check for display type enum values
        display_types = ["table", "bar", "line", "pie", "scalar"]
        found_types = sum(1 for t in display_types if f'"{t}"' in content)
        assert found_types >= 3, \
            f"Card :display enum should include visualization types, found {found_types}/5"

    def test_card_schema_defines_dataset_query_multimethod(self):
        """Verify DatasetQuery uses multi-method dispatch for native vs structured"""
        content = self._read_file(self.CARD_SCHEMA)
        assert "DatasetQuery" in content, "DatasetQuery not defined"
        has_multi = bool(re.search(r':multi|multi', content))
        assert has_multi, "DatasetQuery should use :multi dispatch"
        assert "native" in content.lower(), "DatasetQuery missing native query branch"
        assert "StructuredQuery" in content or "structured" in content.lower(), \
            "DatasetQuery missing structured query branch"

    def test_card_schema_defines_native_query(self):
        """Verify NativeQuery schema has :query string field"""
        content = self._read_file(self.CARD_SCHEMA)
        assert "NativeQuery" in content, "NativeQuery not defined"
        assert ":query" in content, "NativeQuery missing :query field"

    def test_schema_registry_has_registration(self):
        """Verify schema registry provides register and validate functions"""
        content = self._read_file(self.SCHEMA_REGISTRY)
        assert "register" in content.lower(), \
            "Schema registry missing registration function"
        assert "validate" in content.lower(), \
            "Schema registry missing validation function"

    def test_visualization_settings_is_open_map(self):
        """Verify VisualizationSettings allows arbitrary keys (open map)"""
        content = self._read_file(self.CARD_SCHEMA)
        assert "VisualizationSettings" in content, \
            "VisualizationSettings not defined"
        # Should NOT be :closed for visualization settings
        # Look for the definition area - it should be an open map
        vis_match = re.search(
            r'VisualizationSettings.*?(\[:map[^\]]*)', content, re.DOTALL
        )
        if vis_match:
            assert ":closed" not in vis_match.group(1), \
                "VisualizationSettings should be an open map (not :closed)"

    # === Functional Checks ===

    def test_dashboard_schema_has_malli_syntax(self):
        """Verify dashboard schema uses valid Malli syntax patterns"""
        content = self._read_file(self.DASHBOARD_SCHEMA)
        # Check for Malli schema markers
        has_malli = bool(re.search(r'\[:map|\[:vector|\[:enum|\[:string', content))
        assert has_malli, \
            "Dashboard schema missing Malli syntax ([:map, [:vector, [:enum, etc.)"

    def test_card_schema_has_malli_syntax(self):
        """Verify card schema uses valid Malli syntax patterns"""
        content = self._read_file(self.CARD_SCHEMA)
        has_malli = bool(re.search(r'\[:map|\[:vector|\[:enum|\[:string', content))
        assert has_malli, \
            "Card schema missing Malli syntax ([:map, [:vector, [:enum, etc.)"

    def test_schemas_use_proper_clojure_namespace(self):
        """Verify schema files declare proper Clojure namespaces"""
        for path in [self.DASHBOARD_SCHEMA, self.CARD_SCHEMA, self.SCHEMA_REGISTRY]:
            content = self._read_file(path)
            assert "(ns " in content, \
                f"{path} missing Clojure namespace declaration"

    def test_test_files_have_deftest(self):
        """Verify test files contain deftest definitions"""
        for path in [self.DASHBOARD_TEST, self.CARD_TEST]:
            content = self._read_file(path)
            assert "deftest" in content, \
                f"{path} missing deftest definitions"
            test_count = content.count("deftest")
            assert test_count >= 3, \
                f"{path} should have at least 3 tests, found {test_count}"
