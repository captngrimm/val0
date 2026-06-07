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


def _runtime_sequence_with_duplicate_final() -> list[list[str]]:
    texts = [
        "Val, ¿cómo me puedes ayudar?",
        "Organizar mi día",
        "WhatsApp, notas y cabeza",
        "Sí",
        "todo eso",
    ]
    probe = f"""
import asyncio
import json
from types import SimpleNamespace
import bot

processed = set()

def fake_mark_processed_event_once(key, kind):
    if key in processed:
        return False
    processed.add(key)
    return True

bot.mark_processed_event_once = fake_mark_processed_event_once
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
    message_ids = [981001, 981002, 981003, 981004, 981005, 981005]
    for text, message_id in zip({texts + [texts[-1]]!r}, message_ids):
        message = Msg(text, message_id)
        update = SimpleNamespace(message=message, effective_chat=SimpleNamespace(id=bot.KAREN_CHAT_ID))
        await bot.handle_text(update, ctx)
        all_replies.append(message.replies)
    print("===VAL0_ONBOARDING_NO_DOUBLE_REPLY_REPLIES===")
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
    marker = "===VAL0_ONBOARDING_NO_DOUBLE_REPLY_REPLIES==="
    if marker not in proc.stdout:
        raise AssertionError(f"runtime probe marker missing. stdout={proc.stdout!r} stderr={proc.stderr!r}")
    payload = proc.stdout.split(marker, 1)[1].strip().splitlines()[0]
    return json.loads(payload)


def test_duplicate_final_onboarding_update_is_ignored() -> None:
    replies_by_turn = _runtime_sequence_with_duplicate_final()
    assert_true(len(replies_by_turn) == 6, "five live turns plus duplicate final delivery captured")
    assert_true(all(len(replies) == 1 for replies in replies_by_turn[:5]), "original onboarding turns produce one reply each")
    assert_true(replies_by_turn[-1] == [], "duplicate final onboarding delivery produces no reply")

    final_reply = replies_by_turn[4][0]
    assert_contains(final_reply, "revisión diaria piloto incluiría", "final reply contains daily review proposal")
    assert_contains(final_reply, "Todavía no guardé ni configuré nada", "final reply remains no-write")
    assert_contains(final_reply, "No creé tareas, recordatorios ni eventos de calendario", "final reply remains no-action")

    combined = "\n\n".join(reply for replies in replies_by_turn for reply in replies)
    for forbidden in (
        "Tany",
        "Nora",
        "abogada",
        "finca",
        "documentos para preparar",
        "timeline",
        "bróker",
        "broker",
        "Google Calendar",
        "Cita con la bróker",
        "Caso Finca",
    ):
        assert_not_contains(combined, forbidden, f"no stale post-onboarding response: {forbidden}")


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
    test_duplicate_final_onboarding_update_is_ignored()
    test_protected_not_staged()
    print("PASS: onboarding no-double-reply live path smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
