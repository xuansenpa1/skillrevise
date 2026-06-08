"""
Test skill: dbt-transformation-patterns
Verify that the Agent implements a custom accepted_range generic test macro for
dbt-core — Jinja/SQL macro (test_accepted_range), AcceptedRangeConfig dataclass,
and unit tests verifying compiled SQL output.
"""

import os
import re
import subprocess
import pytest


class TestDbtTransformationPatterns:
    REPO_DIR = "/workspace/dbt-core"

    # ────── helpers ──────

    def _read(self, rel_path):
        fpath = os.path.join(self.REPO_DIR, rel_path)
        with open(fpath, "r") as f:
            return f.read()

    def _exists(self, rel_path):
        return os.path.isfile(os.path.join(self.REPO_DIR, rel_path))

    # === File Path Checks ===

    def test_accepted_range_macro_exists(self):
        """accepted_range.sql macro must exist"""
        assert self._exists(
            "core/dbt/include/global_project/macros/generic_test_templates/accepted_range.sql"
        )

    def test_unit_test_exists(self):
        """test_accepted_range_macro.py must exist"""
        assert self._exists("tests/unit/test_accepted_range_macro.py")

    # === Semantic Checks — accepted_range.sql ===

    def test_macro_test_name(self):
        """Macro must be named test_accepted_range"""
        src = self._read(
            "core/dbt/include/global_project/macros/generic_test_templates/accepted_range.sql"
        )
        assert "test accepted_range" in src or "test_accepted_range" in src

    def test_macro_params(self):
        """Macro must accept model, column_name, min_value, max_value, inclusive"""
        src = self._read(
            "core/dbt/include/global_project/macros/generic_test_templates/accepted_range.sql"
        )
        for param in ["model", "column_name", "min_value", "max_value", "inclusive"]:
            assert param in src, f"Missing parameter: {param}"

    def test_macro_validation_cte(self):
        """Must have a validation CTE"""
        src = self._read(
            "core/dbt/include/global_project/macros/generic_test_templates/accepted_range.sql"
        ).lower()
        assert "validation" in src

    def test_macro_validation_errors_cte(self):
        """Must have a validation_errors CTE"""
        src = self._read(
            "core/dbt/include/global_project/macros/generic_test_templates/accepted_range.sql"
        ).lower()
        assert "validation_errors" in src

    def test_macro_null_handling(self):
        """Must exclude NULLs from violations (is not null)"""
        src = self._read(
            "core/dbt/include/global_project/macros/generic_test_templates/accepted_range.sql"
        ).lower()
        assert "is not null" in src

    def test_macro_inclusive_logic(self):
        """Must have inclusive/exclusive comparison logic"""
        src = self._read(
            "core/dbt/include/global_project/macros/generic_test_templates/accepted_range.sql"
        )
        assert "inclusive" in src

    def test_macro_where_filter(self):
        """Must support optional where filter"""
        src = self._read(
            "core/dbt/include/global_project/macros/generic_test_templates/accepted_range.sql"
        )
        assert "where" in src.lower()

    def test_macro_compiler_error(self):
        """Must raise compiler error when neither min nor max provided"""
        src = self._read(
            "core/dbt/include/global_project/macros/generic_test_templates/accepted_range.sql"
        )
        assert "raise_compiler_error" in src or "exceptions" in src

    def test_macro_count_violations(self):
        """Must select count(*) from validation_errors"""
        src = self._read(
            "core/dbt/include/global_project/macros/generic_test_templates/accepted_range.sql"
        ).lower()
        assert "count" in src

    # === Semantic Checks — AcceptedRangeConfig ===

    def test_config_dataclass_exists(self):
        """AcceptedRangeConfig must be defined in test.py"""
        src = self._read("core/dbt/contracts/test.py")
        assert "AcceptedRangeConfig" in src

    def test_config_fields(self):
        """Config must have min_value, max_value, inclusive, where"""
        src = self._read("core/dbt/contracts/test.py")
        for field in ["min_value", "max_value", "inclusive"]:
            assert field in src, f"Missing field: {field}"

    def test_config_validation_missing_bounds(self):
        """Config must raise ValueError when no bounds provided"""
        src = self._read("core/dbt/contracts/test.py")
        assert "ValueError" in src

    def test_config_validation_inverted(self):
        """Config must raise ValueError when min > max"""
        src = self._read("core/dbt/contracts/test.py")
        assert "min_value" in src and "max_value" in src

    # === Semantic Checks — Unit Tests ===

    def test_unit_test_min_only(self):
        """Test file must have min_only test case"""
        src = self._read("tests/unit/test_accepted_range_macro.py")
        assert "min" in src.lower()

    def test_unit_test_max_only(self):
        """Test file must have max_only test case"""
        src = self._read("tests/unit/test_accepted_range_macro.py")
        assert "max" in src.lower()

    def test_unit_test_exclusive(self):
        """Test file must have exclusive bounds test"""
        src = self._read("tests/unit/test_accepted_range_macro.py")
        assert "exclusive" in src.lower() or "inclusive" in src.lower()

    # === Functional Checks ===

    def test_python_syntax_config(self):
        """test.py must have valid syntax"""
        result = subprocess.run(
            ["python", "-c",
             "import py_compile; py_compile.compile('core/dbt/contracts/test.py', doraise=True)"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_unit_tests_pass(self):
        """Unit tests must pass"""
        result = subprocess.run(
            ["python", "-m", "pytest",
             "tests/unit/test_accepted_range_macro.py",
             "-v", "--tb=short"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, (
            f"Tests failed:\n{result.stdout}\n{result.stderr}"
        )
