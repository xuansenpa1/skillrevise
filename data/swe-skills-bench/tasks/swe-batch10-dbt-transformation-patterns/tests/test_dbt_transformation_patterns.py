"""
Test skill: dbt-transformation-patterns
Verify that the Agent correctly implements a Three-Layer dbt
Transformation Pipeline for E-commerce Order Analytics in dbt-core.
"""

import os
import re
import pytest


class TestDbtTransformationPatterns:
    REPO_DIR = "/workspace/dbt-core"

    FIXTURE_BASE = "tests/functional/fixtures/ecommerce_project"

    # === File Path Checks ===

    def test_dbt_project_yml_exists(self):
        """Verify dbt_project.yml was created"""
        path = os.path.join(self.REPO_DIR, self.FIXTURE_BASE, "dbt_project.yml")
        assert os.path.exists(path), "dbt_project.yml not found"

    def test_sources_yml_exists(self):
        """Verify _ecommerce__sources.yml was created"""
        path = os.path.join(
            self.REPO_DIR, self.FIXTURE_BASE,
            "models/staging/ecommerce/_ecommerce__sources.yml",
        )
        assert os.path.exists(path), "_ecommerce__sources.yml not found"

    def test_stg_orders_exists(self):
        """Verify stg_ecommerce__orders.sql was created"""
        path = os.path.join(
            self.REPO_DIR, self.FIXTURE_BASE,
            "models/staging/ecommerce/stg_ecommerce__orders.sql",
        )
        assert os.path.exists(path), "stg_ecommerce__orders.sql not found"

    def test_stg_customers_exists(self):
        """Verify stg_ecommerce__customers.sql was created"""
        path = os.path.join(
            self.REPO_DIR, self.FIXTURE_BASE,
            "models/staging/ecommerce/stg_ecommerce__customers.sql",
        )
        assert os.path.exists(path), "stg_ecommerce__customers.sql not found"

    def test_int_orders_with_customers_exists(self):
        """Verify int_orders_with_customers.sql was created"""
        path = os.path.join(
            self.REPO_DIR, self.FIXTURE_BASE,
            "models/intermediate/int_orders_with_customers.sql",
        )
        assert os.path.exists(path), "int_orders_with_customers.sql not found"

    def test_fct_orders_exists(self):
        """Verify fct_orders.sql was created"""
        path = os.path.join(
            self.REPO_DIR, self.FIXTURE_BASE,
            "models/marts/fct_orders.sql",
        )
        assert os.path.exists(path), "fct_orders.sql not found"

    def test_core_models_yml_exists(self):
        """Verify _core__models.yml was created"""
        path = os.path.join(
            self.REPO_DIR, self.FIXTURE_BASE,
            "models/marts/_core__models.yml",
        )
        assert os.path.exists(path), "_core__models.yml not found"

    def test_singular_test_exists(self):
        """Verify assert_no_negative_totals.sql was created"""
        path = os.path.join(
            self.REPO_DIR, self.FIXTURE_BASE,
            "tests/assert_no_negative_totals.sql",
        )
        assert os.path.exists(path), "assert_no_negative_totals.sql not found"

    # === Semantic Checks: Staging Models ===

    def _load_stg_orders(self):
        path = os.path.join(
            self.REPO_DIR, self.FIXTURE_BASE,
            "models/staging/ecommerce/stg_ecommerce__orders.sql",
        )
        return open(path).read()

    def test_stg_orders_uses_source_macro(self):
        """Verify staging orders uses {{ source('ecommerce', 'raw_orders') }}"""
        source = self._load_stg_orders()
        assert "source(" in source and "ecommerce" in source and "raw_orders" in source, (
            "stg_ecommerce__orders does not use {{ source() }} macro"
        )

    def test_stg_orders_snake_case_aliases(self):
        """Verify staging orders converts camelCase to snake_case"""
        source = self._load_stg_orders()
        snake_cols = ["order_id", "customer_id", "order_date", "order_status", "total_amount"]
        found = sum(1 for col in snake_cols if col in source.lower())
        assert found >= 3, (
            f"Expected at least 3 snake_case aliases, found {found}"
        )

    def test_stg_orders_filters_test_status(self):
        """Verify staging orders excludes test status rows"""
        source = self._load_stg_orders().lower()
        has_filter = (
            "'test'" in source
            or "\"test\"" in source
        ) and "where" in source
        assert has_filter, "stg_orders does not filter out test status rows"

    def test_stg_orders_casts_order_date(self):
        """Verify staging orders casts order_date to date"""
        source = self._load_stg_orders().lower()
        has_cast = (
            "cast(" in source and "date" in source
        ) or "::date" in source
        assert has_cast, "stg_orders does not cast order_date to date"

    # === Semantic Checks: Intermediate Model ===

    def _load_int_orders_with_customers(self):
        path = os.path.join(
            self.REPO_DIR, self.FIXTURE_BASE,
            "models/intermediate/int_orders_with_customers.sql",
        )
        return open(path).read()

    def test_int_model_uses_ref_macro(self):
        """Verify intermediate model uses {{ ref() }} for staging models"""
        source = self._load_int_orders_with_customers()
        assert "ref(" in source and "stg_ecommerce__orders" in source, (
            "Intermediate model does not ref staging orders"
        )
        assert "stg_ecommerce__customers" in source, (
            "Intermediate model does not ref staging customers"
        )

    def test_int_model_left_join(self):
        """Verify intermediate model uses LEFT JOIN"""
        source = self._load_int_orders_with_customers().lower()
        assert "left join" in source, "Intermediate model does not use LEFT JOIN"

    def test_int_model_is_returning_customer(self):
        """Verify is_returning_customer boolean is computed"""
        source = self._load_int_orders_with_customers().lower()
        assert "is_returning_customer" in source, (
            "is_returning_customer column not found"
        )

    # === Semantic Checks: Incremental Mart ===

    def _load_fct_orders(self):
        path = os.path.join(
            self.REPO_DIR, self.FIXTURE_BASE,
            "models/marts/fct_orders.sql",
        )
        return open(path).read()

    def test_fct_orders_incremental_config(self):
        """Verify fct_orders uses incremental materialization config"""
        source = self._load_fct_orders()
        assert "materialized='incremental'" in source or 'materialized="incremental"' in source, (
            "fct_orders missing incremental materialization config"
        )

    def test_fct_orders_unique_key(self):
        """Verify fct_orders has unique_key configuration"""
        source = self._load_fct_orders()
        assert "unique_key" in source, "fct_orders missing unique_key"

    def test_fct_orders_is_incremental_guard(self):
        """Verify fct_orders uses is_incremental() guard"""
        source = self._load_fct_orders()
        assert "is_incremental()" in source, (
            "fct_orders missing is_incremental() guard"
        )

    # === Semantic Checks: Schema tests ===

    def _load_core_models_yml(self):
        path = os.path.join(
            self.REPO_DIR, self.FIXTURE_BASE,
            "models/marts/_core__models.yml",
        )
        return open(path).read()

    def test_core_models_not_null_customer_id(self):
        """Verify not_null test on customer_id in _core__models.yml"""
        content = self._load_core_models_yml()
        assert "not_null" in content and "customer_id" in content, (
            "Missing not_null test on customer_id"
        )

    def test_core_models_not_null_order_month(self):
        """Verify not_null test on order_month in _core__models.yml"""
        content = self._load_core_models_yml()
        assert "not_null" in content and "order_month" in content, (
            "Missing not_null test on order_month"
        )

    def test_core_models_accepted_values_order_status(self):
        """Verify accepted_values test on order_status"""
        content = self._load_core_models_yml()
        assert "accepted_values" in content and "order_status" in content, (
            "Missing accepted_values test on order_status"
        )

    # === Functional Checks ===

    def test_fct_orders_aggregations(self):
        """Verify fct_orders has order_count and order_total aggregations"""
        source = self._load_fct_orders().lower()
        has_count = "count(" in source or "order_count" in source
        has_total = "sum(" in source or "order_total" in source
        assert has_count and has_total, (
            "fct_orders missing count/sum aggregations"
        )

    def test_singular_test_selects_negatives(self):
        """Verify singular test selects rows with negative order_total"""
        path = os.path.join(
            self.REPO_DIR, self.FIXTURE_BASE,
            "tests/assert_no_negative_totals.sql",
        )
        content = open(path).read().lower()
        has_check = "< 0" in content or "negative" in content
        assert "select" in content and has_check, (
            "Singular test does not select negative total rows"
        )

    def test_sources_yml_freshness(self):
        """Verify sources YAML has freshness thresholds"""
        path = os.path.join(
            self.REPO_DIR, self.FIXTURE_BASE,
            "models/staging/ecommerce/_ecommerce__sources.yml",
        )
        content = open(path).read()
        assert "freshness" in content, "Sources YAML missing freshness config"

    def test_sources_yml_defines_raw_tables(self):
        """Verify sources YAML defines raw_orders, raw_customers, raw_products"""
        path = os.path.join(
            self.REPO_DIR, self.FIXTURE_BASE,
            "models/staging/ecommerce/_ecommerce__sources.yml",
        )
        content = open(path).read()
        for table in ["raw_orders", "raw_customers", "raw_products"]:
            assert table in content, f"Source table '{table}' not defined"

    def test_dbt_project_materialization_settings(self):
        """Verify dbt_project.yml sets correct materializations"""
        path = os.path.join(self.REPO_DIR, self.FIXTURE_BASE, "dbt_project.yml")
        content = open(path).read().lower()
        assert "view" in content, "dbt_project.yml missing 'view' materialization"
        assert "ephemeral" in content, "dbt_project.yml missing 'ephemeral' materialization"
        assert "table" in content, "dbt_project.yml missing 'table' materialization"

    def test_stg_customers_lowercases_email(self):
        """Verify stg_ecommerce__customers lowercases email"""
        path = os.path.join(
            self.REPO_DIR, self.FIXTURE_BASE,
            "models/staging/ecommerce/stg_ecommerce__customers.sql",
        )
        content = open(path).read().lower()
        has_lower = "lower(" in content and "email" in content
        assert has_lower, "stg_customers does not lowercase email"
