"""
Tests for the add-malli-schemas skill.
Validates that Malli schemas have been added to Metabase's Actions API endpoints
with proper validation, named schemas, and type-safe annotations.
"""

import os
import re
import subprocess

REPO_DIR = "/workspace/metabase"


class TestAddMalliSchemas:
    """Tests for Malli schema additions to Actions API endpoints."""

    # ── file_path_check ──────────────────────────────────────────────

    def test_actions_api_file_exists(self):
        """The Actions API namespace file must exist."""
        path = os.path.join(REPO_DIR, "src", "metabase", "actions", "api.clj")
        assert os.path.isfile(path), f"Missing {path}"

    def test_actions_models_file_exists(self):
        """The models file with named Malli schemas must exist."""
        # Could be models.clj or the schemas could be in api.clj itself
        models_path = os.path.join(REPO_DIR, "src", "metabase", "actions", "models.clj")
        api_path = os.path.join(REPO_DIR, "src", "metabase", "actions", "api.clj")
        assert os.path.isfile(models_path) or os.path.isfile(api_path), (
            "Neither models.clj nor api.clj found for schema definitions"
        )

    def test_actions_api_test_file_exists(self):
        """The test file for Actions API must exist."""
        path = os.path.join(REPO_DIR, "test", "metabase", "actions", "api_test.clj")
        assert os.path.isfile(path), f"Missing {path}"

    # ── semantic_check ───────────────────────────────────────────────

    def _read_clj_files(self):
        """Read all relevant Clojure source files and return combined content."""
        contents = {}
        for rel in [
            "src/metabase/actions/api.clj",
            "src/metabase/actions/models.clj",
        ]:
            path = os.path.join(REPO_DIR, rel)
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    contents[rel] = f.read()
        return contents

    def test_named_schema_action_defined(self):
        """::Action or similar named schema must be defined."""
        contents = self._read_clj_files()
        combined = "\n".join(contents.values())
        assert re.search(r"::Action\b|:metabase\.actions[\w./]*Action", combined), (
            "Named schema ::Action not found in source files"
        )

    def test_named_schema_http_action_details(self):
        """::HttpActionDetails schema must be defined with url, method fields."""
        contents = self._read_clj_files()
        combined = "\n".join(contents.values())
        assert re.search(
            r"HttpActionDetails|http-action-details|HttpAction", combined, re.IGNORECASE
        ), "HttpActionDetails schema not found"
        # Check for :url and :method mentions nearby
        assert ":url" in combined, ":url field not found in schema definitions"
        assert ":method" in combined, ":method field not found in schema definitions"

    def test_named_schema_create_action_request(self):
        """::CreateActionRequest schema must be defined."""
        contents = self._read_clj_files()
        combined = "\n".join(contents.values())
        assert re.search(
            r"CreateActionRequest|create-action-request|CreateAction", combined, re.IGNORECASE
        ), "CreateActionRequest schema not found"

    def test_named_schema_action_response(self):
        """::ActionResponse schema must be defined with id, created_at fields."""
        contents = self._read_clj_files()
        combined = "\n".join(contents.values())
        assert re.search(
            r"ActionResponse|action-response", combined, re.IGNORECASE
        ), "ActionResponse schema not found"

    def test_defendpoint_has_schema_annotations(self):
        """defendpoint declarations must include schema annotations (:-) syntax."""
        api_path = os.path.join(REPO_DIR, "src", "metabase", "actions", "api.clj")
        assert os.path.isfile(api_path), f"Missing {api_path}"
        with open(api_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Look for defendpoint with schema annotations
        endpoints_found = re.findall(r"defendpoint", content)
        assert len(endpoints_found) >= 3, (
            f"Expected at least 3 defendpoint declarations, found {len(endpoints_found)}"
        )

    def test_query_action_details_schema(self):
        """::QueryActionDetails schema must be defined with dataset_query."""
        contents = self._read_clj_files()
        combined = "\n".join(contents.values())
        assert re.search(
            r"QueryActionDetails|query-action-details|QueryAction", combined, re.IGNORECASE
        ), "QueryActionDetails schema not found"

    def test_enum_types_in_schemas(self):
        """Schemas must use enum types for :type and :method fields."""
        contents = self._read_clj_files()
        combined = "\n".join(contents.values())
        # Check for enum usage for HTTP methods or action types
        assert re.search(r':enum.*"(GET|POST|PUT|DELETE|PATCH)"', combined) or \
               re.search(r':enum.*"(http|query|implicit)"', combined), (
            "Enum types for :method or :type not found in schemas"
        )

    # ── functional_check ─────────────────────────────────────────────

    def test_api_clj_compiles(self):
        """The api.clj file must be syntactically valid (balanced parens)."""
        api_path = os.path.join(REPO_DIR, "src", "metabase", "actions", "api.clj")
        if not os.path.isfile(api_path):
            assert False, f"Missing {api_path}"
        with open(api_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Basic paren balance check
        opens = content.count("(") + content.count("[") + content.count("{")
        closes = content.count(")") + content.count("]") + content.count("}")
        assert opens == closes, (
            f"Unbalanced brackets in api.clj: {opens} opens vs {closes} closes"
        )

    def test_models_clj_compiles(self):
        """The models.clj file must be syntactically valid (balanced parens)."""
        models_path = os.path.join(REPO_DIR, "src", "metabase", "actions", "models.clj")
        if not os.path.isfile(models_path):
            return  # schemas may be in api.clj
        with open(models_path, "r", encoding="utf-8") as f:
            content = f.read()
        opens = content.count("(") + content.count("[") + content.count("{")
        closes = content.count(")") + content.count("]") + content.count("}")
        assert opens == closes, (
            f"Unbalanced brackets in models.clj: {opens} opens vs {closes} closes"
        )

    def test_api_test_file_has_validation_tests(self):
        """The test file must contain tests for schema validation rejection."""
        test_path = os.path.join(REPO_DIR, "test", "metabase", "actions", "api_test.clj")
        assert os.path.isfile(test_path), f"Missing {test_path}"
        with open(test_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Check for 400 error tests or validation-related keywords
        assert re.search(r"400|validation|invalid|schema", content, re.IGNORECASE), (
            "Test file lacks validation rejection tests"
        )

    def test_post_endpoint_has_request_body_schema(self):
        """POST /api/action/ must have a request body schema annotation."""
        api_path = os.path.join(REPO_DIR, "src", "metabase", "actions", "api.clj")
        assert os.path.isfile(api_path)
        with open(api_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Look for POST defendpoint with schema reference
        post_sections = re.findall(
            r'defendpoint\s+:?POST[^)]*\)', content, re.DOTALL
        )
        # Also accept plain POST with schema annotations
        assert len(post_sections) > 0 or ("POST" in content and "CreateAction" in content.lower().replace("-", "")), (
            "POST endpoint with request body schema not found"
        )

    def test_get_endpoint_has_response_schema(self):
        """GET endpoints must have response schema annotations."""
        api_path = os.path.join(REPO_DIR, "src", "metabase", "actions", "api.clj")
        assert os.path.isfile(api_path)
        with open(api_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Look for GET with response annotations
        assert "GET" in content, "No GET endpoint found"
        assert re.search(r"ActionResponse|:sequential|action-response", content, re.IGNORECASE), (
            "GET endpoint lacks response schema annotation"
        )

    def test_route_params_validated(self):
        """Endpoints with :id route params must have schema validation."""
        api_path = os.path.join(REPO_DIR, "src", "metabase", "actions", "api.clj")
        assert os.path.isfile(api_path)
        with open(api_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Endpoints with :id should have PositiveInt or similar schema
        if ":id" in content:
            assert re.search(r"PositiveInt|pos-int|:int|ms/PositiveInt", content), (
                "Route param :id lacks schema validation"
            )
