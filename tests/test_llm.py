from __future__ import annotations


# Command LLM client

from types import SimpleNamespace

from skillrevise.llm import CommandLLMClient


def test_command_llm_client_can_bypass_proxy(monkeypatch) -> None:
    captured = {}

    def fake_run(argv, input, capture_output, text, env, timeout):
        captured["env"] = env
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setenv("SKILL_HARNESS_BYPASS_PROXY", "1")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example")
    monkeypatch.setenv("http_proxy", "http://proxy.example")
    monkeypatch.setattr("skillrevise.llm.client.subprocess.run", fake_run)

    response = CommandLLMClient("fake-llm").complete("prompt", purpose="skill_authoring")

    assert response.text == "ok"
    assert "HTTPS_PROXY" not in captured["env"]
    assert "http_proxy" not in captured["env"]
    assert captured["env"]["SKILL_HARNESS_REVISION_LLM_PURPOSE"] == "skill_authoring"


# Provider command wrapper

import pytest

from skillrevise.llm import command as llm_command


def test_openai_compatible_wrapper_builds_chat_completion_payload(monkeypatch) -> None:
    calls = []

    def fake_post_json(url, headers, payload, timeout_seconds):
        calls.append(
            {
                "url": url,
                "headers": headers,
                "payload": payload,
                "timeout_seconds": timeout_seconds,
            }
        )
        return {"choices": [{"message": {"content": "skill markdown"}}]}

    monkeypatch.setattr(llm_command, "_post_json", fake_post_json)

    output = llm_command.complete_prompt(
        "write a skill",
        {
            "SKILL_HARNESS_REVISION_LLM_PROVIDER": "openai",
            "SKILL_HARNESS_REVISION_LLM_MODEL": "test-model",
            "SKILL_HARNESS_REVISION_LLM_API_KEY": "test-key",
            "SKILL_HARNESS_REVISION_LLM_PURPOSE": "skill_authoring",
            "SKILL_HARNESS_REVISION_LLM_TEMPERATURE": "0.1",
            "SKILL_HARNESS_REVISION_LLM_MAX_TOKENS": "1234",
            "SKILL_HARNESS_REVISION_LLM_HTTP_TIMEOUT": "77",
        },
    )

    assert output == "skill markdown"
    assert calls[0]["url"] == "https://api.openai.com/v1/chat/completions"
    assert calls[0]["headers"]["Authorization"] == "Bearer test-key"
    assert calls[0]["payload"]["model"] == "test-model"
    assert calls[0]["payload"]["temperature"] == 0.1
    assert calls[0]["payload"]["max_tokens"] == 1234
    assert calls[0]["payload"]["messages"][1]["content"] == "write a skill"
    assert calls[0]["timeout_seconds"] == 77


def test_official_openai_gpt5_uses_new_token_parameter(monkeypatch) -> None:
    calls = []

    def fake_post_json(url, headers, payload, timeout_seconds):
        calls.append(payload)
        return {"choices": [{"message": {"content": "OK"}}]}

    monkeypatch.setattr(llm_command, "_post_json", fake_post_json)

    output = llm_command.complete_prompt(
        "ping",
        {
            "SKILL_HARNESS_REVISION_LLM_PROVIDER": "openai",
            "SKILL_HARNESS_REVISION_LLM_MODEL": "gpt-5.5",
            "SKILL_HARNESS_REVISION_LLM_API_KEY": "test-key",
            "SKILL_HARNESS_REVISION_LLM_MAX_TOKENS": "20",
        },
    )

    assert output == "OK"
    assert calls[0]["max_completion_tokens"] == 20
    assert "max_tokens" not in calls[0]
    assert "temperature" not in calls[0]


def test_openai_compatible_wrapper_retries_missing_choices(monkeypatch) -> None:
    calls = []

    def fake_post_json(url, headers, payload, timeout_seconds):
        calls.append(url)
        if len(calls) == 1:
            return {"error": {"message": "temporary upstream issue", "code": "temporarily_unavailable"}}
        return {"choices": [{"message": {"content": "recovered skill"}}]}

    monkeypatch.setattr(llm_command, "_post_json", fake_post_json)
    monkeypatch.setattr(llm_command, "_sleep_before_retry", lambda base_delay_seconds, attempt: None)

    output = llm_command.complete_prompt(
        "write a skill",
        {
            "SKILL_HARNESS_REVISION_LLM_PROVIDER": "openrouter",
            "SKILL_HARNESS_REVISION_LLM_MODEL": "openai/gpt-test",
            "REVISION_OPENROUTER_API_KEY": "revision-key",
            "SKILL_HARNESS_REVISION_LLM_HTTP_RETRY_ATTEMPTS": "2",
        },
    )

    assert output == "recovered skill"
    assert len(calls) == 2


def test_openai_compatible_wrapper_does_not_retry_auth_errors(monkeypatch) -> None:
    calls = []

    def fake_post_json(url, headers, payload, timeout_seconds):
        calls.append(url)
        return {"error": {"message": "Incorrect API key provided", "code": "invalid_api_key"}}

    monkeypatch.setattr(llm_command, "_post_json", fake_post_json)
    monkeypatch.setattr(llm_command, "_sleep_before_retry", lambda base_delay_seconds, attempt: None)

    with pytest.raises(llm_command.LLMCommandError, match="invalid_api_key"):
        llm_command.complete_prompt(
            "write a skill",
            {
                "SKILL_HARNESS_REVISION_LLM_PROVIDER": "openrouter",
                "SKILL_HARNESS_REVISION_LLM_MODEL": "openai/gpt-test",
                "REVISION_OPENROUTER_API_KEY": "revision-key",
                "SKILL_HARNESS_REVISION_LLM_HTTP_RETRY_ATTEMPTS": "3",
            },
        )

    assert len(calls) == 1


def test_anthropic_wrapper_extracts_text_blocks(monkeypatch) -> None:
    calls = []

    def fake_post_json(url, headers, payload, timeout_seconds):
        calls.append({"url": url, "headers": headers, "payload": payload})
        return {"content": [{"type": "text", "text": "{\"labels\": []}"}]}

    monkeypatch.setattr(llm_command, "_post_json", fake_post_json)

    output = llm_command.complete_prompt(
        "diagnose",
        {
            "SKILL_HARNESS_REVISION_LLM_PROVIDER": "anthropic",
            "SKILL_HARNESS_REVISION_LLM_MODEL": "claude-test",
            "SKILL_HARNESS_REVISION_LLM_API_KEY": "test-key",
        },
    )

    assert output == "{\"labels\": []}"
    assert calls[0]["url"] == "https://api.anthropic.com/v1/messages"
    assert calls[0]["headers"]["x-api-key"] == "test-key"
    assert calls[0]["payload"]["model"] == "claude-test"


def test_anthropic_wrapper_extracts_deepseek_compatible_content_shapes(monkeypatch) -> None:
    responses = [
        {"content": "plain text content"},
        {"content": [{"text": "missing type text"}]},
        {"choices": [{"message": {"content": "chat-compatible text"}}]},
    ]

    def fake_post_json(url, headers, payload, timeout_seconds):
        return responses.pop(0)

    monkeypatch.setattr(llm_command, "_post_json", fake_post_json)

    env = {
        "SKILL_HARNESS_REVISION_LLM_PROVIDER": "anthropic",
        "SKILL_HARNESS_REVISION_LLM_MODEL": "deepseek-test",
        "SKILL_HARNESS_REVISION_LLM_API_KEY": "test-key",
    }
    assert llm_command.complete_prompt("revise", env) == "plain text content"
    assert llm_command.complete_prompt("revise", env) == "missing type text"
    assert llm_command.complete_prompt("revise", env) == "chat-compatible text"


def test_anthropic_wrapper_retries_empty_content(monkeypatch) -> None:
    calls = []

    def fake_post_json(url, headers, payload, timeout_seconds):
        calls.append(url)
        if len(calls) == 1:
            return {"content": []}
        return {"content": [{"type": "text", "text": "recovered revision"}]}

    monkeypatch.setattr(llm_command, "_post_json", fake_post_json)
    monkeypatch.setattr(llm_command, "_sleep_before_retry", lambda base_delay_seconds, attempt: None)

    output = llm_command.complete_prompt(
        "revise",
        {
            "SKILL_HARNESS_REVISION_LLM_PROVIDER": "anthropic",
            "SKILL_HARNESS_REVISION_LLM_MODEL": "deepseek-test",
            "SKILL_HARNESS_REVISION_LLM_API_KEY": "test-key",
            "SKILL_HARNESS_REVISION_LLM_HTTP_RETRY_ATTEMPTS": "2",
        },
    )

    assert output == "recovered revision"
    assert len(calls) == 2


def test_ollama_wrapper_uses_local_generate_endpoint(monkeypatch) -> None:
    calls = []

    def fake_post_json(url, headers, payload, timeout_seconds):
        calls.append({"url": url, "headers": headers, "payload": payload})
        return {"response": "# Local Skill"}

    monkeypatch.setattr(llm_command, "_post_json", fake_post_json)

    output = llm_command.complete_prompt(
        "revise",
        {
            "SKILL_HARNESS_REVISION_LLM_PROVIDER": "ollama",
            "SKILL_HARNESS_REVISION_LLM_MODEL": "llama-test",
        },
    )

    assert output == "# Local Skill"
    assert calls[0]["url"] == "http://localhost:11434/api/generate"
    assert calls[0]["payload"]["model"] == "llama-test"
    assert calls[0]["payload"]["stream"] is False


def test_wrapper_requires_revision_model() -> None:
    with pytest.raises(llm_command.LLMCommandError, match="Missing revision model"):
        llm_command.load_config({})


def test_wrapper_ignores_generic_key_base_url_and_model_config() -> None:
    with pytest.raises(llm_command.LLMCommandError, match="Missing revision model"):
        llm_command.load_config(
            {
                "SKILL_HARNESS_LLM_API_KEY": "generic-key",
                "SKILL_HARNESS_LLM_BASE_URL": "https://example.test/v1",
                "SKILL_HARNESS_LLM_MODEL": "generic-model",
            }
        )


def test_wrapper_uses_revision_key_base_url_and_model_config() -> None:
    config = llm_command.load_config(
        {
            "SKILL_HARNESS_REVISION_LLM_API_KEY": "revision-key",
            "SKILL_HARNESS_REVISION_LLM_BASE_URL": "https://example.test/v1",
            "SKILL_HARNESS_REVISION_LLM_MODEL": "revision-model",
        }
    )

    assert config.provider == llm_command.DEFAULT_REVISION_LLM_PROVIDER
    assert config.api_key == "revision-key"
    assert config.base_url == "https://example.test/v1"
    assert config.model == "revision-model"


def test_openrouter_provider_uses_openrouter_key_and_base_url() -> None:
    config = llm_command.load_config(
        {
            "SKILL_HARNESS_REVISION_LLM_PROVIDER": "openrouter",
            "REVISION_OPENROUTER_API_KEY": "openrouter-key",
            "SKILL_HARNESS_REVISION_LLM_MODEL": "openai/gpt-5.2",
        }
    )

    assert config.provider == "openrouter"
    assert config.api_key == "openrouter-key"
    assert config.base_url == "https://openrouter.ai/api/v1"
    assert config.model == "openai/gpt-5.2"


def test_revision_aliases_configure_revision_llm() -> None:
    config = llm_command.load_config(
        {
            "SKILL_HARNESS_REVISION_LLM_PROVIDER": "openrouter",
            "REVISION_OPENROUTER_API_KEY": "revision-key",
            "SKILL_HARNESS_REVISION_LLM_MODEL": "openai/gpt-5.5",
        }
    )

    assert config.provider == "openrouter"
    assert config.api_key == "revision-key"
    assert config.base_url == "https://openrouter.ai/api/v1"
    assert config.model == "openai/gpt-5.5"


def test_revision_llm_ignores_agent_embedding_and_legacy_keys() -> None:
    env = {
        "SKILL_HARNESS_REVISION_LLM_PROVIDER": "openrouter",
        "SKILL_HARNESS_REVISION_LLM_MODEL": "openai/gpt-5.5",
        "AGENT_OPENROUTER_API_KEY": "agent-key",
        "SKILL_HARNESS_PRINCIPLE_EMBEDDING_API_KEY": "embedding-key",
        "OPENROUTER_API_KEY": "legacy-key",
        "OPENAI_API_KEY": "openai-key",
    }

    config = llm_command.load_config(env)

    assert config.api_key is None
    with pytest.raises(llm_command.LLMCommandError, match="Missing REVISION_OPENROUTER_API_KEY"):
        llm_command.complete_prompt("prompt", env)


def test_openai_provider_requires_api_key() -> None:
    with pytest.raises(llm_command.LLMCommandError, match="Missing SKILL_HARNESS_REVISION_LLM_API_KEY"):
        llm_command.complete_prompt(
            "prompt",
            {
                "SKILL_HARNESS_REVISION_LLM_PROVIDER": "openai",
                "SKILL_HARNESS_REVISION_LLM_MODEL": "test-model",
            },
        )


def test_openrouter_provider_requires_api_key() -> None:
    with pytest.raises(llm_command.LLMCommandError, match="Missing REVISION_OPENROUTER_API_KEY"):
        llm_command.complete_prompt(
            "prompt",
            {
                "SKILL_HARNESS_REVISION_LLM_PROVIDER": "openrouter",
                "SKILL_HARNESS_REVISION_LLM_MODEL": "openai/gpt-5.2",
            },
        )


def test_proxy_bypass_strips_process_proxy_environment(monkeypatch) -> None:
    monkeypatch.setenv("SKILL_HARNESS_BYPASS_PROXY", "1")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example")
    monkeypatch.setenv("http_proxy", "http://proxy.example")

    llm_command._strip_proxy_from_process_env()

    assert "HTTPS_PROXY" not in llm_command.os.environ
    assert "http_proxy" not in llm_command.os.environ
    assert llm_command.os.environ["SKILL_HARNESS_BYPASS_PROXY"] == "1"


# LLM authoring, diagnosis, revision, and principles

import pytest

from skillrevise.method.authoring import LLMSkillAuthor, NaiveSkillAuthoringPromptBuilder, SkillCreatorPromptBuilder
from skillrevise.method import principles as principles_module
from skillrevise.method.diagnosis import LLMDiagnoser, NoOpDiagnoser
from skillrevise.llm import StaticLLMClient
from skillrevise.core.metrics import compute_utility
from skillrevise.core.models import (
    DiagnosisEvidence,
    DiagnosisReport,
    ExecutionTrace,
    FailureType,
    PairedEvaluation,
    Skill,
    TaskSpec,
    TrajectoryEvent,
)
from skillrevise.method.principles import GoldenLawBank, PrincipleAbsorber, PrincipleBank, PrincipleRetrievalConfig
from skillrevise.method.revision import FreeFormLLMRevisionEngine, LLMRevisionEngine


VALID_SKILL_MARKDOWN = """
# SWE Validation Workflow

## Purpose
Guide reusable swe-debug execution with explicit validation, environment grounding, fallback handling, and strict checks.

## When to Use
Use for swe-debug tasks where files, tools, commands, or verifier routes may vary across environments.

## Procedure
- First restate the required outcome and smallest verifiable unit of work.
- Inspect the environment to discover relevant files, available tools, and repository-native validation entrypoint.
- Validate inputs, assumptions, target files, and expected outputs before editing or running commands.
- If a planned file, command, tool, or check is unavailable, fall back to the closest environment-supported alternative.
- Before finishing, compare the result against every explicit constraint and verifier signal.

## Constraints / Pitfalls
- Do not assume a fixed path, tool, command, or version before verification.
- Only act after inputs, files, commands, and verifier route are checked in the current environment.
- Stop and re-check when verifier output contradicts the current plan.
"""


def make_task() -> TaskSpec:
    return TaskSpec(
        task_id="llm-task",
        family="swe-debug",
        instruction="Fix a failing validation flow without assuming paths or commands.",
        acceptance_criteria=["Verifier passes.", "Use repository-native validation."],
        metadata={"requires_validation": True},
    )


def make_trace(
    *,
    skill_version: str | None,
    success: bool,
    tokens: int,
    events: list[TrajectoryEvent] | None = None,
) -> ExecutionTrace:
    return ExecutionTrace(
        run_id="run",
        task_id="llm-task",
        skill_version=skill_version,
        success=success,
        status="success" if success else "failure",
        started_at="2026-04-28T00:00:00Z",
        ended_at="2026-04-28T00:00:01Z",
        tokens=tokens,
        tool_calls=5,
        steps=8,
        latency_seconds=10.0,
        outcome_summary="ok" if success else "failed",
        events=events or [],
    )


def bm25_revision_engine(llm: StaticLLMClient, **kwargs) -> LLMRevisionEngine:
    return LLMRevisionEngine(
        llm,
        principle_bank=PrincipleBank.with_seed_golden_laws(
            retrieval_config=PrincipleRetrievalConfig(method="bm25")
        ),
        **kwargs,
    )


def make_evaluation(task: TaskSpec, skill: Skill) -> PairedEvaluation:
    no_skill = make_trace(skill_version=None, success=True, tokens=1400)
    with_skill = make_trace(
        skill_version=skill.version,
        success=False,
        tokens=1900,
        events=[
            TrajectoryEvent(
                step_index=1,
                kind="env_error",
                summary="The skill assumed a fixed command.",
                evidence="pytest -q tests/unit/test_math.py",
            )
        ],
    )
    return PairedEvaluation(
        task=task,
        skill=skill,
        no_skill=no_skill,
        with_skill=with_skill,
        utility=compute_utility(no_skill, with_skill),
    )


def test_llm_skill_author_parses_model_output_and_records_call() -> None:
    llm = StaticLLMClient([VALID_SKILL_MARKDOWN])
    task = make_task()

    skill = LLMSkillAuthor(llm).author(task)

    assert skill.name == "SWE Validation Workflow"
    assert skill.version == "v0"
    assert skill.metadata["author"] == "llm"
    assert skill.metadata["prior_violations"] == []
    assert llm.calls[0]["purpose"] == "skill_authoring"
    assert "platform-agnostic skill authoring constraints" in llm.calls[0]["prompt"]
    assert "Return only Markdown in exactly this structure:" in llm.calls[0]["prompt"]
    assert "## Constraints / Pitfalls" in llm.calls[0]["prompt"]


def test_llm_skill_author_can_use_naive_prompt_strategy() -> None:
    llm = StaticLLMClient([VALID_SKILL_MARKDOWN])
    task = make_task()

    skill = LLMSkillAuthor(llm, prompt_builder=NaiveSkillAuthoringPromptBuilder()).author(task)

    assert skill.metadata["author"] == "llm"
    assert skill.metadata["prompt_strategy"] == "naive"
    assert "platform-agnostic skill authoring constraints" not in llm.calls[0]["prompt"]
    assert "Task family: swe-debug" in llm.calls[0]["prompt"]


def test_llm_skill_author_can_use_skill_creator_prompt_strategy() -> None:
    llm = StaticLLMClient([VALID_SKILL_MARKDOWN])
    task = make_task()

    skill = LLMSkillAuthor(llm, prompt_builder=SkillCreatorPromptBuilder()).author(task)

    assert skill.metadata["author"] == "llm"
    assert skill.metadata["prompt_strategy"] == "skill_creator"
    assert "official skill-creator design principles" in llm.calls[0]["prompt"]
    assert "Protect validation integrity" in llm.calls[0]["prompt"]
    assert "Task family: swe-debug" in llm.calls[0]["prompt"]


def test_llm_skill_author_can_fail_instead_of_falling_back() -> None:
    llm = StaticLLMClient([])
    task = make_task()

    with pytest.raises(RuntimeError, match="LLM skill authoring failed"):
        LLMSkillAuthor(llm, allow_fallback=False).author(task)


def test_llm_diagnoser_parses_json_report() -> None:
    task = make_task()
    skill = Skill(
        name="Brittle Skill",
        purpose="Finish this swe-debug task quickly.",
        when_to_use="Use for similar swe-debug tasks.",
        procedure=["Directly open `tests/unit/test_math.py`.", "Run `pytest -q tests/unit/test_math.py`."],
        constraints=["Prefer a direct fix."],
    )
    llm = StaticLLMClient(
        [
            """
{
  "labels": ["environment_mismatch", "false_certainty"],
  "evidence": [
    {
      "source": "trace",
      "snippet": "fixed command failed",
      "reason": "The skill assumed a command before environment discovery."
    }
  ],
  "causal_judgment": "The skill regresses execution by steering toward an invalid environment assumption.",
  "rewrite_targets": ["Add environment discovery before execution."],
  "summary": "The skill is brittle."
}
"""
        ]
    )

    report = LLMDiagnoser(llm).diagnose(task, skill, make_evaluation(task, skill))

    assert report.labels == [FailureType.ENVIRONMENT_MISMATCH, FailureType.FALSE_CERTAINTY]
    assert report.evidence[0].source == "trace"
    assert report.rewrite_targets == ["Add environment discovery before execution."]
    assert report.evidence[-1].source == "llm_metadata"
    assert llm.calls[0]["purpose"] == "skill_diagnosis"


def test_noop_diagnoser_withholds_failure_analysis() -> None:
    task = make_task()
    skill = Skill(
        name="Brittle Skill",
        purpose="Finish this swe-debug task quickly.",
        when_to_use="Use for similar swe-debug tasks.",
        procedure=["Directly open `tests/unit/test_math.py`."],
        constraints=["Prefer a direct fix."],
    )

    report = NoOpDiagnoser().diagnose(task, skill, make_evaluation(task, skill))

    assert report.labels == []
    assert report.evidence == []
    assert report.rewrite_targets == []
    assert "disabled" in report.summary.lower()


def test_llm_revision_engine_bumps_version_and_parses_revised_skill() -> None:
    task = make_task()
    skill = Skill(
        name="Brittle Skill",
        purpose="Finish this swe-debug task quickly.",
        when_to_use="Use for similar swe-debug tasks.",
        procedure=["Directly open `tests/unit/test_math.py`.", "Run `pytest -q tests/unit/test_math.py`."],
        constraints=["Prefer a direct fix."],
        version="v0",
    )
    diagnosis = DiagnosisReport(
        labels=[FailureType.ENVIRONMENT_MISMATCH],
        evidence=[],
        causal_judgment="The skill assumes a fixed environment.",
        rewrite_targets=["Add environment discovery and fallback handling."],
        summary="Needs grounding.",
    )
    llm = StaticLLMClient([VALID_SKILL_MARKDOWN])

    candidate = bm25_revision_engine(llm).revise(task, skill, diagnosis)

    assert candidate.parent_version == "v0"
    assert candidate.revised_skill.version == "v1"
    assert candidate.revised_skill.metadata["reviser"] == "llm"
    assert candidate.revised_skill.metadata["prior_violations"] == []
    assert "execution evidence and the repair-principle bank" in llm.calls[0]["prompt"]
    assert "Top-k candidate repair principles" in llm.calls[0]["prompt"]
    assert "Principle-bank revision protocol:" in llm.calls[0]["prompt"]
    assert "Structured diagnosis first" in llm.calls[0]["prompt"]
    assert "Verifier Contract" in llm.calls[0]["prompt"]
    assert "Do not invent hidden contracts" in llm.calls[0]["prompt"]
    assert "Failure Ledger" in llm.calls[0]["prompt"]
    assert "Anti-overfitting check" in llm.calls[0]["prompt"]
    assert "Expected verifier alignment" in llm.calls[0]["prompt"]
    assert "Task-local revision memory guard" in llm.calls[0]["prompt"]
    assert "Previous revision trace / task-local memory" in llm.calls[0]["prompt"]
    assert "Minimal repair scope" in llm.calls[0]["prompt"]
    assert "Preserve Ledger" in llm.calls[0]["prompt"]
    assert "Repeated-failure escalation" in llm.calls[0]["prompt"]
    assert "Execution anchor" in llm.calls[0]["prompt"]
    assert "selected_principles" in llm.calls[0]["prompt"]
    assert "execution_anchors" in llm.calls[0]["prompt"]
    assert "acceptance_signals" in llm.calls[0]["prompt"]
    assert "Executable repair guard" in llm.calls[0]["prompt"]
    assert "action, expected observable evidence, and placement" in llm.calls[0]["prompt"]
    assert "not memorize this task's answer" in llm.calls[0]["prompt"]
    assert candidate.principles
    assert candidate.revised_skill.metadata["revision_framework"] == "principle_bank_guided"
    assert candidate.revised_skill.metadata["revision_protocol_version"] == "principle_revision_v2"
    assert candidate.revised_skill.metadata["retrieved_principle_ids"]
    assert "revision_trace" in candidate.revised_skill.metadata
    assert candidate.revised_skill.metadata["golden_law_ids"]
    assert candidate.revised_skill.metadata["principle_ids"]
    assert llm.calls[0]["purpose"] == "skill_revision"


def test_llm_revision_engine_can_disable_principle_memory_but_keep_diagnosis() -> None:
    task = make_task()
    skill = Skill(
        name="Brittle Skill",
        purpose="Finish this swe-debug task quickly.",
        when_to_use="Use for similar swe-debug tasks.",
        procedure=["Directly open `tests/unit/test_math.py`."],
        constraints=["Prefer a direct fix."],
        version="v0",
    )
    diagnosis = DiagnosisReport(
        labels=[FailureType.ENVIRONMENT_MISMATCH],
        evidence=[
            DiagnosisEvidence(
                source="verifier",
                snippet="Solution file not found: /output/result.json",
                reason="The output path contract was missed.",
            )
        ],
        causal_judgment="The skill missed the verifier-visible output path.",
        rewrite_targets=["Add output-path existence checks."],
        summary="Missing output.",
    )
    llm = StaticLLMClient([VALID_SKILL_MARKDOWN])

    candidate = LLMRevisionEngine(
        llm,
        principle_bank=PrincipleBank.with_seed_golden_laws(
            retrieval_config=PrincipleRetrievalConfig(method="bm25")
        ),
        use_principle_memory=False,
    ).revise(task, skill, diagnosis)

    prompt = llm.calls[0]["prompt"]
    assert "Principle-memory ablation" in prompt
    assert "Top-k candidate repair principles" not in prompt
    assert "Principle-bank revision protocol" not in prompt
    assert "Diagnosis-guided revision protocol" in prompt
    assert "Solution file not found" in prompt
    assert candidate.revised_skill.metadata["principle_memory_enabled"] is False
    assert candidate.revised_skill.metadata["revision_framework"] == "diagnosis_guided_no_principle_memory"
    assert candidate.revised_skill.metadata["retrieved_principle_ids"] == []
    assert candidate.principles == []


def test_llm_revision_engine_can_ablate_execution_anchors() -> None:
    task = make_task()
    skill = Skill(
        name="Brittle Skill",
        purpose="Finish this swe-debug task quickly.",
        when_to_use="Use for similar swe-debug tasks.",
        procedure=["Directly open `tests/unit/test_math.py`."],
        constraints=["Prefer a direct fix."],
        version="v0",
    )
    diagnosis = DiagnosisReport(
        labels=[FailureType.ENVIRONMENT_MISMATCH],
        evidence=[],
        causal_judgment="The skill assumes a fixed environment.",
        rewrite_targets=["Add environment discovery."],
        summary="Needs grounding.",
    )
    traced_response = """
REVISION_TRACE_JSON:
```json
{
  "failure_ledger": {"failure_type": {"primary": "path", "secondary_tags": []}},
  "selected_principles": [],
  "execution_anchors": [
    {"action": "Run verifier.", "evidence": "Passes.", "placement": "Final check"}
  ],
  "acceptance_signals": {
    "expected_utility_improvement": "better",
    "expected_failed_assertions_reduced": []
  }
}
```

REVISED_SKILL_MARKDOWN:
""" + VALID_SKILL_MARKDOWN
    llm = StaticLLMClient([traced_response])

    candidate = bm25_revision_engine(llm, revision_ablation="no-execution-anchors").revise(
        task, skill, diagnosis
    )

    prompt = llm.calls[0]["prompt"]
    assert "Execution anchor:" not in prompt
    assert "Executable repair guard" not in prompt
    assert "execution_anchors" not in prompt
    assert "action, expected observable evidence, and placement" not in prompt
    assert candidate.revised_skill.metadata["revision_ablation"] == "no-execution-anchors"
    assert candidate.revised_skill.metadata["removed_mechanism"] == "execution anchors"
    assert "execution_anchors" not in candidate.revised_skill.metadata
    assert "execution_anchors" not in candidate.revised_skill.metadata["revision_trace"]
    assert "execution_anchors" not in candidate.metadata


def test_llm_revision_engine_can_ablate_preserve_ledger() -> None:
    task = make_task()
    skill = Skill(
        name="Brittle Skill",
        purpose="Finish this swe-debug task quickly.",
        when_to_use="Use for similar swe-debug tasks.",
        procedure=["Directly open `tests/unit/test_math.py`."],
        constraints=["Prefer a direct fix."],
        version="v1",
        metadata={
            "selected_principle_ids": ["environment-output-grounding"],
            "revision_trace": {
                "failure_ledger": {"failure_type": {"primary": "schema", "secondary_tags": []}},
                "preserve_ledger": {
                    "passed_checks": ["output path correct"],
                    "successful_choices_to_keep": ["keep /output/result.json"],
                },
                "execution_anchors": [
                    {"action": "Reload output.", "evidence": "JSON parses.", "placement": "Final check"}
                ],
                "acceptance_signals": {"preserve_risk": "low"},
            },
        },
    )
    diagnosis = DiagnosisReport(
        labels=[FailureType.FALSE_CERTAINTY],
        evidence=[],
        causal_judgment="The same schema issue persists.",
        rewrite_targets=["Escalate schema repair."],
        summary="Needs method-level repair.",
    )
    traced_response = """
REVISION_TRACE_JSON:
```json
{
  "failure_ledger": {"failure_type": {"primary": "schema", "secondary_tags": []}},
  "preserve_ledger": {
    "passed_checks": ["output path correct"],
    "successful_choices_to_keep": ["keep /output/result.json"]
  },
  "selected_principles": [
    {
      "principle_id": "environment-output-grounding",
      "why_selected": "path issue",
      "failure_addressed": "missing output",
      "induced_skill_operation": "write final output",
      "preserve_constraint": "keep schema"
    }
  ],
  "execution_anchors": [
    {"action": "Reload output.", "evidence": "JSON parses.", "placement": "Final check"}
  ],
  "acceptance_signals": {
    "expected_utility_improvement": "better",
    "expected_failed_assertions_reduced": [],
    "preserve_risk": "low"
  }
}
```

REVISED_SKILL_MARKDOWN:
""" + VALID_SKILL_MARKDOWN
    llm = StaticLLMClient([traced_response])

    candidate = bm25_revision_engine(llm, revision_ablation="no-preserve-ledger").revise(
        task, skill, diagnosis
    )

    prompt = llm.calls[0]["prompt"]
    assert "Preserve Ledger" not in prompt
    assert "preserve_ledger" not in prompt
    assert "preserve_constraint" not in prompt
    assert "preserve_risk" not in prompt
    assert "previous_preserve_ledger" not in prompt
    assert "output path correct" not in prompt
    assert "keep /output/result.json" not in prompt
    trace = candidate.revised_skill.metadata["revision_trace"]
    assert candidate.revised_skill.metadata["revision_ablation"] == "no-preserve-ledger"
    assert candidate.revised_skill.metadata["removed_mechanism"] == "preserve ledger"
    assert "preserve_ledger" not in trace
    assert "preserve_constraint" not in trace["selected_principles"][0]
    assert "preserve_risk" not in trace["acceptance_signals"]
    assert candidate.revised_skill.metadata["execution_anchors"]


def test_llm_revision_engine_rejects_missing_required_revision_sections_in_strict_mode() -> None:
    task = make_task()
    skill = Skill(
        name="Brittle Skill",
        purpose="Finish this swe-debug task quickly.",
        when_to_use="Use for similar swe-debug tasks.",
        procedure=["Inspect the environment first.", "Run the verifier-visible check."],
        constraints=["Prefer a direct fix."],
        version="v0",
    )
    diagnosis = DiagnosisReport(
        labels=[FailureType.ENVIRONMENT_MISMATCH],
        evidence=[],
        causal_judgment="The skill assumes a fixed environment.",
        rewrite_targets=["Add environment discovery and fallback handling."],
        summary="Needs grounding.",
    )
    missing_procedure_response = """
REVISION_TRACE_JSON:
```json
{
  "failure_ledger": {
    "failure_type": {"primary": "environment", "secondary_tags": []}
  },
  "selected_principles": [],
  "execution_anchors": []
}
```

REVISED_SKILL_MARKDOWN:
# Revised SWE Workflow

## Purpose
Guide reusable swe-debug execution with stronger environment checks.

## When to Use
Use when verifier routes may differ across repositories.

## Constraints / Pitfalls
- Do not assume a fixed path or command before inspection.
"""
    llm = StaticLLMClient([missing_procedure_response])

    with pytest.raises(RuntimeError, match="LLM skill revision failed"):
        bm25_revision_engine(llm, allow_fallback=False).revise(task, skill, diagnosis)


def test_llm_revision_engine_records_revision_trace_and_selected_principles() -> None:
    task = make_task()
    skill = Skill(
        name="Brittle Skill",
        purpose="Finish this swe-debug task quickly.",
        when_to_use="Use for similar swe-debug tasks.",
        procedure=["Directly open `tests/unit/test_math.py`."],
        constraints=["Prefer a direct fix."],
        version="v0",
    )
    diagnosis = DiagnosisReport(
        labels=[FailureType.ENVIRONMENT_MISMATCH],
        evidence=[
            DiagnosisEvidence(
                source="verifier",
                snippet="Solution file not found: /output/scenario_3.json",
                reason="The generated artifact was not verifier-visible.",
            )
        ],
        causal_judgment="The skill writes outputs outside the checked path.",
        rewrite_targets=["Add a final verifier-visible output existence check."],
        summary="Missing output contract.",
    )
    traced_response = """
REVISION_TRACE_JSON:
```json
{
  "verifier_contract": {
    "required_output_paths": ["/output/scenario_3.json"],
    "required_schemas": ["json"],
    "numeric_thresholds": [],
    "pass_fail_assertions": ["required output file exists"]
  },
  "failure_ledger": {
    "failed_checks": ["required output file exists"],
    "actual_behavior": "missing /output/scenario_3.json",
    "likely_cause": "The skill wrote outside the verifier-visible path.",
    "failure_type": {
      "primary": "path",
      "secondary_tags": ["output_contract"]
    }
  },
  "preserve_ledger": {
    "passed_checks": [],
    "successful_choices_to_keep": []
  },
  "selected_principles": [
    {
      "principle_id": "environment-output-grounding",
      "why_selected": "It addresses missing verifier-visible outputs.",
      "failure_addressed": "required output file exists",
      "induced_skill_operation": "write and reload /output/scenario_3.json",
      "preserve_constraint": "do not change unrelated schemas"
    }
  ],
  "ignored_principles": [],
  "repeated_failure_escalation": {
    "triggered": false,
    "reason": "",
    "escalation_action": ""
  },
  "execution_anchors": [
    {
      "action": "Reload /output/scenario_3.json after writing it.",
      "evidence": "The file exists and parses as JSON.",
      "placement": "Final validation section"
    }
  ],
  "acceptance_signals": {
    "expected_utility_improvement": "path failure repaired",
    "expected_failed_assertions_reduced": ["required output file exists"],
    "preserve_risk": "low"
  }
}
```

REVISED_SKILL_MARKDOWN:
""" + VALID_SKILL_MARKDOWN

    llm = StaticLLMClient([traced_response])

    candidate = bm25_revision_engine(llm).revise(task, skill, diagnosis)

    assert candidate.revised_skill.metadata["selected_principle_ids"] == ["environment-output-grounding"]
    assert candidate.revised_skill.metadata["principle_ids"] == ["environment-output-grounding"]
    assert candidate.principles[0].principle_id == "environment-output-grounding"
    assert candidate.revised_skill.metadata["failure_primary"] == "path"
    assert candidate.metadata["failure_primary"] == "path"
    assert candidate.revised_skill.metadata["execution_anchors"][0]["placement"] == "Final validation section"
    assert (
        candidate.revised_skill.metadata["revision_trace"]["failure_ledger"]["failure_type"]["primary"]
        == "path"
    )


def test_llm_revision_engine_includes_previous_trace_as_task_local_memory() -> None:
    task = make_task()
    skill = Skill(
        name="Brittle Skill",
        purpose="Finish this swe-debug task quickly.",
        when_to_use="Use for similar swe-debug tasks.",
        procedure=["Directly open `tests/unit/test_math.py`."],
        constraints=["Prefer a direct fix."],
        version="v1",
        metadata={
            "selected_principle_ids": ["preserve-interface-contract"],
            "revision_trace": {
                "failure_ledger": {
                    "failed_checks": ["value mismatch"],
                    "actual_behavior": "wrong value",
                    "likely_cause": "method issue",
                    "failure_type": {"primary": "method", "secondary_tags": []},
                },
                "preserve_ledger": {
                    "passed_checks": ["output path correct"],
                    "successful_choices_to_keep": ["keep /output/result.json"],
                },
                "execution_anchors": [
                    {
                        "action": "Reload /output/result.json.",
                        "evidence": "JSON parses.",
                        "placement": "Final validation section",
                    }
                ],
            },
        },
    )
    diagnosis = DiagnosisReport(
        labels=[FailureType.FALSE_CERTAINTY],
        evidence=[],
        causal_judgment="The same method issue persists.",
        rewrite_targets=["Escalate method repair."],
        summary="Needs method-level repair.",
    )
    llm = StaticLLMClient([VALID_SKILL_MARKDOWN])

    bm25_revision_engine(llm).revise(task, skill, diagnosis)

    prompt = llm.calls[0]["prompt"]
    assert '"previous_failure_primary": "method"' in prompt
    assert "output path correct" in prompt
    assert "keep /output/result.json" in prompt
    assert "Reload /output/result.json." in prompt
    assert "preserve-interface-contract" in prompt


def test_llm_revision_engine_falls_back_by_default_on_llm_failure() -> None:
    task = make_task()
    skill = Skill(
        name="Brittle Skill",
        purpose="Finish this swe-debug task quickly.",
        when_to_use="Use for similar swe-debug tasks.",
        procedure=["Directly open `tests/unit/test_math.py`."],
        constraints=["Prefer a direct fix."],
        version="v0",
    )
    diagnosis = DiagnosisReport(
        labels=[FailureType.ENVIRONMENT_MISMATCH],
        evidence=[],
        causal_judgment="The skill assumes a fixed environment.",
        rewrite_targets=["Add environment discovery and fallback handling."],
        summary="Needs grounding.",
    )

    candidate = bm25_revision_engine(StaticLLMClient([])).revise(task, skill, diagnosis)

    assert candidate.revised_skill.version == "v1"
    assert candidate.revised_skill.metadata["reviser"] == "llm_fallback"
    assert "No static LLM response left" in candidate.revised_skill.metadata["llm_error"]
    assert candidate.revised_skill.metadata["revision_framework"] == "principle_bank_guided_fallback"


def test_llm_revision_engine_can_fail_instead_of_falling_back() -> None:
    task = make_task()
    skill = Skill(
        name="Brittle Skill",
        purpose="Finish this swe-debug task quickly.",
        when_to_use="Use for similar swe-debug tasks.",
        procedure=["Directly open `tests/unit/test_math.py`."],
        constraints=["Prefer a direct fix."],
        version="v0",
    )
    diagnosis = DiagnosisReport(
        labels=[FailureType.ENVIRONMENT_MISMATCH],
        evidence=[],
        causal_judgment="The skill assumes a fixed environment.",
        rewrite_targets=["Add environment discovery and fallback handling."],
        summary="Needs grounding.",
    )

    with pytest.raises(RuntimeError, match="LLM skill revision failed"):
        bm25_revision_engine(StaticLLMClient([]), allow_fallback=False).revise(task, skill, diagnosis)


def test_principle_bank_retrieves_environment_output_repair_rule() -> None:
    task = make_task()
    diagnosis = DiagnosisReport(
        labels=[FailureType.ENVIRONMENT_MISMATCH],
        evidence=[
            DiagnosisEvidence(
                source="verifier",
                snippet="Solution file not found: /output/result.json",
                reason="The agent wrote the output to a workspace-relative path.",
            )
        ],
        causal_judgment="The skill missed a verifier-visible output path requirement.",
        rewrite_targets=["Add final output path existence checks."],
        summary="Output path grounding failed.",
    )

    bank = PrincipleBank.with_seed_golden_laws(
        retrieval_config=PrincipleRetrievalConfig(method="bm25")
    )
    golden_law_bank = GoldenLawBank.with_seed_golden_laws(
        retrieval_config=PrincipleRetrievalConfig(method="bm25")
    )

    principles = bank.retrieve(task, diagnosis, limit=2)

    assert principles[0].principle_id == "environment-output-grounding"
    assert golden_law_bank.retrieve(task, diagnosis, limit=2)[0].principle_id == "environment-output-grounding"


def test_principle_bank_hybrid_rrf_retrieval_requires_dense_backend(monkeypatch) -> None:
    task = TaskSpec(
        task_id="civ6-adjacency-optimizer",
        family="civ6",
        instruction="Write the final answer to /output/scenario_3.json.",
        acceptance_criteria=["The verifier sees /output/scenario_3.json."],
    )
    diagnosis = DiagnosisReport(
        labels=[FailureType.ENVIRONMENT_MISMATCH],
        evidence=[
            DiagnosisEvidence(
                source="verifier",
                snippet="Solution file not found: /output/scenario_3.json",
                reason="The artifact was not written to the verifier-visible path.",
            )
        ],
        causal_judgment="The skill missed the exact output path contract.",
        rewrite_targets=["Assert every task-specified output path exists before finalizing."],
        summary="Missing output.",
    )
    bank = PrincipleBank.with_seed_golden_laws(
        retrieval_config=PrincipleRetrievalConfig(method="hybrid-rrf")
    )

    monkeypatch.setattr(
        "skillrevise.method.principles._dense_scores",
        lambda query, principles, config: ({}, "no_embedding_backend"),
    )

    with pytest.raises(RuntimeError, match="Dense principle retrieval unavailable"):
        bank.retrieve_candidates(task, diagnosis, limit=3)


def test_embedding_http_ignores_legacy_openai_key(monkeypatch) -> None:
    captured_headers = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"data": [{"embedding": [0.1, 0.2]}]}'

    def fake_urlopen(request, timeout):
        captured_headers.update({key.lower(): value for key, value in request.header_items()})
        return FakeResponse()

    monkeypatch.setenv("OPENAI_API_KEY", "legacy-openai-key")
    monkeypatch.delenv("SKILL_HARNESS_PRINCIPLE_EMBEDDING_API_KEY", raising=False)
    monkeypatch.setattr(principles_module, "_load_local_embedding_config", lambda: {})
    monkeypatch.setattr(principles_module.urllib.request, "urlopen", fake_urlopen)

    embeddings, status = principles_module._compute_embeddings_via_http(
        ["x"],
        PrincipleRetrievalConfig(),
        "qwen/qwen3-embedding-4b",
        "https://example.test/embeddings",
    )

    assert status == "http"
    assert embeddings == [[0.1, 0.2]]
    assert "authorization" not in captured_headers


def test_principle_absorber_adds_utility_positive_repair() -> None:
    task = make_task()
    before_skill = Skill(
        name="Brittle Skill",
        purpose="Finish quickly.",
        when_to_use="Use for similar tasks.",
        procedure=["Directly run a fixed command."],
        constraints=["Prefer speed."],
        version="v0",
    )
    after_skill = Skill(
        name="Validated Skill",
        purpose="Finish with validation.",
        when_to_use="Use when verifier output matters.",
        procedure=["Inspect verifier.", "Run the smallest reliable check."],
        constraints=["Do not assume fixed commands."],
        version="v1",
    )
    diagnosis = DiagnosisReport(
        labels=[FailureType.FALSE_CERTAINTY],
        evidence=[
            DiagnosisEvidence(
                source="verifier",
                snippet="expected output file missing",
                reason="The skill did not check the verifier-visible output path.",
            )
        ],
        causal_judgment="The skill claimed success too early.",
        rewrite_targets=["Add a final verifier-visible output existence check."],
        summary="Needs verification.",
    )
    before_eval = PairedEvaluation(
        task=task,
        skill=before_skill,
        no_skill=make_trace(skill_version=None, success=False, tokens=1000),
        with_skill=make_trace(skill_version="v0", success=False, tokens=1200),
        utility=compute_utility(
            make_trace(skill_version=None, success=False, tokens=1000),
            make_trace(skill_version="v0", success=False, tokens=1200),
        ),
    )
    after_eval = PairedEvaluation(
        task=task,
        skill=after_skill,
        no_skill=before_eval.no_skill,
        with_skill=make_trace(skill_version="v1", success=True, tokens=900),
        utility=compute_utility(before_eval.no_skill, make_trace(skill_version="v1", success=True, tokens=900)),
    )
    bank = PrincipleBank([])
    absorber = PrincipleAbsorber(bank)

    absorbed = absorber.absorb(
        task=task,
        before_skill=before_skill,
        after_skill=after_skill,
        diagnosis=diagnosis,
        revision=bm25_revision_engine(StaticLLMClient([VALID_SKILL_MARKDOWN])).revise(task, before_skill, diagnosis),
        before_eval=before_eval,
        after_eval=after_eval,
    )

    assert absorbed is not None
    assert absorbed in bank.principles
    assert absorbed.acceptance_evidence
    assert "verifier-visible output" in absorbed.repair_rule


def test_principle_absorber_keeps_task_anchors_out_of_bank_rule() -> None:
    task = TaskSpec(
        task_id="dialogue-parser",
        family="game",
        instruction="Parse a branching dialogue graph.",
        acceptance_criteria=["Verifier passes."],
    )
    before_skill = Skill(
        name="Dialogue Skill",
        purpose="Parse dialogue.",
        when_to_use="Use for graph parsing.",
        procedure=["Build nodes and edges."],
        constraints=["Validate graph."],
        version="v0",
    )
    after_skill = Skill(
        name="Dialogue Skill",
        purpose="Parse dialogue.",
        when_to_use="Use for graph parsing.",
        procedure=["Build nodes and edges.", "Validate sentinels according to verifier semantics."],
        constraints=["Validate graph."],
        version="v2",
    )
    diagnosis = DiagnosisReport(
        labels=[FailureType.FALSE_CERTAINTY, FailureType.CONTEXT_POLLUTION],
        evidence=[
            DiagnosisEvidence(
                source="verifier",
                snippet="End may be an edge target but should not become a node during reachability.",
                reason="The previous skill materialized a task-local terminal sentinel.",
            )
        ],
        causal_judgment="The skill treated a verifier exception as an ordinary graph object.",
        rewrite_targets=[
            'For graph tasks, keep edges with `to == "End"` while excluding `End` from JSON `nodes`.'
        ],
        summary="Terminal sentinel handling was too concrete.",
    )
    before_eval = PairedEvaluation(
        task=task,
        skill=before_skill,
        no_skill=make_trace(skill_version=None, success=False, tokens=1000),
        with_skill=make_trace(skill_version="v0", success=False, tokens=1200),
        utility=compute_utility(
            make_trace(skill_version=None, success=False, tokens=1000),
            make_trace(skill_version="v0", success=False, tokens=1200),
        ),
    )
    after_eval = PairedEvaluation(
        task=task,
        skill=after_skill,
        no_skill=before_eval.no_skill,
        with_skill=make_trace(skill_version="v2", success=True, tokens=900),
        utility=compute_utility(before_eval.no_skill, make_trace(skill_version="v2", success=True, tokens=900)),
    )

    absorbed = PrincipleAbsorber(PrincipleBank([])).absorb(
        task=task,
        before_skill=before_skill,
        after_skill=after_skill,
        diagnosis=diagnosis,
        revision=bm25_revision_engine(StaticLLMClient([VALID_SKILL_MARKDOWN])).revise(task, before_skill, diagnosis),
        before_eval=before_eval,
        after_eval=after_eval,
    )

    assert absorbed is not None
    bank_text = " ".join(
        [
            absorbed.repair_rule,
            absorbed.action_template,
            absorbed.trigger_evidence,
            absorbed.retrieval_text,
            " ".join(absorbed.supporting_cases),
        ]
    )
    assert "End" not in bank_text
    assert "dialogue-parser" not in bank_text
    assert "sentinel" in absorbed.repair_rule
    assert absorbed.supporting_episodes[0]["local_anchors"]["raw_rewrite_target"]


def test_freeform_revision_omits_structured_principle_bank() -> None:
    task = make_task()
    skill = Skill(
        name="Brittle Skill",
        purpose="Finish this swe-debug task quickly.",
        when_to_use="Use for similar swe-debug tasks.",
        procedure=["Directly open `tests/unit/test_math.py`."],
        constraints=["Prefer a direct fix."],
        version="v0",
    )
    diagnosis = DiagnosisReport(
        labels=[FailureType.ENVIRONMENT_MISMATCH],
        evidence=[
            DiagnosisEvidence(
                source="trace",
                snippet="fixed command failed",
                reason="The skill assumed a command before environment discovery.",
            )
        ],
        causal_judgment="The skill assumes a fixed environment.",
        rewrite_targets=["Add environment discovery."],
        summary="Needs grounding.",
    )
    llm = StaticLLMClient([VALID_SKILL_MARKDOWN])

    candidate = FreeFormLLMRevisionEngine(llm).revise(task, skill, diagnosis)

    assert candidate.revised_skill.metadata["reviser"] == "llm_freeform"
    assert llm.calls[0]["purpose"] == "skill_revision_freeform"
    assert "Retrieved seed golden laws:" not in llm.calls[0]["prompt"]
    assert "Golden-law revision protocol:" not in llm.calls[0]["prompt"]
    assert "Retrieved repair principles" not in llm.calls[0]["prompt"]
    assert "Principle-bank revision protocol:" not in llm.calls[0]["prompt"]
    assert "REVISION_TRACE_JSON" not in llm.calls[0]["prompt"]
    assert "predefined failure taxonomy" in llm.calls[0]["prompt"]
    assert "Do not regress other verifier checks" in llm.calls[0]["prompt"]
