#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/product/POWERCLUB_CRM_01A_CORPORATE_BRIEF_MVP_SCOPE.md"
PROTECTED = (
    (Path("clients") / "karen" / "CLIENT_FOLDERS.json").as_posix(),
    (Path("clients") / "karen" / "CLIENT_GROCERY.md").as_posix(),
    "bot.py",
)


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r}")


def read_doc() -> str:
    assert_true(DOC.exists(), "Power Club CRM brief exists")
    return DOC.read_text(encoding="utf-8")


def test_required_sections() -> None:
    text = read_doc()
    for needle in (
        "Executive Summary",
        "Problem Summary",
        "Current Flow Assumptions",
        "Target Users",
        "CRM MVP Scope",
        "Suggested Data Fields",
        "Operator / Asesor Workflow",
        "Manager Workflow",
        "Dashboard Requirements",
        "30/60/90 Roadmap",
        "Pilot Proposal",
        "Pricing Options",
        "Boundaries / What Phase 1 Does NOT Include",
        "Meeting Questions for Karen / GM",
        "Next Recommended Step",
    ):
        assert_contains(text, needle, "required Power Club section")


def test_known_pilot_facts_and_boundaries() -> None:
    text = read_doc()
    for needle in (
        "around 10 branches",
        "35-45 users/operators",
        "1,500-2,000 records per month",
        "Excel/export",
        "lost sales",
        "poor follow-up",
        "low visibility",
        "General Manager",
        "pilot",
        "not a production CRM",
        "no live backend integration",
        "Phase 1 does not send WhatsApp automation",
        "No real customer data in demo materials",
        "Karen live files",
        "Broad Val0 runtime refactor",
    ):
        assert_contains(text, needle, "Power Club pilot facts and boundaries")


def test_no_forbidden_leakage_or_overreach() -> None:
    text = read_doc()
    for needle in (
        "CLIENT_FOLDERS.json",
        "CLIENT_GROCERY.md",
        "/clients/karen",
        "payment integration included",
        "WhatsApp automation included",
        "full SaaS included",
        "production-ready CRM",
        "real-time integration included",
    ):
        assert_not_contains(text, needle, "Power Club doc avoids leakage/overreach")


def test_protected_not_staged() -> None:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", *PROTECTED],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert_true(proc.stdout.strip() == "", "protected runtime/client files are not staged")


def main() -> int:
    test_required_sections()
    test_known_pilot_facts_and_boundaries()
    test_no_forbidden_leakage_or_overreach()
    test_protected_not_staged()
    print("PASS: Power Club CRM brief smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
