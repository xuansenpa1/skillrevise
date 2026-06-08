#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from skillrevise.benchmarks.skilllearnbench import SkillLearnBenchTaskLoader


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Export SkillLearnBench instances into a flat SkillsBench-style task root "
            "with manifests and train/heldout jobs."
        )
    )
    parser.add_argument("skilllearnbench_root", help="Path to SkillLearnBench repository root.")
    parser.add_argument("--output-root", required=True, help="Destination root containing tasks/ and manifests.")
    parser.add_argument(
        "--manifest-root",
        help=(
            "Path prefix written into manifest metadata.repo_path. Use the server path when "
            "exporting locally for a remote run. Defaults to --output-root resolved locally."
        ),
    )
    parser.add_argument("--task", action="append", help="Restrict to one or more SkillLearnBench families.")
    parser.add_argument(
        "--link-mode",
        choices=("hardlink", "copy"),
        default="hardlink",
        help="Use hardlinks to save space when source and destination are on the same filesystem.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Remove --output-root before exporting.")
    parser.add_argument(
        "--include-solution",
        action="store_true",
        help="Also export solution/ directories. Default is false to avoid leaking oracle solutions.",
    )
    args = parser.parse_args(argv)

    source_root = Path(args.skilllearnbench_root).resolve()
    output_root = Path(args.output_root).resolve()
    manifest_root = Path(args.manifest_root) if args.manifest_root else output_root
    if args.overwrite and output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    tasks_root = output_root / "tasks"
    tasks_root.mkdir(parents=True, exist_ok=True)

    wanted = set(args.task or [])
    tasks = SkillLearnBenchTaskLoader().load(source_root)
    records: list[dict[str, Any]] = []
    for task in tasks:
        family = str(task.metadata.get("skilllearnbench_task") or task.family)
        if wanted and family not in wanted:
            continue
        instance = str(task.metadata.get("skilllearnbench_instance") or task.task_id.split("/")[-1])
        index = _instance_index(family, instance)
        source_instance = Path(str(task.context.get("instance_dir") or "")).resolve()
        if not source_instance.is_dir():
            raise SystemExit(f"Missing SkillLearnBench instance directory for {task.task_id}: {source_instance}")
        target = tasks_root / instance
        _export_instance(
            source_instance,
            target,
            link_mode=args.link_mode,
            include_solution=args.include_solution,
        )
        records.append(
            _manifest_record(
                task=task,
                family=family,
                instance=instance,
                instance_index=index,
                repo_path=manifest_root / "tasks" / instance,
            )
        )

    if not records:
        raise SystemExit("No SkillLearnBench tasks matched the requested filters.")
    records.sort(key=lambda item: str(item["task_id"]))
    train = [record for record in records if record["metadata"].get("skilllearnbench_instance_index") == 1]
    heldout = [record for record in records if int(record["metadata"].get("skilllearnbench_instance_index") or 0) >= 2]

    _write_manifest(output_root / "skillsbench_tasks.json", records)
    _write_manifest(output_root / "train_tasks.json", train)
    _write_manifest(output_root / "heldout_tasks.json", heldout)
    _write_jobs(output_root / "all_jobs.json", records)
    _write_jobs(output_root / "train_jobs.json", train)
    _write_jobs(output_root / "heldout_jobs.json", heldout)
    _write_readme(output_root, records=records, train=train, heldout=heldout, source_root=source_root)

    summary = {
        "output_root": str(output_root),
        "manifest_root": str(manifest_root),
        "num_tasks": len(records),
        "num_train": len(train),
        "num_heldout": len(heldout),
        "link_mode": args.link_mode,
        "include_solution": bool(args.include_solution),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _export_instance(source: Path, target: Path, *, link_mode: str, include_solution: bool) -> None:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    for name in ("instruction.md", "task.toml"):
        _copy_or_link_file(source / name, target / name, link_mode=link_mode)
    for name in ("environment", "tests"):
        _copy_or_link_tree(source / name, target / name, link_mode=link_mode)
    _ensure_skill_copy_sources(target / "environment")
    if include_solution and (source / "solution").exists():
        _copy_or_link_tree(source / "solution", target / "solution", link_mode=link_mode)


def _copy_or_link_tree(source: Path, target: Path, *, link_mode: str) -> None:
    if not source.exists():
        return
    for path in source.rglob("*"):
        rel = path.relative_to(source)
        out = target / rel
        if path.is_dir():
            out.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            _copy_or_link_file(path, out, link_mode=link_mode)
        elif path.is_symlink():
            out.parent.mkdir(parents=True, exist_ok=True)
            out.symlink_to(path.readlink())


def _copy_or_link_file(source: Path, target: Path, *, link_mode: str) -> None:
    if not source.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        target.unlink()
    if link_mode == "hardlink":
        try:
            os.link(source, target)
            return
        except OSError:
            pass
    shutil.copy2(source, target)


def _manifest_record(
    *,
    task,
    family: str,
    instance: str,
    instance_index: int,
    repo_path: Path,
) -> dict[str, Any]:
    metadata = dict(task.metadata)
    metadata.update(
        {
            "repo_path": str(repo_path),
            "skillsbench_task_dir": str(repo_path),
            "verifier_command": "bash tests/test.sh",
            "default_command": "bash tests/test.sh",
            "skilllearnbench_family": family,
            "skilllearnbench_instance": instance,
            "skilllearnbench_instance_index": instance_index,
            "skilllearnbench_original_task_id": task.task_id,
            "split": "train" if instance_index == 1 else "heldout",
        }
    )
    return {
        "task_id": instance,
        "family": family,
        "instruction": task.instruction,
        "acceptance_criteria": [
            "The exported SkillLearnBench task instruction is satisfied.",
            "The SkillsBench-style verifier command succeeds: `bash tests/test.sh`.",
            "Do not rely on files from solution/ or hidden oracle answers.",
        ],
        "tags": _dedupe(["skilllearnbench", *task.tags]),
        "metadata": metadata,
    }


def _ensure_skill_copy_sources(environment_dir: Path) -> None:
    dockerfile = environment_dir / "Dockerfile"
    if not dockerfile.exists():
        return
    for source in _dockerfile_copy_sources(dockerfile):
        normalized = source.rstrip("/")
        if normalized == "skills" or normalized.startswith("skills/"):
            (environment_dir / normalized).mkdir(parents=True, exist_ok=True)


def _dockerfile_copy_sources(dockerfile: Path) -> list[str]:
    sources: list[str] = []
    continued = ""
    for raw_line in dockerfile.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if continued:
            line = continued + line
            continued = ""
        if line.endswith("\\"):
            continued = line[:-1] + " "
            continue
        if not line.upper().startswith("COPY "):
            continue
        body = line[5:].strip()
        if body.startswith("["):
            try:
                values = json.loads(body)
            except json.JSONDecodeError:
                continue
            if isinstance(values, list) and len(values) >= 2:
                sources.extend(str(value) for value in values[:-1])
            continue
        try:
            parts = shlex.split(body)
        except ValueError:
            continue
        if any(part.startswith("--from=") for part in parts):
            continue
        parts = [part for part in parts if not part.startswith("--")]
        if len(parts) >= 2:
            sources.extend(parts[:-1])
    return sources


def _write_manifest(path: Path, records: list[dict[str, Any]]) -> None:
    payload = {
        "benchmark": "skilllearnbench-as-skillsbench",
        "count": len(records),
        "tasks": records,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_jobs(path: Path, records: list[dict[str, Any]]) -> None:
    jobs = [{"name": record["task_id"], "task_id": record["task_id"]} for record in records]
    path.write_text(json.dumps(jobs, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_readme(
    output_root: Path,
    *,
    records: list[dict[str, Any]],
    train: list[dict[str, Any]],
    heldout: list[dict[str, Any]],
    source_root: Path,
) -> None:
    families = sorted({str(record["family"]) for record in records})
    readme = f"""# SkillLearnBench As SkillsBench

Source: `{source_root}`

This export flattens SkillLearnBench into the same task-directory shape used by
our SkillsBench runs:

- `tasks/<family>-<index>/instruction.md`
- `tasks/<family>-<index>/environment/`
- `tasks/<family>-<index>/tests/`
- `tasks/<family>-<index>/task.toml`

No `solution/` directory is exported by default.

Primary experiment shape:

- treat every SkillLearnBench instance as an independent normal task
- run all tasks from `skillsbench_tasks.json` / `all_jobs.json`
- score only verifier Task Success (`reward >= 1`)
- do not run SkillLearnBench coverage / safety / executability LLM-judge metrics
- use `--max-heldout 0` so sibling instances are not injected as transfer context

Manifests:

- `skillsbench_tasks.json`: all `{len(records)}` instances
- `train_tasks.json`: `{len(train)}` `instance-1` tasks, compatibility only
- `heldout_tasks.json`: `{len(heldout)}` `instance-2+` tasks, compatibility only

Jobs:

- `all_jobs.json`
- `train_jobs.json`, compatibility only
- `heldout_jobs.json`, compatibility only

Use with `--manifest-kind skillsbench`, `--workspace-root <this export root>`,
and the same Docker/BenchFlow harness used for SkillsBench. These verifiers
expect the benchmark container paths such as `/tests`, `/logs`, `/app`, and
`/root`, so plain host execution of `bash tests/test.sh` is not sufficient.

Families: `{", ".join(families)}`
"""
    (output_root / "README.md").write_text(readme, encoding="utf-8")


def _instance_index(family: str, instance: str) -> int:
    match = re.fullmatch(rf"{re.escape(family)}-(\d+)", instance)
    if not match:
        raise ValueError(f"Cannot parse SkillLearnBench instance index from {instance}")
    return int(match.group(1))


def _dedupe(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item)
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
