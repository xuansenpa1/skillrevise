from __future__ import annotations


# Authoring prior and diagnosis constraints

from skillrevise.method.authoring import (
    NaiveSkillAuthoringPromptBuilder,
    PriorGuidedSkillAuthor,
    SkillAuthoringPromptBuilder,
    TemplateSkillAuthor,
)
from skillrevise.method.authoring import SkillConstraintChecker
from skillrevise.method.diagnosis import HeuristicDiagnoser
from skillrevise.core.models import FailureType, TaskSpec
from skillrevise.method.revision import HeuristicRevisionEngine


def make_task() -> TaskSpec:
    return TaskSpec(
        task_id="task-prior",
        family="swe-debug",
        instruction="Fix a failing validation flow without assuming paths or commands.",
        acceptance_criteria=["Verifier passes.", "Use repository-native validation."],
        metadata={
            "default_path": "tests/unit/test_math.py",
            "default_command": "pytest -q tests/unit/test_math.py",
        },
    )


def test_direct_skill_violates_platform_agnostic_authoring_prior() -> None:
    task = make_task()
    skill = TemplateSkillAuthor().author(task)
    violations = SkillConstraintChecker().check(skill, task)
    codes = {violation.code for violation in violations}

    assert "missing_workflow_explicitness" in codes
    assert "missing_environment_grounding" in codes
    assert "missing_fallback_handling" in codes
    assert "over_specific_literals" in codes


def test_prior_guided_author_outputs_constraint_checked_skill() -> None:
    task = make_task()
    skill = PriorGuidedSkillAuthor().author(task)
    violations = SkillConstraintChecker().check(skill, task)

    assert skill.metadata["author"] == "prior_guided"
    assert [violation.code for violation in violations] == []


def test_revision_reduces_authoring_prior_violations() -> None:
    task = make_task()
    direct = TemplateSkillAuthor().author(task)
    checker = SkillConstraintChecker()
    before = checker.check(direct, task)
    diagnosis = HeuristicDiagnoser(checker).diagnose(
        task,
        direct,
        evaluation=type(
            "Eval",
            (),
            {
                "no_skill": type("Trace", (), {"success": True, "tokens": 1500})(),
                "with_skill": type(
                    "Trace",
                    (),
                    {
                        "success": False,
                        "tokens": 2000,
                        "events": [],
                    },
                )(),
                "utility": type("Utility", (), {"overall_score": -1.0, "success_gain": -1.0, "efficiency_gain": -0.2})(),
            },
        )(),
    )
    revised = HeuristicRevisionEngine().revise(task, direct, diagnosis).revised_skill
    after = checker.check(revised, task)

    assert len(after) < len(before)
    assert FailureType.WRONG_ABSTRACTION_LEVEL in diagnosis.labels


def test_diagnosis_turns_verifier_assertions_into_specific_rewrite_targets() -> None:
    task = make_task()
    skill = PriorGuidedSkillAuthor().author(task)
    verifier_text = "\n".join(
        [
            "FAILED ::test_graph_logic[reachability] - AssertionError: Unreachable nodes found: ['End']",
            "FAILED ::test_visualization_validity[shapes] - AssertionError: Choice nodes should be visualized as diamonds",
        ]
    )

    diagnosis = HeuristicDiagnoser().diagnose(
        task,
        skill,
        evaluation=type(
            "Eval",
            (),
            {
                "no_skill": type("Trace", (), {"success": False, "tokens": 1500})(),
                "with_skill": type(
                    "Trace",
                    (),
                    {
                        "success": False,
                        "tokens": 1800,
                        "events": [
                            type(
                                "Event",
                                (),
                                {
                                    "kind": "verifier",
                                    "summary": verifier_text,
                                    "evidence": verifier_text,
                                },
                            )()
                        ],
                    },
                )(),
                "utility": type("Utility", (), {"overall_score": -0.4, "success_gain": -0.1, "efficiency_gain": -0.2})(),
            },
        )(),
    )

    assert "terminal-sentinel convention" in diagnosis.rewrite_targets[0]
    assert 'to == "End"' in diagnosis.rewrite_targets[0]
    assert any("post-write check" in target for target in diagnosis.rewrite_targets)
    assert any('"End" not in node_ids' in target for target in diagnosis.rewrite_targets)
    assert any("already-passing graph contracts" in target for target in diagnosis.rewrite_targets)
    assert any("shape=diamond" in target for target in diagnosis.rewrite_targets)


def test_prompt_builder_contains_authoring_prior_and_task_context() -> None:
    prompt = SkillAuthoringPromptBuilder().build(make_task())

    assert "platform-agnostic skill authoring constraints" in prompt
    assert "Task family: swe-debug" in prompt
    assert "Verifier passes." in prompt


def test_naive_prompt_builder_omits_principle_guidance_but_keeps_task_context() -> None:
    prompt = NaiveSkillAuthoringPromptBuilder().build(make_task())

    assert "platform-agnostic skill authoring constraints" not in prompt
    assert "Validate inputs" not in prompt
    assert "Ground the procedure" not in prompt
    assert "Task family: swe-debug" in prompt
    assert "Verifier passes." in prompt
    assert "Return only Markdown in exactly this structure:" in prompt


# Skill markdown parsing

import pytest

from skillrevise.method.authoring import FileSkillAuthor
from skillrevise.core.models import TaskSpec
from skillrevise.method.skill_parser import parse_skill_markdown


def test_parse_heading_based_skill_markdown() -> None:
    skill = parse_skill_markdown(
        """
# Repository Validation Workflow

## Purpose
Guide repository changes with validated execution.

## When to Use
Use when files and commands must be discovered from the environment.

## Procedure
- Inspect the repository before selecting files.
- Validate assumptions before editing.
- Run the smallest reliable checker.

## Constraints / Pitfalls
- Do not hard-code paths before verifying them.
- Stop when verifier output contradicts the plan.
""",
        default_name="Fallback Name",
    )

    assert skill.name == "Repository Validation Workflow"
    assert skill.purpose == "Guide repository changes with validated execution."
    assert skill.when_to_use.startswith("Use when files")
    assert skill.procedure == [
        "Inspect the repository before selecting files.",
        "Validate assumptions before editing.",
        "Run the smallest reliable checker.",
    ]
    assert skill.constraints[0] == "Do not hard-code paths before verifying them."


def test_parse_key_value_skill_inside_markdown_fence() -> None:
    skill = parse_skill_markdown(
        """```markdown
Skill Name: Validation Skill
Purpose: Keep execution grounded in available repository tools.
When to Use: Use when the validation route is uncertain.
Procedure:
1. Inspect available files and commands.
2. Confirm inputs before acting.
3. Use fallback alternatives if the first checker is unavailable.
Constraints / Pitfalls:
- Only proceed after assumptions are checked.
- Avoid unconditional path or command assumptions.
```""",
        default_name="Fallback Name",
        version="v3",
        metadata={"source": "test"},
    )

    assert skill.name == "Validation Skill"
    assert skill.version == "v3"
    assert skill.metadata == {"source": "test"}
    assert len(skill.procedure) == 3
    assert "fallback alternatives" in skill.procedure[2]


def test_parse_skill_markdown_requires_core_sections() -> None:
    with pytest.raises(ValueError, match="Procedure"):
        parse_skill_markdown(
            """
# Incomplete Skill

## Purpose
Guide work.

## When to Use
Use for local tasks.

## Constraints / Pitfalls
- Check assumptions.
""",
            default_name="Fallback Name",
        )


def test_file_skill_author_loads_markdown_as_initial_skill(tmp_path) -> None:
    skill_path = tmp_path / "skill.md"
    skill_path.write_text(
        """
# Reusable Skill

## Purpose
Guide a reusable workflow.

## When to Use
Use when matching tasks need a fixed starting skill.

## Procedure
- Inspect inputs.
- Run checks.

## Constraints / Pitfalls
- Do not assume success without verification.
"""
    )
    task = TaskSpec(
        task_id="t",
        family="family",
        instruction="Do it.",
        acceptance_criteria=["Pass."],
    )

    skill = FileSkillAuthor(skill_path).author(task)

    assert skill.version == "v0"
    assert skill.metadata["author"] == "file"
    assert skill.metadata["source_path"] == str(skill_path)
    assert skill.name == "Reusable Skill"
