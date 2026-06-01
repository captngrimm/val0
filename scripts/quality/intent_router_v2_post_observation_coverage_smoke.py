#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs" / "architecture" / "ROUTER_12_POST_OBSERVATION_COVERAGE_UPDATE.md"
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
    assert_true(result.returncode == 0, f"coverage json runs: {result.stderr}")
    rows = json.loads(result.stdout)
    assert_true(isinstance(rows, list) and rows, "coverage json rows")
    return rows


def test_router_12_report_exists_and_describes_update() -> None:
    assert_true(REPORT.exists(), "ROUTER-12 report exists")
    text = REPORT.read_text(encoding="utf-8")
    for needle in (
        "ROUTER-11 Results",
        "document_summary",
        "gcal_delete",
        "reminder_query",
        "reminder_delete",
        "COVERED`: 11",
        "NEEDS_LIVE_OBSERVATION`: 4",
        "NEEDS_ACTUAL_LABEL`: 0",
        "SHADOW_ONLY`: 2",
        "pending_action_reply",
        "reminder_update",
        "task_complete",
        "task_delete",
        "full smoke passed",
        "No runtime behavior changed",
    ):
        assert_contains(text, needle, "ROUTER-12 report")


def test_coverage_output_after_router_11() -> None:
    rows = _coverage_rows()
    by_intent = {str(row.get("intent")): row for row in rows}
    for intent in ("document_summary", "gcal_delete", "reminder_query", "reminder_delete"):
        row = by_intent.get(intent)
        assert_true(row is not None, f"{intent} exists in coverage")
        assert_true(row.get("status") == "COVERED", f"{intent} is COVERED")

    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status") or "")
        status_counts[status] = status_counts.get(status, 0) + 1
    assert_true(status_counts.get("COVERED", 0) >= 11, "COVERED count at least 11")
    assert_true(status_counts.get("NEEDS_ACTUAL_LABEL", 0) == 0, "no missing actual labels")
    assert_true(status_counts.get("SHADOW_ONLY", 0) == 2, "shadow-only count remains 2")

    for intent in ("pending_action_reply", "reminder_update", "task_complete", "task_delete"):
        row = by_intent.get(intent)
        assert_true(row is not None, f"{intent} exists in coverage")
        assert_true(row.get("status") == "NEEDS_LIVE_OBSERVATION", f"{intent} remains live observation gap")


def test_marching_order_mentions_router_12() -> None:
    assert_true(ARCH_DOC.exists(), "marching order doc exists")
    text = ARCH_DOC.read_text(encoding="utf-8")
    for needle in (
        "ROUTER-12 Post-Observation Coverage Update",
        "docs/architecture/ROUTER_12_POST_OBSERVATION_COVERAGE_UPDATE.md",
        "11 `COVERED`",
        "4 `NEEDS_LIVE_OBSERVATION`",
        "there is no behavior change",
    ):
        assert_contains(text, needle, "marching order ROUTER-12")


def main() -> int:
    test_router_12_report_exists_and_describes_update()
    test_coverage_output_after_router_11()
    test_marching_order_mentions_router_12()
    print("PASS: Intent Router v2 post-observation coverage smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
