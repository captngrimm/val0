#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = ROOT / "docs/product/VAL_AIOPS_DEMO_01C_VISUAL_VERIFICATION_AND_DEMO_RUNBOOK.md"
STAGE_DIR = ROOT / "docs/demo/aiops_discovery"
HTML = STAGE_DIR / "index.html"
JS = STAGE_DIR / "app.js"
CLIENT_ZERO_PATH = Path("clients") / "karen"
PROTECTED = (
    (CLIENT_ZERO_PATH / "CLIENT_FOLDERS.json").as_posix(),
    (CLIENT_ZERO_PATH / "CLIENT_GROCERY.md").as_posix(),
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


def read_text(path: Path) -> str:
    assert_true(path.exists(), f"{path.relative_to(ROOT)} exists")
    return path.read_text(encoding="utf-8")


def test_runbook_required_demo_copy() -> None:
    text = read_text(RUNBOOK)
    for needle in (
        "docs/demo/aiops_discovery/index.html",
        "Este es un stage interno de Val AI Ops Discovery",
        "estructurar diagnósticos",
        "detectar oportunidades",
        "Mapa IA 30/60/90",
        "Iniciar diagnóstico AI Ops con Carlos",
        "Start Diagnostic",
        "Summarize Notes",
        "Suggest Next Question",
        "Detect Opportunities",
        "Generate Draft Map",
        "Esto no promete automatizar todo",
        "piloto pequeño y medible",
        "diagnóstico AI Ops 30/60/90",
    ):
        assert_contains(text, needle, "AI Ops demo runbook required copy")


def test_runbook_sample_notes_and_boundaries() -> None:
    text = read_text(RUNBOOK)
    for needle in (
        "Carlos runs a service business.",
        "Leads arrive through WhatsApp and referrals.",
        "Follow-up is manual.",
        "Quotes are tracked in Excel or notebooks.",
        "Some prospects are lost because nobody follows up.",
        "Carlos wants better visibility and fewer missed opportunities.",
        "No fake autonomy",
        "No professional replacement claims",
        "No ChatGPT/OpenAI visible branding",
        "No real client data",
        "no local screenshot-capable browser binary was available",
    ):
        assert_contains(text, needle, "AI Ops runbook notes/boundaries")


def test_stage_has_matching_sample_notes_and_controls() -> None:
    visible_stage = read_text(HTML) + "\n\n" + read_text(JS)
    for needle in (
        "Val AI Ops Discovery",
        "Mapa IA 30/60/90",
        "Carlos runs a service business.",
        "Leads arrive through WhatsApp and referrals.",
        "Quotes are tracked in Excel or notebooks.",
        "Generate Draft Map",
        "Detected opportunities",
        "Recommended first pilot",
    ):
        assert_contains(visible_stage, needle, "AI Ops stage supports runbook")
    for needle in (
        "ChatGPT",
        "OpenAI",
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
    ):
        assert_not_contains(visible_stage, needle, "AI Ops visible stage stays offline/branded")


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
    test_runbook_required_demo_copy()
    test_runbook_sample_notes_and_boundaries()
    test_stage_has_matching_sample_notes_and_controls()
    test_protected_not_staged()
    print("PASS: AI Ops demo runbook smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
