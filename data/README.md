# Benchmark Data

This directory contains the final benchmark bundles used by the SkillRevise
main experiments. Each bundle is already materialized into a SkillsBench-style
layout and can be loaded directly by the `skillrevise` CLI.

Bundles:

- `skillsbench/`: final 86-task SkillsBench subset.
- `swe-skills-bench/`: final 70-task SWE-Skills-Bench subset exported into SkillsBench-style task directories.
- `skilllearnbench/`: final 50-task SkillLearnBench subset exported into SkillsBench-style task directories.

Each bundle contains:

- `tasks/`: task directories with `instruction.md`, `task.toml`, `environment/`, and `tests/`.
- `skillsbench_tasks.json`: task manifest for `--manifest-kind skillsbench`.
- `all_jobs.json`: compact task id list for batch launchers.

From the repository root, load a bundle with:

```bash
skillrevise data/skillsbench/skillsbench_tasks.json --manifest-kind skillsbench --workspace-root .
```
