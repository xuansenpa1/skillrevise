#!/usr/bin/env python3
"""Audit skill files before publishing them."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".py", ".sh", ".toml"}


@dataclass(frozen=True)
class Finding:
    severity: str
    category: str
    path: str
    line: int
    text: str


ERROR_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "redacted_placeholder",
        re.compile(r"\[REDACTED[^\]]*\]|REDACTED_(PATH|SECRET|TOKEN|KEY)", re.IGNORECASE),
    ),
    (
        "local_absolute_path",
        re.compile(r"/Users/[^\s`\"')]+|/private/var/[^\s`\"')]+|/Volumes/[^\s`\"')]+|[A-Za-z]:\\Users\\[^\s`\"')]+"),
    ),
    (
        "secret_like_value",
        re.compile(
            r"(?<![A-Za-z0-9_])sk-[A-Za-z0-9_-]{20,}(?![A-Za-z0-9_])|"
            r"(?<![A-Za-z0-9_])gh[pousr]_[A-Za-z0-9_]{20,}(?![A-Za-z0-9_])|"
            r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])|"
            r"(?<![A-Za-z0-9_-])AIza[0-9A-Za-z_-]{25,}(?![A-Za-z0-9_-])|"
            r"(?<![A-Za-z0-9-])xox[baprs]-[A-Za-z0-9-]{20,}(?![A-Za-z0-9-])"
        ),
    ),
)

WARNING_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("container_path", re.compile(r"/root/|/workspace/|/tmp/|/logs/")),
    (
        "test_or_verifier_reference",
        re.compile(
            r"tests?/test|test_outputs\.py|pytest|verifier|reward\.txt|unit_test|expected output",
            re.IGNORECASE,
        ),
    ),
    (
        "task_manifest_reference",
        re.compile(r"instruction\.md|task\.toml|solve\.sh|task_id|task id", re.IGNORECASE),
    ),
    (
        "answer_artifact_reference",
        re.compile(r"answer\.json|output\.json|report\.json|solution\.py|loss\.npz", re.IGNORECASE),
    ),
)


def iter_candidate_files(paths: Iterable[Path], extensions: set[str] = DEFAULT_EXTENSIONS) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file():
            if path.suffix in extensions:
                files.append(path)
            continue
        if not path.is_dir():
            raise FileNotFoundError(path)
        files.extend(p for p in path.rglob("*") if p.is_file() and p.suffix in extensions)
    return sorted(set(files))


def audit_files(files: Iterable[Path], root: Path | None = None) -> list[Finding]:
    findings: list[Finding] = []
    patterns = (("error", ERROR_PATTERNS), ("warning", WARNING_PATTERNS))
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(errors="replace")
        display_path = str(path.relative_to(root)) if root and path.is_relative_to(root) else str(path)
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            for severity, pattern_group in patterns:
                for category, pattern in pattern_group:
                    if pattern.search(line):
                        findings.append(
                            Finding(
                                severity=severity,
                                category=category,
                                path=display_path,
                                line=line_no,
                                text=stripped[:240],
                            )
                        )
    return findings


def summarize(findings: Sequence[Finding], files_scanned: int) -> dict[str, object]:
    by_severity: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for finding in findings:
        by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
        by_category[finding.category] = by_category.get(finding.category, 0) + 1
    return {
        "files_scanned": files_scanned,
        "findings": len(findings),
        "by_severity": by_severity,
        "by_category": by_category,
    }


def print_text_report(summary: dict[str, object], findings: Sequence[Finding], max_examples: int) -> None:
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not findings:
        return
    print("\nExamples:")
    for finding in findings[:max_examples]:
        print(f"- [{finding.severity}] {finding.category}: {finding.path}:{finding.line}: {finding.text}")
    if len(findings) > max_examples:
        print(f"... {len(findings) - max_examples} more findings omitted")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan skill files/resources for publishability risks such as redacted placeholders, "
            "local paths, secret-like values, and task-specific verifier references."
        )
    )
    parser.add_argument("paths", nargs="+", help="Skill files or directories to audit.")
    parser.add_argument("--json-output", help="Optional path for a JSON audit report.")
    parser.add_argument("--max-examples", type=int, default=50, help="Maximum text examples to print.")
    parser.add_argument(
        "--fail-on",
        choices=("error", "warning", "never"),
        default="error",
        help="Exit non-zero when findings at this level are present.",
    )
    args = parser.parse_args(argv)

    roots = [Path(p).resolve() for p in args.paths]
    files = iter_candidate_files(roots)
    root = roots[0] if len(roots) == 1 and roots[0].is_dir() else None
    findings = audit_files(files, root=root)
    report = {
        "summary": summarize(findings, len(files)),
        "findings": [asdict(finding) for finding in findings],
    }

    if args.json_output:
        Path(args.json_output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print_text_report(report["summary"], findings, args.max_examples)

    has_errors = any(f.severity == "error" for f in findings)
    has_warnings = bool(findings)
    if args.fail_on == "error" and has_errors:
        return 1
    if args.fail_on == "warning" and has_warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
