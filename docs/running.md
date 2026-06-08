# Running SkillRevise

This page gives the practical commands for using the public release. Run the
commands from the repository root unless noted otherwise.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

The core package is mostly standard-library based. Install the benchmark extra
when you need the SWE export helper:

```bash
python -m pip install -e ".[benchmarks]"
```

## Smoke Check

```bash
pytest
```

Run a baseline-only episode on one bundled task:

```bash
skillrevise data/skillsbench/skillsbench_tasks.json \
  --manifest-kind skillsbench \
  --workspace-root . \
  --baseline-only \
  --limit 1 \
  --output runs/baseline_smoke.json
```

## LLM-Backed Runs

`skillrevise` talks to LLMs through an external command. The bundled
`skillrevise-llm` command reads a prompt from stdin and writes the completion to
stdout.

Set provider credentials through environment variables. Example with a generic
OpenAI-compatible endpoint:

```bash
export SKILL_HARNESS_REVISION_LLM_PROVIDER=openai
export SKILL_HARNESS_REVISION_LLM_MODEL="<model-name>"
export SKILL_HARNESS_REVISION_LLM_API_KEY="<api-key>"
```

Then run:

```bash
skillrevise data/skillsbench/skillsbench_tasks.json \
  --manifest-kind skillsbench \
  --workspace-root . \
  --limit 1 \
  --author-mode llm-principle-bank \
  --diagnosis-mode llm \
  --revision-mode llm-principle-bank \
  --llm-command "python -m skillrevise.llm.command" \
  --output runs/llm_run.json \
  --summary-output runs/llm_summary.json \
  --max-revisions 3
```

If you have an external repair-principle bank, add:

```bash
--principle-bank path/to/principle_bank.json
```

If no external bank is provided, SkillRevise uses its built-in seed principles.

## Bundled Benchmark Commands

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

Use `--limit N` for quick checks and `--output` plus `--summary-output` for
artifact paths.

## Export And Selection Helpers

The release keeps only the helpers needed to recreate the public task bundles or
inspect publishable skill artifacts:

```bash
python scripts/export_swe_skills_bench_as_skillsbench.py path/to/SWE-Skills-Bench \
  --output-root data/swe-skills-bench \
  --manifest-root data/swe-skills-bench

python scripts/export_skilllearnbench_as_skillsbench.py path/to/SkillLearnBench \
  --output-root data/skilllearnbench \
  --manifest-root data/skilllearnbench

python scripts/select_swe_tasks.py --help
python scripts/select_skilllearnbench_tasks.py --help
python scripts/audit_publishable_skills.py path/to/candidate_skills
```

The public `data/` directory already contains the final selected and processed
benchmark bundles, so these scripts are mainly for transparency and reuse.
