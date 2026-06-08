from __future__ import annotations


# Revision loop behavior

from skillrevise.core.agents import MockAgentAdapter
from skillrevise.method.authoring import TemplateSkillAuthor
from skillrevise.method.diagnosis import HeuristicDiagnoser, NoOpDiagnoser
from skillrevise.core.loop import HarnessLoop
from skillrevise.core.models import (
    DiagnosisEvidence,
    DiagnosisReport,
    ExecutionTrace,
    FailureType,
    PairedEvaluation,
    RevisionCandidate,
    Skill,
    TaskSpec,
    TrajectoryEvent,
    UtilityBreakdown,
)
from skillrevise.method.principles import PrincipleAbsorber, PrincipleBank
from skillrevise.method.revision import HeuristicRevisionEngine
from skillrevise.core.runner import PairedRunner


def make_task(task_id: str, default_path: str, default_command: str) -> TaskSpec:
    return TaskSpec(
        task_id=task_id,
        family="swe-debug",
        instruction="Fix the failure using repository-native validation and fallback logic.",
        acceptance_criteria=["Use validation and fallback."],
        metadata={
            "base_success": 0.62,
            "success_threshold": 0.6,
            "base_tokens": 1800,
            "base_steps": 12,
            "base_tool_calls": 7,
            "base_latency_seconds": 20.0,
            "requires_validation": True,
            "default_path": default_path,
            "default_command": default_command,
            "skill_keywords": ["verify", "repository-native", "fallback", "smallest reliable checker"],
            "anti_patterns": [default_path, default_command],
        },
    )


def build_loop(max_revisions: int = 1) -> HarnessLoop:
    return HarnessLoop(
        author=TemplateSkillAuthor(),
        runner=PairedRunner(MockAgentAdapter()),
        diagnoser=HeuristicDiagnoser(),
        reviser=HeuristicRevisionEngine(),
        max_revisions=max_revisions,
    )


def test_revision_loop_selects_revised_skill_when_direct_skill_regresses() -> None:
    task = make_task("t0", "tests/unit/test_math.py", "pytest -q tests/unit/test_math.py")
    result = build_loop().run_task(task)

    assert result.initial_skill.version == "v0"
    assert result.selected_skill.version == "v1"
    assert result.selected_evaluation.with_skill.success is True
    assert result.selected_evaluation.utility.overall_score > result.iterations[0].evaluation.utility.overall_score
    assert "Do not assume a fixed path" in result.selected_skill.constraints[0]


def test_revision_loop_can_absorb_accepted_repair_principle() -> None:
    task = make_task("absorb", "tests/unit/test_math.py", "pytest -q tests/unit/test_math.py")
    task.metadata["success_threshold"] = 0.9
    bank = PrincipleBank([])
    loop = HarnessLoop(
        author=TemplateSkillAuthor(),
        runner=PairedRunner(MockAgentAdapter()),
        diagnoser=HeuristicDiagnoser(),
        reviser=HeuristicRevisionEngine(),
        max_revisions=1,
        principle_absorber=PrincipleAbsorber(bank),
    )

    result = loop.run_task(task)

    assert result.selected_skill.version == "v1"
    assert loop.absorbed_principles
    assert bank.principles == loop.absorbed_principles
    assert loop.absorbed_principles[0].acceptance_evidence


class EvidenceDiagnoser:
    def diagnose(self, task, skill, evaluation):
        return DiagnosisReport(
            labels=[FailureType.WRONG_ABSTRACTION_LEVEL],
            evidence=[
                DiagnosisEvidence(
                    source="verifier",
                    snippet="partial reward with missing graph constraints",
                    reason="The skill missed a verifier-visible graph constraint.",
                )
            ],
            causal_judgment="The skill partially solves the task but regresses against no-skill.",
            rewrite_targets=["Tighten verifier-visible graph checks."],
            summary="Partial repair evidence.",
        )


class BaselineRegressionAdapter:
    def run(self, task: TaskSpec, skill: Skill | None) -> ExecutionTrace:
        reward = 0.833
        tokens = 1000
        tool_calls = 6
        steps = 12
        latency = 10.0
        if skill is not None and skill.version == "v0":
            reward = 0.667
            tokens = 2500
            tool_calls = 12
            steps = 28
            latency = 100.0
        elif skill is not None:
            reward = 0.667
            tokens = 1400
            tool_calls = 8
            steps = 16
            latency = 30.0
        return ExecutionTrace(
            run_id="baseline-regression",
            task_id=task.task_id,
            skill_version=None if skill is None else skill.version,
            success=False,
            status="failure",
            started_at="2026-05-14T00:00:00Z",
            ended_at="2026-05-14T00:00:01Z",
            tokens=tokens,
            tool_calls=tool_calls,
            steps=steps,
            latency_seconds=latency,
            outcome_summary=f"reward={reward}",
            metadata={"reward": reward},
        )


def test_absorption_blocks_revision_that_still_regresses_against_no_skill() -> None:
    task = make_task("regression", "tests/test.py", "pytest")
    bank = PrincipleBank([])
    loop = HarnessLoop(
        author=TemplateSkillAuthor(),
        runner=PairedRunner(BaselineRegressionAdapter()),
        diagnoser=EvidenceDiagnoser(),
        reviser=FixedReviser(),
        max_revisions=1,
        principle_absorber=PrincipleAbsorber(bank),
    )

    result = loop.run_task(task)

    assert result.selected_skill.version == "v1"
    assert result.selected_evaluation.utility.overall_score > result.iterations[0].evaluation.utility.overall_score
    assert result.selected_evaluation.utility.overall_score < 0
    assert loop.absorbed_principles == []
    assert bank.principles == []


def test_diagnosis_flags_environment_mismatch_and_false_certainty() -> None:
    task = make_task("t1", "ci/test_pipeline.py", "pytest -q ci/test_pipeline.py")
    result = build_loop().run_task(task)
    labels = set(result.iterations[0].diagnosis.labels)

    assert FailureType.ENVIRONMENT_MISMATCH in labels
    assert FailureType.FALSE_CERTAINTY in labels
    assert FailureType.WRONG_ABSTRACTION_LEVEL in labels


def test_transfer_signal_is_recorded_for_heldout_family_tasks() -> None:
    source = make_task("source", "tests/unit/test_math.py", "pytest -q tests/unit/test_math.py")
    sibling = make_task("sibling", "ci/test_pipeline.py", "pytest -q ci/test_pipeline.py")
    result = build_loop().run_task(source, heldout_tasks=[sibling])

    assert result.selected_evaluation.transfer_summary["num_tasks"] == 1.0
    assert result.selected_evaluation.utility.transfer_gain >= 0.0


class InvalidRewardAdapter:
    def run(self, task: TaskSpec, skill: Skill | None) -> ExecutionTrace:
        return ExecutionTrace(
            run_id="invalid",
            task_id=task.task_id,
            skill_version=None if skill is None else skill.version,
            success=False,
            status="failure",
            started_at="2026-05-04T00:00:00Z",
            ended_at="2026-05-04T00:00:01Z",
            tokens=0,
            tool_calls=0,
            steps=0,
            latency_seconds=1.0,
            outcome_summary="infra failure",
            metadata={"reward": None},
        )


class AlwaysDiagnoser:
    def diagnose(self, task, skill, evaluation):
        return DiagnosisReport(
            labels=[FailureType.WRONG_ABSTRACTION_LEVEL],
            evidence=[],
            causal_judgment="invalid run",
            rewrite_targets=["would revise"],
            summary="invalid",
        )


class ExplodingReviser:
    def revise(self, task, skill, diagnosis):
        raise AssertionError("Invalid benchmark runs should not trigger revision.")


class SuccessfulAdapter:
    def run(self, task: TaskSpec, skill: Skill | None) -> ExecutionTrace:
        return ExecutionTrace(
            run_id="success",
            task_id=task.task_id,
            skill_version=None if skill is None else skill.version,
            success=skill is not None,
            status="success" if skill is not None else "failure",
            started_at="2026-05-04T00:00:00Z",
            ended_at="2026-05-04T00:00:01Z",
            tokens=1000,
            tool_calls=5,
            steps=10,
            latency_seconds=1.0,
            outcome_summary="success" if skill is not None else "baseline failed",
            metadata={"reward": 1.0 if skill is not None else 0.0},
        )


class AlwaysLabelsDiagnoser:
    def diagnose(self, task, skill, evaluation):
        return DiagnosisReport(
            labels=[FailureType.CONTEXT_POLLUTION],
            evidence=[],
            causal_judgment="Successful skill is slightly verbose but not failing.",
            rewrite_targets=["Trim wording."],
            summary="non-blocking",
        )


def test_invalid_benchmark_reward_stops_before_revision() -> None:
    task = make_task("invalid", "tests/test.py", "pytest")
    loop = HarnessLoop(
        author=TemplateSkillAuthor(),
        runner=PairedRunner(InvalidRewardAdapter()),
        diagnoser=AlwaysDiagnoser(),
        reviser=ExplodingReviser(),
        max_revisions=1,
    )

    result = loop.run_task(task)

    assert len(result.iterations) == 1
    assert result.iterations[0].revision is None
    assert "no valid benchmark reward" in result.selected_evaluation.utility.notes[0]


def test_no_diagnosis_ablation_can_still_trigger_revision() -> None:
    task = make_task("no-diagnosis", "tests/test.py", "pytest")
    loop = HarnessLoop(
        author=TemplateSkillAuthor(),
        runner=PairedRunner(FlatRewardAdapter()),
        diagnoser=NoOpDiagnoser(),
        reviser=FixedReviser(),
        max_revisions=1,
        require_diagnosis_for_revision=False,
    )

    result = loop.run_task(task)

    assert result.iterations[0].diagnosis.labels == []
    assert result.iterations[0].revision is not None
    assert result.iterations[1].skill.version == "v1"


def test_successful_skill_is_not_revised_for_nonblocking_labels() -> None:
    task = make_task("success", "tests/test.py", "pytest")
    loop = HarnessLoop(
        author=TemplateSkillAuthor(),
        runner=PairedRunner(SuccessfulAdapter()),
        diagnoser=AlwaysLabelsDiagnoser(),
        reviser=ExplodingReviser(),
        max_revisions=1,
    )

    result = loop.run_task(task)

    assert len(result.iterations) == 1
    assert result.selected_skill.version == "v0"
    assert result.selected_evaluation.with_skill.success is True
    assert result.iterations[0].revision is None


class FlakyEvaluationAdapter:
    def __init__(self) -> None:
        self.calls: dict[str, int] = {}

    def run(self, task: TaskSpec, skill: Skill | None) -> ExecutionTrace:
        key = "no-skill" if skill is None else skill.version
        self.calls[key] = self.calls.get(key, 0) + 1
        if skill is not None and self.calls[key] == 1:
            return make_retry_trace(task, skill, status="failure", reward=None, tool_calls=0, events=0)
        return make_retry_trace(task, skill, status="success", reward=1.0, tool_calls=3, events=2)


class AlwaysInvalidEvaluationAdapter:
    def __init__(self) -> None:
        self.calls: dict[str, int] = {}

    def run(self, task: TaskSpec, skill: Skill | None) -> ExecutionTrace:
        key = "no-skill" if skill is None else skill.version
        self.calls[key] = self.calls.get(key, 0) + 1
        return make_retry_trace(
            task,
            skill,
            status="timeout",
            reward=None,
            tool_calls=0,
            events=0,
            timed_out=True,
        )


def test_runner_retries_invalid_evaluation_until_valid() -> None:
    task = make_task("flaky", "tests/test.py", "pytest")
    adapter = FlakyEvaluationAdapter()
    runner = PairedRunner(adapter, max_evaluation_attempts=3)
    skill = Skill("test", "test", "test", ["test"], [], version="v0")

    evaluation = runner.evaluate(task, skill)

    assert adapter.calls["v0"] == 2
    assert evaluation.with_skill.success is True
    assert evaluation.with_skill.metadata["evaluation_retry_attempts"] == 2
    assert evaluation.with_skill.metadata["evaluation_retry_recovered"] is True
    assert evaluation.with_skill.metadata["evaluation_previous_attempts"][0]["retry_reasons"] == [
        "missing_reward",
        "empty_trace",
    ]


def test_runner_marks_evaluation_failed_after_retry_exhaustion() -> None:
    task = make_task("always-invalid", "tests/test.py", "pytest")
    adapter = AlwaysInvalidEvaluationAdapter()
    runner = PairedRunner(adapter, max_evaluation_attempts=3)
    skill = Skill("test", "test", "test", ["test"], [], version="v0")

    evaluation = runner.evaluate(task, skill)

    assert adapter.calls["v0"] == 3
    assert evaluation.with_skill.success is False
    assert evaluation.with_skill.metadata["evaluation_retry_attempts"] == 3
    assert evaluation.with_skill.metadata["evaluation_retry_exhausted"] is True
    assert evaluation.with_skill.metadata["evaluation_forced_failed_after_retries"] is True
    assert evaluation.with_skill.metadata["evaluation_retry_reasons"] == [
        "timed_out",
        "missing_reward",
        "empty_trace",
    ]
    assert "no valid benchmark reward" in evaluation.utility.notes[0]


class FlatRewardAdapter:
    def run(self, task: TaskSpec, skill: Skill | None) -> ExecutionTrace:
        return ExecutionTrace(
            run_id="flat",
            task_id=task.task_id,
            skill_version=None if skill is None else skill.version,
            success=False,
            status="failure",
            started_at="2026-05-04T00:00:00Z",
            ended_at="2026-05-04T00:00:01Z",
            tokens=0,
            tool_calls=0,
            steps=0,
            latency_seconds=1.0,
            outcome_summary="flat reward",
            metadata={"reward": 0.0},
        )


class FixedReviser:
    def revise(self, task, skill, diagnosis):
        revised = Skill(
            name=skill.name,
            purpose=skill.purpose,
            when_to_use=skill.when_to_use,
            procedure=skill.procedure + ["Extra step."],
            constraints=skill.constraints,
            version="v1",
        )
        return RevisionCandidate(parent_version=skill.version, revised_skill=revised, rationale="test")


class BumpingReviser:
    def revise(self, task, skill, diagnosis):
        version_num = int(skill.version.removeprefix("v") or "0") + 1
        revised = Skill(
            name=skill.name,
            purpose=skill.purpose,
            when_to_use=skill.when_to_use,
            procedure=skill.procedure + [f"Revision {version_num}."],
            constraints=skill.constraints,
            version=f"v{version_num}",
        )
        return RevisionCandidate(parent_version=skill.version, revised_skill=revised, rationale="test")


def test_rejected_revision_evaluation_is_recorded() -> None:
    task = make_task("flat", "tests/test.py", "pytest")
    loop = HarnessLoop(
        author=TemplateSkillAuthor(),
        runner=PairedRunner(FlatRewardAdapter()),
        diagnoser=AlwaysDiagnoser(),
        reviser=FixedReviser(),
        max_revisions=1,
    )

    result = loop.run_task(task)

    assert [iteration.skill.version for iteration in result.iterations] == ["v0", "v1"]
    assert result.selected_skill.version == "v0"
    assert result.iterations[0].revision is not None
    assert result.iterations[1].revision is None


def test_can_explore_after_rejected_revision_without_selecting_it() -> None:
    task = make_task("flat-explore", "tests/test.py", "pytest")
    loop = HarnessLoop(
        author=TemplateSkillAuthor(),
        runner=PairedRunner(FlatRewardAdapter()),
        diagnoser=AlwaysDiagnoser(),
        reviser=BumpingReviser(),
        max_revisions=2,
        continue_after_non_improving_revision=True,
    )

    result = loop.run_task(task)

    assert [iteration.skill.version for iteration in result.iterations] == ["v0", "v1", "v2"]
    assert result.selected_skill.version == "v0"
    assert result.iterations[0].revision is not None
    assert result.iterations[1].revision is not None
    assert result.iterations[2].revision is None


def test_empty_timeout_trace_does_not_win_token_tiebreak() -> None:
    task = make_task("trace-quality", "tests/test.py", "pytest")
    loop = build_loop()
    normal_failure = make_paired_evaluation(
        task,
        version="v0",
        tokens=500,
        tool_calls=4,
        steps=8,
        reward=0.0,
        timed_out=False,
        events=1,
    )
    empty_timeout = make_paired_evaluation(
        task,
        version="v1",
        tokens=0,
        tool_calls=0,
        steps=0,
        reward=None,
        timed_out=True,
        events=0,
    )

    assert not loop._is_better(empty_timeout, normal_failure)
    assert loop._is_better(normal_failure, empty_timeout)


def make_paired_evaluation(
    task: TaskSpec,
    *,
    version: str,
    tokens: int,
    tool_calls: int,
    steps: int,
    reward: float | None,
    timed_out: bool,
    events: int,
) -> PairedEvaluation:
    skill = Skill(
        name="test",
        purpose="test",
        when_to_use="test",
        procedure=["test"],
        constraints=[],
        version=version,
    )
    trace = ExecutionTrace(
        run_id=version,
        task_id=task.task_id,
        skill_version=version,
        success=False,
        status="timeout" if timed_out else "failure",
        started_at="2026-05-04T00:00:00Z",
        ended_at="2026-05-04T00:00:01Z",
        tokens=tokens,
        tool_calls=tool_calls,
        steps=steps,
        latency_seconds=1.0,
        outcome_summary="test",
        events=[
            TrajectoryEvent(step_index=index, kind="tool", summary="step")
            for index in range(events)
        ],
        metadata={"reward": reward, "timed_out": timed_out},
    )
    return PairedEvaluation(
        task=task,
        skill=skill,
        no_skill=trace,
        with_skill=trace,
        utility=UtilityBreakdown(
            success_gain=0.0,
            token_gain=0.0,
            tool_gain=0.0,
            step_gain=0.0,
            latency_gain=0.0,
            efficiency_gain=0.0,
            transfer_gain=0.0,
            interference_cost=0.0,
            overall_score=0.0,
        ),
    )


def make_retry_trace(
    task: TaskSpec,
    skill: Skill | None,
    *,
    status: str,
    reward: float | None,
    tool_calls: int,
    events: int,
    timed_out: bool = False,
) -> ExecutionTrace:
    return ExecutionTrace(
        run_id="retry",
        task_id=task.task_id,
        skill_version=None if skill is None else skill.version,
        success=status == "success",
        status=status,
        started_at="2026-05-04T00:00:00Z",
        ended_at="2026-05-04T00:00:01Z",
        tokens=100 if tool_calls else 0,
        tool_calls=tool_calls,
        steps=events,
        latency_seconds=1.0,
        outcome_summary="retry test",
        events=[
            TrajectoryEvent(step_index=index, kind="tool", summary="step")
            for index in range(events)
        ],
        metadata={"reward": reward, "timed_out": timed_out},
    )
