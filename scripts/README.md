# Scripts

This directory contains the reusable benchmark-preparation and publication-audit scripts kept in the GitHub release.

Included scripts:

- `export_skilllearnbench_as_skillsbench.py`: convert SkillLearnBench tasks into the harness interface.
- `export_swe_skills_bench_as_skillsbench.py`: convert SWE-Skills-Bench tasks into the harness interface; requires PyYAML.
- `select_skilllearnbench_tasks.py`: read a SkillLearnBench task-selection file and materialize selected manifest/jobs.
- `select_swe_tasks.py`: read a SWE-Skills-Bench task-selection file and materialize selected manifest/jobs.
- `audit_publishable_skills.py`: scan candidate public skill bundles for redacted placeholders, local paths, secret-like strings, and task-specific verifier references.
