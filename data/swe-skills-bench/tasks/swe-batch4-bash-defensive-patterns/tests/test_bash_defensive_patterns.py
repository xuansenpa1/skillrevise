"""
Tests for skill: bash-defensive-patterns
Repo: koalaman/shellcheck
Image: zhangyiiiiii/swe-skills-bench-python
Task: Write a defensive Bash script library with strict mode, error
      trapping, safe file ops, retry logic, and argument validation.
"""

import os
import re
import subprocess

import pytest

REPO_DIR = "/workspace/shellcheck"
LIB_DIR = os.path.join(REPO_DIR, "examples", "defensive-lib", "lib")
SCRIPTS_DIR = os.path.join(REPO_DIR, "examples", "defensive-lib", "scripts")

CORE_FILE = os.path.join(LIB_DIR, "core.sh")
FILE_OPS_FILE = os.path.join(LIB_DIR, "file_ops.sh")
PROCESS_OPS_FILE = os.path.join(LIB_DIR, "process_ops.sh")
VALIDATION_FILE = os.path.join(LIB_DIR, "validation.sh")
DEPLOY_FILE = os.path.join(SCRIPTS_DIR, "deploy.sh")


# ---------------------------------------------------------------------------
# Layer 1 — file_path_check
# ---------------------------------------------------------------------------

class TestFilePathCheck:
    """Verify all required defensive Bash files exist."""

    def test_core_exists(self):
        assert os.path.isfile(CORE_FILE), f"Missing {CORE_FILE}"

    def test_file_ops_exists(self):
        assert os.path.isfile(FILE_OPS_FILE), f"Missing {FILE_OPS_FILE}"

    def test_process_ops_exists(self):
        assert os.path.isfile(PROCESS_OPS_FILE), f"Missing {PROCESS_OPS_FILE}"

    def test_validation_exists(self):
        assert os.path.isfile(VALIDATION_FILE), f"Missing {VALIDATION_FILE}"

    def test_deploy_script_exists(self):
        assert os.path.isfile(DEPLOY_FILE), f"Missing {DEPLOY_FILE}"


# ---------------------------------------------------------------------------
# Layer 2 — semantic_check
# ---------------------------------------------------------------------------

class TestSemanticCore:
    """Verify core.sh structure and patterns."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open(CORE_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()

    def test_strict_mode(self):
        assert "set -Eeuo pipefail" in self.src or (
            "set -e" in self.src and "set -u" in self.src
        ), "core.sh must set strict mode (set -Eeuo pipefail)"

    def test_shebang(self):
        assert self.src.strip().startswith("#!/bin/bash"), (
            "core.sh must start with #!/bin/bash"
        )

    def test_init_strict_mode_function(self):
        assert "init_strict_mode" in self.src, (
            "core.sh must define init_strict_mode function"
        )

    def test_cleanup_handler(self):
        assert "cleanup_handler" in self.src or "cleanup" in self.src, (
            "core.sh must define a cleanup handler"
        )

    def test_trap_exit(self):
        assert re.search(r"trap\s+.*EXIT", self.src), (
            "core.sh must set up EXIT trap"
        )

    def test_register_cleanup(self):
        assert "register_cleanup" in self.src, (
            "core.sh must define register_cleanup function"
        )

    def test_log_functions(self):
        for fn in ["log_info", "log_warn", "log_error"]:
            assert fn in self.src, f"core.sh must define {fn} function"

    def test_die_function(self):
        assert "die" in self.src, "core.sh must define die function"

    def test_stderr_output(self):
        assert ">&2" in self.src or "1>&2" in self.src or "stderr" in self.src.lower(), (
            "Log functions must output to stderr"
        )


class TestSemanticFileOps:
    """Verify safe file operation functions."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open(FILE_OPS_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()

    def test_safe_write(self):
        assert "safe_write" in self.src, "file_ops.sh must define safe_write"

    def test_backup_and_replace(self):
        assert "backup_and_replace" in self.src, (
            "file_ops.sh must define backup_and_replace"
        )

    def test_safe_copy(self):
        assert "safe_copy" in self.src, "file_ops.sh must define safe_copy"

    def test_locked_operation(self):
        assert "locked_operation" in self.src, (
            "file_ops.sh must define locked_operation"
        )

    def test_atomic_mv(self):
        assert "mv " in self.src or "mv\t" in self.src, (
            "safe_write should use mv for atomic writes"
        )

    def test_flock_usage(self):
        assert "flock" in self.src, (
            "locked_operation should use flock for file locking"
        )

    def test_bak_backup(self):
        assert ".bak" in self.src, (
            "backup_and_replace should create .bak backup copies"
        )


class TestSemanticProcessOps:
    """Verify process operations."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open(PROCESS_OPS_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()

    def test_retry_with_backoff(self):
        assert "retry_with_backoff" in self.src, (
            "process_ops.sh must define retry_with_backoff"
        )

    def test_run_with_timeout(self):
        assert "run_with_timeout" in self.src, (
            "process_ops.sh must define run_with_timeout"
        )

    def test_run_parallel(self):
        assert "run_parallel" in self.src, (
            "process_ops.sh must define run_parallel"
        )

    def test_manage_pid_file(self):
        assert "manage_pid_file" in self.src, (
            "process_ops.sh must define manage_pid_file"
        )

    def test_exponential_backoff(self):
        assert "*" in self.src or "**" in self.src or "double" in self.src.lower() or "2" in self.src, (
            "retry_with_backoff should implement exponential backoff"
        )


class TestSemanticValidation:
    """Verify input validation functions."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open(VALIDATION_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()

    def test_parse_args(self):
        assert "parse_args" in self.src, "validation.sh must define parse_args"

    def test_require_commands(self):
        assert "require_commands" in self.src, (
            "validation.sh must define require_commands"
        )

    def test_validate_path(self):
        assert "validate_path" in self.src, (
            "validation.sh must define validate_path"
        )

    def test_is_integer(self):
        assert "is_integer" in self.src, (
            "validation.sh must define is_integer"
        )

    def test_command_v_check(self):
        assert "command -v" in self.src, (
            "require_commands should use 'command -v' to check availability"
        )

    def test_safe_variable_expansion(self):
        assert "${" in self.src, "Variables should use ${} expansion syntax"


class TestSemanticDeployScript:
    """Verify deploy.sh uses all library modules."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open(DEPLOY_FILE, "r", encoding="utf-8") as f:
            self.src = f.read()

    def test_sources_core(self):
        assert "core.sh" in self.src, "deploy.sh must source core.sh"

    def test_sources_file_ops(self):
        assert "file_ops.sh" in self.src, "deploy.sh must source file_ops.sh"

    def test_sources_process_ops(self):
        assert "process_ops.sh" in self.src, "deploy.sh must source process_ops.sh"

    def test_sources_validation(self):
        assert "validation.sh" in self.src, "deploy.sh must source validation.sh"

    def test_dry_run_flag(self):
        assert "dry-run" in self.src or "dry_run" in self.src, (
            "deploy.sh must support --dry-run flag"
        )

    def test_app_argument(self):
        assert "--app" in self.src or "app" in self.src, (
            "deploy.sh must accept --app argument"
        )

    def test_env_argument(self):
        assert "--env" in self.src, "deploy.sh must accept --env argument"


# ---------------------------------------------------------------------------
# Layer 3 — functional_check
# ---------------------------------------------------------------------------

class TestFunctionalCoreShSource:
    """Source core.sh and verify strict mode behavior."""

    def test_core_parses_without_error(self):
        result = subprocess.run(
            ["bash", "-n", CORE_FILE],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, (
            f"core.sh has syntax errors: {result.stderr}"
        )

    def test_file_ops_parses(self):
        result = subprocess.run(
            ["bash", "-n", FILE_OPS_FILE],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, (
            f"file_ops.sh has syntax errors: {result.stderr}"
        )

    def test_process_ops_parses(self):
        result = subprocess.run(
            ["bash", "-n", PROCESS_OPS_FILE],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, (
            f"process_ops.sh has syntax errors: {result.stderr}"
        )

    def test_validation_parses(self):
        result = subprocess.run(
            ["bash", "-n", VALIDATION_FILE],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, (
            f"validation.sh has syntax errors: {result.stderr}"
        )

    def test_deploy_parses(self):
        result = subprocess.run(
            ["bash", "-n", DEPLOY_FILE],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, (
            f"deploy.sh has syntax errors: {result.stderr}"
        )


class TestFunctionalDeployMissingArgs:
    """Verify deploy.sh errors on missing required arguments."""

    def test_missing_app_arg_fails(self):
        result = subprocess.run(
            ["bash", DEPLOY_FILE, "--env", "staging", "--version", "1.0.0"],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode != 0, (
            "deploy.sh should fail when --app is missing"
        )

    def test_deploy_dry_run(self):
        result = subprocess.run(
            ["bash", DEPLOY_FILE, "--app", "myapp", "--env", "staging",
             "--version", "1.2.3", "--dry-run"],
            capture_output=True, text=True, timeout=30,
        )
        # Dry run might fail if docker/curl/jq not available
        # but should at least parse arguments without crash
        output = result.stdout + result.stderr
        assert "myapp" in output or "dry" in output.lower() or result.returncode == 0, (
            f"--dry-run should log steps; got: {output[-500:]}"
        )


class TestFunctionalRetryLogic:
    """Test retry_with_backoff via a sourced invocation."""

    def test_retry_failing_command(self):
        script = (
            f'source "{CORE_FILE}" && '
            f'source "{PROCESS_OPS_FILE}" && '
            f'retry_with_backoff 2 0 false; echo "exit:$?"'
        )
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True, text=True, timeout=30,
        )
        output = result.stdout + result.stderr
        # It should attempt retries and eventually fail
        assert result.returncode != 0 or "exit:1" in output or "fail" in output.lower(), (
            f"retry_with_backoff should fail after retries; got: {output[-500:]}"
        )
