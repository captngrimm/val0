#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/diagnostics/intent_router_v2_coverage_report.py"
DOC = ROOT / "docs/architecture/ROUTER_COVERAGE_01_ADAPTIVE_INTAKE_COVERAGE_UPDATE.md"
CLIENT_ZERO_PATH = Path("clients") / "karen"
PROTECTED = (
    (CLIENT_ZERO_PATH / "CLIENT_FOLDERS.json").as_posix(),
    (CLIENT_ZERO_PATH / "CLIENT_GROCERY.md").as_posix(),
)

ADAPTIVE_LABELS = (
    "adaptive_intake_start",
    "adaptive_intake_domain",
    "adaptive_intake_followup",
    "adaptive_intake_recommendation",
)


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: {actual!r} != {expected!r}")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def test_coverage_report_recognizes_adaptive_labels() -> None:
    result = subprocess.run(
        ["python3", "scripts/diagnostics/intent_router_v2_coverage_report.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"coverage json runs: {result.stderr}")
    rows = json.loads(result.stdout)
    by_intent = {str(row.get("intent")): row for row in rows}
    for label in ADAPTIVE_LABELS:
        row = by_intent.get(label)
        assert_true(row is not None, f"coverage row exists for {label}")
        assert_true(int(row.get("sample_count") or 0) > 0, f"{label} has sample coverage")
        assert_true(bool(row.get("has_shadow_classifier")), f"{label} has classifier coverage")
        assert_true(not bool(row.get("has_actual_label")), f"{label} does not claim actual label yet")
        assert_true(not bool(row.get("observed_in_report_or_logs")), f"{label} does not claim observation yet")
        assert_equal(str(row.get("status")), "SHADOW_ONLY", f"{label} remains shadow-only")


def test_text_report_mentions_adaptive_labels() -> None:
    result = subprocess.run(
        ["python3", "scripts/diagnostics/intent_router_v2_coverage_report.py", "--no-write"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"coverage text runs: {result.stderr}")
    for label in ADAPTIVE_LABELS:
        assert_contains(result.stdout, label, f"text report includes {label}")
    assert_contains(result.stdout, "SHADOW_ONLY", "text report includes shadow-only status")


def test_source_and_doc_boundaries() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    for label in ADAPTIVE_LABELS:
        assert_contains(source, label, f"coverage source knows {label}")
    assert_contains(source, "SHADOW_ONLY_INTENTS", "coverage source keeps shadow-only set")

    doc = DOC.read_text(encoding="utf-8")
    for needle in (
        "diagnostic/tooling only",
        "does not edit `bot.py`",
        "does not route live messages through Intent Router v2",
        "runtime handlers via `core/adaptive_intake.py`",
        "sample coverage",
        "classifier: yes",
        "actual label: no",
        "observed: no",
        "status: `SHADOW_ONLY`",
    ):
        assert_contains(doc, needle, f"doc boundary {needle}")


def test_protected_not_staged() -> None:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", *PROTECTED],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert_true(proc.stdout.strip() == "", "protected live data files are not staged")


def main() -> int:
    test_coverage_report_recognizes_adaptive_labels()
    test_text_report_mentions_adaptive_labels()
    test_source_and_doc_boundaries()
    test_protected_not_staged()
    print("PASS: router adaptive intake coverage smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
