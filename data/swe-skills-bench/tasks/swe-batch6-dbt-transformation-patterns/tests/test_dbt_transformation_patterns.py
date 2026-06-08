"""
Tests for dbt-transformation-patterns skill.
Verifies creation of a dbt analytics pipeline with staging, intermediate, and mart
models following the medallion architecture, plus macros, snapshots, seeds, and tests.
"""

import csv
import io
import os
import re

import pytest
import yaml


class TestDbtTransformationPatterns:
    """Tests for dbt-transformation-patterns skill."""

    REPO_DIR = "/workspace/dbt-core"

    # ------------------------------------------------------------------ #
    #  file_path_check – verify expected files exist
    # ------------------------------------------------------------------ #

    def test_dbt_project_yml_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "dbt_project.yml"))

    def test_stripe_sources_yml_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "staging", "stripe", "_stripe__sources.yml"))

    def test_stg_stripe_payments_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "staging", "stripe", "stg_stripe__payments.sql"))

    def test_stg_stripe_customers_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "staging", "stripe", "stg_stripe__customers.sql"))

    def test_shopify_sources_yml_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "staging", "shopify", "_shopify__sources.yml"))

    def test_stg_shopify_orders_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "staging", "shopify", "stg_shopify__orders.sql"))

    def test_stg_shopify_order_items_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "staging", "shopify", "stg_shopify__order_items.sql"))

    def test_app_sources_yml_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "staging", "app", "_app__sources.yml"))

    def test_stg_app_users_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "staging", "app", "stg_app__users.sql"))

    def test_stg_app_products_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "staging", "app", "stg_app__products.sql"))

    def test_int_orders_enriched_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "intermediate", "int_orders_enriched.sql"))

    def test_int_order_items_with_products_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "intermediate", "int_order_items_with_products.sql"))

    def test_int_customer_orders_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "intermediate", "int_customer_orders.sql"))

    def test_dim_customers_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "marts", "core", "dim_customers.sql"))

    def test_dim_products_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "marts", "core", "dim_products.sql"))

    def test_fct_orders_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "marts", "core", "fct_orders.sql"))

    def test_fct_revenue_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "marts", "finance", "fct_revenue.sql"))

    def test_core_models_yml_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "marts", "core", "_core__models.yml"))

    def test_finance_models_yml_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "models", "marts", "finance", "_finance__models.yml"))

    def test_snap_products_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "snapshots", "snap_products.sql"))

    def test_cents_to_dollars_macro_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "macros", "cents_to_dollars.sql"))

    def test_generate_surrogate_key_macro_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "macros", "generate_surrogate_key.sql"))

    def test_assert_positive_revenue_test_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "tests", "assert_positive_revenue.sql"))

    def test_country_codes_seed_exists(self):
        assert os.path.isfile(os.path.join(self.REPO_DIR, "seeds", "country_codes.csv"))

    # ------------------------------------------------------------------ #
    #  semantic_check – structural / content validation
    # ------------------------------------------------------------------ #

    def _read(self, relpath):
        path = os.path.join(self.REPO_DIR, relpath)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_dbt_project_yml_structure(self):
        """dbt_project.yml has correct project name and model configs."""
        data = yaml.safe_load(self._read("dbt_project.yml"))
        assert data.get("name") == "ecommerce_analytics"
        models_cfg = data.get("models", {}).get("ecommerce_analytics", {})
        staging_cfg = models_cfg.get("staging", {})
        assert staging_cfg.get("+materialized") == "view"

    def test_staging_models_use_cte_pattern(self):
        """Staging SQL models follow the CTE pattern (with source as ...)."""
        for relpath in [
            "models/staging/stripe/stg_stripe__payments.sql",
            "models/staging/shopify/stg_shopify__orders.sql",
            "models/staging/app/stg_app__users.sql",
        ]:
            content = self._read(relpath).lower()
            assert "with" in content and "source" in content, \
                f"{relpath} should use CTE pattern"
            assert "{{ source(" in self._read(relpath) or "{{source(" in self._read(relpath), \
                f"{relpath} should reference a dbt source"

    def test_stripe_sources_freshness(self):
        """Stripe source YAML defines freshness checks."""
        data = yaml.safe_load(self._read("models/staging/stripe/_stripe__sources.yml"))
        sources = data.get("sources", [])
        assert len(sources) >= 1
        src = sources[0]
        freshness = src.get("freshness") or {}
        # Could be on source level or table level
        text = self._read("models/staging/stripe/_stripe__sources.yml").lower()
        assert "freshness" in text, "Stripe source should define freshness"

    def test_fct_orders_incremental(self):
        """fct_orders.sql is configured as incremental."""
        content = self._read("models/marts/core/fct_orders.sql")
        assert "incremental" in content.lower(), "fct_orders should be incremental"
        assert "is_incremental()" in content, "fct_orders should use is_incremental() macro"

    def test_fct_revenue_incremental(self):
        """fct_revenue.sql is configured as incremental with daily aggregation."""
        content = self._read("models/marts/finance/fct_revenue.sql")
        assert "incremental" in content.lower()
        assert "date_trunc" in content.lower() or "trunc" in content.lower(), \
            "fct_revenue should aggregate by date"

    def test_dim_customers_customer_segment(self):
        """dim_customers.sql includes customer segment logic."""
        content = self._read("models/marts/core/dim_customers.sql")
        assert "customer_segment" in content.lower() or "segment" in content.lower()
        assert "VIP" in content or "vip" in content.lower()
        assert "Regular" in content or "regular" in content.lower()

    def test_country_codes_csv_valid(self):
        """country_codes.csv is a valid CSV with expected columns."""
        content = self._read("seeds/country_codes.csv")
        reader = csv.reader(io.StringIO(content))
        headers = [h.lower().strip() for h in next(reader)]
        assert any("code" in h for h in headers), "CSV should have a code column"
        assert any("country" in h or "name" in h for h in headers), "CSV should have a country/name column"
        rows = list(reader)
        assert len(rows) >= 5, "CSV should have at least 5 country rows"

    # ------------------------------------------------------------------ #
    #  functional_check – deeper content validation
    # ------------------------------------------------------------------ #

    def test_cents_to_dollars_macro_logic(self):
        """cents_to_dollars macro divides by 100."""
        content = self._read("macros/cents_to_dollars.sql")
        assert "100" in content, "cents_to_dollars should divide by 100"
        assert re.search(r"macro\s+cents_to_dollars", content, re.IGNORECASE), \
            "Should define a macro named cents_to_dollars"

    def test_generate_surrogate_key_macro_uses_hash(self):
        """generate_surrogate_key macro uses MD5 or hashing."""
        content = self._read("macros/generate_surrogate_key.sql").lower()
        assert "md5" in content or "hash" in content or "sha" in content, \
            "Surrogate key macro should use a hash function"

    def test_snap_products_scd_type2(self):
        """snap_products.sql implements SCD Type 2 snapshotting."""
        content = self._read("snapshots/snap_products.sql").lower()
        assert "snapshot" in content
        assert "strategy" in content, "Snapshot should define a strategy"
        assert "updated_at" in content or "timestamp" in content, \
            "Snapshot should reference a timestamp column"

    def test_assert_positive_revenue_test(self):
        """assert_positive_revenue.sql checks for no negative revenue."""
        content = self._read("tests/assert_positive_revenue.sql").lower()
        assert "fct_revenue" in content or "revenue" in content
        assert "<" in content or "negative" in content or "<= 0" in content or "< 0" in content, \
            "Test should check for negative or zero revenue"

    def test_core_models_yml_has_tests(self):
        """_core__models.yml defines tests for dim_customers."""
        data = yaml.safe_load(self._read("models/marts/core/_core__models.yml"))
        models = data.get("models", [])
        model_names = [m.get("name", "") for m in models]
        assert "dim_customers" in model_names, "Should document dim_customers model"
        dim_cust = [m for m in models if m.get("name") == "dim_customers"][0]
        columns = dim_cust.get("columns", [])
        col_names = [c.get("name", "") for c in columns]
        assert "customer_key" in col_names or "email" in col_names, \
            "dim_customers should test key columns"

    def test_intermediate_models_are_ephemeral_or_referenced(self):
        """Intermediate models should be ephemeral or at least reference staging models."""
        for relpath in [
            "models/intermediate/int_orders_enriched.sql",
            "models/intermediate/int_order_items_with_products.sql",
            "models/intermediate/int_customer_orders.sql",
        ]:
            content = self._read(relpath)
            assert "ref(" in content, f"{relpath} should use ref() to reference other models"

    def test_stg_stripe_payments_filters_failed(self):
        """stg_stripe__payments.sql filters out failed payments."""
        content = self._read("models/staging/stripe/stg_stripe__payments.sql").lower()
        assert "failed" in content, "Should filter out payments with status 'failed'"

    def test_stg_shopify_orders_filters_voided(self):
        """stg_shopify__orders.sql filters out voided orders."""
        content = self._read("models/staging/shopify/stg_shopify__orders.sql").lower()
        assert "voided" in content, "Should filter out voided orders"
