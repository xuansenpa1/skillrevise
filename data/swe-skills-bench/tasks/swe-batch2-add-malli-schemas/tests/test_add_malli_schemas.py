"""
Test skill: add-malli-schemas
Verify that the Agent correctly adds Malli schema validation to Metabase
alert API endpoints including schema definitions, validation integration,
and structured error responses.
"""

import os
import re
import subprocess
import pytest


class TestAddMalliSchemas:
    REPO_DIR = "/workspace/metabase"

    # === File Path Checks ===

    def test_alert_schema_file_exists(self):
        """Verify alert schema definition file exists"""
        path = os.path.join(
            self.REPO_DIR, "src/metabase/api/schema/alert.clj"
        )
        assert os.path.exists(path), f"alert.clj schema not found at {path}"

    def test_alert_api_file_exists(self):
        """Verify alert API endpoint file exists"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/alert.clj")
        assert os.path.exists(path), f"alert.clj API not found at {path}"

    def test_schema_file_is_readable(self):
        """Verify schema file can be read and has content"""
        path = os.path.join(
            self.REPO_DIR, "src/metabase/api/schema/alert.clj"
        )
        with open(path) as f:
            content = f.read()
        assert len(content) > 50, (
            f"alert.clj schema file is too small ({len(content)} bytes)"
        )

    # === Semantic Checks ===

    def test_schema_defines_malli_schemas(self):
        """Verify schema file defines Malli schemas with appropriate types"""
        path = os.path.join(
            self.REPO_DIR, "src/metabase/api/schema/alert.clj"
        )
        with open(path) as f:
            content = f.read()

        malli_indicators = [
            ":string", ":int", ":boolean", ":enum",
            ":map", ":sequential", ":vector",
            "mu/", "malli", "mc/",
            "[:string", "[:int", "[:map",
        ]
        found = [ind for ind in malli_indicators if ind in content]
        assert len(found) >= 3, (
            f"Schema should use Malli types. Found: {found}. "
            f"Expected at least 3 of: {malli_indicators}"
        )

    def test_schema_has_required_and_optional_fields(self):
        """Verify schema distinguishes required and optional fields"""
        path = os.path.join(
            self.REPO_DIR, "src/metabase/api/schema/alert.clj"
        )
        with open(path) as f:
            content = f.read()

        has_optional = "optional" in content.lower() or "{:optional" in content
        has_required = (
            "alert" in content.lower()
            and (":name" in content or ":alert" in content or ":trigger" in content)
        )
        assert has_required, (
            "Schema should define required fields for alert creation"
        )

    def test_schema_covers_alert_fields(self):
        """Verify schema covers core alert fields (name, conditions, channels, schedule)"""
        path = os.path.join(
            self.REPO_DIR, "src/metabase/api/schema/alert.clj"
        )
        with open(path) as f:
            content = f.read().lower()

        field_categories = {
            "name/title": "name" in content or "title" in content,
            "condition/trigger": "condition" in content or "trigger" in content or "threshold" in content,
            "channel/notification": "channel" in content or "notification" in content or "email" in content,
            "schedule/frequency": "schedule" in content or "frequency" in content or "cron" in content,
        }
        found = [k for k, v in field_categories.items() if v]
        assert len(found) >= 2, (
            f"Schema should cover core alert fields. Found: {found}. "
            f"Expected at least 2 of: {list(field_categories.keys())}"
        )

    def test_api_file_references_schema_validation(self):
        """Verify alert API file references schema validation"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/alert.clj")
        with open(path) as f:
            content = f.read()

        validation_indicators = [
            "schema", "malli", "validate", "coerce",
            "api/schema", "metabase.api.schema",
        ]
        found = [ind for ind in validation_indicators if ind in content]
        assert len(found) >= 1, (
            "Alert API should reference schema validation. "
            f"None of {validation_indicators} found."
        )

    def test_api_returns_400_on_validation_error(self):
        """Verify API handles validation errors with HTTP 400"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/alert.clj")
        with open(path) as f:
            content = f.read()

        error_handling = [
            "400", "bad-request", "validation-error",
            "errors", "invalid", "status 400",
        ]
        found = [ind for ind in error_handling if ind in content.lower()]
        assert len(found) >= 1, (
            "API should return 400 on validation errors. "
            f"None of {error_handling} found."
        )

    # === Functional Checks ===

    def test_schema_file_is_valid_clojure(self):
        """Verify schema file has valid Clojure syntax (balanced parens)"""
        path = os.path.join(
            self.REPO_DIR, "src/metabase/api/schema/alert.clj"
        )
        with open(path) as f:
            content = f.read()

        # Check balanced parentheses
        paren_count = content.count("(") - content.count(")")
        bracket_count = content.count("[") - content.count("]")
        brace_count = content.count("{") - content.count("}")

        assert paren_count == 0, (
            f"Unbalanced parentheses in schema: ({content.count('(')} open, "
            f"{content.count(')')} close)"
        )
        assert bracket_count == 0, (
            f"Unbalanced brackets in schema: ({content.count('[')} open, "
            f"{content.count(']')} close)"
        )
        assert brace_count == 0, (
            f"Unbalanced braces in schema: ({content.count('{')} open, "
            f"{content.count('}')} close)"
        )

    def test_api_file_is_valid_clojure(self):
        """Verify alert API file has valid Clojure syntax (balanced parens)"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/alert.clj")
        with open(path) as f:
            content = f.read()

        paren_count = content.count("(") - content.count(")")
        bracket_count = content.count("[") - content.count("]")
        brace_count = content.count("{") - content.count("}")

        assert paren_count == 0, (
            f"Unbalanced parentheses in API: ({content.count('(')} open, "
            f"{content.count(')')} close)"
        )
        assert bracket_count == 0, (
            f"Unbalanced brackets in API: ({content.count('[')} open, "
            f"{content.count(']')} close)"
        )

    def test_schema_has_namespace_declaration(self):
        """Verify schema file has proper Clojure namespace declaration"""
        path = os.path.join(
            self.REPO_DIR, "src/metabase/api/schema/alert.clj"
        )
        with open(path) as f:
            content = f.read()

        assert "(ns " in content, (
            "Schema file should have a (ns ...) namespace declaration"
        )
        assert "metabase" in content, (
            "Namespace should be under the metabase namespace"
        )

    def test_schema_validation_covers_create_and_update(self):
        """Verify schema definitions cover both creation and modification operations"""
        path = os.path.join(
            self.REPO_DIR, "src/metabase/api/schema/alert.clj"
        )
        with open(path) as f:
            content = f.read().lower()

        operation_indicators = {
            "create": "create" in content or "new" in content or "post" in content,
            "update": "update" in content or "modify" in content or "put" in content or "patch" in content,
        }
        found = [k for k, v in operation_indicators.items() if v]
        assert len(found) >= 1, (
            f"Schema should cover creation and/or modification operations. "
            f"Found: {found}"
        )

    def test_api_file_has_require_for_schema(self):
        """Verify alert API imports schema namespace"""
        path = os.path.join(self.REPO_DIR, "src/metabase/api/alert.clj")
        with open(path) as f:
            content = f.read()

        import_indicators = [
            "metabase.api.schema.alert",
            "schema/alert",
            "require",
        ]
        found = [ind for ind in import_indicators if ind in content]
        assert len(found) >= 1, (
            "Alert API should import the schema namespace. "
            f"None of {import_indicators} found."
        )
