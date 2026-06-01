#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs" / "product" / "ROADMAP_02_VALPRIME_SIGNAL_PROTOCOL.md"
SOURCE_INDEX = ROOT / "docs" / "product" / "VAL0_SOURCE_OF_TRUTH_INDEX.md"
PROMPT = ROOT / "docs" / "product" / "ROADMAP_NEWSLETTER_INTAKE_PROMPT.md"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def main() -> int:
    assert_true(PROTOCOL.exists(), "ROADMAP-02 protocol doc exists")
    protocol = PROTOCOL.read_text(encoding="utf-8")
    for needle in (
        "ValPrime is the roadmap keeper",
        "no Notion dependency",
        "/roadmap_signal",
        "/roadmap_review",
        "/roadmap_decision",
        "No automatic roadmap changes",
    ):
        assert_contains(protocol, needle, "ROADMAP-02 protocol")

    index = SOURCE_INDEX.read_text(encoding="utf-8")
    assert_contains(index, "ROADMAP_02_VALPRIME_SIGNAL_PROTOCOL.md", "source-of-truth index")
    assert_contains(index, "ValPrime is the roadmap keeper", "source-of-truth index")

    prompt = PROMPT.read_text(encoding="utf-8")
    assert_contains(prompt, "/roadmap_signal", "newsletter intake prompt")
    assert_contains(prompt, "Do not depend on Notion", "newsletter intake prompt")

    print("PASS: Roadmap ValPrime signal protocol smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
