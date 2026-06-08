"""
Tests for skill: dbt-transformation-patterns
Repo: dbt-labs/dbt-core
Image: zhangyiiiiii/swe-skills-bench-python
Task: Build a dbt project with staging, intermediate, and marts layers for an
      e-commerce data warehouse with incremental materialization.
"""

import os
import re

import pytest
import yaml

REPO_DIR = "/workspace/dbt-core"
PROJECT_DIR = os.path.join(REPO_DIR, "examples", "ecommerce_analytics")

PROJECT_YML = os.path.join(PROJECT_DIR, "dbt_project.yml")
STRIPE_SOURCES = os.path.join(PROJECT_DIR, "models", "staging", "stripe", "_stripe__sources.yml")
SHOPIFY_SOURCES = os.path.join(PROJECT_DIR, "models", "staging", "shopify", "_shopify__sources.yml")
STG_CUSTOMERS = os.path.join(PROJECT_DIR, "models", "staging", "stripe", "stg_stripe__customers.sql")
STG_PAYMENTS = os.path.join(PROJECT_DIR, "models", "staging", "stripe", "stg_stripe__payments.sql")
STG_ORDERS = os.path.join(PROJECT_DIR, "models", "staging", "shopify", "stg_shopify__orders.sql")
INT_PAYMENTS = os.path.join(PROJECT_DIR, "models", "intermediate", "int_payments_pivoted.sql")
DIM_CUSTOMERS = os.path.join(PROJECT_DIR, "models", "marts", "core", "dim_customers.sql")
FCT_ORDERS = os.path.join(PROJECT_DIR, "models", "marts", "core", "fct_orders.sql")
CORE_MODELS = os.path.join(PROJECT_DIR, "models", "marts", "core", "_core__models.yml")
MACRO_CENTS = os.path.join(PROJECT_DIR, "macros", "cents_to_dollars.sql")


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Layer 1 — file_path_check
# ---------------------------------------------------------------------------

class TestFilePathCheck:
    """Verify all required dbt project files exist."""

    def test_project_yml(self):
        assert os.path.isfile(PROJECT_YML), f"Missing {PROJECT_YML}"

    def test_stripe_sources(self):
        assert os.path.isfile(STRIPE_SOURCES), f"Missing {STRIPE_SOURCES}"

    def test_shopify_sources(self):
        assert os.path.isfile(SHOPIFY_SOURCES), f"Missing {SHOPIFY_SOURCES}"

    def test_stg_customers(self):
        assert os.path.isfile(STG_CUSTOMERS), f"Missing {STG_CUSTOMERS}"

    def test_stg_payments(self):
        assert os.path.isfile(STG_PAYMENTS), f"Missing {STG_PAYMENTS}"

    def test_stg_orders(self):
        assert os.path.isfile(STG_ORDERS), f"Missing {STG_ORDERS}"

    def test_int_payments(self):
        assert os.path.isfile(INT_PAYMENTS), f"Missing {INT_PAYMENTS}"

    def test_dim_customers(self):
        assert os.path.isfile(DIM_CUSTOMERS), f"Missing {DIM_CUSTOMERS}"

    def test_fct_orders(self):
        assert os.path.isfile(FCT_ORDERS), f"Missing {FCT_ORDERS}"

    def test_core_models(self):
        assert os.path.isfile(CORE_MODELS), f"Missing {CORE_MODELS}"

    def test_macro_cents(self):
        assert os.path.isfile(MACRO_CENTS), f"Missing {MACRO_CENTS}"


# ---------------------------------------------------------------------------
# Layer 2 — semantic_check
# ---------------------------------------------------------------------------

class TestSemanticProjectYml:
    """Verify dbt_project.yml structure."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.cfg = _load_yaml(PROJECT_YML)

    def test_project_name(self):
        assert self.cfg.get("name") == "ecommerce_analytics", (
            f"Expected name 'ecommerce_analytics'; got {self.cfg.get('name')}"
        )

    def test_version(self):
        assert self.cfg.get("version") == "1.0.0", (
            f"Expected version '1.0.0'; got {self.cfg.get('version')}"
        )

    def test_model_paths(self):
        paths = self.cfg.get("model-paths", self.cfg.get("source-paths", []))
        assert "models" in paths, f"Expected model-paths ['models']; got {paths}"

    def test_staging_materialization(self):
        models = self.cfg.get("models", {})
        raw = yaml.dump(models)
        assert "view" in raw, "Staging materialization should be 'view'"

    def test_intermediate_materialization(self):
        models = self.cfg.get("models", {})
        raw = yaml.dump(models)
        assert "ephemeral" in raw, "Intermediate materialization should be 'ephemeral'"

    def test_marts_materialization(self):
        models = self.cfg.get("models", {})
        raw = yaml.dump(models)
        assert "table" in raw, "Marts materialization should be 'table'"

    def test_vars_payment_methods(self):
        vars_section = self.cfg.get("vars", {})
        methods = vars_section.get("payment_methods", [])
        assert "credit_card" in methods, f"Expected credit_card in vars; got {methods}"
        assert "bank_transfer" in methods, f"Expected bank_transfer in vars; got {methods}"
        assert "gift_card" in methods, f"Expected gift_card in vars; got {methods}"


class TestSemanticStripeSources:
    """Verify Stripe source definitions."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.cfg = _load_yaml(STRIPE_SOURCES)
        self.raw = yaml.dump(self.cfg)

    def test_source_name(self):
        sources = self.cfg.get("sources", [])
        names = [s.get("name") for s in sources]
        assert "stripe" in names, f"Expected source 'stripe'; found {names}"

    def test_freshness_config(self):
        assert "freshness" in self.raw, "Stripe source should have freshness config"

    def test_loaded_at_field(self):
        assert "_fivetran_synced" in self.raw, (
            "Should use _fivetran_synced as loaded_at_field"
        )

    def test_customers_table(self):
        assert "customers" in self.raw, "Should define customers table"

    def test_payments_table(self):
        assert "payments" in self.raw, "Should define payments table"

    def test_unique_test(self):
        assert "unique" in self.raw, "Should have unique test on id columns"

    def test_not_null_test(self):
        assert "not_null" in self.raw, "Should have not_null test on id columns"

    def test_relationships_test(self):
        assert "relationships" in self.raw, (
            "payments.customer_id should have relationships test"
        )


class TestSemanticStagingSQL:
    """Verify staging SQL patterns."""

    def test_customers_source_ref(self):
        src = _read(STG_CUSTOMERS)
        assert "source('stripe', 'customers')" in src or "source('stripe','customers')" in src, (
            "stg_stripe__customers should reference source('stripe', 'customers')"
        )

    def test_customers_rename_id(self):
        src = _read(STG_CUSTOMERS)
        assert "customer_id" in src, "Should rename id → customer_id"

    def test_customers_deduplicate(self):
        src = _read(STG_CUSTOMERS).lower()
        assert "row_number" in src or "qualify" in src or "dedup" in src, (
            "Should deduplicate customers by customer_id"
        )

    def test_payments_cents_to_dollars(self):
        src = _read(STG_PAYMENTS)
        assert "cents_to_dollars" in src, (
            "stg_stripe__payments should use the cents_to_dollars macro"
        )

    def test_payments_status_mapping(self):
        src = _read(STG_PAYMENTS)
        assert "completed" in src and "failed" in src, (
            "Should map status values: success→completed, fail→failed"
        )

    def test_orders_filter_deleted(self):
        src = _read(STG_ORDERS)
        assert "deleted" in src, "stg_shopify__orders should filter out deleted orders"


class TestSemanticIntermediatePayments:
    """Verify intermediate payment pivot model."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.src = _read(INT_PAYMENTS)

    def test_jinja_for_loop(self):
        assert "{% for" in self.src or "{%- for" in self.src, (
            "Should use Jinja for-loop for pivot columns"
        )

    def test_payment_methods_var(self):
        assert "var('payment_methods')" in self.src, (
            "Should reference var('payment_methods')"
        )

    def test_group_by_order_id(self):
        assert "order_id" in self.src.lower() and "group by" in self.src.lower(), (
            "Should group by order_id"
        )


class TestSemanticMartsModels:
    """Verify marts dimension and fact models."""

    def test_dim_customers_join(self):
        src = _read(DIM_CUSTOMERS)
        assert "stg_stripe__customers" in src, (
            "dim_customers should reference stg_stripe__customers"
        )

    def test_dim_customers_metrics(self):
        src = _read(DIM_CUSTOMERS).lower()
        assert "total_orders" in src or "count" in src, (
            "dim_customers should compute total_orders"
        )
        assert "total_amount" in src or "sum" in src, (
            "dim_customers should compute total_amount_spent"
        )

    def test_fct_orders_incremental(self):
        src = _read(FCT_ORDERS)
        assert "incremental" in src, "fct_orders should use incremental materialization"

    def test_fct_orders_unique_key(self):
        src = _read(FCT_ORDERS)
        assert "unique_key" in src and "order_id" in src, (
            "fct_orders should set unique_key='order_id'"
        )

    def test_fct_orders_is_incremental(self):
        src = _read(FCT_ORDERS)
        assert "is_incremental()" in src, (
            "fct_orders should use is_incremental() filter"
        )

    def test_fct_orders_payment_join(self):
        src = _read(FCT_ORDERS)
        assert "int_payments_pivoted" in src, (
            "fct_orders should join with int_payments_pivoted"
        )


class TestSemanticCoreModelsYml:
    """Verify model documentation and tests."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.cfg = _load_yaml(CORE_MODELS)
        self.raw = yaml.dump(self.cfg)

    def test_dim_customers_documented(self):
        assert "dim_customers" in self.raw, "Should document dim_customers"

    def test_fct_orders_documented(self):
        assert "fct_orders" in self.raw, "Should document fct_orders"

    def test_unique_tests(self):
        assert "unique" in self.raw, "Should have unique tests"

    def test_not_null_tests(self):
        assert "not_null" in self.raw, "Should have not_null tests"


# ---------------------------------------------------------------------------
# Layer 3 — functional_check
# ---------------------------------------------------------------------------

class TestFunctionalMacro:
    """Verify cents_to_dollars macro."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.src = _read(MACRO_CENTS)

    def test_macro_definition(self):
        assert "{% macro cents_to_dollars" in self.src or "{%- macro cents_to_dollars" in self.src, (
            "Should define cents_to_dollars macro"
        )

    def test_division_by_100(self):
        assert "100" in self.src, "Macro should divide by 100"

    def test_round_function(self):
        assert "round" in self.src.lower(), "Macro should round to 2 decimals"


class TestFunctionalSQLSyntax:
    """Verify SQL files have basic syntax correctness."""

    SQL_FILES = [
        STG_CUSTOMERS, STG_PAYMENTS, STG_ORDERS,
        INT_PAYMENTS, DIM_CUSTOMERS, FCT_ORDERS,
    ]

    def test_all_have_select(self):
        for path in self.SQL_FILES:
            src = _read(path).lower()
            assert "select" in src, f"{path} should contain a SELECT statement"

    def test_all_have_from(self):
        for path in self.SQL_FILES:
            src = _read(path).lower()
            assert "from" in src, f"{path} should contain a FROM clause"

    def test_no_select_star_in_staging(self):
        for path in [STG_CUSTOMERS, STG_PAYMENTS, STG_ORDERS]:
            src = _read(path)
            # Allow select * in CTEs but final select should be explicit
            assert "select\n    *\nfrom" not in src.lower().replace(" ", ""), (
                f"{path} final select should not be SELECT * (best practice)"
            )


class TestFunctionalYAMLValidity:
    """Verify all YAML files parse correctly."""

    YAML_FILES = [
        PROJECT_YML, STRIPE_SOURCES, SHOPIFY_SOURCES, CORE_MODELS,
    ]

    def test_all_yaml_valid(self):
        for path in self.YAML_FILES:
            with open(path, "r", encoding="utf-8") as f:
                doc = yaml.safe_load(f)
            assert doc is not None, f"Failed to parse {path}"

    def test_all_yaml_have_content(self):
        for path in self.YAML_FILES:
            with open(path, "r", encoding="utf-8") as f:
                doc = yaml.safe_load(f)
            assert isinstance(doc, dict), f"{path} should be a YAML mapping"


class TestFunctionalIncrementalPattern:
    """Verify incremental materialization pattern in fct_orders."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.src = _read(FCT_ORDERS)

    def test_config_block(self):
        assert "config(" in self.src or "config (" in self.src, (
            "fct_orders should have a config block"
        )

    def test_this_reference(self):
        assert "{{ this }}" in self.src, (
            "Incremental filter should reference {{ this }}"
        )

    def test_max_ordered_at(self):
        assert "max(ordered_at)" in self.src.lower() or "max(ordered_at)" in self.src, (
            "Incremental filter should select max(ordered_at) from {{ this }}"
        )
