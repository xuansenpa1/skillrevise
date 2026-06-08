from __future__ import annotations


# SWE-Skills-Bench export

import json
from pathlib import Path

from scripts.export_swe_skills_bench_as_skillsbench import export_swe_skills_bench


def test_export_swe_skills_bench_as_skillsbench(tmp_path: Path) -> None:
    swe_root = tmp_path / "SWE-Skills-Bench-main"
    (swe_root / "tasks" / "batch1").mkdir(parents=True)
    (swe_root / "tests" / "batch1").mkdir(parents=True)
    (swe_root / "skills" / "demo-skill").mkdir(parents=True)
    (swe_root / "tasks" / "batch1" / "demo-skill.md").write_text("Fix the demo project.")
    (swe_root / "tests" / "batch1" / "test_demo_skill.py").write_text("def test_ok():\n    assert True\n")
    (swe_root / "tests" / "batch1" / "_dependency_utils.py").write_text("HELPER = True\n")
    (swe_root / "skills" / "demo-skill" / "SKILL.md").write_text("# Demo Skill\n")
    config = {
        "skills": [
            {
                "id": "demo-skill",
                "repo": {"url": "https://example.com/demo.git", "commit": "abc123"},
                "environment": {
                    "base_image": "python:3.11",
                    "limits": {"cpus": "2", "memory": "2g", "total_timeout_sec": 1200},
                    "evaluation": [
                        {
                            "method": "build_check",
                            "enabled": True,
                            "params": {"build_command": "python -m compileall .", "timeout": 300},
                        },
                        {
                            "method": "unit_test",
                            "enabled": True,
                            "params": {"test_command": "python -m pytest /workspace/tests/test_demo_skill.py", "timeout": 200},
                        },
                    ],
                },
            }
        ]
    }

    out = tmp_path / "exported"
    summary = export_swe_skills_bench(
        swe_root,
        out,
        config=config,
        include_reference_skill=True,
        overwrite=True,
    )

    task_dir = out / "tasks" / "swe-batch1-demo-skill"
    manifest = json.loads((out / "swe_skillsbench_tasks.json").read_text())
    jobs = json.loads((out / "all_jobs.json").read_text())

    assert summary["num_tasks"] == 1
    assert manifest["tasks"][0]["task_id"] == "swe-batch1-demo-skill"
    assert manifest["tasks"][0]["metadata"]["repo_path"] == str(task_dir)
    assert manifest["tasks"][0]["metadata"]["verifier_command"] == "bash tests/test.sh"
    assert jobs == [{"name": "swe-batch1-demo-skill", "task_id": "swe-batch1-demo-skill"}]
    assert (task_dir / "instruction.md").read_text().startswith("# SWE-Skills-Bench: demo-skill")
    assert "FROM python:3.11" in (task_dir / "environment" / "Dockerfile").read_text()
    assert "reward.txt" in (task_dir / "tests" / "test.sh").read_text()
    assert (task_dir / "tests" / "test_demo_skill.py").exists()
    assert (task_dir / "tests" / "_dependency_utils.py").exists()
    assert (task_dir / "reference_skill" / "SKILL.md").read_text() == "# Demo Skill\n"


# Benchmark task selection

from scripts import select_skilllearnbench_tasks, select_swe_tasks


def test_select_swe_tasks_accepts_source_batch_skill_entries(tmp_path: Path) -> None:
    export_root = tmp_path / "swe_export"
    export_root.mkdir()
    (export_root / "swe_skillsbench_tasks.json").write_text(
        json.dumps(
            {
                "benchmark": "swe-skills-bench-as-skillsbench",
                "count": 3,
                "tasks": [
                    {"task_id": "swe-batch1-alpha-skill", "family": "alpha-skill"},
                    {"task_id": "swe-batch2-beta-skill", "family": "beta-skill"},
                    {"task_id": "swe-batch3-gamma-skill", "family": "gamma-skill"},
                ],
            }
        )
    )
    (export_root / "all_jobs.json").write_text(
        json.dumps(
            [
                {"name": "alpha", "task_id": "swe-batch1-alpha-skill"},
                {"name": "beta", "task_id": "swe-batch2-beta-skill"},
                {"name": "gamma", "task_id": "swe-batch3-gamma-skill"},
            ]
        )
    )
    selection = tmp_path / "selected.txt"
    selection.write_text("batch2/beta-skill\nswe-batch1-alpha-skill\n")

    assert select_swe_tasks.main([str(export_root), "--selection", str(selection), "--name", "demo"]) == 0

    manifest = json.loads((export_root / "demo_tasks.json").read_text())
    jobs = json.loads((export_root / "demo_jobs.json").read_text())
    assert manifest["benchmark"] == "swe-skills-bench-as-skillsbench-demo"
    assert manifest["count"] == 2
    assert [task["task_id"] for task in manifest["tasks"]] == [
        "swe-batch2-beta-skill",
        "swe-batch1-alpha-skill",
    ]
    assert [job["task_id"] for job in jobs] == [
        "swe-batch2-beta-skill",
        "swe-batch1-alpha-skill",
    ]


def test_select_skilllearnbench_tasks_preserves_selection_order(tmp_path: Path) -> None:
    export_root = tmp_path / "skilllearnbench_export"
    export_root.mkdir()
    (export_root / "skillsbench_tasks.json").write_text(
        json.dumps(
            {
                "benchmark": "skilllearnbench-as-skillsbench",
                "count": 3,
                "tasks": [
                    {"task_id": "family-a-1", "family": "family-a"},
                    {"task_id": "family-b-1", "family": "family-b"},
                    {"task_id": "family-c-1", "family": "family-c"},
                ],
            }
        )
    )
    (export_root / "all_jobs.json").write_text(
        json.dumps(
            [
                {"name": "a", "task_id": "family-a-1"},
                {"name": "b", "task_id": "family-b-1"},
                {"name": "c", "task_id": "family-c-1"},
            ]
        )
    )
    selection = tmp_path / "selected50.txt"
    selection.write_text("family-c-1\nfamily-a-1\n")

    assert select_skilllearnbench_tasks.main([str(export_root), "--selection", str(selection), "--name", "selected50"]) == 0

    manifest = json.loads((export_root / "selected50_tasks.json").read_text())
    jobs = json.loads((export_root / "selected50_jobs.json").read_text())
    assert manifest["benchmark"] == "skilllearnbench-as-skillsbench-selected50"
    assert manifest["selection"]["task_ids"] == ["family-c-1", "family-a-1"]
    assert [task["task_id"] for task in manifest["tasks"]] == ["family-c-1", "family-a-1"]
    assert [job["task_id"] for job in jobs] == ["family-c-1", "family-a-1"]


# Publishability audit script

from scripts import audit_publishable_skills


def test_audit_publishable_skills_flags_redacted_and_local_paths(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "Use [REDACTED_PATH] if present.\n"
        "Project: /Users/example/private-project\n"
    )

    files = audit_publishable_skills.iter_candidate_files([tmp_path / "skills"])
    findings = audit_publishable_skills.audit_files(files, root=tmp_path / "skills")

    assert {finding.category for finding in findings} == {
        "redacted_placeholder",
        "local_absolute_path",
    }
    assert {finding.severity for finding in findings} == {"error"}
    assert audit_publishable_skills.main([str(tmp_path / "skills")]) == 1


def test_audit_publishable_skills_warns_on_benchmark_paths_by_default(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "Run pytest in /root/project and write report.json when debugging.\n"
    )

    files = audit_publishable_skills.iter_candidate_files([tmp_path / "skills"])
    findings = audit_publishable_skills.audit_files(files, root=tmp_path / "skills")

    assert {finding.category for finding in findings} == {
        "container_path",
        "test_or_verifier_reference",
        "answer_artifact_reference",
    }
    assert {finding.severity for finding in findings} == {"warning"}
    assert audit_publishable_skills.main([str(tmp_path / "skills")]) == 0
    assert audit_publishable_skills.main([str(tmp_path / "skills"), "--fail-on", "warning"]) == 1


def test_audit_publishable_skills_does_not_flag_hyphenated_words_as_openai_keys(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("https://example.com/ai-task-automation-revolution\n")

    files = audit_publishable_skills.iter_candidate_files([tmp_path / "skills"])
    findings = audit_publishable_skills.audit_files(files, root=tmp_path / "skills")

    assert findings == []
