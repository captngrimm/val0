#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "docs" / "product" / "ROADMAP_01_DYNAMIC_INTAKE_DESIGN.md"
TEMPLATE = ROOT / "docs" / "product" / "ROADMAP_INTAKE_RESPONSE_TEMPLATE.md"
PROMPT = ROOT / "docs" / "product" / "ROADMAP_NEWSLETTER_INTAKE_PROMPT.md"
SOURCE_INDEX = ROOT / "docs" / "product" / "VAL0_SOURCE_OF_TRUTH_INDEX.md"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def _combined_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in (DESIGN, TEMPLATE, PROMPT, SOURCE_INDEX))


def main() -> int:
    for path, label in (
        (DESIGN, "roadmap intake design"),
        (TEMPLATE, "roadmap intake response template"),
        (PROMPT, "newsletter intake prompt"),
    ):
        assert_true(path.exists(), f"{label} exists")

    index = SOURCE_INDEX.read_text(encoding="utf-8")
    for needle in (
        "ROADMAP_01_DYNAMIC_INTAKE_DESIGN.md",
        "ROADMAP_INTAKE_RESPONSE_TEMPLATE.md",
        "ROADMAP_NEWSLETTER_INTAKE_PROMPT.md",
    ):
        assert_contains(index, needle, "source-of-truth index")

    text = _combined_text()
    required = (
        "newsletters",
        "ValPrime",
        "parking lot",
        "active sprint",
        "ROADMAP_UPDATE_CANDIDATE",
        "Do not auto-update roadmap without explicit approval",
        "Obsidian",
        "OPEL",
        "Milkshake Time",
    )
    for needle in required:
        assert_contains(text, needle, "roadmap intake docs")

    print("PASS: Roadmap dynamic intake docs smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
