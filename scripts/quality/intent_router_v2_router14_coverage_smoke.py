#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs" / "architecture" / "ROUTER_14_FINAL_SHADOW_COVERAGE_UPDATE.md"
ARCH_DOC = ROOT / "docs" / "architecture" / "INTENT_ROUTER_V2_MARCHING_ORDER.md"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def _coverage_rows() -> list[dict]:
    result = subprocess.run(
        ["python3", "scripts/diagnostics/intent_router_v2_coverage_report.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"coverage report runs: {result.stderr}")
    rows = json.loads(result.stdout)
    assert_true(isinstance(rows, list) and rows, "coverage rows exist")
    return rows


def test_router14_report_content() -> None:
    assert_true(REPORT.exists(), "ROUTER-14 report exists")
    text = REPORT.read_text(encoding="utf-8")
    for needle in (
        "ROUTER-13 Observation Results",
        "document_summary",
        "gcal_delete",
        "reminder_query",
        "reminder_delete",
        "reminder_create",
        "pending_action_reply",
        "reminder_update",
        "task_complete",
        "task_delete",
        "Shadow mode was disabled",
        "full smoke passed 24/24",
        "No runtime behavior changed",
    ):
        assert_contains(text, needle, "ROUTER-14 report")


def test_coverage_stays_honest_after_router13() -> None:
    rows = _coverage_rows()
    by_intent = {str(row.get("intent")): row for row in rows}
    for intent in ("document_summary", "gcal_delete", "reminder_query", "reminder_delete"):
        assert_true(by_intent.get(intent, {}).get("status") == "COVERED", f"{intent} is covered")
    for intent in ("pending_action_reply", "reminder_update", "task_complete", "task_delete"):
        assert_true(
            by_intent.get(intent, {}).get("status") == "NEEDS_LIVE_OBSERVATION",
            f"{intent} remains an observation gap",
        )

    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status") or "")
        counts[status] = counts.get(status, 0) + 1
    assert_true(counts.get("COVERED") == 11, "covered count remains 11")
    assert_true(counts.get("NEEDS_LIVE_OBSERVATION") == 4, "live observation gaps remain 4")
    assert_true(counts.get("NEEDS_ACTUAL_LABEL", 0) == 0, "actual label gaps remain 0")
    assert_true(counts.get("SHADOW_ONLY") == 2, "shadow-only count remains 2")


def test_marching_order_mentions_router14() -> None:
    assert_true(ARCH_DOC.exists(), "marching order doc exists")
    text = ARCH_DOC.read_text(encoding="utf-8")
    for needle in (
        "ROUTER-14 Final Shadow Coverage Update",
        "docs/architecture/ROUTER_14_FINAL_SHADOW_COVERAGE_UPDATE.md",
        "11 `COVERED`",
        "4 `NEEDS_LIVE_OBSERVATION`",
        "full smoke passed 24/24",
    ):
        assert_contains(text, needle, "marching order ROUTER-14")


def main() -> int:
    test_router14_report_content()
    test_coverage_stays_honest_after_router13()
    test_marching_order_mentions_router14()
    print("PASS: Intent Router v2 ROUTER-14 coverage smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
