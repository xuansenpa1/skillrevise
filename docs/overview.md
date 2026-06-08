# SkillRevise Overview

SkillRevise is an execution-grounded framework for improving cold-start LLM-authored agent skills. A skill is treated as a procedural artifact that must be tested against the same environment and verifier where it will be used. The framework revises an initial skill from execution evidence, then keeps the best observed version under measured utility.

## Problem Setting

Agent skills describe reusable workflows, constraints, validation steps, and recovery strategies. In cold-start settings, the available skill is often written by an expert or generated once by an LLM. Such skills may look well formed while still being behaviorally weak: they may miss local setup steps, over-assume file paths, skip validation, or fail to preserve already-correct behavior.

SkillRevise addresses this gap by revising the skill artifact itself, rather than only retrying a single answer or accumulating a large history of prior trajectories.

## Method Components

SkillRevise uses three main components.

**Diagnosis** converts execution evidence into repair constraints. It records verifier-facing requirements, failure attribution, and preservation constraints so the revision knows what failed and what should not regress.

**Principle Memory** stores reusable repair principles. A principle describes when a repair pattern applies, what defect it addresses, what behavior the skill should induce, how to verify the repair, and when the pattern should not transfer.

**Revision Operator** edits the current skill using the diagnosis and selected principles. Revisions are execution-anchored: each meaningful text edit should induce a concrete action, inspection, validation, or fallback in the next run.

## Revision Loop

The bounded revision episode follows this flow:

1. Load a task manifest and materialize each task into a `TaskSpec`.
2. Create or load an initial skill.
3. Execute the task with the current skill.
4. Diagnose verifier-facing failures from the trajectory and result evidence.
5. Retrieve and bind relevant repair principles.
6. Generate an anchored candidate revision.
7. Re-execute the candidate on the same task.
8. Select the best observed skill by utility, not by generation order.

The standard paper setting uses a revision budget of three rounds. Larger budgets expand the candidate pool, while the utility gate acts as a rollback mechanism when later revisions are worse.

## Package Layout

- `skillrevise/core/`: task/result models, agents, execution loop, metrics, artifact I/O, and run reporting.
- `skillrevise/method/`: skill authoring, diagnosis, revision, principle retrieval, and skill parsing.
- `skillrevise/benchmarks/`: SkillsBench-style loaders, SkillLearnBench and SWE export support, ALFWorld loading, verifier helpers, and task selection.
- `skillrevise/llm/`: command-based LLM client and provider wrappers for OpenAI-compatible, OpenRouter, Anthropic, and Ollama-style endpoints.
- `scripts/`: release helpers for exporting benchmark data, selecting tasks, and auditing candidate skill bundles.
- `data/`: final public benchmark bundles in SkillsBench-style layout.

## Paper Link

Paper: [SkillRevise: Improving LLM-Authored Agent Skills via Trace-Conditioned Skill Revision](https://arxiv.org/abs/2606.01139)
