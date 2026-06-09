#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGE_DIR = ROOT / "docs/demo/aiops_discovery"
HTML = STAGE_DIR / "index.html"
CSS = STAGE_DIR / "styles.css"
JS = STAGE_DIR / "app.js"
DOC = ROOT / "docs/product/VAL_AIOPS_DEMO_01D_VOICE_LITE_WOW_LAYER.md"
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


def read_static_stage() -> str:
    return "\n\n".join(read(path) for path in (HTML, CSS, JS))


def test_voice_lite_controls_exist() -> None:
    text = read_static_stage()
    for needle in (
        "Voice Lite",
        "Speak Intro",
        "Speak First Question",
        "Speak Opportunity Summary",
        "Speak Pilot Recommendation",
        "Stop Voice",
        "voiceStatus",
        "Voice ready",
        "Voice not supported in this browser",
        "Speaking...",
        "Stopped",
    ):
        assert_contains(text, needle, "Voice Lite controls/status")


def test_required_voice_phrases_exist() -> None:
    text = read_static_stage() + "\n\n" + read(DOC)
    for needle in (
        "Perfecto, Boss. Estamos iniciando un diagnóstico AI Ops para Carlos.",
        "Carlos, un gusto.",
        "Te haré unas preguntas cortas",
        "Primera pregunta: ¿qué tipo de negocio tienes",
        "por dónde llegan normalmente tus clientes o leads",
        "Estoy viendo posibles oportunidades en captura de leads",
        "seguimiento manual",
        "visibilidad del estado de cada oportunidad",
        "Mi recomendación inicial es empezar con un piloto pequeño",
        "seguimiento de leads y recordatorios de próxima acción",
        "no promete automatizar todo desde el primer día",
    ):
        assert_contains(text, needle, "required Voice Lite phrase")


def test_voice_lite_uses_browser_tts_without_network_or_stt() -> None:
    text = read_static_stage()
    for needle in (
        "speechSynthesis",
        "SpeechSynthesisUtterance",
        "window.speechSynthesis.cancel",
        "window.speechSynthesis.speak",
        "addEventListener",
    ):
        assert_contains(text, needle, "browser-native TTS")
    for needle in (
        "SpeechRecognition",
        "webkitSpeechRecognition",
        "getUserMedia",
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "http://",
        "https://",
        "ChatGPT",
        "OpenAI",
        "full duplex",
        "avatar",
    ):
        assert_not_contains(text, needle, "Voice Lite avoids forbidden runtime/network surface")


def test_doc_records_boundaries() -> None:
    text = read(DOC)
    for needle in (
        "text-to-speech only",
        "Speech input is intentionally skipped",
        "No autoplay",
        "No microphone permission",
        "No external voice service",
        "No network calls",
        "No real LLM calls",
        "No fake autonomy",
        "No professional replacement claims",
    ):
        assert_contains(text, needle, "Voice Lite design doc boundaries")


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
    test_voice_lite_controls_exist()
    test_required_voice_phrases_exist()
    test_voice_lite_uses_browser_tts_without_network_or_stt()
    test_doc_records_boundaries()
    test_protected_not_staged()
    print("PASS: AI Ops Voice Lite smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
