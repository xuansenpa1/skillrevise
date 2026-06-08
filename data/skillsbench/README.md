# SkillsBench Final 86

This bundle contains the final 86-task SkillsBench-style task set used by the SkillRevise main experiments.

Layout:

- `tasks/`: materialized task directories with `instruction.md`, `task.toml`, `environment/`, and `tests/`.
- `skillsbench_tasks.json`: SkillRevise/SkillsBench-style task manifest.
- `all_jobs.json`: task ids for batch launchers.

When loading this manifest with `skillrevise`, pass `--manifest-kind skillsbench --workspace-root .` from the repository root so relative task paths resolve correctly.
