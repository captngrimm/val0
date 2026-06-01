#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs" / "architecture" / "ROUTER_07_SHADOW_OBSERVATION_REPORT.md"
ARCH_DOC = ROOT / "docs" / "architecture" / "INTENT_ROUTER_V2_MARCHING_ORDER.md"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def test_report_content() -> None:
    assert_true(REPORT.exists(), "ROUTER-07 report exists")
    text = REPORT.read_text(encoding="utf-8")
    for needle in (
        "2026-05-31 late evening Panama time",
        "task_query",
        "agenda_query",
        "gcal_create",
        "destructive_confirmation",
        "reminder_create",
        "document_ocr",
        "case_status",
        "match=True",
        "Karen RC full smoke passed after disable",
        "No behavior change occurred",
    ):
        assert_contains(text, needle, "ROUTER-07 report content")


def test_architecture_doc_mentions_report() -> None:
    assert_true(ARCH_DOC.exists(), "architecture doc exists")
    text = ARCH_DOC.read_text(encoding="utf-8")
    for needle in (
        "ROUTER-07 Shadow Observation Report",
        "docs/architecture/ROUTER_07_SHADOW_OBSERVATION_REPORT.md",
        "first clean real shadow observation pass",
        "full smoke passed after shadow mode was disabled",
        "There was no behavior change",
    ):
        assert_contains(text, needle, "architecture doc ROUTER-07 content")


def test_no_runtime_files_required() -> None:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, "git status succeeded")
    allowed_prefixes = (
        " M clients/karen/CLIENT_GROCERY.md",
        " M docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md",
        "A  docs/architecture/ROUTER_07_SHADOW_OBSERVATION_REPORT.md",
        "?? docs/architecture/ROUTER_07_SHADOW_OBSERVATION_REPORT.md",
        "A  scripts/quality/router_shadow_observation_report_smoke.py",
        "?? scripts/quality/router_shadow_observation_report_smoke.py",
        " M scripts/quality/intent_router_v2_docs_smoke.py",
    )
    for raw in result.stdout.splitlines():
        if not raw.strip():
            continue
        assert_true(
            raw.startswith(allowed_prefixes),
            f"unexpected runtime change in status: {raw}",
        )


def main() -> int:
    test_report_content()
    test_architecture_doc_mentions_report()
    test_no_runtime_files_required()
    print("PASS: Router shadow observation report smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
