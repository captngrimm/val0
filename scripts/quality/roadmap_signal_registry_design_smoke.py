#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "docs" / "product" / "ROADMAP_03_SIGNAL_REGISTRY_STORAGE_DESIGN.md"
SCHEMA = ROOT / "docs" / "product" / "ROADMAP_SIGNAL_SCHEMA_V0.md"
SOURCE_INDEX = ROOT / "docs" / "product" / "VAL0_SOURCE_OF_TRUTH_INDEX.md"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def main() -> int:
    assert_true(DESIGN.exists(), "ROADMAP-03 design exists")
    assert_true(SCHEMA.exists(), "ROADMAP signal schema exists")

    design = DESIGN.read_text(encoding="utf-8")
    for needle in (
        "ValPrime",
        "OPEL",
        "Obsidian",
        "source-of-truth",
        "No Notion dependency",
        "No automatic roadmap changes",
        "captured",
        "triaged",
        "roadmap_candidate",
        "implemented",
        "archived",
    ):
        assert_contains(design, needle, "ROADMAP-03 design")

    schema = SCHEMA.read_text(encoding="utf-8")
    for needle in (
        "/roadmap_signal",
        "signal_id",
        "created_at",
        "source_type",
        "source_ref",
        "decision_category",
        "approval_required",
    ):
        assert_contains(schema, needle, "ROADMAP signal schema")

    index = SOURCE_INDEX.read_text(encoding="utf-8")
    assert_contains(index, "ROADMAP_03_SIGNAL_REGISTRY_STORAGE_DESIGN.md", "source-of-truth index")
    assert_contains(index, "ROADMAP_SIGNAL_SCHEMA_V0.md", "source-of-truth index")

    print("PASS: Roadmap signal registry design smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
