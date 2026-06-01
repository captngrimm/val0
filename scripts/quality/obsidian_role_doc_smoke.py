#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "architecture" / "OBSIDIAN_01_VAULT_ROLE_CLARIFICATION.md"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def main() -> int:
    assert_true(DOC.exists(), "OBSIDIAN-01 doc exists")
    text = DOC.read_text(encoding="utf-8")
    required = (
        "/home/forge/valeria_vault",
        "/home/forge/valeria_vault/.obsidian",
        "ValPrime",
        "OPEL",
        "Repo docs and smokes",
        "visual second brain",
        "Split-brain",
        "Drift",
        "no runtime behavior",
        "does not wire Obsidian into Val0",
    )
    for needle in required:
        assert_contains(text, needle, "OBSIDIAN-01 doc")

    print("PASS: Obsidian vault role documentation smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
