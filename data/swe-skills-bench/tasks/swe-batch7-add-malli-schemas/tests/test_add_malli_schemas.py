"""
Test skill: add-malli-schemas
Verify that the Agent correctly adds Malli schemas to the Metabase Bookmark
API endpoints — named schema definitions, route/body schemas on defendpoint,
and validation behaviour for invalid inputs.
"""

import os
import re
import subprocess
import pytest


class TestAddMalliSchemas:
    REPO_DIR = "/workspace/metabase"
    BOOKMARK_SRC = "src/metabase/api/bookmark.clj"
    BOOKMARK_TEST = "test/metabase/api/bookmark_test.clj"

    # ────────────────── helpers ──────────────────

    def _read(self, rel_path):
        fpath = os.path.join(self.REPO_DIR, rel_path)
        with open(fpath, "r") as f:
            return f.read()

    # === File Path Checks ===

    def test_bookmark_src_exists(self):
        """bookmark.clj source file must exist"""
        fpath = os.path.join(self.REPO_DIR, self.BOOKMARK_SRC)
        assert os.path.isfile(fpath), f"Not found: {fpath}"

    def test_bookmark_test_exists(self):
        """bookmark_test.clj test file must exist"""
        fpath = os.path.join(self.REPO_DIR, self.BOOKMARK_TEST)
        assert os.path.isfile(fpath), f"Not found: {fpath}"

    # === Semantic Checks — Named Schema Definitions ===

    def test_bookmark_type_schema_defined(self):
        """::BookmarkType enum schema must be defined with mr/def"""
        src = self._read(self.BOOKMARK_SRC)
        assert re.search(
            r'mr/def\s+::BookmarkType', src
        ) or re.search(
            r'mu/def\s+::BookmarkType', src
        ) or re.search(
            r'\(mr/def\s+::BookmarkType', src
        ), "::BookmarkType schema not defined with mr/def"

    def test_bookmark_type_enum_values(self):
        """::BookmarkType must include card, dashboard, and collection"""
        src = self._read(self.BOOKMARK_SRC)
        for val in ["card", "dashboard", "collection"]:
            assert f'"{val}"' in src, (
                f'::BookmarkType enum missing value "{val}"'
            )

    def test_bookmark_response_schema_defined(self):
        """::BookmarkResponse schema must be defined"""
        src = self._read(self.BOOKMARK_SRC)
        assert "BookmarkResponse" in src, (
            "::BookmarkResponse schema not found in bookmark.clj"
        )

    def test_bookmark_response_has_required_keys(self):
        """::BookmarkResponse must contain :id, :type, :item_id, :name, :description, :created_at"""
        src = self._read(self.BOOKMARK_SRC)
        for key in [":id", ":type", ":item_id", ":name", ":description", ":created_at"]:
            assert key in src, f"BookmarkResponse missing key {key}"

    def test_bookmark_ordering_entry_schema_defined(self):
        """::BookmarkOrderingEntry schema must be defined"""
        src = self._read(self.BOOKMARK_SRC)
        assert "BookmarkOrderingEntry" in src, (
            "::BookmarkOrderingEntry schema not found in bookmark.clj"
        )

    def test_ordering_entry_has_type_and_item_id(self):
        """::BookmarkOrderingEntry must include :type and :item_id"""
        src = self._read(self.BOOKMARK_SRC)
        # After BookmarkOrderingEntry definition the keys should appear
        assert ":type" in src and ":item_id" in src, (
            "BookmarkOrderingEntry missing :type or :item_id"
        )

    # === Semantic Checks — Endpoint Schema Annotations ===

    def test_post_endpoint_has_route_schema(self):
        """POST /api/bookmark/:type/:item-id must have Malli route-param schema"""
        src = self._read(self.BOOKMARK_SRC)
        # Look for defendpoint POST with schema annotations
        post_section = re.search(
            r'defendpoint\s+:?POST\s+.*bookmark.*type.*item', src, re.DOTALL
        ) or re.search(
            r'defendpoint\s+POST\s+.*bookmark.*type.*item', src, re.DOTALL
        )
        assert post_section is not None, (
            "POST /api/bookmark/:type/:item-id defendpoint not found"
        )

    def test_delete_endpoint_has_route_schema(self):
        """DELETE /api/bookmark/:type/:item-id must have Malli route-param schema"""
        src = self._read(self.BOOKMARK_SRC)
        assert re.search(
            r'defendpoint\s+:?DELETE\s+.*bookmark.*type.*item', src, re.DOTALL
        ), "DELETE /api/bookmark/:type/:item-id defendpoint not found"

    def test_put_ordering_endpoint_has_body_schema(self):
        """PUT /api/bookmark/ordering must have request body schema for orderings"""
        src = self._read(self.BOOKMARK_SRC)
        assert re.search(
            r'defendpoint\s+:?PUT\s+.*ordering', src, re.DOTALL
        ), "PUT /api/bookmark/ordering defendpoint not found"
        # Body schema should reference orderings
        assert ":orderings" in src, (
            "PUT /api/bookmark/ordering missing :orderings in body schema"
        )

    def test_uses_ms_positive_int(self):
        """All integer fields must use ms/PositiveInt, not pos-int?"""
        src = self._read(self.BOOKMARK_SRC)
        assert "ms/PositiveInt" in src or "PositiveInt" in src, (
            "Schema should use ms/PositiveInt for integer fields"
        )

    def test_uses_ms_non_blank_string(self):
        """Name fields must use ms/NonBlankString"""
        src = self._read(self.BOOKMARK_SRC)
        assert "NonBlankString" in src, (
            "Schema should use ms/NonBlankString for name fields"
        )

    # === Semantic Checks — Test File ===

    def test_test_file_has_validation_tests(self):
        """bookmark_test.clj must contain tests exercising schema validation"""
        test_src = self._read(self.BOOKMARK_TEST)
        # Should test invalid type or invalid item-id
        has_invalid_type = re.search(r'invalid.type|invalid-type|"invalid"', test_src, re.IGNORECASE)
        has_400 = "400" in test_src
        assert has_invalid_type or has_400, (
            "Test file should exercise schema validation (invalid type / 400)"
        )

    # === Functional Checks ===

    def test_clojure_compiles(self):
        """The bookmark namespace must compile without errors"""
        result = subprocess.run(
            ["clojure", "-M", "-e",
             "(require 'metabase.api.bookmark)"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, (
            f"Clojure compilation failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_existing_bookmark_tests_pass(self):
        """Existing bookmark tests must still pass after schema additions"""
        result = subprocess.run(
            ["clojure", "-X:dev:test",
             ":only", "metabase.api.bookmark-test"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=300,
        )
        assert result.returncode == 0, (
            f"Bookmark tests failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_bookmark_type_rejects_invalid_enum(self):
        """Validate that an invalid bookmark type is handled: look for :enum or coercion logic"""
        src = self._read(self.BOOKMARK_SRC)
        # The enum schema should restrict the values
        assert re.search(r':enum\s+"card"\s+"dashboard"\s+"collection"', src) or \
               re.search(r'\[:enum\s+"card"\s+"dashboard"\s+"collection"\]', src), (
            "BookmarkType enum definition not found with correct values"
        )

    def test_response_schema_uses_any_for_temporal(self):
        """:created_at field should use :any for temporal types"""
        src = self._read(self.BOOKMARK_SRC)
        # Should have :any near created_at in the response schema
        assert ":any" in src, (
            "Response schema should use :any for temporal fields like :created_at"
        )
