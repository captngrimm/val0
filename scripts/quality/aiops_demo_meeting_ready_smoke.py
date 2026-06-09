#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGE_DIR = ROOT / "docs/demo/aiops_discovery"
HTML = STAGE_DIR / "index.html"
CSS = STAGE_DIR / "styles.css"
JS = STAGE_DIR / "app.js"
DOC = ROOT / "docs/product/VAL_AIOPS_DEMO_01E_MEETING_READY_POLISH.md"
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


def read(path: Path) -> str:
    assert_true(path.exists(), f"{path.relative_to(ROOT)} exists")
    return path.read_text(encoding="utf-8")


def read_stage() -> str:
    return "\n\n".join(read(path) for path in (HTML, CSS, JS))


def test_meeting_ready_controls_exist() -> None:
    text = read_stage()
    for needle in (
        "Copy Report",
        "copyReportButton",
        "navigator.clipboard",
        "Clipboard unavailable",
        "Clipboard blocked",
        "Print / Save as PDF",
        "printReportButton",
        "window.print",
        "Demo Mode Checklist",
        "Open stage.",
        "Start Diagnostic.",
        "Load/paste Carlos sample notes.",
        "Try Voice Lite intro/question.",
        "Copy or print report.",
    ):
        assert_contains(text, needle, "meeting-ready stage controls")


def test_talk_track_and_do_not_say() -> None:
    text = read(DOC)
    for needle in (
        "La voz depende del navegador; la parte importante es el diagnóstico y el mapa.",
        "Este es un stage interno de Val AI Ops Discovery.",
        "Lo uso para estructurar diagnósticos, detectar oportunidades y producir un Mapa IA 30/60/90.",
        "No estamos prometiendo automatizar todo.",
        "Primero buscamos el proceso más rentable para un piloto pequeño y medible.",
        "El siguiente paso sería convertir este mapa en un piloto de una semana con una métrica clara.",
        "Esto reemplaza a tu equipo.",
        "Val automatiza todo.",
        "Esto es ChatGPT.",
        "La IA decide sola.",
        "No necesitamos revisar tus procesos.",
    ):
        assert_contains(text, needle, "meeting-ready talk track/do-not-say")


def test_report_sections_and_boundaries() -> None:
    text = read_stage() + "\n\n" + read(DOC)
    for needle in (
        "Executive summary",
        "Current processes",
        "Pain points",
        "Opportunities",
        "Recommended pilot",
        "30/60/90 roadmap",
        "Limits / boundaries",
        "Next steps",
        "No fake autonomy",
        "No professional replacement claims",
        "No network calls",
        "No real LLM calls",
    ):
        assert_contains(text, needle, "meeting-ready report sections/boundaries")


def test_visible_stage_has_no_provider_branding_or_network_calls() -> None:
    text = read_stage()
    for needle in (
        "ChatGPT",
        "OpenAI",
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "http://",
        "https://",
    ):
        assert_not_contains(text, needle, "visible stage avoids provider branding/network")


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
    test_meeting_ready_controls_exist()
    test_talk_track_and_do_not_say()
    test_report_sections_and_boundaries()
    test_visible_stage_has_no_provider_branding_or_network_calls()
    test_protected_not_staged()
    print("PASS: AI Ops meeting-ready smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
