#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.onboarding_discovery import (  # noqa: E402
    classify_onboarding_discovery_choice,
    render_onboarding_discovery_choice_reply,
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
        self.message_id = 930001
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
    print("===VAL0_ONBOARDING_FOLLOWUP_REPLIES===")
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
    marker = "===VAL0_ONBOARDING_FOLLOWUP_REPLIES==="
    if marker not in proc.stdout:
        raise AssertionError(f"runtime probe marker missing. stdout={proc.stdout!r} stderr={proc.stderr!r}")
    payload = proc.stdout.split(marker, 1)[1].strip().splitlines()[0]
    return json.loads(payload)


def _assert_followup_reply(reply: str, expected: str, label: str) -> None:
    assert_contains(reply, expected, f"{label} expected setup question")
    assert_contains(reply, "un solo flujo primero", f"{label} one-flow framing")
    assert_contains(reply, "founder beta", f"{label} founder-beta framing")
    assert_contains(reply, "Todavía no guardo nada ni creo acciones", f"{label} no data/action mutation claim")
    assert_true(reply.count("¿") <= 1, f"{label} asks at most one next question")
    assert_true("¿" in reply or "Dime en una frase" in reply, f"{label} includes one next prompt")
    assert_not_contains(reply, "setup completo", f"{label} does not claim setup complete")
    assert_not_contains(reply, "ya quedó configurado", f"{label} does not claim configured")
    assert_not_contains(reply, "Karen", f"{label} no Karen private data")
    assert_not_contains(reply, "Caso Finca", f"{label} no private case data")
    assert_not_contains(reply, "CLIENT_", f"{label} no internal client file data")
    assert_not_contains(reply, "AGI", f"{label} no AGI claim")
    assert_not_contains(reply, "IA mágica", f"{label} no magic claim")


def test_static_choice_classifier_and_replies() -> None:
    assert_true(
        classify_onboarding_discovery_choice("agenda", active_context=False) is None,
        "contextless agenda is not hijacked",
    )
    assert_true(
        classify_onboarding_discovery_choice("Val, quiero ordenar documentos", active_context=False) == "documents",
        "obvious direct document choice is handled",
    )

    expectations = {
        "day": "¿Dónde tienes tus pendientes ahora",
        "reminders": "¿Qué tipo de cosas se te pierden más",
        "documents": "¿Qué quieres ordenar primero",
        "clients": "¿A quién o qué tienes que perseguir más",
        "ideas": "¿Qué quieres guardar sin que se pierda",
        "other": "Dime en una frase qué te gustaría ordenar",
    }
    for choice, expected in expectations.items():
        _assert_followup_reply(render_onboarding_discovery_choice_reply(choice), expected, f"static {choice}")


def test_runtime_followup_sequences() -> None:
    cases = (
        ("organizar mi día", "¿Dónde tienes tus pendientes ahora", "runtime day"),
        ("pendientes", "¿Qué tipo de cosas se te pierden más", "runtime reminders"),
        ("documentos", "¿Qué quieres ordenar primero", "runtime documents"),
        ("clientes", "¿A quién o qué tienes que perseguir más", "runtime clients"),
        ("ideas", "¿Qué quieres guardar sin que se pierda", "runtime ideas"),
        ("otro", "Dime en una frase qué te gustaría ordenar", "runtime other"),
    )
    for followup, expected, label in cases:
        replies = _runtime_sequence_replies(["Val, ¿cómo me puedes ayudar?", followup])
        assert_true(len(replies) == 2, f"{label} sends discovery plus one followup reply")
        _assert_followup_reply(replies[-1], expected, label)


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
    test_static_choice_classifier_and_replies()
    test_runtime_followup_sequences()
    _assert_protected_not_staged()
    print("PASS: onboarding discovery follow-up smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
