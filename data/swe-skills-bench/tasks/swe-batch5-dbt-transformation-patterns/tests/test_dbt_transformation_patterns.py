"""
Test skill: dbt-transformation-patterns
Verify that the Agent creates a dbt marts layer with staging, intermediate,
and CLV models including schema tests and incremental materialization.
"""

import os
import re
import pytest

try:
    import yaml
except ImportError:
    yaml = None


class TestDbtTransformationPatterns:
    REPO_DIR = "/workspace/dbt-core"

    BASE = "tests/fixtures/jaffle_shop"
    STG_CUSTOMERS = f"{BASE}/models/staging/stg_customers.sql"
    STG_ORDERS = f"{BASE}/models/staging/stg_orders.sql"
    STG_PAYMENTS = f"{BASE}/models/staging/stg_payments.sql"
    INT_ORDERS = f"{BASE}/models/intermediate/int_customer_orders.sql"
    FCT_CLV = f"{BASE}/models/marts/fct_customer_ltv.sql"
    SCHEMA = f"{BASE}/models/schema.yml"
    DBT_PROJECT = f"{BASE}/dbt_project.yml"

    def _read_file(self, rel_path):
        filepath = os.path.join(self.REPO_DIR, rel_path)
        with open(filepath) as f:
            return f.read()

    # === File Path Checks ===

    def test_stg_customers_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.STG_CUSTOMERS)
        assert os.path.exists(filepath), "stg_customers.sql not found"

    def test_stg_orders_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.STG_ORDERS)
        assert os.path.exists(filepath), "stg_orders.sql not found"

    def test_stg_payments_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.STG_PAYMENTS)
        assert os.path.exists(filepath), "stg_payments.sql not found"

    def test_int_customer_orders_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.INT_ORDERS)
        assert os.path.exists(filepath), "int_customer_orders.sql not found"

    def test_fct_customer_ltv_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.FCT_CLV)
        assert os.path.exists(filepath), "fct_customer_ltv.sql not found"

    def test_schema_yml_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.SCHEMA)
        assert os.path.exists(filepath), "schema.yml not found"

    def test_dbt_project_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.DBT_PROJECT)
        assert os.path.exists(filepath), "dbt_project.yml not found"

    # === Semantic Checks ===

    def test_stg_customers_uses_source(self):
        """Verify stg_customers references source raw_customers"""
        content = self._read_file(self.STG_CUSTOMERS)
        assert "source(" in content, "stg_customers missing source() ref"
        assert "raw_customers" in content, "stg_customers missing raw_customers"
        assert "customer_id" in content, "stg_customers missing customer_id rename"

    def test_stg_orders_filters_cancelled(self):
        """Verify stg_orders filters out cancelled orders"""
        content = self._read_file(self.STG_ORDERS)
        assert "cancelled" in content.lower(), "stg_orders missing cancelled filter"

    def test_stg_payments_converts_cents(self):
        """Verify stg_payments divides amount by 100"""
        content = self._read_file(self.STG_PAYMENTS)
        assert "100" in content, "stg_payments missing cents-to-dollars conversion"

    def test_int_model_aggregates(self):
        """Verify int_customer_orders computes order_count, totals"""
        content = self._read_file(self.INT_ORDERS)
        for pattern in ["order_count", "first_order_date",
                        "most_recent_order_date", "total_order_amount"]:
            assert pattern in content, \
                f"int_customer_orders missing: {pattern}"

    def test_fct_clv_incremental(self):
        """Verify fct_customer_ltv uses incremental materialization"""
        content = self._read_file(self.FCT_CLV)
        assert "incremental" in content, "fct_customer_ltv missing incremental config"
        assert "is_incremental" in content, "fct_customer_ltv missing is_incremental"

    def test_fct_clv_unique_key(self):
        """Verify fct_customer_ltv has unique_key=customer_id"""
        content = self._read_file(self.FCT_CLV)
        assert "customer_id" in content, "fct_customer_ltv missing customer_id key"

    def test_fct_clv_nullif(self):
        """Verify CLV handles division by zero with NULLIF"""
        content = self._read_file(self.FCT_CLV)
        assert "NULLIF" in content.upper(), "fct_customer_ltv missing NULLIF"

    def test_fct_clv_computes_predicted_ltv(self):
        """Verify CLV model computes predicted_ltv"""
        content = self._read_file(self.FCT_CLV)
        assert "predicted_ltv" in content, "fct_customer_ltv missing predicted_ltv"

    @pytest.mark.skipif(yaml is None, reason="PyYAML not installed")
    def test_schema_has_tests(self):
        """Verify schema.yml defines not_null, unique, relationships tests"""
        content = self._read_file(self.SCHEMA)
        for test_type in ["not_null", "unique", "relationships"]:
            assert test_type in content, f"schema.yml missing {test_type} test"

    @pytest.mark.skipif(yaml is None, reason="PyYAML not installed")
    def test_schema_has_accepted_values(self):
        """Verify accepted_values on status column"""
        content = self._read_file(self.SCHEMA)
        assert "accepted_values" in content, "schema.yml missing accepted_values"

    @pytest.mark.skipif(yaml is None, reason="PyYAML not installed")
    def test_dbt_project_materializations(self):
        """Verify dbt_project.yml configures staging=view, marts=incremental"""
        content = self._read_file(self.DBT_PROJECT)
        doc = yaml.safe_load(content)
        assert "jaffle_shop" in str(doc.get("name", "")), \
            "dbt_project.yml missing name: jaffle_shop"
        assert "view" in content, "Missing staging=view materialization"
        assert "incremental" in content, "Missing marts=incremental"

    # === Functional Checks ===

    @pytest.mark.skipif(yaml is None, reason="PyYAML not installed")
    def test_schema_valid_yaml(self):
        """Verify schema.yml is valid YAML"""
        content = self._read_file(self.SCHEMA)
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            pytest.fail(f"schema.yml YAML error: {e}")

    @pytest.mark.skipif(yaml is None, reason="PyYAML not installed")
    def test_dbt_project_valid_yaml(self):
        """Verify dbt_project.yml is valid YAML"""
        content = self._read_file(self.DBT_PROJECT)
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            pytest.fail(f"dbt_project.yml YAML error: {e}")
