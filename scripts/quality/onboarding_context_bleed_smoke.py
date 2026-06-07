#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
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


def _runtime_sequence_replies_by_turn(texts: list[str]) -> list[list[str]]:
    probe = f"""
import asyncio
import json
from types import SimpleNamespace
import bot

bot.mark_processed_event_once = lambda *_args, **_kwargs: True
bot._audit = lambda *_args, **_kwargs: None

class Msg:
    def __init__(self, text, message_id):
        self.text = text
        self.message_id = message_id
        self.replies = []
    async def reply_text(self, text, **_kwargs):
        self.replies.append(text)
        return text

class Ctx:
    def __init__(self):
        self.chat_data = {{}}
        self.user_data = {{}}

async def main():
    ctx = Ctx()
    all_replies = []
    for idx, text in enumerate({texts!r}, start=0):
        message = Msg(text, 970001 + idx)
        update = SimpleNamespace(message=message, effective_chat=SimpleNamespace(id=bot.KAREN_CHAT_ID))
        await bot.handle_text(update, ctx)
        all_replies.append(message.replies)
    print("===VAL0_ONBOARDING_CONTEXT_BLEED_REPLIES===")
    print(json.dumps(all_replies, ensure_ascii=False))

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
    marker = "===VAL0_ONBOARDING_CONTEXT_BLEED_REPLIES==="
    if marker not in proc.stdout:
        raise AssertionError(f"runtime probe marker missing. stdout={proc.stdout!r} stderr={proc.stderr!r}")
    payload = proc.stdout.split(marker, 1)[1].strip().splitlines()[0]
    return json.loads(payload)


def test_onboarding_sequence_does_not_bleed_into_legal_context() -> None:
    replies_by_turn = _runtime_sequence_replies_by_turn(
        [
            "Val, ¿cómo me puedes ayudar?",
            "Organizar mi día",
            "WhatsApp, notas y cabeza",
            "Sí",
            "todo eso",
        ]
    )
    assert_true(len(replies_by_turn) == 5, "five onboarding turns captured")
    assert_true(all(len(replies) == 1 for replies in replies_by_turn), "each onboarding turn produces exactly one reply")

    opening = replies_by_turn[0][0]
    assert_contains(opening, "Por ahora puedo ayudarte como operadora personal desde Telegram", "opening frames Telegram as current surface")
    assert_not_contains(opening, "operadora personal por Telegram", "opening avoids Telegram-only product framing")

    recommendation = replies_by_turn[2][0]
    assert_contains(
        recommendation,
        "Perfecto, entonces tus pendientes están regados entre WhatsApp, notas y tu cabeza",
        "recommendation uses natural scattered-source phrasing",
    )
    assert_not_contains(recommendation, "eso me dice algo importante", "recommendation avoids stiff phrase")

    final_reply = replies_by_turn[-1][0]
    assert_contains(final_reply, "revisión diaria piloto incluiría", "final reply contains daily review proposal")
    assert_contains(final_reply, "agenda, tareas, recordatorios, prioridades y pendientes sin fecha", "final reply contains full daily review contents")
    assert_contains(final_reply, "Todavía no guardé ni configuré nada", "final reply remains no-write")
    assert_contains(final_reply, "No creé tareas, recordatorios ni eventos de calendario", "final reply remains no-action")

    combined = "\n\n".join(reply for replies in replies_by_turn for reply in replies)
    for forbidden in (
        "Nora",
        "Caso Finca",
        "abogada",
        "finca",
        "documentos registrados",
        "revisión legal",
        "paquete para",
        "herederos",
    ):
        assert_not_contains(combined, forbidden, f"onboarding sequence has no unrelated legal/document wording: {forbidden}")


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
    test_onboarding_sequence_does_not_bleed_into_legal_context()
    test_protected_not_staged()
    print("PASS: onboarding context bleed smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
