"""
Tests for the dbt-transformation-patterns skill.

Validates that a medallion architecture dbt project was implemented
with staging, intermediate, and marts layers, incremental models,
and schema tests.

Repo: dbt-core (https://github.com/dbt-labs/dbt-core)
"""

import os
import re

REPO_DIR = "/workspace/dbt-core"
BASE = os.path.join(REPO_DIR, "tests", "functional", "medallion")


class TestFilePathCheck:
    """Verify all required files were created."""

    def test_stg_orders_exists(self):
        path = os.path.join(BASE, "models", "staging", "stg_orders.sql")
        assert os.path.isfile(path), f"Expected stg_orders.sql"

    def test_stg_customers_exists(self):
        path = os.path.join(BASE, "models", "staging", "stg_customers.sql")
        assert os.path.isfile(path), f"Expected stg_customers.sql"

    def test_stg_payments_exists(self):
        path = os.path.join(BASE, "models", "staging", "stg_payments.sql")
        assert os.path.isfile(path), f"Expected stg_payments.sql"

    def test_staging_schema_exists(self):
        path = os.path.join(BASE, "models", "staging", "schema.yml")
        assert os.path.isfile(path), f"Expected staging schema.yml"

    def test_int_orders_exists(self):
        path = os.path.join(
            BASE, "models", "intermediate",
            "int_orders_with_payments.sql",
        )
        assert os.path.isfile(path), f"Expected int_orders_with_payments.sql"

    def test_fct_orders_exists(self):
        path = os.path.join(BASE, "models", "marts", "fct_orders.sql")
        assert os.path.isfile(path), f"Expected fct_orders.sql"

    def test_dim_customers_exists(self):
        path = os.path.join(BASE, "models", "marts", "dim_customers.sql")
        assert os.path.isfile(path), f"Expected dim_customers.sql"

    def test_marts_schema_exists(self):
        path = os.path.join(BASE, "models", "marts", "schema.yml")
        assert os.path.isfile(path), f"Expected marts schema.yml"

    def test_dbt_project_yml_exists(self):
        path = os.path.join(BASE, "dbt_project.yml")
        assert os.path.isfile(path), f"Expected dbt_project.yml"


class TestSemanticStagingLayer:
    """Verify staging models use sources, casting, and filtering."""

    def test_stg_orders_source_ref(self):
        path = os.path.join(BASE, "models", "staging", "stg_orders.sql")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"\{\{.*source\(.*'raw'.*'orders'\s*\)", content), (
            "Expected {{ source('raw', 'orders') }} in stg_orders"
        )

    def test_stg_orders_filters_deleted(self):
        path = os.path.join(BASE, "models", "staging", "stg_orders.sql")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"is_deleted.*false|where.*not.*deleted", content, re.IGNORECASE), (
            "Expected filtering of deleted records"
        )

    def test_stg_customers_dedup(self):
        path = os.path.join(BASE, "models", "staging", "stg_customers.sql")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"row_number\(\)", content, re.IGNORECASE), (
            "Expected row_number() for deduplication"
        )

    def test_stg_payments_case_statement(self):
        path = os.path.join(BASE, "models", "staging", "stg_payments.sql")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"case|CASE", content), (
            "Expected CASE statement for payment status pivoting"
        )

    def test_stg_payments_status_values(self):
        path = os.path.join(BASE, "models", "staging", "stg_payments.sql")
        with open(path, "r") as f:
            content = f.read()
        for status in ["pending", "completed", "failed", "refunded"]:
            assert status in content.lower(), (
                f"Expected status value '{status}'"
            )

    def test_staging_schema_sources(self):
        path = os.path.join(BASE, "models", "staging", "schema.yml")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"sources:", content), (
            "Expected sources: definition in staging schema"
        )

    def test_staging_freshness(self):
        path = os.path.join(BASE, "models", "staging", "schema.yml")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"freshness|warn_after|error_after", content), (
            "Expected freshness checks in sources"
        )

    def test_staging_unique_tests(self):
        path = os.path.join(BASE, "models", "staging", "schema.yml")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"unique", content), (
            "Expected unique test on primary keys"
        )

    def test_staging_not_null_tests(self):
        path = os.path.join(BASE, "models", "staging", "schema.yml")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"not_null", content), (
            "Expected not_null tests"
        )


class TestSemanticIntermediateLayer:
    """Verify intermediate model joins and aggregation."""

    def _read(self):
        path = os.path.join(
            BASE, "models", "intermediate",
            "int_orders_with_payments.sql",
        )
        with open(path, "r") as f:
            return f.read()

    def test_join_orders_payments(self):
        content = self._read()
        assert re.search(r"join|JOIN", content), (
            "Expected JOIN between orders and payments"
        )

    def test_total_paid(self):
        content = self._read()
        assert re.search(r"total_paid", content), (
            "Expected total_paid aggregation"
        )

    def test_total_refunded(self):
        content = self._read()
        assert re.search(r"total_refunded", content), (
            "Expected total_refunded aggregation"
        )

    def test_net_amount(self):
        content = self._read()
        assert re.search(r"net_amount", content), (
            "Expected net_amount calculation"
        )


class TestSemanticMartsLayer:
    """Verify fact and dimension tables."""

    def test_fct_orders_incremental(self):
        path = os.path.join(BASE, "models", "marts", "fct_orders.sql")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"is_incremental\(\)", content), (
            "Expected is_incremental() Jinja macro"
        )

    def test_fct_orders_unique_key(self):
        path = os.path.join(BASE, "models", "marts", "fct_orders.sql")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"unique_key.*order_id|unique_key", content), (
            "Expected unique_key = 'order_id' for merge"
        )

    def test_fct_orders_payment_status(self):
        path = os.path.join(BASE, "models", "marts", "fct_orders.sql")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"payment_status|paid|refunded|pending", content, re.IGNORECASE), (
            "Expected derived payment_status column"
        )

    def test_dim_customers_lifetime_value(self):
        path = os.path.join(BASE, "models", "marts", "dim_customers.sql")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"lifetime_value", content), (
            "Expected lifetime_value aggregation"
        )

    def test_dim_customers_first_order(self):
        path = os.path.join(BASE, "models", "marts", "dim_customers.sql")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"first_order_date|min\(", content, re.IGNORECASE), (
            "Expected first_order_date (min order date)"
        )

    def test_dim_customers_order_count(self):
        path = os.path.join(BASE, "models", "marts", "dim_customers.sql")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"number_of_orders|count\(", content, re.IGNORECASE), (
            "Expected number_of_orders count"
        )

    def test_marts_schema_tests(self):
        path = os.path.join(BASE, "models", "marts", "schema.yml")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"unique", content) and re.search(r"not_null", content), (
            "Expected unique and not_null tests in marts schema"
        )

    def test_marts_descriptions(self):
        path = os.path.join(BASE, "models", "marts", "schema.yml")
        with open(path, "r") as f:
            content = f.read()
        assert re.search(r"description:", content), (
            "Expected description fields in marts schema"
        )


class TestSemanticDbtProject:
    """Verify dbt_project.yml configuration."""

    def _read(self):
        path = os.path.join(BASE, "dbt_project.yml")
        with open(path, "r") as f:
            return f.read()

    def test_project_name(self):
        content = self._read()
        assert re.search(r"name.*medallion_demo|medallion", content), (
            "Expected project name: medallion_demo"
        )

    def test_staging_materialization(self):
        content = self._read()
        assert re.search(r"staging.*view|view", content), (
            "Expected staging materialization: view"
        )

    def test_marts_materialization(self):
        content = self._read()
        assert re.search(r"marts.*incremental|incremental", content), (
            "Expected marts materialization: incremental"
        )

    def test_vars(self):
        content = self._read()
        assert re.search(r"vars:|start_date", content), (
            "Expected vars with start_date"
        )


class TestFunctionalYamlValidity:
    """Validate YAML files are well-formed."""

    def test_dbt_project_valid_yaml(self):
        import yaml
        path = os.path.join(BASE, "dbt_project.yml")
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict), "dbt_project.yml should be valid YAML dict"

    def test_staging_schema_valid_yaml(self):
        import yaml
        path = os.path.join(BASE, "models", "staging", "schema.yml")
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict), "staging schema.yml should be valid YAML"

    def test_marts_schema_valid_yaml(self):
        import yaml
        path = os.path.join(BASE, "models", "marts", "schema.yml")
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict), "marts schema.yml should be valid YAML"
