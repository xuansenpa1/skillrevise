# Bundled Benchmarks

The `data/` directory contains the final benchmark bundles used by the main
SkillRevise experiments. Each bundle is already converted to a SkillsBench-style
layout and can be loaded directly with `--manifest-kind skillsbench`.

## Bundles

| Bundle | Tasks | Manifest |
| --- | ---: | --- |
| `data/skillsbench/` | 86 | `data/skillsbench/skillsbench_tasks.json` |
| `data/swe-skills-bench/` | 70 | `data/swe-skills-bench/skillsbench_tasks.json` |
| `data/skilllearnbench/` | 50 | `data/skilllearnbench/skillsbench_tasks.json` |

## Common Layout

Each bundle contains:

- `README.md`: bundle-specific notes.
- `skillsbench_tasks.json`: manifest consumed by the SkillRevise loader.
- `all_jobs.json`: compact task-id list for batch launchers.
- `tasks/`: materialized task directories.

Each task directory is expected to contain:

- `instruction.md`: task instruction shown to the agent.
- `task.toml`: SkillsBench-style task metadata.
- `environment/`: task files, repositories, fixtures, or other inputs.
- `tests/test.sh`: verifier entrypoint.

The manifest is a JSON object with `benchmark`, `count`, and `tasks` fields.
Each task item contains a `task_id`, `family`, instruction text, acceptance
criteria, tags or context when available, and metadata. For bundled tasks,
`metadata.repo_path` is relative to the repository root so it works when commands
are run with `--workspace-root .`.

## Loading Bundles

From the repository root:

```bash
skillrevise data/skillsbench/skillsbench_tasks.json \
  --manifest-kind skillsbench \
  --workspace-root .

skillrevise data/swe-skills-bench/skillsbench_tasks.json \
  --manifest-kind skillsbench \
  --workspace-root .

skillrevise data/skilllearnbench/skillsbench_tasks.json \
  --manifest-kind skillsbench \
  --workspace-root .
```
