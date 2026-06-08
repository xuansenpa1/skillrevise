# SkillRevise Overview

SkillRevise is an execution-grounded harness for improving LLM-authored agent
skills. A skill is treated as an executable artifact: it is authored, used on a
task, judged by verifier-facing evidence, revised from the failure signal, and
accepted only when the observed utility improves.

## Revision Loop

The default loop has these stages:

1. Load a task manifest and materialize each task into a `TaskSpec`.
2. Create an initial skill from a template, a prior skill, an LLM author, or a
   user-provided Markdown file.
3. Run the task through an agent backend or benchmark adapter.
4. Diagnose verifier-facing failures from the execution trace.
5. Retrieve optional repair principles from an in-memory seed bank or an
   external principle-bank JSON.
6. Revise the skill with a heuristic or LLM-backed revision engine.
7. Re-run the candidate and compare it with the best observed version.
8. Keep the candidate only if the utility gate accepts it, then write run and
   summary artifacts.

This structure separates skill generation from evaluation so the same loop can
work across benchmark adapters and task families.

## Package Layout

- `skillrevise/core/`: task/result models, agents, execution loop, metrics,
  artifact I/O, and run reporting.
- `skillrevise/method/`: skill authoring, diagnosis, revision, principle
  retrieval, and skill parsing.
- `skillrevise/benchmarks/`: SkillsBench-style loaders, SkillLearnBench and
  SWE export support, ALFWorld loading, verifier helpers, and task selection.
- `skillrevise/llm/`: command-based LLM client and a small provider wrapper for
  OpenAI-compatible, OpenRouter, Anthropic, and Ollama-style endpoints.
- `scripts/`: release-oriented helpers for exporting benchmark data, selecting
  tasks, and auditing candidate skill bundles.
- `data/`: the final public benchmark bundles in SkillsBench-style layout.
