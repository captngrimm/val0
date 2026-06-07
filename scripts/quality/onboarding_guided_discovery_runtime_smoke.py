#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.onboarding_discovery import (  # noqa: E402
    is_onboarding_discovery_query,
    render_onboarding_discovery_reply,
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


def _runtime_replies(text: str) -> list[str]:
    probe = f"""
import asyncio
import json
from types import SimpleNamespace
import bot

bot.mark_processed_event_once = lambda *_args, **_kwargs: True
bot._audit = lambda *_args, **_kwargs: None

class Msg:
    def __init__(self, text):
        self.text = text
        self.message_id = 920001
        self.replies = []
    async def reply_text(self, text, **_kwargs):
        self.replies.append(text)
        return text

class Ctx:
    def __init__(self):
        self.chat_data = {{}}
        self.user_data = {{}}

async def main():
    message = Msg({text!r})
    update = SimpleNamespace(message=message, effective_chat=SimpleNamespace(id=bot.KAREN_CHAT_ID))
    await bot.handle_text(update, Ctx())
    print("===VAL0_ONBOARDING_REPLIES===")
    print(json.dumps(message.replies, ensure_ascii=False))

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
    marker = "===VAL0_ONBOARDING_REPLIES==="
    if marker not in proc.stdout:
        raise AssertionError(f"runtime probe marker missing. stdout={proc.stdout!r} stderr={proc.stderr!r}")
    payload = proc.stdout.split(marker, 1)[1].strip().splitlines()[0]
    return json.loads(payload)


def _assert_discovery_reply(reply: str, label: str) -> None:
    assert_contains(reply, "workflow primero", f"{label} one workflow first")
    assert_contains(reply, "Organizar mi día", f"{label} concrete day example")
    assert_contains(reply, "Pendientes/recordatorios", f"{label} reminders example")
    assert_contains(reply, "Documentos/casos", f"{label} documents example")
    assert_contains(reply, "Clientes/seguimiento", f"{label} client follow-up example")
    assert_contains(reply, "Ideas/carpetas", f"{label} folders example")
    assert_contains(reply, "¿Cuál te duele más esta semana?", f"{label} pain this week framing")
    assert_contains(reply, "founder beta", f"{label} founder beta boundary")
    assert_contains(reply, "no soy magia AI", f"{label} no magic AI claim")
    assert_contains(reply, "no hago full autonomy", f"{label} no full autonomy claim")
    assert_true("AGI" not in reply, f"{label} no explicit AGI language")
    assert_not_contains(reply, "Karen", f"{label} no Karen private data")
    assert_not_contains(reply, "Caso Finca", f"{label} no private case data")
    assert_not_contains(reply, "CLIENT_", f"{label} no internal client files")
    assert_not_contains(reply, "smoke", f"{label} no smoke details")
    assert_not_contains(reply, "implementation", f"{label} no implementation details")


def test_helper_classification() -> None:
    positives = (
        "Val, ¿cómo me puedes ayudar?",
        "Val, ¿qué puedes hacer?",
        "Val, ayúdame a empezar",
        "Val, no sé qué necesito",
    )
    for phrase in positives:
        assert_true(is_onboarding_discovery_query(phrase), f"classifies onboarding phrase: {phrase}")
    assert_true(not is_onboarding_discovery_query("Val, qué tengo mañana?"), "agenda phrase not onboarding discovery")
    assert_true(not is_onboarding_discovery_query("Val, resume el documento 1"), "document summary phrase not onboarding discovery")


def test_static_reply_shape() -> None:
    _assert_discovery_reply(render_onboarding_discovery_reply(), "static discovery reply")


def test_runtime_route() -> None:
    for phrase in (
        "Val, ¿cómo me puedes ayudar?",
        "Val, ¿qué puedes hacer?",
        "Val, ayúdame a empezar",
        "Val, no sé qué necesito",
    ):
        replies = _runtime_replies(phrase)
        assert_true(len(replies) == 1, f"runtime sends one reply for {phrase}")
        _assert_discovery_reply(replies[0], f"runtime {phrase}")


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
    test_helper_classification()
    test_static_reply_shape()
    test_runtime_route()
    _assert_protected_not_staged()
    print("PASS: onboarding guided discovery runtime smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
