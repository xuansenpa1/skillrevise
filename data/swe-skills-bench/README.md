# SWE-Skills-Bench Final 70

This bundle contains the final 70-task SWE-Skills-Bench subset used by the
SkillRevise main experiments, exported into SkillsBench-style task directories.

Layout:

- `tasks/`: materialized task directories with `instruction.md`, `task.toml`, `environment/`, and `tests/`.
- `skillsbench_tasks.json`: SkillRevise/SkillsBench-style task manifest.
- `all_jobs.json`: task ids for batch launchers.

Each task directory contains a Dockerfile based on the original SWE-Skills-Bench
base image and repo commit, plus `tests/test.sh`, which runs the original
build/unit-test verifier and writes `/logs/verifier/reward.txt`.

When loading this manifest with `skillrevise`, pass `--manifest-kind skillsbench
--workspace-root .` from the repository root so relative task paths resolve
correctly.
