# SkillRevise

SkillRevise is an execution-grounded harness for improving LLM-authored agent skills. It runs a task with an initial skill, diagnoses verifier-facing failures, retrieves repair principles, revises the skill, re-executes the candidate, and keeps the best observed version under a utility gate.

This repository contains the public release code and the final benchmark bundles:

- `skillrevise/`: Python package and CLI, organized by subsystem.
  - `core/`: task/result models, execution loop, runners, metrics, artifacts, and reporting.
  - `method/`: skill authoring, diagnosis, revision, skill parsing, and principle memory.
  - `benchmarks/`: SkillsBench, SkillLearnBench, SWE/SkillsBench conversion, ALFWorld, verifier, and task-selection adapters.
  - `llm/`: command LLM client and provider wrapper used by `skillrevise-llm`.
- `scripts/`: minimal benchmark-export, task-selection, and skill-audit helpers.
- `data/`: final SkillsBench-style benchmark bundles for SkillsBench, SWE-Skills-Bench, and SkillLearnBench.
- `docs/`: release documentation for the harness, bundled benchmarks, and execution commands.
- `tests/`: unit tests for the harness and scripts.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

The core harness uses the Python standard library plus `tomli` on Python 3.9/3.10. The SWE-Skills-Bench export helper requires PyYAML.

## Documentation

- [Overview](docs/overview.md)
- [Bundled Benchmarks](docs/benchmarks.md)
- [Running SkillRevise](docs/running.md)

## Task Manifests

The generic manifest format is a JSON list of tasks:

```json
[
  {
    "task_id": "demo-task",
    "family": "swe-debug",
    "instruction": "Fix the failing workflow and validate the result.",
    "acceptance_criteria": ["The change passes the relevant check."],
    "metadata": {}
  }
]
```

The bundled `data/` directory already contains the final SkillsBench-style task bundles used in the main experiments. The CLI also supports loading external SkillsBench, SkillLearnBench, and ALFWorld manifests through `--manifest-kind`.

## Common Commands

```bash
# Baseline only
skillrevise path/to/tasks.json --baseline-only --output runs/baseline.json

# Run an LLM-backed SkillRevise episode
# Add `--principle-bank path/to/principle_bank.json` if you want to use an external bank.
skillrevise path/to/tasks.json \
  --author-mode llm-principle-bank \
  --diagnosis-mode llm \
  --revision-mode llm-principle-bank \
  --llm-command "python -m skillrevise.llm.command" \
  --output runs/llm_run.json \
  --summary-output runs/llm_summary.json \
  --max-revisions 3

# Convert a SkillsBench-style task directory into a generic manifest
skillrevise-convert-skillsbench path/to/tasks --output tasks.json

# Use a bundled final benchmark dataset
skillrevise data/skillsbench/skillsbench_tasks.json --manifest-kind skillsbench --workspace-root .

skillrevise data/swe-skills-bench/skillsbench_tasks.json --manifest-kind skillsbench --workspace-root .

skillrevise data/skilllearnbench/skillsbench_tasks.json --manifest-kind skillsbench --workspace-root .

# Audit a candidate skill bundle before publishing it separately
python scripts/audit_publishable_skills.py path/to/candidate_skills

# Use the bundled LLM wrapper directly
echo "Write a one-sentence skill." | skillrevise-llm

# Run tests
pytest
```

## Security Notes

Do not commit API keys, local configuration, SSH keys, or `.env` files. If a candidate skill bundle is published separately, run `scripts/audit_publishable_skills.py` and manually review warnings about task-specific paths, verifier files, and expected outputs.

## Citation

If you use this harness in research, please cite the SkillRevise paper:
[https://arxiv.org/abs/2606.01139](https://arxiv.org/abs/2606.01139).
