from __future__ import annotations


# Artifact persistence

from pathlib import Path

from skillrevise.core.artifacts import ArtifactStore
from skillrevise.core.models import ExecutionTrace, Skill, TaskSpec, TrajectoryEvent


def test_artifact_store_writes_task_skill_and_trace(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    assert store.root.is_absolute()

    run_dir = store.start_run("task-x", "v0")
    task = TaskSpec(task_id="task-x", family="demo", instruction="Do X", acceptance_criteria=["Pass"])
    skill = Skill(
        name="Demo",
        purpose="Purpose",
        when_to_use="When",
        procedure=["Step 1"],
        constraints=["Constraint 1"],
    )
    trace = ExecutionTrace(
        run_id="run-1",
        task_id="task-x",
        skill_version="v0",
        success=True,
        status="success",
        started_at="t0",
        ended_at="t1",
        tokens=10,
        tool_calls=1,
        steps=1,
        latency_seconds=0.2,
        outcome_summary="ok",
        events=[TrajectoryEvent(step_index=1, kind="demo", summary="ok")],
    )

    task_path = store.write_task(task, run_dir)
    skill_path = store.write_skill(skill, run_dir)
    trace_path = store.write_trace(trace, run_dir)

    assert task_path.exists()
    assert skill_path.exists()
    assert trace_path.exists()


# Utility metrics

import pytest

from skillrevise.core.metrics import UtilityWeights, compute_utility, utility_weights_for_preset
from skillrevise.core.models import ExecutionTrace


def make_trace(*, success: bool, reward: float | None | str = "missing", latency_seconds: float = 10.0) -> ExecutionTrace:
    metadata = {} if reward == "missing" else {"reward": reward}
    return ExecutionTrace(
        run_id="run",
        task_id="task",
        skill_version=None,
        success=success,
        status="success" if success else "failure",
        started_at="2026-05-04T00:00:00Z",
        ended_at="2026-05-04T00:00:01Z",
        tokens=100,
        tool_calls=4,
        steps=8,
        latency_seconds=latency_seconds,
        outcome_summary="ok",
        metadata=metadata,
    )


def test_utility_weight_presets_are_independent_copies() -> None:
    first = utility_weights_for_preset("success-only")
    second = utility_weights_for_preset("success-only")

    assert first == UtilityWeights(alpha=1.0, beta=0.0, gamma=0.0, lam=0.0)
    assert first is not second


def test_utility_weight_preset_rejects_unknown_name() -> None:
    with pytest.raises(ValueError, match="Unknown utility preset"):
        utility_weights_for_preset("missing")


def test_compute_utility_uses_continuous_reward_when_present() -> None:
    no_skill = make_trace(success=False, reward=0.25)
    with_skill = make_trace(success=False, reward=0.75)

    utility = compute_utility(no_skill, with_skill, weights=UtilityWeights(beta=0.0))

    assert utility.success_gain == 0.5
    assert utility.overall_score == 0.5


def test_compute_utility_skips_invalid_benchmark_runs() -> None:
    no_skill = make_trace(success=False, reward=None, latency_seconds=10.0)
    with_skill = make_trace(success=False, reward=None, latency_seconds=1.0)

    utility = compute_utility(no_skill, with_skill)

    assert utility.overall_score == 0.0
    assert utility.efficiency_gain == 0.0
    assert "no valid benchmark reward" in utility.notes[0]


# Reporting summaries

from skillrevise.core.agents import MockAgentAdapter
from skillrevise.method.authoring import TemplateSkillAuthor
from skillrevise.method.diagnosis import HeuristicDiagnoser
from skillrevise.core.loop import HarnessLoop
from skillrevise.core.models import ExecutionTrace, TaskSpec
from skillrevise.core.reporting import summarize_baseline_runs, summarize_results
from skillrevise.method.revision import HeuristicRevisionEngine
from skillrevise.core.runner import PairedRunner


def make_task(task_id: str, path: str, command: str) -> TaskSpec:
    return TaskSpec(
        task_id=task_id,
        family="swe-debug",
        instruction="Fix the failing validation flow without assuming fixed paths.",
        acceptance_criteria=["Verifier passes.", "Use fallback when the first checker is unavailable."],
        metadata={
            "base_success": 0.62,
            "success_threshold": 0.6,
            "base_tokens": 1800,
            "base_steps": 12,
            "base_tool_calls": 7,
            "base_latency_seconds": 20.0,
            "requires_validation": True,
            "default_path": path,
            "default_command": command,
            "skill_keywords": ["verify", "repository-native", "fallback", "smallest reliable checker"],
            "anti_patterns": [path, command],
        },
    )


def build_loop() -> HarnessLoop:
    return HarnessLoop(
        author=TemplateSkillAuthor(),
        runner=PairedRunner(MockAgentAdapter()),
        diagnoser=HeuristicDiagnoser(),
        reviser=HeuristicRevisionEngine(),
        max_revisions=1,
    )


def test_summarize_results_builds_main_transfer_and_failure_tables() -> None:
    source = make_task("source", "tests/unit/test_math.py", "pytest -q tests/unit/test_math.py")
    sibling = make_task("sibling", "ci/test_pipeline.py", "pytest -q ci/test_pipeline.py")

    result = build_loop().run_task(source, heldout_tasks=[sibling])
    summary = summarize_results([result])

    assert summary["num_tasks"] == 1
    assert summary["main_table"]["selected_skill"]["success_rate"] == 1.0
    assert summary["main_table"]["revision_delta"]["overall_score"] > 0.0
    assert summary["transfer_table"]["selected_skill"]["num_evaluated"] == 1.0
    assert summary["failure_taxonomy_table"]["initial"]["environment_mismatch"] >= 1
    assert summary["selection_table"]["changed_by_revision"] == 1
    assert summary["selection_table"]["accepted_skills"] == 1
    assert summary["selection_table"]["rejected_skills"] == 0
    assert summary["family_table"][0]["family"] == "swe-debug"
    assert summary["per_task"][0]["selected_version"] == "v1"
    assert summary["per_task"][0]["skill_accepted"] is True
    assert summary["per_task"][0]["selected_outcome_score"] == 1.0


def test_summarize_baseline_runs_reports_no_skill_scores() -> None:
    task = make_task("source", "tests/unit/test_math.py", "pytest -q tests/unit/test_math.py")
    trace = ExecutionTrace(
        run_id="run",
        task_id=task.task_id,
        skill_version=None,
        success=False,
        status="failure",
        started_at="2026-05-04T00:00:00Z",
        ended_at="2026-05-04T00:00:01Z",
        tokens=10,
        tool_calls=2,
        steps=3,
        latency_seconds=4.0,
        outcome_summary="partial",
        metadata={"reward": 0.5},
    )

    summary = summarize_baseline_runs([(task, trace)])

    assert summary["baseline_table"]["outcome_score"] == 0.5
    assert summary["per_task"][0]["outcome_score"] == 0.5
    assert summary["per_task"][0]["success"] is False
