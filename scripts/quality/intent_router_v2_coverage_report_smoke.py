#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "diagnostics" / "intent_router_v2_coverage_report.py"
REPORT = ROOT / "docs" / "architecture" / "ROUTER_09_COVERAGE_GAP_REPORT.md"
ARCH_DOC = ROOT / "docs" / "architecture" / "INTENT_ROUTER_V2_MARCHING_ORDER.md"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def test_script_exists_compiles_and_runs() -> None:
    assert_true(SCRIPT.exists(), "coverage diagnostics script exists")
    source = SCRIPT.read_text(encoding="utf-8")
    for needle in (
        "--json",
        "COVERED",
        "SHADOW_ONLY",
        "NEEDS_ACTUAL_LABEL",
        "NEEDS_LIVE_OBSERVATION",
        "tmp/router_coverage/intent_router_v2_coverage_report.txt",
        "SAMPLES",
    ):
        assert_contains(source, needle, "coverage diagnostics source")

    compile_result = subprocess.run(
        ["./scripts/val0py", "-m", "py_compile", "scripts/diagnostics/intent_router_v2_coverage_report.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(compile_result.returncode == 0, f"coverage script compiles: {compile_result.stderr}")

    run_result = subprocess.run(
        ["python3", "scripts/diagnostics/intent_router_v2_coverage_report.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(run_result.returncode == 0, f"coverage script runs: {run_result.stderr}")
    assert_contains(run_result.stdout, "task_delete", "coverage output has task_delete")
    assert_contains(run_result.stdout, "gcal_delete", "coverage output has gcal_delete")

    json_result = subprocess.run(
        ["python3", "scripts/diagnostics/intent_router_v2_coverage_report.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(json_result.returncode == 0, f"coverage json runs: {json_result.stderr}")
    rows = json.loads(json_result.stdout)
    assert_true(isinstance(rows, list) and rows, "coverage json has rows")
    assert_true(any(row.get("intent") == "document_summary" for row in rows), "json has document_summary")
    status_by_intent = {str(row.get("intent")): str(row.get("status")) for row in rows}
    for intent in (
        "pending_action_reply",
        "reminder_delete",
        "reminder_query",
        "reminder_update",
        "task_complete",
    ):
        assert_true(
            status_by_intent.get(intent) == "NEEDS_LIVE_OBSERVATION",
            f"{intent} moved past missing actual label",
        )


def test_report_doc_content() -> None:
    assert_true(REPORT.exists(), "coverage report doc exists")
    text = REPORT.read_text(encoding="utf-8")
    for needle in (
        "47 representative Karen phrases",
        "COVERED",
        "SHADOW_ONLY",
        "NEEDS_ACTUAL_LABEL",
        "NEEDS_LIVE_OBSERVATION",
        "task_delete",
        "reminder_delete",
        "document_summary",
        "gcal_delete",
        "classifier coverage",
        "actual handler labels",
        "sample harness coverage",
        "clean shadow observation",
        "Karen RC full smoke passing",
        "not a router refactor",
        "ROUTER-10",
        "pending_action_reply",
        "task_complete",
    ):
        assert_contains(text, needle, "coverage report doc")


def test_marching_order_mentions_router_09() -> None:
    assert_true(ARCH_DOC.exists(), "marching order doc exists")
    text = ARCH_DOC.read_text(encoding="utf-8")
    for needle in (
        "ROUTER-09 Coverage Gap Report",
        "docs/architecture/ROUTER_09_COVERAGE_GAP_REPORT.md",
        "scripts/diagnostics/intent_router_v2_coverage_report.py",
        "NEEDS_ACTUAL_LABEL",
        "NEEDS_LIVE_OBSERVATION",
        "ROUTER-10 Missing Actual Labels",
    ):
        assert_contains(text, needle, "marching order ROUTER-09")


def main() -> int:
    test_script_exists_compiles_and_runs()
    test_report_doc_content()
    test_marching_order_mentions_router_09()
    print("PASS: Intent Router v2 coverage report smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
