#!/usr/bin/env python3
"""Export SWE-Skills-Bench tasks into the SkillsBench-style layout."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Sequence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Export SWE-Skills-Bench task prompts, tests, and verifier settings "
            "as SkillsBench-style task directories plus a SkillRevise manifest."
        )
    )
    parser.add_argument("swe_skills_bench_root", help="Path to SWE-Skills-Bench repository root.")
    parser.add_argument("--output-root", required=True, help="Destination root containing tasks/ and manifests.")
    parser.add_argument("--config", help="Benchmark config YAML. Defaults to config/benchmark_config.yaml.")
    parser.add_argument(
        "--manifest-root",
        help=(
            "Path prefix written into manifest metadata.repo_path. Use the server path when "
            "exporting locally for a remote run. Defaults to --output-root resolved locally."
        ),
    )
    parser.add_argument("--batch", action="append", help="Restrict to one or more batch names, e.g. batch1.")
    parser.add_argument("--skill", action="append", help="Restrict to one or more SWE-Skills-Bench skill ids.")
    parser.add_argument("--overwrite", action="store_true", help="Remove --output-root before exporting.")
    parser.add_argument(
        "--include-reference-skill",
        action="store_true",
        help="Copy benchmark-provided reference skills into reference_skill/. Default is false.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail instead of skipping tasks with missing config or test files.",
    )
    args = parser.parse_args(argv)

    swe_root = Path(args.swe_skills_bench_root).resolve()
    config_path = Path(args.config).resolve() if args.config else swe_root / "config" / "benchmark_config.yaml"
    output_root = Path(args.output_root).resolve()
    manifest_root = Path(args.manifest_root) if args.manifest_root else output_root
    config = load_config(config_path)

    summary = export_swe_skills_bench(
        swe_root,
        output_root,
        config=config,
        manifest_root=manifest_root,
        batches=args.batch,
        skills=args.skill,
        include_reference_skill=args.include_reference_skill,
        overwrite=args.overwrite,
        strict=args.strict,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def load_config(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on local env
        raise SystemExit(
            "SWE-Skills-Bench export requires PyYAML. Install it with `python -m pip install pyyaml`."
        ) from exc
    payload = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Config did not parse as a mapping: {path}")
    return payload


def export_swe_skills_bench(
    swe_root: Path,
    output_root: Path,
    *,
    config: dict[str, Any],
    manifest_root: Path | None = None,
    batches: Sequence[str] | None = None,
    skills: Sequence[str] | None = None,
    include_reference_skill: bool = False,
    overwrite: bool = False,
    strict: bool = False,
) -> dict[str, Any]:
    if overwrite and output_root.exists():
        shutil.rmtree(output_root)
    tasks_root = output_root / "tasks"
    tasks_root.mkdir(parents=True, exist_ok=True)
    manifest_root = output_root if manifest_root is None else manifest_root

    skill_configs_by_id = skill_configs(config)
    wanted_batches = set(batches or discover_batches(swe_root))
    wanted_skills = set(skills or [])
    records: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []

    for task_file in discover_task_files(swe_root, wanted_batches):
        batch = task_file.parent.name
        skill_id = task_file.stem
        if wanted_skills and skill_id not in wanted_skills:
            continue
        skill_config = skill_configs_by_id.get(skill_id)
        if not isinstance(skill_config, dict):
            skipped.append(_skip(batch, skill_id, "missing skill config"))
            continue
        test_file = find_test_file(swe_root, batch, skill_id)
        if test_file is None:
            skipped.append(_skip(batch, skill_id, "missing test file"))
            continue
        records.append(
            write_task(
                swe_root=swe_root,
                tasks_root=tasks_root,
                manifest_root=manifest_root,
                batch=batch,
                skill_id=skill_id,
                task_file=task_file,
                test_file=test_file,
                skill_config=skill_config,
                include_reference_skill=include_reference_skill,
            )
        )

    if skipped and strict:
        preview = ", ".join(f"{item['batch']}/{item['skill_id']} ({item['reason']})" for item in skipped[:10])
        suffix = "..." if len(skipped) > 10 else ""
        raise SystemExit(f"Skipped {len(skipped)} task(s): {preview}{suffix}")
    if not records:
        raise SystemExit("No SWE-Skills-Bench tasks were exported.")

    records.sort(key=lambda item: str(item["task_id"]))
    write_manifest(output_root / "swe_skillsbench_tasks.json", records)
    write_jobs(output_root / "all_jobs.json", records)
    write_export_metadata(output_root / "swe_skillsbench_export.json", records, skipped, swe_root, include_reference_skill)
    write_readme(output_root, records, skipped, include_reference_skill)
    return {
        "output_root": str(output_root),
        "manifest_root": str(manifest_root),
        "num_tasks": len(records),
        "num_skipped": len(skipped),
        "include_reference_skill": include_reference_skill,
    }


def discover_batches(swe_root: Path) -> list[str]:
    tasks_dir = swe_root / "tasks"
    return sorted(path.name for path in tasks_dir.iterdir() if path.is_dir())


def discover_task_files(swe_root: Path, batches: set[str]) -> list[Path]:
    task_files: list[Path] = []
    for batch in sorted(batches):
        batch_dir = swe_root / "tasks" / batch
        if batch_dir.is_dir():
            task_files.extend(sorted(batch_dir.glob("*.md")))
    return task_files


def skill_configs(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    skills = config.get("skills")
    if not isinstance(skills, list):
        return {}
    return {
        str(item.get("id")): dict(item)
        for item in skills
        if isinstance(item, dict) and item.get("id")
    }


def find_test_file(swe_root: Path, batch: str, skill_id: str) -> Path | None:
    test_dir = swe_root / "tests" / batch
    exact = test_dir / f"test_{skill_id.replace('-', '_')}.py"
    if exact.exists():
        return exact
    tokens = [token for token in re.split(r"[-_]+", skill_id) if token]
    candidates = sorted(test_dir.glob("test_*.py")) if test_dir.is_dir() else []
    for candidate in candidates:
        stem = candidate.stem.lower()
        if all(token.lower() in stem for token in tokens):
            return candidate
    return None


def write_task(
    *,
    swe_root: Path,
    tasks_root: Path,
    manifest_root: Path,
    batch: str,
    skill_id: str,
    task_file: Path,
    test_file: Path,
    skill_config: dict[str, Any],
    include_reference_skill: bool,
) -> dict[str, Any]:
    task_id = safe_task_id(batch, skill_id)
    task_dir = tasks_root / task_id
    if task_dir.exists():
        shutil.rmtree(task_dir)
    task_dir.mkdir(parents=True, exist_ok=True)

    prompt = task_file.read_text(encoding="utf-8", errors="replace").strip()
    write_text(task_dir / "instruction.md", instruction_for(batch, skill_id, prompt))
    write_text(task_dir / "task.toml", task_toml_for(batch, skill_id, task_file, test_file, skill_config))
    write_text(task_dir / "environment" / "Dockerfile", dockerfile_for(skill_config))
    write_text(task_dir / "tests" / "test.sh", test_script_for(test_file, skill_config))
    (task_dir / "tests" / "test.sh").chmod(0o755)
    copy_test_files(test_file, task_dir)
    if include_reference_skill:
        copy_reference_skill(swe_root, skill_id, task_dir)

    tags = ["swe-skills-bench", batch, skill_id]
    repo = dict(skill_config.get("repo") or {})
    env = dict(skill_config.get("environment") or {})
    repo_path = manifest_root / "tasks" / task_id
    timeout_seconds = verifier_timeout(evaluation_configs(skill_config))
    return {
        "task_id": task_id,
        "family": skill_id,
        "instruction": instruction_for(batch, skill_id, prompt),
        "acceptance_criteria": [
            "The exported SWE-Skills-Bench task instruction is satisfied.",
            "The SkillsBench-style verifier command succeeds: `bash tests/test.sh`.",
            "Do not rely on reference_skill/ unless it was intentionally provided for a reference run.",
        ],
        "tags": tags,
        "metadata": {
            "repo_path": str(repo_path),
            "skillsbench_task_dir": str(repo_path),
            "verifier_command": "bash tests/test.sh",
            "default_command": "bash tests/test.sh",
            "timeout_seconds": timeout_seconds,
            "source_benchmark": "SWE-Skills-Bench",
            "source_batch": batch,
            "source_skill_id": skill_id,
            "source_task_path": str(task_file.relative_to(swe_root)),
            "source_test_path": str(test_file.relative_to(swe_root)),
            "repo_url": repo.get("url"),
            "repo_commit": repo.get("commit"),
            "base_image": env.get("base_image"),
            "include_reference_skill": include_reference_skill,
        },
    }


def safe_task_id(batch: str, skill_id: str) -> str:
    return f"swe-{batch}-{skill_id}".lower()


def instruction_for(batch: str, skill_id: str, prompt: str) -> str:
    return "\n".join([f"# SWE-Skills-Bench: {skill_id} ({batch})", "", prompt, ""])


def task_toml_for(batch: str, skill_id: str, task_file: Path, test_file: Path, skill_config: dict[str, Any]) -> str:
    env = dict(skill_config.get("environment") or {})
    limits = dict(env.get("limits") or {})
    evals = evaluation_configs(skill_config)
    cpus = int(float(limits.get("cpus") or 4))
    memory_mb = parse_memory_mb(limits.get("memory") or "8g")
    tags = ["swe-skills-bench", batch, skill_id]
    tag_literal = ", ".join(json.dumps(tag) for tag in tags)
    return "\n".join(
        [
            'version = "1.0"',
            "",
            "[metadata]",
            'author_name = "SWE-Skills-Bench"',
            'difficulty = "hard"',
            f"category = {json.dumps(skill_id)}",
            f"tags = [{tag_literal}]",
            'source_benchmark = "SWE-Skills-Bench"',
            f"source_batch = {json.dumps(batch)}",
            f"source_skill_id = {json.dumps(skill_id)}",
            f"source_task_path = {json.dumps(str(task_file.name))}",
            f"source_test_path = {json.dumps(str(test_file.name))}",
            "",
            "[verifier]",
            f"timeout_sec = {float(verifier_timeout(evals))}",
            "",
            "[agent]",
            f"timeout_sec = {float(agent_timeout(skill_config))}",
            "",
            "[environment]",
            "build_timeout_sec = 3600.0",
            f"cpus = {cpus}",
            f"memory_mb = {memory_mb}",
            "",
        ]
    )


def repo_name_from_url(url: str) -> str:
    name = url.rstrip("/").split("/")[-1]
    return name[:-4] if name.endswith(".git") else name


def dockerfile_for(skill_config: dict[str, Any]) -> str:
    env = dict(skill_config.get("environment") or {})
    repo = dict(skill_config.get("repo") or {})
    base_image = env.get("base_image") or "ubuntu:24.04"
    repo_url = repo.get("url")
    commit = repo.get("commit")
    lines = [
        f"FROM {base_image}",
        "USER root",
        "",
        "ENV DEBIAN_FRONTEND=noninteractive",
        "",
        "RUN if ! command -v git >/dev/null 2>&1 || ! command -v python >/dev/null 2>&1; then \\",
        "      apt-get update && apt-get install -y git ca-certificates python3 python3-pip && \\",
        "      rm -rf /var/lib/apt/lists/*; \\",
        "    fi",
        "RUN if ! command -v python >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then \\",
        "      ln -s /usr/bin/python3 /usr/local/bin/python; \\",
        "    fi",
        "RUN mkdir -p /workspace /logs/verifier /tmp/benchmark_tests",
        "",
    ]
    if repo_url:
        repo_dir = f"/workspace/{repo_name_from_url(str(repo_url))}"
        checkout = f"git checkout {shell_single_quote(str(commit))}" if commit else "true"
        lines.extend(
            [
                "RUN set -eux; \\",
                f"    repo_dir={shell_single_quote(repo_dir)}; \\",
                f"    if [ ! -d \"$repo_dir/.git\" ]; then rm -rf \"$repo_dir\" && git clone {shell_single_quote(str(repo_url))} \"$repo_dir\"; fi; \\",
                "    cd \"$repo_dir\"; \\",
                f"    {checkout}",
                "",
                f"WORKDIR {repo_dir}",
            ]
        )
    else:
        lines.append("WORKDIR /workspace")
    lines.extend(["", 'CMD ["/bin/bash"]', ""])
    return "\n".join(lines)


def test_script_for(test_file: Path, skill_config: dict[str, Any]) -> str:
    repo = dict(skill_config.get("repo") or {})
    repo_url = repo.get("url") or ""
    repo_dir = f"/workspace/{repo_name_from_url(str(repo_url))}" if repo_url else "/workspace"
    test_name = test_file.name
    lines = [
        "#!/usr/bin/env bash",
        "set -uo pipefail",
        "",
        "mkdir -p /logs/verifier /tmp/benchmark_tests",
        f"cp /tests/{test_name} /tmp/benchmark_tests/{test_name}",
        "if [ -f /tests/_dependency_utils.py ]; then cp /tests/_dependency_utils.py /tmp/benchmark_tests/_dependency_utils.py; fi",
        "if ! python -m pytest --version >/dev/null 2>&1; then",
        "  python -m pip install pytest -q --break-system-packages >/logs/verifier/pip_pytest.log 2>&1 || \\",
        "    python -m pip install pytest -q >/logs/verifier/pip_pytest.log 2>&1",
        "fi",
        "",
        "reward=1",
    ]
    build_index = 0
    unit_index = 0
    for item in evaluation_configs(skill_config):
        if not item.get("enabled", True):
            continue
        method = item.get("method")
        params = dict(item.get("params") or {})
        if method == "build_check":
            command = str(params.get("build_command") or "").strip()
            if command:
                lines.extend(
                    [
                        f"echo '[swe-skills-bench] build_check {build_index}: {command}' | tee -a /logs/verifier/test_output.log",
                        f"( cd {shell_single_quote(repo_dir)} && {command} ) >>/logs/verifier/build_{build_index}.log 2>&1",
                        "status=$?",
                        "if [ \"$status\" -ne 0 ]; then",
                        f"  echo '[swe-skills-bench] build_check {build_index} failed with exit code '$status | tee -a /logs/verifier/test_output.log",
                        "  reward=0",
                        "fi",
                        "",
                    ]
                )
                build_index += 1
        elif method == "unit_test":
            command = f"python -m pytest /tmp/benchmark_tests/{test_name} -v --tb=short"
            lines.extend(
                [
                    "if [ \"$reward\" -eq 1 ]; then",
                    f"  echo '[swe-skills-bench] unit_test {unit_index}: {command}' | tee -a /logs/verifier/test_output.log",
                    "  cd /tmp/benchmark_tests && unset PYTHONPATH",
                    f"  {command} 2>&1 | tee -a /logs/verifier/test_output.log",
                    "  status=${PIPESTATUS[0]}",
                    "  if [ \"$status\" -ne 0 ]; then reward=0; fi",
                    "fi",
                    "",
                ]
            )
            unit_index += 1
    lines.extend(["echo \"$reward\" > /logs/verifier/reward.txt", "exit 0", ""])
    return "\n".join(lines)


def evaluation_configs(skill_config: dict[str, Any]) -> list[dict[str, Any]]:
    env = dict(skill_config.get("environment") or {})
    values = skill_config.get("evaluation") or env.get("evaluation") or []
    return [dict(item) for item in values if isinstance(item, dict)]


def verifier_timeout(evals: list[dict[str, Any]]) -> int:
    total = 0
    for item in evals:
        params = dict(item.get("params") or {})
        total += int(params.get("timeout") or 600)
    return max(900, total + 300)


def agent_timeout(skill_config: dict[str, Any]) -> int:
    env = dict(skill_config.get("environment") or {})
    limits = dict(env.get("limits") or {})
    return int(limits.get("total_timeout_sec") or limits.get("timeout_per_command") or 1800)


def parse_memory_mb(value: Any) -> int:
    text = str(value or "").strip().lower()
    if not text:
        return 8192
    match = re.fullmatch(r"([0-9.]+)\s*([gmk]?)b?", text)
    if not match:
        return 8192
    amount = float(match.group(1))
    unit = match.group(2)
    if unit == "g":
        return int(amount * 1024)
    if unit == "k":
        return max(1, int(amount / 1024))
    return int(amount)


def copy_test_files(test_file: Path, task_dir: Path) -> None:
    tests_dir = task_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(test_file, tests_dir / test_file.name)
    dep_utils = test_file.parent / "_dependency_utils.py"
    if dep_utils.exists():
        shutil.copy2(dep_utils, tests_dir / "_dependency_utils.py")


def copy_reference_skill(swe_root: Path, skill_id: str, task_dir: Path) -> None:
    source = swe_root / "skills" / skill_id
    if not source.exists():
        return
    shutil.copytree(source, task_dir / "reference_skill", dirs_exist_ok=True)


def write_manifest(path: Path, records: list[dict[str, Any]]) -> None:
    payload = {
        "benchmark": "swe-skills-bench-as-skillsbench",
        "count": len(records),
        "tasks": records,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_jobs(path: Path, records: list[dict[str, Any]]) -> None:
    jobs = [{"name": record["task_id"], "task_id": record["task_id"]} for record in records]
    path.write_text(json.dumps(jobs, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_export_metadata(
    path: Path,
    records: list[dict[str, Any]],
    skipped: list[dict[str, str]],
    swe_root: Path,
    include_reference_skill: bool,
) -> None:
    payload = {
        "benchmark_name": "swe-skills-bench-as-skillsbench",
        "source_root": str(swe_root),
        "task_count": len(records),
        "skipped_count": len(skipped),
        "skipped": skipped,
        "layout": "SkillsBench-style task directories",
        "verifier_command": "bash tests/test.sh",
        "reward_rule": "reward=1 iff all enabled SWE-Skills-Bench build_check/unit_test evaluators pass",
        "include_reference_skill": include_reference_skill,
        "task_ids": [record["task_id"] for record in records],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_readme(
    output_root: Path,
    records: list[dict[str, Any]],
    skipped: list[dict[str, str]],
    include_reference_skill: bool,
) -> None:
    reference_line = (
        "- `reference_skill/` copied from the original benchmark because `--include-reference-skill` was used."
        if include_reference_skill
        else "- `reference_skill/` is omitted by default to avoid leaking benchmark-provided skills into generated-skill evaluation."
    )
    lines = [
        "# SWE-Skills-Bench As SkillsBench",
        "",
        "This export flattens SWE-Skills-Bench into SkillsBench-style task directories for SkillRevise.",
        "",
        f"Exported tasks: {len(records)}",
        f"Skipped tasks: {len(skipped)}",
        "",
        "Each task directory contains:",
        "- `instruction.md` copied from the corresponding SWE-Skills-Bench task prompt.",
        "- `task.toml` with source metadata, verifier timeout, agent timeout, and environment resources.",
        "- `environment/Dockerfile` based on the original SWE-Skills-Bench base image and repo commit.",
        "- `tests/test.sh`, which runs the original build/unit-test verifier and writes `/logs/verifier/reward.txt`.",
        "- `tests/test_*.py` copied from the original benchmark.",
        reference_line,
        "",
        "Reward rule: a task receives reward 1 only when every enabled original evaluator passes.",
        "",
    ]
    output_root.joinpath("README.md").write_text("\n".join(lines), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def shell_single_quote(text: str) -> str:
    return "'" + text.replace("'", "'\"'\"'") + "'"


def _skip(batch: str, skill_id: str, reason: str) -> dict[str, str]:
    return {"batch": batch, "skill_id": skill_id, "reason": reason}


if __name__ == "__main__":
    raise SystemExit(main())
