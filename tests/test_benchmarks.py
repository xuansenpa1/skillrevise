from __future__ import annotations


# ALFWorld loader

import json
from pathlib import Path

from skillrevise.benchmarks.alfworld import ALFWorldTaskLoader


def write_problem(root: Path, split: str, scenario: str, trial: str, instruction: str) -> Path:
    problem = root / "json_2.1.1" / split / scenario / trial
    problem.mkdir(parents=True)
    (problem / "traj_data.json").write_text(
        json.dumps({"turk_annotations": {"anns": [{"task_desc": instruction}]}})
    )
    (problem / "initial_state.pddl").write_text("(problem)")
    (problem / "game.tw-pddl").write_text("(game)")
    return problem


def test_alfworld_loader_loads_split(tmp_path: Path) -> None:
    (tmp_path / "logic").mkdir()
    (tmp_path / "logic" / "alfred.pddl").write_text("(domain)")
    problem = write_problem(
        tmp_path,
        "train",
        "pick_and_place_simple-Apple-None-Table-1",
        "trial_001",
        "put an apple on the table",
    )

    [task] = ALFWorldTaskLoader(tmp_path).load("train")

    assert task.task_id == "train__pick_and_place_simple-Apple-None-Table-1__trial_001"
    assert task.family == "pick_and_place_simple"
    assert task.instruction == "put an apple on the table"
    assert task.metadata["benchmark"] == "alfworld"
    assert task.metadata["problem_path"] == str(problem.resolve())
    assert task.context["split"] == "train"


def test_alfworld_loader_accepts_manifest_records(tmp_path: Path) -> None:
    (tmp_path / "logic").mkdir()
    (tmp_path / "logic" / "alfred.pddl").write_text("(domain)")
    problem = write_problem(
        tmp_path,
        "valid_seen",
        "look_at_obj_in_light-Book-None-DeskLamp-2",
        "trial_002",
        "look at a book under a lamp",
    )
    manifest = tmp_path / "tasks.json"
    manifest.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "task_id": "custom-task",
                        "problem_path": str(problem),
                        "family": "custom-family",
                        "instruction": "Override instruction.",
                    }
                ]
            }
        )
    )

    [task] = ALFWorldTaskLoader(tmp_path).load(manifest)

    assert task.task_id == "custom-task"
    assert task.family == "custom-family"
    assert task.instruction == "Override instruction."
    assert task.metadata["split"] == "valid_seen"


# SkillsBench loader and splits

from skillrevise.benchmarks.skillsbench import SkillsBenchTaskLoader, build_family_index, family_coverage, select_sibling_tasks


def test_skillsbench_loader_normalizes_common_fields(tmp_path: Path) -> None:
    repo_root = tmp_path / "repos"
    repo_root.mkdir()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "id": "task-a",
                    "subdomain": "python-ci",
                    "requirement": "Fix the CI failure.",
                    "acceptance": "Verifier passes.",
                    "repo_path": "repos/demo-repo",
                    "commit": "abc123",
                }
            ]
        )
    )

    tasks = SkillsBenchTaskLoader(tmp_path).load(manifest)
    assert len(tasks) == 1
    task = tasks[0]
    assert task.task_id == "task-a"
    assert task.family == "python-ci"
    assert task.instruction == "Fix the CI failure."
    assert task.acceptance_criteria == ["Verifier passes."]
    assert task.metadata["repo_path"] == str((tmp_path / "repos" / "demo-repo").resolve())
    assert task.metadata["commit"] == "abc123"


def test_family_index_and_sibling_selection_are_stable(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            [
                {"task_id": "a", "family": "f1", "instruction": "A", "acceptance_criteria": []},
                {"task_id": "b", "family": "f1", "instruction": "B", "acceptance_criteria": []},
                {"task_id": "c", "family": "f2", "instruction": "C", "acceptance_criteria": []},
            ]
        )
    )
    tasks = SkillsBenchTaskLoader().load(manifest)
    families = build_family_index(tasks)
    coverage = family_coverage(tasks)

    assert coverage == {"f1": 2, "f2": 1}
    siblings = select_sibling_tasks(tasks[0], families)
    assert [item.task_id for item in siblings] == ["b"]


# SkillsBench conversion

import json
from pathlib import Path

import pytest

from skillrevise.benchmarks.convert_skillsbench import load_skillsbench_task_directories, normalize_tasks


def test_normalize_tasks_applies_defaults_and_resolves_repo_path(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    manifest = tmp_path / "skillsbench.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "id": "sb-1",
                    "subdomain": "python-ci",
                    "prompt": "Fix the failing tests.",
                    "acceptance": "pytest passes",
                    "repo_path": "repos/project-a",
                }
            ]
        )
    )

    tasks = normalize_tasks(
        manifest,
        workspace_root=workspace,
        default_verifier_command="pytest -q",
        default_timeout_seconds=1200,
        strict=True,
    )

    assert len(tasks) == 1
    assert tasks[0].task_id == "sb-1"
    assert tasks[0].family == "python-ci"
    assert tasks[0].instruction == "Fix the failing tests."
    assert tasks[0].acceptance_criteria == ["pytest passes"]
    assert tasks[0].metadata["repo_path"] == str((workspace / "repos" / "project-a").resolve())
    assert tasks[0].metadata["verifier_command"] == "pytest -q"
    assert tasks[0].metadata["timeout_seconds"] == 1200


def test_normalize_tasks_strict_mode_reports_missing_experiment_fields(tmp_path: Path) -> None:
    manifest = tmp_path / "skillsbench.jsonl"
    manifest.write_text('{"id": "bad", "prompt": "Do something."}\n')

    with pytest.raises(ValueError, match="missing metadata.repo_path"):
        normalize_tasks(manifest, strict=True)


def test_load_skillsbench_task_directories_converts_repo_layout(tmp_path: Path) -> None:
    task_dir = tmp_path / "skillsbench" / "tasks" / "demo-task"
    tests_dir = task_dir / "tests"
    tests_dir.mkdir(parents=True)
    (task_dir / "instruction.md").write_text("Create the expected output file.")
    (tests_dir / "test.sh").write_text("#!/bin/bash\npytest /tests/test_outputs.py\n")
    (tests_dir / "test_outputs.py").write_text("def test_ok():\n    assert True\n")
    (task_dir / "task.toml").write_text(
        """
version = "1.0"

[metadata]
difficulty = "medium"
category = "software"
tags = ["python", "testing"]

[verifier]
timeout_sec = 900.0

[agent]
timeout_sec = 600.0
"""
    )

    tasks = load_skillsbench_task_directories(tmp_path / "skillsbench")

    assert len(tasks) == 1
    assert tasks[0].task_id == "demo-task"
    assert tasks[0].family == "software"
    assert tasks[0].instruction == "Create the expected output file."
    assert tasks[0].tags == ["python", "testing"]
    assert tasks[0].metadata["repo_path"] == str(task_dir.resolve())
    assert tasks[0].metadata["verifier_command"] == "bash tests/test.sh"
    assert tasks[0].metadata["timeout_seconds"] == 900
    assert "tests/test_outputs.py" in tasks[0].acceptance_criteria[-1]


# SkillsBench adapter

import sys
from pathlib import Path

from skillrevise.core.artifacts import ArtifactStore
from skillrevise.core.models import TaskSpec, TrajectoryEvent
from skillrevise.benchmarks.skillsbench_adapter import (
    CommandAgentHarness,
    HarnessExecution,
    SkillsBenchAgentAdapter,
    _bypass_proxy_enabled,
    _without_proxy_env,
)
from skillrevise.benchmarks.verifier import VerifierResult


class FakeHarness:
    def execute(self, task, workspace, skill_path, run_dir):
        assert workspace.exists()
        if skill_path is not None:
            assert skill_path.exists()
        return HarnessExecution(
            status="success",
            tokens=123,
            tool_calls=4,
            steps=5,
            latency_seconds=1.5,
            outcome_summary="harness ok",
            events=[TrajectoryEvent(step_index=1, kind="tool", summary="ran tool")],
            metadata={"source": "fake"},
            stdout="hello",
            stderr="",
        )


class FakeVerifier:
    def verify(self, workspace, task):
        return VerifierResult(success=True, summary="verified", exit_code=0)


class FakeBenchFlowHarness:
    def execute(self, task, workspace, skill_path, run_dir):
        return HarnessExecution(
            status="failure",
            tokens=10,
            tool_calls=2,
            steps=3,
            latency_seconds=1.0,
            outcome_summary="BenchFlow failed; reward=0.0",
            events=[TrajectoryEvent(step_index=1, kind="verifier", summary="FAILED scan_rnn")],
            metadata={"reward": 0.0, "result_path": str(run_dir / "result.json")},
            stdout="",
            stderr="",
        )


def test_skillsbench_adapter_materializes_workspace_and_writes_artifacts(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("demo")

    adapter = SkillsBenchAgentAdapter(
        harness=FakeHarness(),
        artifact_store=ArtifactStore(tmp_path / "artifacts"),
        verifier=FakeVerifier(),
    )
    task = TaskSpec(
        task_id="task-y",
        family="demo",
        instruction="Do Y",
        acceptance_criteria=["Pass"],
        metadata={"repo_path": str(repo)},
    )

    trace = adapter.run(task, None)
    assert trace.success is True
    assert trace.tokens == 123
    assert any(event.kind == "verifier" for event in trace.events)


def test_skillsbench_adapter_can_disable_separate_verifier(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("demo")

    adapter = SkillsBenchAgentAdapter(
        harness=FakeHarness(),
        artifact_store=ArtifactStore(tmp_path / "artifacts"),
        verifier=FakeVerifier(),
        disable_verifier=True,
    )
    task = TaskSpec(
        task_id="task-no-verifier",
        family="demo",
        instruction="Do Y",
        acceptance_criteria=["Pass"],
        metadata={"repo_path": str(repo)},
    )

    trace = adapter.run(task, None)
    assert trace.success is True
    assert not any(event.kind == "verifier" for event in trace.events)


def test_skillsbench_adapter_skips_local_verifier_when_harness_returns_reward(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("demo")

    adapter = SkillsBenchAgentAdapter(
        harness=FakeBenchFlowHarness(),
        artifact_store=ArtifactStore(tmp_path / "artifacts"),
        verifier=FakeVerifier(),
    )
    task = TaskSpec(
        task_id="task-benchflow",
        family="demo",
        instruction="Do Y",
        acceptance_criteria=["Pass"],
        metadata={"repo_path": str(repo)},
    )

    trace = adapter.run(task, None)

    assert trace.success is False
    assert trace.metadata["reward"] == 0.0
    assert len([event for event in trace.events if event.kind == "verifier"]) == 1


def test_command_agent_harness_returns_timeout_execution(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    harness = CommandAgentHarness(
        [
            sys.executable,
            "-c",
            "import time; print('starting harness', flush=True); time.sleep(3)",
        ],
        env={
            "SKILL_REVISE_TIMEOUT_GRACE_SECONDS": "0",
            "SKILL_REVISE_OUTER_TIMEOUT_EXTRA_SECONDS": "0",
        },
    )
    task = TaskSpec(
        task_id="timeout-task",
        family="demo",
        instruction="Do Y",
        acceptance_criteria=["Pass"],
        metadata={"timeout_seconds": 1},
    )

    execution = harness.execute(task, workspace, None, run_dir)

    assert execution.status == "timeout"
    assert execution.metadata["timed_out"] is True
    assert execution.metadata["outer_timeout_seconds"] == 1
    assert "Harness timed out after 1 seconds." in execution.outcome_summary


def test_proxy_bypass_strips_proxy_environment() -> None:
    env = {
        "SKILL_REVISE_BYPASS_PROXY": "1",
        "HTTPS_PROXY": "http://proxy.example",
        "http_proxy": "http://proxy.example",
        "OPENAI_API_KEY": "keep",
    }

    cleaned = _without_proxy_env(env)

    assert _bypass_proxy_enabled(env)
    assert "HTTPS_PROXY" not in cleaned
    assert "http_proxy" not in cleaned
    assert cleaned["OPENAI_API_KEY"] == "keep"
    assert cleaned["SKILL_REVISE_BYPASS_PROXY"] == "1"
