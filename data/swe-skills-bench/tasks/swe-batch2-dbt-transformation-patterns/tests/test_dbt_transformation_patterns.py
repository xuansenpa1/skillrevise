"""
Test skill: dbt-transformation-patterns
Verify that the Agent implements incremental merge materialization for
dbt core with full-load first run, merge updates, unique key handling,
schema evolution detection, and error handling.
"""

import os
import re
import ast
import subprocess
import pytest


class TestDbtTransformationPatterns:
    REPO_DIR = "/workspace/dbt-core"

    # === File Path Checks ===

    def test_incremental_merge_py_exists(self):
        """Verify incremental_merge.py exists"""
        path = os.path.join(
            self.REPO_DIR,
            "core", "dbt", "materializations", "incremental_merge.py",
        )
        assert os.path.exists(path), (
            f"incremental_merge.py not found at {path}"
        )

    def test_schema_evolution_py_exists(self):
        """Verify schema_evolution.py exists"""
        path = os.path.join(
            self.REPO_DIR,
            "core", "dbt", "materializations", "schema_evolution.py",
        )
        assert os.path.exists(path), (
            f"schema_evolution.py not found at {path}"
        )

    # === Semantic Checks ===

    def test_full_table_creation(self):
        """Verify first-run full table creation logic"""
        path = os.path.join(
            self.REPO_DIR,
            "core", "dbt", "materializations", "incremental_merge.py",
        )
        with open(path) as f:
            content = f.read()

        create_indicators = [
            "create", "CREATE", "full", "first_run",
            "table", "TABLE", "exists",
        ]
        found = [ind for ind in create_indicators if ind in content]
        assert len(found) >= 2, (
            f"Should handle first-run full table creation. Found: {found}"
        )

    def test_merge_semantics(self):
        """Verify merge/upsert logic for subsequent runs"""
        path = os.path.join(
            self.REPO_DIR,
            "core", "dbt", "materializations", "incremental_merge.py",
        )
        with open(path) as f:
            content = f.read()

        merge_indicators = [
            "merge", "MERGE", "upsert", "UPSERT",
            "insert", "INSERT", "update", "UPDATE",
            "MATCHED", "matched",
        ]
        found = [ind for ind in merge_indicators if ind in content]
        assert len(found) >= 3, (
            f"Should implement merge semantics. Found: {found}"
        )

    def test_unique_key_handling(self):
        """Verify unique key configuration for merge matching"""
        path = os.path.join(
            self.REPO_DIR,
            "core", "dbt", "materializations", "incremental_merge.py",
        )
        with open(path) as f:
            content = f.read()

        key_indicators = [
            "unique_key", "unique", "key", "composite",
            "match", "primary",
        ]
        found = [ind for ind in key_indicators if ind in content]
        assert len(found) >= 2, (
            f"Should support unique key configuration. Found: {found}"
        )

    def test_updated_at_column(self):
        """Verify configurable updated_at column for change detection"""
        path = os.path.join(
            self.REPO_DIR,
            "core", "dbt", "materializations", "incremental_merge.py",
        )
        with open(path) as f:
            content = f.read()

        ts_indicators = [
            "updated_at", "timestamp", "incremental",
            "changed", "new_rows", "filter",
        ]
        found = [ind for ind in ts_indicators if ind in content]
        assert len(found) >= 2, (
            f"Should use updated_at for incremental detection. Found: {found}"
        )

    def test_schema_evolution_detection(self):
        """Verify schema evolution detection and on_schema_change config"""
        path = os.path.join(
            self.REPO_DIR,
            "core", "dbt", "materializations", "schema_evolution.py",
        )
        with open(path) as f:
            content = f.read()

        schema_indicators = [
            "on_schema_change", "schema", "column",
            "ignore", "append_new_columns", "fail",
        ]
        found = [ind for ind in schema_indicators if ind in content]
        assert len(found) >= 3, (
            f"Should handle schema evolution. Found: {found}"
        )

    def test_append_new_columns(self):
        """Verify append_new_columns alters target table"""
        path = os.path.join(
            self.REPO_DIR,
            "core", "dbt", "materializations", "schema_evolution.py",
        )
        with open(path) as f:
            content = f.read()

        alter_indicators = [
            "ALTER", "alter", "ADD", "add", "column",
            "append", "missing",
        ]
        found = [ind for ind in alter_indicators if ind in content]
        assert len(found) >= 2, (
            f"Should support appending new columns. Found: {found}"
        )

    def test_missing_unique_key_error(self):
        """Verify error raised when unique key not specified"""
        path = os.path.join(
            self.REPO_DIR,
            "core", "dbt", "materializations", "incremental_merge.py",
        )
        with open(path) as f:
            content = f.read()

        error_indicators = [
            "raise", "Error", "error", "required",
            "must", "missing", "unique_key",
        ]
        found = [ind for ind in error_indicators if ind in content]
        assert len(found) >= 3, (
            f"Should raise error for missing unique key. Found: {found}"
        )

    def test_fallback_full_refresh(self):
        """Verify fallback to full refresh when target table missing"""
        path = os.path.join(
            self.REPO_DIR,
            "core", "dbt", "materializations", "incremental_merge.py",
        )
        with open(path) as f:
            content = f.read()

        fallback_indicators = [
            "full_refresh", "fallback", "not exist",
            "dropped", "missing", "create",
        ]
        found = [ind for ind in fallback_indicators if ind in content]
        assert len(found) >= 2, (
            f"Should fall back to full refresh. Found: {found}"
        )

    # === Functional Checks ===

    def test_incremental_merge_valid_python(self):
        """Verify incremental_merge.py is valid Python"""
        path = os.path.join(
            self.REPO_DIR,
            "core", "dbt", "materializations", "incremental_merge.py",
        )
        with open(path) as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"incremental_merge.py has syntax error: {e}")

    def test_schema_evolution_valid_python(self):
        """Verify schema_evolution.py is valid Python"""
        path = os.path.join(
            self.REPO_DIR,
            "core", "dbt", "materializations", "schema_evolution.py",
        )
        with open(path) as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"schema_evolution.py has syntax error: {e}")

    def test_callable_definitions(self):
        """Verify modules define callable functions or classes"""
        combined = ""
        for fname in ["incremental_merge.py", "schema_evolution.py"]:
            path = os.path.join(
                self.REPO_DIR,
                "core", "dbt", "materializations", fname,
            )
            with open(path) as f:
                combined += f.read()

        defs = re.findall(r"^(?:def |class )\w+", combined, re.MULTILINE)
        assert len(defs) >= 4, (
            f"Should define at least 4 functions/classes. Found: {defs}"
        )
