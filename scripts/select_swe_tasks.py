#!/usr/bin/env python3
"""Materialize a selected SWE-Skills-Bench subset from an exported manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from skillrevise.benchmarks.task_selection import normalize_swe_task_id, select_tasks


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read a SWE task selection file and filter a full "
            "SWE-Skills-Bench-as-SkillsBench export into selected tasks/jobs."
        )
    )
    parser.add_argument("export_root", help="Root produced by export_swe_skills_bench_as_skillsbench.py.")
    parser.add_argument("--selection", required=True, help="Task selection file. Text or JSON is supported.")
    parser.add_argument("--name", help="Selection name. Defaults to the selection filename stem.")
    parser.add_argument("--output-root", help="Directory for selected manifest/jobs. Defaults to export_root.")
    parser.add_argument("--tasks-manifest", help="Full tasks manifest. Defaults to export_root/swe_skillsbench_tasks.json.")
    parser.add_argument("--jobs", help="Full jobs JSON. Defaults to export_root/all_jobs.json.")
    parser.add_argument("--tasks-output", help="Selected tasks manifest path.")
    parser.add_argument("--jobs-output", help="Selected jobs JSON path.")
    parser.add_argument("--allow-missing", action="store_true", help="Skip selected ids missing from tasks or jobs.")
    args = parser.parse_args(argv)

    export_root = Path(args.export_root).resolve()
    selection_path = Path(args.selection).resolve()
    selection_name = args.name or selection_path.stem
    output_root = Path(args.output_root).resolve() if args.output_root else export_root
    tasks_manifest = Path(args.tasks_manifest).resolve() if args.tasks_manifest else export_root / "swe_skillsbench_tasks.json"
    jobs_path = Path(args.jobs).resolve() if args.jobs else export_root / "all_jobs.json"
    tasks_output = Path(args.tasks_output).resolve() if args.tasks_output else output_root / f"{selection_name}_tasks.json"
    jobs_output = Path(args.jobs_output).resolve() if args.jobs_output else output_root / f"{selection_name}_jobs.json"

    summary = select_tasks(
        manifest_path=tasks_manifest,
        jobs_path=jobs_path,
        selection_path=selection_path,
        tasks_output=tasks_output,
        jobs_output=jobs_output,
        benchmark_name=f"swe-skills-bench-as-skillsbench-{selection_name}",
        selection_name=selection_name,
        normalizer=normalize_swe_task_id,
        allow_missing=args.allow_missing,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
