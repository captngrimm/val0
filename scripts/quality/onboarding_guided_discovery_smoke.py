#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "docs" / "product" / "ONBOARDING_01A_GUIDED_WORKFLOW_DISCOVERY_DESIGN.md"
EXAMPLES = ROOT / "docs" / "product" / "ONBOARDING_01A_DISCOVERY_SCRIPT_EXAMPLES.md"
PROTECTED = (
    "clients/karen/CLIENT_FOLDERS.json",
    "clients/karen/CLIENT_GROCERY.md",
)


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r}")


def _read(path: Path) -> str:
    assert_true(path.exists(), f"{path} exists")
    return path.read_text(encoding="utf-8")


def _assert_protected_not_staged() -> None:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", *PROTECTED],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert_true(proc.stdout.strip() == "", "protected live data files are not staged")


def test_guided_discovery_docs() -> None:
    combined = _read(DESIGN) + "\n" + _read(EXAMPLES)
    for needle in (
        "guided workflow discovery",
        "one workflow first",
        "pain before features",
        "concrete examples",
        "agenda / tasks / reminders",
        "documents / case / admin",
        "clients / business follow-up",
        "ideas / folders",
        "routines",
        "boundaries",
        "founder beta",
        "privacy",
        "trust",
        "avoid feature dumping",
        "no feature dumping",
        "magic AI",
        "AGI",
    ):
        assert_contains(combined, needle, f"guided discovery concept {needle}")


def main() -> int:
    test_guided_discovery_docs()
    _assert_protected_not_staged()
    print("PASS: onboarding guided discovery smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
