#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.onboarding_discovery import (  # noqa: E402
    classify_onboarding_daily_sources_answer,
    render_onboarding_daily_recommendation_reply,
)


PROTECTED = (
    "clients/karen/CLIENT_FOLDERS.json",
    "clients/karen/CLIENT_GROCERY.md",
)


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def _runtime_sequence_replies(texts: list[str]) -> list[str]:
    probe = f"""
import asyncio
import json
from types import SimpleNamespace
import bot

bot.mark_processed_event_once = lambda *_args, **_kwargs: True
bot._audit = lambda *_args, **_kwargs: None

class Msg:
    def __init__(self, text, replies):
        self.text = text
        self.message_id = 940001
        self.replies = replies
    async def reply_text(self, text, **_kwargs):
        self.replies.append(text)
        return text

class Ctx:
    def __init__(self):
        self.chat_data = {{}}
        self.user_data = {{}}

async def main():
    replies = []
    ctx = Ctx()
    for text in {texts!r}:
        message = Msg(text, replies)
        update = SimpleNamespace(message=message, effective_chat=SimpleNamespace(id=bot.KAREN_CHAT_ID))
        await bot.handle_text(update, ctx)
    print("===VAL0_ONBOARDING_RECOMMENDATION_REPLIES===")
    print(json.dumps(replies, ensure_ascii=False))

asyncio.run(main())
"""
    proc = subprocess.run(
        ["./scripts/val0py", "-"],
        cwd=ROOT,
        input=probe,
        text=True,
        capture_output=True,
        check=True,
    )
    marker = "===VAL0_ONBOARDING_RECOMMENDATION_REPLIES==="
    if marker not in proc.stdout:
        raise AssertionError(f"runtime probe marker missing. stdout={proc.stdout!r} stderr={proc.stderr!r}")
    payload = proc.stdout.split(marker, 1)[1].strip().splitlines()[0]
    return json.loads(payload)


def _assert_recommendation(reply: str, expected_source: str, label: str) -> None:
    assert_contains(reply, f"tus pendientes están regados entre {expected_source}", f"{label} summarizes source")
    assert_contains(reply, "Perfecto, entonces", f"{label} natural reasoning tone")
    assert_not_contains(reply, "eso me dice algo importante", f"{label} no stiff reasoning tone")
    assert_contains(reply, "No empezaría por documentos ni por carpetas todavía", f"{label} explains what not to start with")
    assert_contains(reply, "Empezaría por Organizar mi día", f"{label} recommends daily flow")
    assert_contains(reply, "porque primero necesitamos capturar", f"{label} explains why")
    assert_contains(reply, "revisión diaria simple", f"{label} scattered responsibility rationale")
    assert_contains(reply, "Semana 1 sería sencilla", f"{label} week 1 plan")
    assert_contains(reply, "Ver dónde entran tus pendientes", f"{label} gather sources")
    assert_contains(reply, "Separar agenda, tareas y recordatorios", f"{label} separates categories")
    assert_contains(reply, "revisión diaria corta", f"{label} warm daily review")
    assert_contains(reply, "solo cuando tú confirmes", f"{label} confirmation before reminders/tasks")
    assert_contains(reply, "Todavía no guardé nada", f"{label} nothing saved")
    assert_contains(reply, "no configuré nada", f"{label} nothing configured")
    assert_contains(reply, "no creé tareas, recordatorios ni eventos de calendario", f"{label} no actions created")
    assert_contains(reply, "founder beta", f"{label} founder beta framing")
    assert_contains(reply, "un solo flujo primero", f"{label} one-flow framing")
    assert_contains(reply, "¿Te parece que probemos Organizar mi día como primer flujo piloto?", f"{label} asks confirmation")
    assert_not_contains(reply, "Karen", f"{label} no Karen private data")
    assert_not_contains(reply, "Caso Finca", f"{label} no private case data")
    assert_not_contains(reply, "CLIENT_", f"{label} no internal client file data")
    assert_not_contains(reply, "AGI", f"{label} no AGI claim")
    assert_not_contains(reply, "IA mágica", f"{label} no magic claim")
    assert_not_contains(reply, "Ejemplos concretos:", f"{label} no raw feature dump")


def test_static_daily_source_classifier_and_renderer() -> None:
    assert_true(
        classify_onboarding_daily_sources_answer("WhatsApp", active_context=False) is None,
        "contextless WhatsApp does not trigger onboarding recommendation",
    )
    assert_true(
        classify_onboarding_daily_sources_answer("WhatsApp y notas", active_context=True) == "WhatsApp y notas",
        "active WhatsApp/notas source classified",
    )
    assert_true(
        classify_onboarding_daily_sources_answer("todo regado", active_context=True) == "varios lugares",
        "active scattered source classified",
    )
    assert_true(
        classify_onboarding_daily_sources_answer("en la cabeza", active_context=True) == "tu cabeza",
        "active head source classified",
    )
    _assert_recommendation(render_onboarding_daily_recommendation_reply("WhatsApp y notas"), "WhatsApp y notas", "static")


def test_runtime_daily_recommendation_sequences() -> None:
    cases = (
        ("WhatsApp y notas", "WhatsApp y notas", "runtime WhatsApp/notas"),
        ("todo regado", "varios lugares", "runtime scattered"),
        ("en la cabeza", "tu cabeza", "runtime head"),
    )
    for answer, expected_source, label in cases:
        replies = _runtime_sequence_replies(["Val, ¿cómo me puedes ayudar?", "organizar mi día", answer])
        assert_true(len(replies) == 3, f"{label} sends discovery, followup, recommendation")
        _assert_recommendation(replies[-1], expected_source, label)


def _assert_protected_not_staged() -> None:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", *PROTECTED],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert_true(proc.stdout.strip() == "", "protected live data files are not staged")


def main() -> int:
    test_static_daily_source_classifier_and_renderer()
    test_runtime_daily_recommendation_sequences()
    _assert_protected_not_staged()
    print("PASS: onboarding discovery recommendation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
