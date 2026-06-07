#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.onboarding_discovery import (  # noqa: E402
    classify_onboarding_daily_review_contents,
    render_onboarding_daily_review_contents_reply,
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
        self.message_id = 960001
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
    print("===VAL0_ONBOARDING_DAILY_REVIEW_REPLIES===")
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
    marker = "===VAL0_ONBOARDING_DAILY_REVIEW_REPLIES==="
    if marker not in proc.stdout:
        raise AssertionError(f"runtime probe marker missing. stdout={proc.stdout!r} stderr={proc.stderr!r}")
    payload = proc.stdout.split(marker, 1)[1].strip().splitlines()[0]
    return json.loads(payload)


def _assert_safe_reply(reply: str, label: str) -> None:
    assert_contains(reply, "Todavía no guardé ni configuré nada", f"{label} says nothing saved/configured")
    assert_contains(reply, "no creé tareas, recordatorios ni eventos de calendario", f"{label} says no actions created")
    assert_not_contains(reply, "setup completo", f"{label} does not claim setup complete")
    assert_not_contains(reply, "ya quedó configurado", f"{label} does not claim configured")
    assert_not_contains(reply, "Karen", f"{label} no Karen private data")
    assert_not_contains(reply, "Caso Finca", f"{label} no private case data")
    assert_not_contains(reply, "CLIENT_", f"{label} no internal client file data")
    assert_not_contains(reply, "AGI", f"{label} no AGI claim")
    assert_not_contains(reply, "IA mágica", f"{label} no magic claim")


def _assert_full_reply(reply: str, label: str) -> None:
    assert_contains(
        reply,
        "revisión diaria piloto incluiría: agenda, tareas, recordatorios, prioridades y pendientes sin fecha",
        f"{label} summarizes all contents",
    )
    assert_contains(reply, "ver cada mañana qué tienes encima", f"{label} daily review structure")
    assert_contains(reply, "qué no se puede olvidar", f"{label} remembers important items")
    assert_contains(reply, "qué va primero", f"{label} priorities structure")
    assert_contains(reply, "¿Quieres que dejemos este diseño como propuesta", f"{label} asks next confirmation")
    _assert_safe_reply(reply, label)


def _assert_agenda_tasks_reply(reply: str, label: str) -> None:
    assert_contains(reply, "revisión diaria piloto incluiría: agenda y tareas", f"{label} summarizes selected contents")
    assert_contains(reply, "ver cada mañana qué tienes encima", f"{label} daily review structure")
    assert_contains(reply, "¿Quieres que dejemos este diseño como propuesta", f"{label} asks next confirmation")
    _assert_safe_reply(reply, label)


def _assert_simple_reply(reply: str, label: str) -> None:
    assert_contains(reply, "Empezamos más simple", f"{label} acknowledges simple mode")
    assert_contains(reply, "solo tres cosas: agenda, tareas importantes y pendientes sin fecha", f"{label} minimal review")
    assert_contains(reply, "sin convertirlo en un monstruo", f"{label} warm no-overbuild rationale")
    assert_contains(reply, "¿Te parece esta versión simple para el piloto?", f"{label} asks simple confirmation")
    _assert_safe_reply(reply, label)


def test_static_classifier_and_renderers() -> None:
    assert_true(
        classify_onboarding_daily_review_contents("todo eso", active_context=False) is None,
        "contextless todo eso is not hijacked",
    )
    assert_true(
        classify_onboarding_daily_review_contents("todo eso", active_context=True)
        == ["agenda", "tasks", "reminders", "priorities", "undated"],
        "all contents classified",
    )
    assert_true(
        classify_onboarding_daily_review_contents("agenda y tareas", active_context=True) == ["agenda", "tasks"],
        "agenda and tasks classified",
    )
    assert_true(
        classify_onboarding_daily_review_contents("más simple", active_context=True) == ["agenda", "tasks", "undated"],
        "simple contents classified",
    )
    _assert_full_reply(
        render_onboarding_daily_review_contents_reply(["agenda", "tasks", "reminders", "priorities", "undated"]),
        "static all",
    )
    _assert_simple_reply(render_onboarding_daily_review_contents_reply(["agenda", "tasks", "undated"]), "static simple")


def test_runtime_daily_review_selection_sequences() -> None:
    cases = (
        ("todo eso", _assert_full_reply, "runtime all"),
        ("agenda y tareas", _assert_agenda_tasks_reply, "runtime agenda tasks"),
        ("más simple", _assert_simple_reply, "runtime simple"),
    )
    for final_text, assertion, label in cases:
        replies = _runtime_sequence_replies(
            ["Val, ¿cómo me puedes ayudar?", "organizar mi día", "WhatsApp y notas", "sí", final_text]
        )
        assert_true(len(replies) == 5, f"{label} sends full onboarding sequence")
        assertion(replies[-1], label)


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
    test_static_classifier_and_renderers()
    test_runtime_daily_review_selection_sequences()
    _assert_protected_not_staged()
    print("PASS: onboarding daily review selection smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
