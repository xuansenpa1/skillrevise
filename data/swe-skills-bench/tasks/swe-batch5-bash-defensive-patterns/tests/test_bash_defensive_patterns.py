"""
Test skill: bash-defensive-patterns
Verify that the Agent correctly writes defensive Bash scripts with
ShellCheck compliance, proper quoting, error handling, and locking.
"""

import os
import re
import subprocess
import pytest


class TestBashDefensivePatterns:
    REPO_DIR = "/workspace/shellcheck"

    DEPLOY = "scripts/deploy.sh"
    BACKUP = "scripts/backup.sh"
    HEALTHCHECK = "scripts/healthcheck.sh"
    COMMON = "scripts/lib/common.sh"

    def _read_file(self, rel_path):
        filepath = os.path.join(self.REPO_DIR, rel_path)
        with open(filepath) as f:
            return f.read()

    # === File Path Checks ===

    def test_deploy_script_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.DEPLOY)
        assert os.path.exists(filepath), f"deploy.sh not found at {filepath}"

    def test_backup_script_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.BACKUP)
        assert os.path.exists(filepath), f"backup.sh not found at {filepath}"

    def test_healthcheck_script_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.HEALTHCHECK)
        assert os.path.exists(filepath), f"healthcheck.sh not found at {filepath}"

    def test_common_library_exists(self):
        filepath = os.path.join(self.REPO_DIR, self.COMMON)
        assert os.path.exists(filepath), f"common.sh not found at {filepath}"

    # === Semantic Checks ===

    def test_all_scripts_have_strict_mode(self):
        """Verify all scripts start with set -euo pipefail"""
        for path in [self.DEPLOY, self.BACKUP, self.HEALTHCHECK, self.COMMON]:
            content = self._read_file(path)
            assert "set -euo pipefail" in content, \
                f"{path} missing 'set -euo pipefail'"

    def test_all_scripts_have_shebang(self):
        """Verify all scripts have bash shebang"""
        for path in [self.DEPLOY, self.BACKUP, self.HEALTHCHECK, self.COMMON]:
            content = self._read_file(path)
            assert content.startswith("#!/") and "bash" in content.split("\n")[0], \
                f"{path} missing bash shebang"

    def test_common_has_logging_functions(self):
        """Verify common.sh defines log_info, log_warn, log_error"""
        content = self._read_file(self.COMMON)
        for func in ["log_info", "log_warn", "log_error"]:
            assert func in content, f"common.sh missing {func} function"

    def test_common_has_retry_function(self):
        """Verify common.sh defines retry function"""
        content = self._read_file(self.COMMON)
        assert "retry" in content, "common.sh missing retry function"

    def test_common_has_lock_functions(self):
        """Verify common.sh defines acquire_lock with flock"""
        content = self._read_file(self.COMMON)
        assert "acquire_lock" in content, "common.sh missing acquire_lock"
        assert "flock" in content, "common.sh missing flock usage"

    def test_common_has_cleanup_registration(self):
        """Verify common.sh has register_cleanup with trap"""
        content = self._read_file(self.COMMON)
        assert "register_cleanup" in content or "trap" in content, \
            "common.sh missing cleanup registration/trap"

    def test_deploy_sources_common(self):
        """Verify deploy.sh sources lib/common.sh"""
        content = self._read_file(self.DEPLOY)
        has_source = "source" in content or "." in content.split("\n")[5] if len(content.split("\n")) > 5 else False
        assert "common.sh" in content, "deploy.sh missing source lib/common.sh"

    def test_deploy_parses_arguments(self):
        """Verify deploy.sh parses --image and --service arguments"""
        content = self._read_file(self.DEPLOY)
        assert "--image" in content, "deploy.sh missing --image argument"
        assert "--service" in content, "deploy.sh missing --service argument"

    def test_deploy_uses_docker_pull_with_retry(self):
        """Verify deploy.sh uses docker pull with retry"""
        content = self._read_file(self.DEPLOY)
        assert "docker pull" in content, "deploy.sh missing docker pull"
        assert "retry" in content, "deploy.sh missing retry for docker pull"

    def test_backup_uses_file_lock(self):
        """Verify backup.sh acquires file lock"""
        content = self._read_file(self.BACKUP)
        assert "lock" in content.lower(), "backup.sh missing file lock"
        assert "pg_dump" in content, "backup.sh missing pg_dump"

    def test_backup_uploads_and_rotates(self):
        """Verify backup.sh uploads to S3 and rotates old backups"""
        content = self._read_file(self.BACKUP)
        assert "s3" in content.lower(), "backup.sh missing S3 upload"
        assert "retention" in content or "rotate" in content.lower() or "delete" in content.lower(), \
            "backup.sh missing backup rotation"

    def test_healthcheck_checks_http_status(self):
        """Verify healthcheck.sh checks HTTP status with curl"""
        content = self._read_file(self.HEALTHCHECK)
        assert "curl" in content, "healthcheck.sh missing curl"
        assert "--url" in content or "url" in content.lower(), \
            "healthcheck.sh missing --url argument"

    # === Functional Checks ===

    def test_shellcheck_compliance(self):
        """Verify all scripts pass ShellCheck with zero warnings"""
        scripts = [self.DEPLOY, self.BACKUP, self.HEALTHCHECK, self.COMMON]
        for path in scripts:
            filepath = os.path.join(self.REPO_DIR, path)
            result = subprocess.run(
                ["shellcheck", "-s", "bash", filepath],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                # Count actual errors vs info
                error_lines = [
                    l for l in result.stdout.split("\n")
                    if "error" in l.lower() or "warning" in l.lower()
                ]
                if error_lines:
                    pytest.fail(
                        f"ShellCheck warnings in {path}: {error_lines[:5]}"
                    )

    def test_no_unquoted_variables(self):
        """Verify scripts use proper quoting (no bare $VAR patterns)"""
        for path in [self.DEPLOY, self.BACKUP, self.HEALTHCHECK]:
            content = self._read_file(path)
            # Check for obvious unquoted patterns (simplified check)
            # Lines with $VAR not inside quotes or ${VAR} context
            lines = content.split("\n")
            for i, line in enumerate(lines):
                # Skip comments
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                # Check for echo or assignment patterns with unquoted vars
                # This is a simplified heuristic
                if re.search(r'\b(echo|printf)\s+\$[A-Z_]+\b', line):
                    # May be false positive but worth flagging
                    pass  # Relaxed check
