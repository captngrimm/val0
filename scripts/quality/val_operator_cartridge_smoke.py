#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARTRIDGE = ROOT / "docs" / "product" / "VAL_OPERATOR_PERSONALITY_CARTRIDGE_V1.md"
REPAIR = ROOT / "docs" / "product" / "CONVERSATIONAL_REPAIR_LAYER_V1.md"
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


def test_cartridge_concepts() -> None:
    text = _read(CARTRIDGE)
    combined = text + "\n" + _read(REPAIR)
    for needle in (
        "conversational repair",
        "ambiguity detection",
        "preference-based educated guesses",
        "confidence",
        "truth-grounding",
        "correction logging",
        "stand-your-ground",
        "playful but honest software framing",
        "facts",
        "assumptions",
        "guesses",
        "recommendations",
        "uncertainty",
        "examples",
        "no fake consciousness",
        "no always-agree-with-Boss",
    ):
        assert_contains(combined, needle, f"cartridge concept {needle}")


def test_repair_layer_concepts() -> None:
    text = _read(REPAIR)
    for needle in (
        "Problem Statement",
        "Behavior Model",
        "Ambiguity Classes",
        "Response Patterns",
        "Correction-Pattern Loop",
        "Low Risk",
        "Medium Risk",
        "High Risk",
        "Examples And Anti-Examples",
        "Val0 / ValPrime Runtime",
    ):
        assert_contains(text, needle, f"repair layer section {needle}")


def main() -> int:
    test_cartridge_concepts()
    test_repair_layer_concepts()
    _assert_protected_not_staged()
    print("PASS: Val operator cartridge smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
