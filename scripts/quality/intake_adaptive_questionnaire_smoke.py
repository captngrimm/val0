#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "docs/product/INTAKE_01A_ADAPTIVE_USER_INSIGHT_QUESTIONNAIRE_DESIGN.md"
QUESTION_BANK = ROOT / "docs/product/INTAKE_01A_QUESTION_BANK_AND_PATTERNS.md"
CLIENT_ZERO_PATH = Path("clients") / "karen"
PROTECTED_FOLDERS = CLIENT_ZERO_PATH / "CLIENT_FOLDERS.json"
PROTECTED_GROCERY = CLIENT_ZERO_PATH / "CLIENT_GROCERY.md"
PROTECTED = (
    PROTECTED_FOLDERS.as_posix(),
    PROTECTED_GROCERY.as_posix(),
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


def read_docs() -> str:
    assert_true(DESIGN.exists(), "design doc exists")
    assert_true(QUESTION_BANK.exists(), "question bank doc exists")
    return DESIGN.read_text(encoding="utf-8") + "\n\n" + QUESTION_BANK.read_text(encoding="utf-8")


def test_required_concepts() -> None:
    text = read_docs()
    required = (
        "consent-based intake",
        "guided discovery",
        "adaptive questioning",
        "one question at a time",
        "one workflow first",
        "explain reasoning",
        "state assumptions",
        "ask permission before saving",
        "no manipulation",
        "no coercion",
        "no fake certainty",
        "no diagnosing",
        "no professional replacement",
        "question bank",
        "examples",
        "anti-examples",
        "user-controlled personalization",
        "no dark patterns",
    )
    for needle in required:
        assert_contains(text, needle, f"required concept {needle}")

    assert_contains(text, "role/work type", "context extraction role/work type")
    assert_contains(text, "privacy sensitivity", "context extraction privacy sensitivity")
    assert_contains(text, "confidence level", "context extraction confidence level")
    assert_contains(text, "cashier", "cashier example present")
    assert_contains(text, "overwhelmed", "overwhelm example present")


def test_no_forbidden_leakage() -> None:
    text = read_docs()
    assert_not_contains(text, "CLIENT_GROCERY.md", "does not mention protected grocery live file")
    assert_not_contains(text, "CLIENT_FOLDERS.json", "does not mention protected folders live file")
    assert_not_contains(text, "/" + CLIENT_ZERO_PATH.as_posix(), "does not mention live client path")
    assert_not_contains(text, "Insan" + "ity", "does not leak old nickname")


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
    test_required_concepts()
    test_no_forbidden_leakage()
    test_protected_not_staged()
    print("PASS: intake adaptive questionnaire smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
