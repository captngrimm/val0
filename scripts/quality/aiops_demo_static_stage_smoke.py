#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGE_DIR = ROOT / "docs/demo/aiops_discovery"
HTML = STAGE_DIR / "index.html"
CSS = STAGE_DIR / "styles.css"
JS = STAGE_DIR / "app.js"
DOC = ROOT / "docs/product/VAL_AIOPS_DEMO_01B_STATIC_STAGE_AND_MOCK_REPORT.md"
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


def read_stage() -> str:
    for path in (HTML, CSS, JS, DOC):
        assert_true(path.exists(), f"{path.relative_to(ROOT)} exists")
    return "\n\n".join(
        path.read_text(encoding="utf-8") for path in (HTML, CSS, JS, DOC)
    )


def read_visible_stage() -> str:
    return "\n\n".join(path.read_text(encoding="utf-8") for path in (HTML, CSS, JS))


def test_static_stage_required_content() -> None:
    text = read_stage()
    for needle in (
        "Val AI Ops Discovery",
        "Mapa IA 30/60/90",
        "Founder-beta diagnostic stage",
        "Iniciar diagnostico AI Ops",
        "Empresa X",
        "Business type",
        "Lead/client channels",
        "Critical processes",
        "Manual/repetitive work",
        "Tools used",
        "Where time is lost",
        "Current bottleneck",
        "Desired 30/60/90 outcome",
        "Meeting notes",
        "Current summary",
        "Suggested next question",
        "Detected opportunities",
        "Risks / things not to promise",
        "Recommended first pilot",
        "Executive summary",
        "Current processes",
        "Pain points",
        "Opportunities",
        "Recommended pilot",
        "30/60/90 roadmap",
        "Limits / boundaries",
        "Next steps",
        "Human confirmation required",
    ):
        assert_contains(text, needle, "AI Ops static stage required content")


def test_mock_controls_and_static_boundaries() -> None:
    text = read_stage()
    for needle in (
        "Start Diagnostic",
        "Summarize Notes",
        "Suggest Next Question",
        "Detect Opportunities",
        "Generate Draft Map",
        "addEventListener",
    ):
        assert_contains(text, needle, "AI Ops mock controls")
    visible_stage = read_visible_stage()
    for needle in (
        "ChatGPT",
        "OpenAI",
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "full autonomy",
        "replaces professionals",
        "CLIENT_FOLDERS.json",
        "CLIENT_GROCERY.md",
        "DB migration",
        "OAuth",
        "systemd",
    ):
        assert_not_contains(visible_stage, needle, "AI Ops static stage avoids forbidden surface")


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
    test_static_stage_required_content()
    test_mock_controls_and_static_boundaries()
    test_protected_not_staged()
    print("PASS: AI Ops static stage smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
