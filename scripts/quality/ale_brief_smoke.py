#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BRIEF = ROOT / "docs/product/ALE_BRIEF_01_FOUNDER_PARTNER_INTERNAL_BRIEF.md"
TALK_TRACK = ROOT / "docs/product/ALE_BRIEF_01_TALK_TRACK_AND_BOUNDARIES.md"
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
    assert_true(BRIEF.exists(), "Ale founder/partner brief exists")
    assert_true(TALK_TRACK.exists(), "Ale talk track exists")
    return BRIEF.read_text(encoding="utf-8") + "\n\n" + TALK_TRACK.read_text(encoding="utf-8")


def test_required_concepts() -> None:
    text = read_docs()
    required = (
        "Ale",
        "founder beta",
        "trusted partner",
        "personal operator",
        "Telegram for now",
        "one workflow first",
        "Organizar mi día",
        "Google Calendar optional",
        "confirmation",
        "no full autonomy",
        "no fake consciousness",
        "no professional replacement",
        "no overpromising",
        "feedback",
        "$30",
        "soft close",
        "boundaries",
        "Simple English",
        "Spanish-first",
        "optional support/practice",
        "not replacing the Spanish pitch",
        "Why Not Just ChatGPT",
        "one-week test",
        "mental load",
        "It is my pleasure",
    )
    for needle in required:
        assert_contains(text, needle, f"required Ale brief concept {needle}")


def test_no_forbidden_scope_or_client_leakage() -> None:
    text = read_docs()
    for needle in (
        "CLIENT_GROCERY.md",
        "CLIENT_FOLDERS.json",
        "/" + "clients" + "/" + "karen",
        "Insan" + "ity",
        "profile write implemented",
        "DB schema migration added",
    ):
        assert_not_contains(text, needle, "Ale docs avoid forbidden/runtime leakage")


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
    test_no_forbidden_scope_or_client_leakage()
    test_protected_not_staged()
    print("PASS: Ale founder/partner brief smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
