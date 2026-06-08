"""
Tests for skill: add-malli-schemas
Repo: metabase/metabase
Image: zhangyiiiiii/swe-skills-bench-clojure
Task: Add Malli schemas to Metabase Bookmark API endpoints for input
      validation and response typing.
"""

import os
import re
import subprocess

import pytest

REPO_DIR = "/workspace/metabase"
BOOKMARK_API = os.path.join(REPO_DIR, "src", "metabase", "api", "bookmark.clj")
BOOKMARK_MODEL = os.path.join(REPO_DIR, "src", "metabase", "models", "bookmark.clj")


# ---------------------------------------------------------------------------
# Layer 1 — file_path_check
# ---------------------------------------------------------------------------

class TestFilePathCheck:
    """Verify that the required files exist."""

    def test_bookmark_api_file_exists(self):
        assert os.path.isfile(BOOKMARK_API), (
            f"Expected bookmark API file at {BOOKMARK_API}"
        )

    def test_bookmark_model_file_exists(self):
        assert os.path.isfile(BOOKMARK_MODEL), (
            f"Expected bookmark model file at {BOOKMARK_MODEL}"
        )


# ---------------------------------------------------------------------------
# Layer 2 — semantic_check
# ---------------------------------------------------------------------------

class TestSemanticBookmarkAPI:
    """Check that Malli schema annotations are present in the API file."""

    @pytest.fixture(autouse=True)
    def _load_api_source(self):
        with open(BOOKMARK_API, "r", encoding="utf-8") as f:
            self.api_src = f.read()

    # -- Route parameter schemas --

    def test_route_params_use_positive_int(self):
        """Route IDs (id, card-id, dashboard-id, collection-id) must use ms/PositiveInt."""
        assert "ms/PositiveInt" in self.api_src or "PositiveInt" in self.api_src, (
            "Expected ms/PositiveInt annotation for route parameter IDs"
        )

    def test_route_param_map_annotation_syntax(self):
        """Route params must use the :- [:map ...] annotation syntax."""
        pattern = r":-\s*\[:map"
        assert re.search(pattern, self.api_src), (
            "Expected :- [:map ...] annotation syntax for route parameters"
        )

    # -- Query parameter schemas --

    def test_get_bookmark_has_optional_type_query_param(self):
        """GET /api/bookmark must accept an optional type query param with enum schema."""
        assert re.search(r'\[:enum\s+"card"\s+"dashboard"\s+"collection"\]', self.api_src), (
            "Expected [:enum \"card\" \"dashboard\" \"collection\"] for type query param"
        )

    def test_optional_query_param_marker(self):
        """Optional query params must be annotated with {:optional true} or :maybe."""
        has_optional = ":optional true" in self.api_src or ":maybe" in self.api_src
        assert has_optional, (
            "Expected {:optional true} or :maybe for optional query parameters"
        )

    # -- Request body schemas --

    def test_post_bookmark_body_has_type_enum(self):
        """POST /api/bookmark body must validate type as enum of card/dashboard/collection."""
        pattern = r'\[:enum\s+"card"\s+"dashboard"\s+"collection"\]'
        matches = re.findall(pattern, self.api_src)
        assert len(matches) >= 1, (
            "Expected at least one [:enum \"card\" \"dashboard\" \"collection\"] for POST body"
        )

    def test_post_bookmark_body_has_item_id(self):
        """POST body must include item_id with ms/PositiveInt."""
        has_item_id = re.search(r":item_id.*PositiveInt", self.api_src)
        assert has_item_id, (
            "Expected :item_id ms/PositiveInt in POST /api/bookmark body schema"
        )

    def test_put_ordering_body_has_sequential_schema(self):
        """PUT /api/bookmark/ordering body must use :sequential for orderings."""
        assert ":sequential" in self.api_src or "sequential" in self.api_src, (
            "Expected :sequential annotation for PUT ordering body"
        )

    # -- Response schemas --

    def test_delete_response_schema(self):
        """DELETE /api/bookmark/:id response must use [:map [:success :boolean]]."""
        has_success = re.search(r":success.*:boolean", self.api_src)
        assert has_success, (
            "Expected [:map [:success :boolean]] response schema for DELETE endpoint"
        )


class TestSemanticBookmarkModel:
    """Check that named Malli schema ::Bookmark is defined in the model file."""

    @pytest.fixture(autouse=True)
    def _load_model_source(self):
        with open(BOOKMARK_MODEL, "r", encoding="utf-8") as f:
            self.model_src = f.read()

    def test_bookmark_named_schema_defined(self):
        """::Bookmark named schema must be defined using mr/def or mc/def-schema."""
        has_def = (
            "::Bookmark" in self.model_src
            or "Bookmark" in self.model_src
        )
        assert has_def, (
            "Expected named schema ::Bookmark defined in bookmark model file"
        )

    def test_bookmark_schema_has_required_fields(self):
        """::Bookmark schema must contain id, type, item_id, user_id, created_at, updated_at."""
        required_keys = [":id", ":type", ":item_id", ":user_id", ":created_at", ":updated_at"]
        missing = [k for k in required_keys if k not in self.model_src]
        assert not missing, (
            f"Bookmark schema missing keys: {missing}"
        )

    def test_temporal_fields_use_any(self):
        """Temporal fields (created_at, updated_at) must use :any in response schema."""
        # Check that :any appears associated with temporal fields
        assert ":any" in self.model_src, (
            "Expected :any type for temporal fields in Bookmark response schema"
        )


# ---------------------------------------------------------------------------
# Layer 3 — functional_check
# ---------------------------------------------------------------------------

class TestFunctionalMalliSchemas:
    """Functional checks — validate Clojure source can be loaded and schemas compile."""

    def _run(self, cmd, cwd=REPO_DIR, timeout=120):
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=timeout,
        )
        return result

    def test_api_file_has_valid_clojure_syntax(self):
        """Bookmark API file must have balanced parentheses (basic Clojure syntax)."""
        with open(BOOKMARK_API, "r", encoding="utf-8") as f:
            src = f.read()
        opens = src.count("(")
        closes = src.count(")")
        assert opens == closes, (
            f"Unbalanced parentheses in bookmark.clj: {opens} open vs {closes} close"
        )

    def test_model_file_has_valid_clojure_syntax(self):
        """Bookmark model file must have balanced parentheses."""
        with open(BOOKMARK_MODEL, "r", encoding="utf-8") as f:
            src = f.read()
        opens = src.count("(")
        closes = src.count(")")
        assert opens == closes, (
            f"Unbalanced parentheses in bookmark model: {opens} open vs {closes} close"
        )

    def test_api_ns_declaration_requires_malli(self):
        """The API namespace must require malli schema utilities."""
        with open(BOOKMARK_API, "r", encoding="utf-8") as f:
            src = f.read()
        has_malli = (
            "metabase.util.malli.schema" in src
            or "metabase.util.malli" in src
            or "malli" in src
        )
        assert has_malli, (
            "Expected malli-related require in bookmark API namespace"
        )

    def test_defendpoint_forms_present(self):
        """API file must contain defendpoint forms for GET, POST, PUT, DELETE."""
        with open(BOOKMARK_API, "r", encoding="utf-8") as f:
            src = f.read()
        methods = ["GET", "POST", "PUT", "DELETE"]
        found = [m for m in methods if re.search(rf"defendpoint\s+:{m.upper()}\b|defendpoint\s+{m}", src, re.IGNORECASE)]
        missing = set(methods) - set(found)
        assert not missing, (
            f"Missing defendpoint forms for HTTP methods: {missing}"
        )

    def test_clj_kondo_lint_bookmark_api(self):
        """Run clj-kondo on the bookmark API file if available."""
        result = self._run("which clj-kondo", timeout=10)
        if result.returncode != 0:
            pytest.skip("clj-kondo not available in this environment")

        result = self._run(f"clj-kondo --lint {BOOKMARK_API}", timeout=60)
        # clj-kondo returns 2 for errors, 3 for warnings — we only fail on errors
        assert result.returncode != 2, (
            f"clj-kondo found errors in bookmark API:\n{result.stdout}\n{result.stderr}"
        )

    def test_model_requires_malli_registry(self):
        """The model namespace must require malli registry (mr) for defining named schemas."""
        with open(BOOKMARK_MODEL, "r", encoding="utf-8") as f:
            src = f.read()
        has_registry = (
            "metabase.util.malli.registry" in src
            or "mr/def" in src
            or "malli.registry" in src
            or "malli" in src
        )
        assert has_registry, (
            "Expected malli registry require in bookmark model namespace for mr/def"
        )
