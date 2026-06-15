import json
import pytest
from argparse import Namespace

from skillrevise.cli import (
    _apply_ablation_condition,
    _apply_budget_override,
    _experiment_config,
    _filter_tasks,
    _load_baseline_trace_cache,
    _resolve_utility_weights,
)
from skillrevise.core.models import TaskSpec


def make_task(task_id: str, family: str) -> TaskSpec:
    return TaskSpec(task_id=task_id, family=family, instruction="Do it", acceptance_criteria=["Pass"])


def test_filter_tasks_by_id_family_and_limit() -> None:
    tasks = [make_task("a", "f1"), make_task("b", "f1"), make_task("c", "f2")]

    selected = _filter_tasks(tasks, task_ids=["a", "b"], families=["f1"], limit=1)

    assert [task.task_id for task in selected] == ["a"]


def test_filter_tasks_errors_when_empty() -> None:
    with pytest.raises(SystemExit, match="No tasks selected"):
        _filter_tasks([make_task("a", "f1")], task_ids=["missing"])


def test_apply_budget_override_updates_task_metadata() -> None:
    task = make_task("a", "f1")

    [updated] = _apply_budget_override([task], 120)

    assert updated.metadata["timeout_seconds"] == 120
    assert updated.metadata["budget_seconds"] == 120
    assert task.metadata == {}


def test_resolve_utility_weights_applies_overrides() -> None:
    args = Namespace(
        utility_preset="success-only",
        utility_alpha=None,
        utility_beta=0.2,
        utility_gamma=0.3,
        utility_lambda=0.4,
    )

    weights = _resolve_utility_weights(args)

    assert weights.alpha == 1.0
    assert weights.beta == 0.2
    assert weights.gamma == 0.3
    assert weights.lam == 0.4


def test_experiment_config_prefers_principle_bank_names() -> None:
    args = Namespace(
        utility_preset="success-only",
        max_revisions=1,
        max_heldout=2,
        budget_seconds=None,
        repeat=1,
        author_mode="llm-principle-bank",
        diagnosis_mode="heuristic",
        revision_mode="llm-principle-bank",
        principle_bank="principles.json",
        principle_limit=4,
        enable_principle_absorption=True,
        principle_bank_output="updated.json",
        baseline_only=False,
        baseline_run=None,
        strict_llm=False,
        initial_skill=None,
    )
    weights = Namespace(alpha=1.0, beta=0.0, gamma=0.0, lam=0.0)

    config = _experiment_config(args, weights)

    assert config["principle_bank"] == "principles.json"
    assert config["principle_limit"] == 4
    assert config["enable_principle_absorption"] is True
    assert config["principle_bank_output"] == "updated.json"
    assert config["initial_skill"] is None


def test_experiment_config_uses_default_principle_limit() -> None:
    args = Namespace(
        utility_preset="success-only",
        max_revisions=1,
        max_heldout=None,
        budget_seconds=None,
        repeat=1,
        author_mode="llm-principle-bank",
        diagnosis_mode="heuristic",
        revision_mode="llm-principle-bank",
        principle_bank=None,
        principle_limit=None,
        enable_principle_absorption=False,
        principle_bank_output=None,
        baseline_only=False,
        baseline_run=None,
        strict_llm=False,
        initial_skill="skill_v0.md",
    )
    weights = Namespace(alpha=1.0, beta=0.0, gamma=0.0, lam=0.0)

    config = _experiment_config(args, weights)

    assert config["principle_bank"] is None
    assert config["principle_limit"] == 4
    assert config["initial_skill"] == "skill_v0.md"


def test_apply_ablation_condition_sets_factorial_flags() -> None:
    args = Namespace(
        ablation_condition="no-principle-memory-no-diagnosis",
        disable_principle_memory=False,
        diagnosis_mode="heuristic",
    )

    _apply_ablation_condition(args)

    assert args.disable_principle_memory is True
    assert args.diagnosis_mode == "none"


def test_experiment_config_records_ablation_flags() -> None:
    args = Namespace(
        ablation_condition="no-principle-memory",
        utility_preset="success-only",
        max_revisions=3,
        max_heldout=None,
        budget_seconds=None,
        repeat=1,
        author_mode="llm-principle-bank",
        diagnosis_mode="heuristic",
        revision_mode="llm-principle-bank",
        revision_ablation="no-execution-anchors",
        disable_principle_memory=True,
        principle_bank="principles.json",
        principle_limit=3,
        enable_principle_absorption=True,
        principle_bank_output=None,
        baseline_only=False,
        baseline_run=None,
        strict_llm=False,
        initial_skill=None,
    )
    weights = Namespace(alpha=1.0, beta=0.0, gamma=0.0, lam=0.0)

    config = _experiment_config(args, weights)

    assert config["ablation_condition"] == "no-principle-memory"
    assert config["revision_ablation"] == "no-execution-anchors"
    assert config["revision_removed_mechanism"] == "execution anchors"
    assert config["diagnosis_enabled"] is True
    assert config["principle_memory_enabled"] is False


def test_load_baseline_trace_cache_reuses_no_skill_traces(tmp_path) -> None:
    path = tmp_path / "baseline.json"
    path.write_text(
        json.dumps(
            {
                "baseline_results": [
                    {
                        "task": {"task_id": "task-a"},
                        "no_skill": {
                            "run_id": "run-a",
                            "task_id": "task-a",
                            "skill_version": None,
                            "success": False,
                            "status": "failed",
                            "started_at": "start",
                            "ended_at": "end",
                            "tokens": 12,
                            "tool_calls": 3,
                            "steps": 4,
                            "latency_seconds": 5.5,
                            "outcome_summary": "reward 0.5",
                            "events": [{"step_index": 1, "kind": "tool", "summary": "ran"}],
                            "metadata": {"reward": 0.5},
                        },
                    }
                ]
            }
        )
    )

    traces = _load_baseline_trace_cache(path)

    assert traces["task-a"].tokens == 12
    assert traces["task-a"].metadata["reward"] == 0.5
    assert traces["task-a"].events[0].kind == "tool"
