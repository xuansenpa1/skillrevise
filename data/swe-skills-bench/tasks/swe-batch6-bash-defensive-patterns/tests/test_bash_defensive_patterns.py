"""
Test skill: bash-defensive-patterns
Verify that the Agent writes defensive Bash deployment scripts with
strict mode, lock files, atomic symlink updates, health checks with
retries, rollback, and log rotation.
"""

import os
import re
import subprocess
import pytest


class TestBashDefensivePatterns:
    REPO_DIR = "/workspace/shellcheck"

    # === File Path Checks ===

    def test_deploy_script_exists(self):
        assert os.path.exists(os.path.join(self.REPO_DIR, "scripts/deploy.sh"))

    def test_health_check_script_exists(self):
        assert os.path.exists(os.path.join(self.REPO_DIR, "scripts/health-check.sh"))

    def test_rollback_script_exists(self):
        assert os.path.exists(os.path.join(self.REPO_DIR, "scripts/rollback.sh"))

    def test_log_rotate_script_exists(self):
        assert os.path.exists(os.path.join(self.REPO_DIR, "scripts/log-rotate.sh"))

    def test_common_lib_exists(self):
        assert os.path.exists(os.path.join(self.REPO_DIR, "scripts/lib/common.sh"))

    # === Semantic Checks ===

    def test_all_scripts_have_strict_mode(self):
        """All scripts should start with set -Eeuo pipefail"""
        for script in ("deploy.sh", "health-check.sh", "rollback.sh", "log-rotate.sh", "lib/common.sh"):
            path = os.path.join(self.REPO_DIR, f"scripts/{script}")
            with open(path) as f:
                content = f.read()
            assert "set -" in content, f"{script} missing strict mode"
            assert "pipefail" in content, f"{script} missing pipefail"

    def test_common_has_logging_functions(self):
        """common.sh should define log_info, log_warn, log_error, log_debug"""
        path = os.path.join(self.REPO_DIR, "scripts/lib/common.sh")
        with open(path) as f:
            content = f.read()
        for func in ("log_info", "log_warn", "log_error", "log_debug"):
            assert func in content, f"Missing {func} function"

    def test_common_has_require_var(self):
        """common.sh should define require_var function"""
        path = os.path.join(self.REPO_DIR, "scripts/lib/common.sh")
        with open(path) as f:
            content = f.read()
        assert "require_var" in content, "Missing require_var function"

    def test_common_has_require_command(self):
        """common.sh should define require_command function"""
        path = os.path.join(self.REPO_DIR, "scripts/lib/common.sh")
        with open(path) as f:
            content = f.read()
        assert "require_command" in content, "Missing require_command"

    def test_common_has_lock_functions(self):
        """common.sh should define acquire_lock and release_lock"""
        path = os.path.join(self.REPO_DIR, "scripts/lib/common.sh")
        with open(path) as f:
            content = f.read()
        assert "acquire_lock" in content, "Missing acquire_lock"
        assert "release_lock" in content, "Missing release_lock"

    def test_deploy_has_atomic_symlink(self):
        """deploy.sh should use atomic symlink update (ln + mv)"""
        path = os.path.join(self.REPO_DIR, "scripts/deploy.sh")
        with open(path) as f:
            content = f.read()
        assert "ln -sfn" in content or "ln -s" in content, "Missing symlink creation"
        assert "mv" in content, "Missing atomic mv for symlink swap"

    def test_deploy_has_checksum_verification(self):
        """deploy.sh should verify artifacts with SHA256 checksum"""
        path = os.path.join(self.REPO_DIR, "scripts/deploy.sh")
        with open(path) as f:
            content = f.read()
        assert "sha256" in content.lower() or "checksum" in content.lower(), (
            "Deploy should verify artifact checksum"
        )

    def test_deploy_has_dry_run(self):
        """deploy.sh should support --dry-run mode"""
        path = os.path.join(self.REPO_DIR, "scripts/deploy.sh")
        with open(path) as f:
            content = f.read()
        assert "dry" in content.lower() or "DRY" in content, (
            "Deploy should support dry-run mode"
        )

    def test_deploy_sources_common(self):
        """deploy.sh should source the common library"""
        path = os.path.join(self.REPO_DIR, "scripts/deploy.sh")
        with open(path) as f:
            content = f.read()
        assert "source" in content or "." in content.split("\n")[0:20].__repr__(), (
            "Deploy should source common.sh"
        )

    def test_health_check_has_retry_loop(self):
        """health-check.sh should implement a retry loop"""
        path = os.path.join(self.REPO_DIR, "scripts/health-check.sh")
        with open(path) as f:
            content = f.read()
        assert "retry" in content.lower() or "attempt" in content.lower() or "while" in content or "for" in content, (
            "Health check should have retry loop"
        )

    def test_health_check_uses_curl(self):
        """health-check.sh should use curl for HTTP health checks"""
        path = os.path.join(self.REPO_DIR, "scripts/health-check.sh")
        with open(path) as f:
            content = f.read()
        assert "curl" in content, "Health check should use curl"
        assert "max-time" in content or "timeout" in content.lower(), (
            "Should set request timeout"
        )

    def test_rollback_determines_previous_version(self):
        """rollback.sh should determine previous version from releases directory"""
        path = os.path.join(self.REPO_DIR, "scripts/rollback.sh")
        with open(path) as f:
            content = f.read()
        assert "releases" in content or "previous" in content.lower(), (
            "Rollback should find previous version"
        )

    def test_rollback_exits_with_code_2_on_critical(self):
        """rollback.sh should exit 2 when rollback itself fails"""
        path = os.path.join(self.REPO_DIR, "scripts/rollback.sh")
        with open(path) as f:
            content = f.read()
        assert "exit 2" in content, "Rollback failure should exit with code 2"
        assert "CRITICAL" in content, "Should log CRITICAL on rollback failure"

    def test_log_rotate_has_compression(self):
        """log-rotate.sh should support gzip compression"""
        path = os.path.join(self.REPO_DIR, "scripts/log-rotate.sh")
        with open(path) as f:
            content = f.read()
        assert "gzip" in content or "compress" in content.lower(), (
            "Log rotation should support compression"
        )

    def test_log_rotate_has_retention(self):
        """log-rotate.sh should enforce max-age retention"""
        path = os.path.join(self.REPO_DIR, "scripts/log-rotate.sh")
        with open(path) as f:
            content = f.read()
        assert "max-age" in content or "max_age" in content or "find" in content, (
            "Should enforce retention by age"
        )

    # === Functional Checks ===

    def test_scripts_have_shebang(self):
        """All scripts should start with #!/usr/bin/env bash or #!/bin/bash"""
        for script in ("deploy.sh", "health-check.sh", "rollback.sh", "log-rotate.sh"):
            path = os.path.join(self.REPO_DIR, f"scripts/{script}")
            with open(path) as f:
                first_line = f.readline().strip()
            assert first_line.startswith("#!"), f"{script} missing shebang"
            assert "bash" in first_line, f"{script} shebang should reference bash"

    def test_scripts_pass_shellcheck(self):
        """All scripts should pass shellcheck (if available)"""
        try:
            subprocess.run(["shellcheck", "--version"], capture_output=True, timeout=10)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("shellcheck not available")
        for script in ("deploy.sh", "health-check.sh", "rollback.sh", "log-rotate.sh", "lib/common.sh"):
            path = os.path.join(self.REPO_DIR, f"scripts/{script}")
            result = subprocess.run(
                ["shellcheck", "-S", "warning", path],
                capture_output=True, text=True, timeout=30
            )
            assert result.returncode == 0, (
                f"shellcheck warnings in {script}:\n{result.stdout}"
            )

    def test_common_sh_sources_cleanly(self):
        """common.sh should source without errors"""
        path = os.path.join(self.REPO_DIR, "scripts/lib/common.sh")
        result = subprocess.run(
            ["bash", "-n", path],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0, f"common.sh syntax error: {result.stderr}"
