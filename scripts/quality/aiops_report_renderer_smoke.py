#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

import sys

sys.path.insert(0, str(ROOT))

from core.aiops_report import render_aiops_map_markdown, sample_aiops_session


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r}")


def test_report_renderer_outputs_required_sections() -> None:
    report = render_aiops_map_markdown(sample_aiops_session())
    for needle in (
        "Mapa IA 30/60/90 - Empresa X",
        "Executive Summary",
        "Current Processes",
        "Pain Points",
        "Opportunities",
        "Recommended Pilot",
        "30/60/90 Roadmap",
        "Limits / Boundaries",
        "Next Steps",
        "Human confirmation is required",
    ):
        assert_contains(report, needle, "AI Ops report renderer")


def test_report_renderer_is_generic_and_bounded() -> None:
    report = render_aiops_map_markdown(sample_aiops_session())
    for needle in (
        "ChatGPT",
        "OpenAI",
        "full autonomy",
        "replaces professionals",
        "CLIENT_FOLDERS.json",
        "CLIENT_GROCERY.md",
        "memory persisted",
        "DB write",
    ):
        assert_not_contains(report, needle, "AI Ops report avoids forbidden claims/leakage")


def main() -> int:
    test_report_renderer_outputs_required_sections()
    test_report_renderer_is_generic_and_bounded()
    print("PASS: AI Ops report renderer smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
