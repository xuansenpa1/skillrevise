"""
Tests for the dbt-transformation-patterns skill.
Validates dbt models for e-commerce order analytics with staging,
intermediate, and marts layers plus tests and documentation.
"""

import os
import re

REPO_DIR = "/workspace/dbt-core"
MODELS_DIR = os.path.join(REPO_DIR, "models")
STAGING_DIR = os.path.join(MODELS_DIR, "staging", "ecommerce")
INTERMEDIATE_DIR = os.path.join(MODELS_DIR, "intermediate")
MARTS_DIR = os.path.join(MODELS_DIR, "marts")


class TestDbtTransformationPatterns:
    """Tests for the dbt e-commerce transformation models."""

    # ── file_path_check ──────────────────────────────────────────────

    def test_sources_yml_exists(self):
        """Source definitions YAML must exist."""
        path = os.path.join(STAGING_DIR, "_ecommerce__sources.yml")
        assert os.path.isfile(path), f"Missing {path}"

    def test_staging_orders_exists(self):
        """Staging orders model must exist."""
        path = os.path.join(STAGING_DIR, "stg_ecommerce__orders.sql")
        assert os.path.isfile(path), f"Missing {path}"

    def test_staging_order_items_exists(self):
        """Staging order items model must exist."""
        path = os.path.join(STAGING_DIR, "stg_ecommerce__order_items.sql")
        assert os.path.isfile(path), f"Missing {path}"

    def test_staging_customers_exists(self):
        """Staging customers model must exist."""
        path = os.path.join(STAGING_DIR, "stg_ecommerce__customers.sql")
        assert os.path.isfile(path), f"Missing {path}"

    def test_staging_products_exists(self):
        """Staging products model must exist."""
        path = os.path.join(STAGING_DIR, "stg_ecommerce__products.sql")
        assert os.path.isfile(path), f"Missing {path}"

    def test_intermediate_enriched_exists(self):
        """Intermediate enriched order items model must exist."""
        path = os.path.join(INTERMEDIATE_DIR, "int_order_items_enriched.sql")
        assert os.path.isfile(path), f"Missing {path}"

    def test_fct_orders_exists(self):
        """Fact orders mart model must exist."""
        path = os.path.join(MARTS_DIR, "fct_orders.sql")
        assert os.path.isfile(path), f"Missing {path}"

    def test_dim_customers_exists(self):
        """Customer dimension mart model must exist."""
        path = os.path.join(MARTS_DIR, "dim_customers.sql")
        assert os.path.isfile(path), f"Missing {path}"

    # ── semantic_check ───────────────────────────────────────────────

    def _read(self, path):
        if not os.path.isfile(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_status_mapping(self):
        """Staging orders must map status codes to labels."""
        content = self._read(os.path.join(STAGING_DIR, "stg_ecommerce__orders.sql"))
        for mapping in ["pending", "shipped", "delivered", "cancelled", "refunded"]:
            assert mapping in content.lower(), f"Status mapping '{mapping}' not found"

    def test_filter_test_orders(self):
        """Staging orders must filter out test orders."""
        content = self._read(os.path.join(STAGING_DIR, "stg_ecommerce__orders.sql"))
        assert re.search(r"is_test|test.*false|is_test\s*=\s*false", content, re.IGNORECASE), (
            "Test order filtering not found"
        )

    def test_line_total_computation(self):
        """Staging order items must compute line_total = quantity * unit_price."""
        content = self._read(os.path.join(STAGING_DIR, "stg_ecommerce__order_items.sql"))
        assert re.search(r"quantity\s*\*\s*unit_price|line_total", content, re.IGNORECASE), (
            "line_total computation not found"
        )

    def test_null_price_handling(self):
        """Staging products must replace null price with 0."""
        content = self._read(os.path.join(STAGING_DIR, "stg_ecommerce__products.sql"))
        assert re.search(r"coalesce|COALESCE|ifnull|IFNULL|0\.00|0", content), (
            "Null price handling not found"
        )

    def test_customer_segment(self):
        """dim_customers must classify segments: vip, regular, new."""
        content = self._read(os.path.join(MARTS_DIR, "dim_customers.sql"))
        for segment in ["vip", "regular", "new"]:
            assert segment in content.lower(), f"Segment '{segment}' not found"

    def test_discount_calculation(self):
        """fct_orders must compute discount_amount and net_revenue."""
        content = self._read(os.path.join(MARTS_DIR, "fct_orders.sql"))
        assert re.search(r"discount|net_revenue", content, re.IGNORECASE), (
            "Discount/net_revenue computation not found"
        )

    def test_excluded_cancelled_refunded(self):
        """Intermediate enriched model must exclude cancelled/refunded orders."""
        content = self._read(os.path.join(INTERMEDIATE_DIR, "int_order_items_enriched.sql"))
        assert re.search(r"cancelled|refunded|cancel|refund", content, re.IGNORECASE), (
            "Cancelled/refunded exclusion not found"
        )

    def test_marts_yml_exists(self):
        """Marts documentation YAML must exist."""
        path = os.path.join(MARTS_DIR, "_marts__models.yml")
        assert os.path.isfile(path), f"Missing {path}"

    def test_staging_yml_exists(self):
        """Staging models documentation YAML must exist."""
        path = os.path.join(STAGING_DIR, "_ecommerce__models.yml")
        assert os.path.isfile(path), f"Missing {path}"

    # ── functional_check ─────────────────────────────────────────────

    def test_sources_define_tables(self):
        """Sources must define raw_orders, raw_customers, raw_products, raw_order_items."""
        content = self._read(os.path.join(STAGING_DIR, "_ecommerce__sources.yml"))
        for table in ["raw_orders", "raw_customers", "raw_products", "raw_order_items"]:
            assert table in content, f"Source table '{table}' not defined"

    def test_freshness_check(self):
        """Sources must define freshness checks."""
        content = self._read(os.path.join(STAGING_DIR, "_ecommerce__sources.yml"))
        assert re.search(r"freshness|loaded_at", content, re.IGNORECASE), (
            "Freshness check not found in sources"
        )

    def test_unique_not_null_tests(self):
        """Model YAMLs must define unique and not_null tests."""
        staging_yml = self._read(os.path.join(STAGING_DIR, "_ecommerce__models.yml"))
        marts_yml = self._read(os.path.join(MARTS_DIR, "_marts__models.yml"))
        combined = staging_yml + marts_yml
        assert "unique" in combined, "unique test not found in model YAML"
        assert "not_null" in combined, "not_null test not found in model YAML"

    def test_relationships_test(self):
        """Marts YAML must define relationships test for fct_orders -> dim_customers."""
        content = self._read(os.path.join(MARTS_DIR, "_marts__models.yml"))
        assert re.search(r"relationships|customer_id", content, re.IGNORECASE), (
            "Relationships test not found"
        )

    def test_dim_products_exists(self):
        """Product dimension must exist."""
        path = os.path.join(MARTS_DIR, "dim_products.sql")
        assert os.path.isfile(path), f"Missing {path}"

    def test_int_customer_orders_exists(self):
        """Intermediate customer orders model must exist."""
        path = os.path.join(INTERMEDIATE_DIR, "int_customer_orders.sql")
        assert os.path.isfile(path), f"Missing {path}"
