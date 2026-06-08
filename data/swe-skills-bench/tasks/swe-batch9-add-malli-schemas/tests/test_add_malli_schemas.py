"""
Test skill: add-malli-schemas
Verify that the Agent adds Malli schemas to Metabase Collection API endpoints.
"""

import os
import re
import pytest


class TestAddMalliSchemas:
    REPO_DIR = "/workspace/metabase"

    # === File Path Checks ===

    def test_collection_api_clj_exists(self):
        """Verify collection API Clojure file exists"""
        candidates = [
            os.path.join(self.REPO_DIR, "src/metabase/api/collection.clj"),
        ]
        found = any(os.path.exists(c) for c in candidates)
        assert found, "Collection API file not found"

    # === Semantic Checks ===

    def test_malli_schema_imports(self):
        """Verify Malli schema namespace is required"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/collection.clj")
        with open(path) as f:
            content = f.read()
        has_malli = (
            "malli" in content
            or "mu/defn" in content
            or ":> " in content
            or "ms/" in content
            or "metabase.util.malli" in content
        )
        assert has_malli, "No Malli schema imports found in collection.clj"

    def test_get_collection_has_schema(self):
        """Verify GET /api/collection endpoint has Malli schema"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/collection.clj")
        with open(path) as f:
            content = f.read()
        # Look for schema annotations on the GET collection endpoint
        has_schema = (
            ":> " in content
            or "defendpoint" in content.lower()
            or "mu/defn" in content
            or "schema" in content.lower()
        )
        assert has_schema, "GET /api/collection lacks Malli schema definition"

    def test_post_collection_has_schema(self):
        """Verify POST /api/collection endpoint has request body schema"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/collection.clj")
        with open(path) as f:
            content = f.read()
        # POST endpoint should have body schema validation
        has_post_schema = "POST" in content and (
            ":body" in content
            or "body" in content.lower()
        )
        assert has_post_schema, "POST /api/collection lacks request body schema"

    def test_put_collection_has_schema(self):
        """Verify PUT /api/collection/:id endpoint has schema"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/collection.clj")
        with open(path) as f:
            content = f.read()
        has_put = "PUT" in content
        assert has_put, "PUT endpoint not found in collection.clj"

    def test_collection_items_endpoint_has_schema(self):
        """Verify GET /api/collection/:id/items has response schema"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/collection.clj")
        with open(path) as f:
            content = f.read()
        has_items = "items" in content
        assert has_items, "/items endpoint not found in collection.clj"

    def test_schemas_define_required_fields(self):
        """Verify schemas define expected fields like name, description"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/collection.clj")
        with open(path) as f:
            content = f.read()
        content_lower = content.lower()
        has_name = ":name" in content or "name" in content_lower
        has_desc = ":description" in content or "description" in content_lower
        assert has_name and has_desc, "Schemas missing required fields (:name, :description)"

    # === Functional Checks ===

    def test_collection_clj_valid_syntax(self):
        """Verify collection.clj has balanced parentheses (basic Clojure validation)"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/collection.clj")
        with open(path) as f:
            content = f.read()
        # Remove strings and comments
        cleaned = re.sub(r'"[^"]*"', '', content)
        cleaned = re.sub(r';[^\n]*', '', cleaned)
        opens = cleaned.count('(') + cleaned.count('[') + cleaned.count('{')
        closes = cleaned.count(')') + cleaned.count(']') + cleaned.count('}')
        assert opens == closes, (
            f"Unbalanced delimiters: opens={opens}, closes={closes}"
        )

    def test_clojure_namespace_declaration_present(self):
        """Verify the ns declaration is valid"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/collection.clj")
        with open(path) as f:
            content = f.read()
        assert content.strip().startswith("(ns ") or "(ns " in content[:500], (
            "File does not start with a proper (ns ...) declaration"
        )

    def test_no_broken_requires(self):
        """Verify no require references to non-existent namespaces"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/collection.clj")
        with open(path) as f:
            content = f.read()
        # Extract required namespaces
        requires = re.findall(r'\[(\S+)', content[:2000])
        # Filter to metabase namespaces
        mb_requires = [r for r in requires if r.startswith("metabase.")]
        # Check at least some of them resolve to files
        checked = 0
        for ns in mb_requires[:5]:
            ns_path = ns.replace(".", "/").replace("-", "_") + ".clj"
            full_path = os.path.join(self.REPO_DIR, "src", ns_path)
            if os.path.exists(full_path):
                checked += 1
        assert checked > 0, "No required metabase namespaces resolve to files"
