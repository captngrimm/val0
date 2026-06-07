#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.onboarding_discovery import (  # noqa: E402
    classify_onboarding_recommendation_reply,
    render_onboarding_daily_pilot_confirm_reply,
    render_onboarding_pivot_reply,
    render_onboarding_recommendation_cancel_reply,
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
        self.message_id = 950001
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
    print("===VAL0_ONBOARDING_CONFIRM_ADJUST_REPLIES===")
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
    marker = "===VAL0_ONBOARDING_CONFIRM_ADJUST_REPLIES==="
    if marker not in proc.stdout:
        raise AssertionError(f"runtime probe marker missing. stdout={proc.stdout!r} stderr={proc.stderr!r}")
    payload = proc.stdout.split(marker, 1)[1].strip().splitlines()[0]
    return json.loads(payload)


def _assert_safe_reply(reply: str, label: str) -> None:
    assert_not_contains(reply, "setup completo", f"{label} does not claim setup complete")
    assert_not_contains(reply, "ya quedó configurado", f"{label} does not claim configured")
    assert_not_contains(reply, "Karen", f"{label} no Karen private data")
    assert_not_contains(reply, "Caso Finca", f"{label} no private case data")
    assert_not_contains(reply, "CLIENT_", f"{label} no internal client file data")
    assert_not_contains(reply, "AGI", f"{label} no AGI claim")
    assert_not_contains(reply, "IA mágica", f"{label} no magic claim")


def _assert_confirm_reply(reply: str, label: str) -> None:
    assert_contains(reply, "dejamos Organizar mi día como primer flujo piloto", f"{label} confirms pilot flow")
    assert_contains(reply, "qué debe traer tu revisión diaria", f"{label} asks next setup question")
    assert_contains(reply, "agenda", f"{label} agenda option")
    assert_contains(reply, "tareas", f"{label} task option")
    assert_contains(reply, "recordatorios", f"{label} reminder option")
    assert_contains(reply, "prioridades", f"{label} priority option")
    assert_contains(reply, "pendientes sin fecha", f"{label} undated pending option")
    assert_contains(reply, "Todavía no guardé ni configuré nada", f"{label} no saved/configured claim")
    assert_contains(reply, "No creé tareas, recordatorios ni eventos de calendario", f"{label} no created actions")
    _assert_safe_reply(reply, label)


def _assert_pivot_reply(reply: str, expected: str, question: str, label: str) -> None:
    assert_contains(reply, expected, f"{label} acknowledges pivot")
    assert_contains(reply, "No lo forzamos", f"{label} does not fight user")
    assert_contains(reply, question, f"{label} asks category setup question")
    assert_contains(reply, "Todavía no guardo nada ni creo acciones", f"{label} no data/action mutation claim")
    _assert_safe_reply(reply, label)


def _assert_cancel_reply(reply: str, label: str) -> None:
    assert_contains(reply, "no lo forzamos", f"{label} acknowledges no/cancel")
    assert_contains(reply, "escoger otro flujo o dejarlo aquí", f"{label} offers alternate or stop")
    assert_contains(reply, "Todavía no guardé ni configuré nada", f"{label} no saved/configured claim")
    _assert_safe_reply(reply, label)


def test_static_classifier_and_renderers() -> None:
    assert_true(
        classify_onboarding_recommendation_reply("sí", active_context=False) is None,
        "contextless confirmation is not hijacked",
    )
    assert_true(classify_onboarding_recommendation_reply("sí", active_context=True) == "confirm", "sí confirms")
    assert_true(classify_onboarding_recommendation_reply("dale", active_context=True) == "confirm", "dale confirms")
    assert_true(
        classify_onboarding_recommendation_reply("mejor documentos", active_context=True) == "pivot:documents",
        "documents pivot classified",
    )
    assert_true(
        classify_onboarding_recommendation_reply("prefiero clientes", active_context=True) == "pivot:clients",
        "clients pivot classified",
    )
    assert_true(classify_onboarding_recommendation_reply("no", active_context=True) == "cancel", "no cancels")

    _assert_confirm_reply(render_onboarding_daily_pilot_confirm_reply(), "static confirm")
    _assert_pivot_reply(
        render_onboarding_pivot_reply("documents"),
        "cambiamos a documentos",
        "¿Qué quieres ordenar primero",
        "static documents pivot",
    )
    _assert_cancel_reply(render_onboarding_recommendation_cancel_reply(), "static cancel")


def test_runtime_confirm_and_adjust_sequences() -> None:
    cases = (
        ("sí", _assert_confirm_reply, "runtime sí"),
        ("dale", _assert_confirm_reply, "runtime dale"),
        (
            "mejor documentos",
            lambda reply, label: _assert_pivot_reply(reply, "cambiamos a documentos", "¿Qué quieres ordenar primero", label),
            "runtime documents pivot",
        ),
        (
            "prefiero clientes",
            lambda reply, label: _assert_pivot_reply(reply, "cambiamos a clientes", "¿A quién o qué tienes que perseguir más", label),
            "runtime clients pivot",
        ),
        ("no", _assert_cancel_reply, "runtime no"),
    )
    for final_text, assertion, label in cases:
        replies = _runtime_sequence_replies(
            ["Val, ¿cómo me puedes ayudar?", "organizar mi día", "WhatsApp y notas", final_text]
        )
        assert_true(len(replies) == 4, f"{label} sends discovery, followup, recommendation, final reply")
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
    test_runtime_confirm_and_adjust_sequences()
    _assert_protected_not_staged()
    print("PASS: onboarding discovery confirm/adjust smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
