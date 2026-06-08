#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.adaptive_intake import (  # noqa: E402
    classify_adaptive_intake_domain,
    is_adaptive_intake_trigger,
    maybe_handle_adaptive_intake,
)


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
    for idx, text in enumerate({texts!r}, start=0):
        message = Msg(text, 991001 + idx)
        update = SimpleNamespace(message=message, effective_chat=SimpleNamespace(id=bot.KAREN_CHAT_ID))
        await bot.handle_text(update, ctx)
        all_replies.append(message.replies)
    print("===VAL0_ADAPTIVE_INTAKE_REPLIES===")
    print(json.dumps(all_replies, ensure_ascii=False))

asyncio.run(main())
"""
    proc = subprocess.run(
        ["./scripts/val0py", "-"],
        cwd=ROOT,
        input=probe,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise AssertionError(f"runtime probe failed rc={proc.returncode}. stdout={proc.stdout!r} stderr={proc.stderr!r}")
    marker = "===VAL0_ADAPTIVE_INTAKE_REPLIES==="
    if marker not in proc.stdout:
        raise AssertionError(f"runtime probe marker missing. stdout={proc.stdout!r} stderr={proc.stderr!r}")
    payload = proc.stdout.split(marker, 1)[1].strip().splitlines()[0]
    return json.loads(payload)


def _assert_safe(reply: str, label: str) -> None:
    for needle in (
        "guardé",
        "guardado",
        "configuré",
        "creé tareas",
        "creé recordatorios",
        "creé eventos",
        "Google Calendar",
        "Karen",
        "Caso Finca",
        "Nora",
        "abogada",
        "diagnóstico",
        "reemplazo",
        "soy consciente",
        "tengo conciencia",
        "CLIENT_",
    ):
        assert_not_contains(reply, needle, f"{label} safe output")


def test_static_classifiers() -> None:
    for phrase in (
        "Val, no sé qué necesito",
        "Val, ayúdame a empezar",
        "Val, estoy perdida",
        "Val, estoy perdido",
        "Val, tengo demasiadas cosas",
        "Val, no sé por dónde empezar",
    ):
        assert_true(is_adaptive_intake_trigger(phrase), f"adaptive trigger: {phrase}")
    assert_true(not is_adaptive_intake_trigger("Val, ¿cómo me puedes ayudar?"), "existing onboarding trigger not hijacked")
    assert_true(classify_adaptive_intake_domain("trabajo") == "work", "work domain")
    assert_true(classify_adaptive_intake_domain("agenda") == "time_day", "time/day domain")
    assert_true(classify_adaptive_intake_domain("todo me sirve") == "too_broad", "too broad domain")


def test_runtime_adaptive_intake_work_flow() -> None:
    replies = _runtime_sequence_replies_by_turn(["Val, no sé qué necesito", "sí", "trabajo", "soy cajera"])
    assert_true([len(turn) for turn in replies] == [1, 1, 1, 1], "adaptive work sequence one reply per turn")
    assert_contains(replies[0][0], "2 o 3 preguntas rápidas", "permission asks short questions")
    assert_contains(replies[0][0], "No guardo nada sin que tú me confirmes", "permission says no saving without confirmation")
    assert_contains(replies[1][0], "¿Dónde sientes más desorden ahora", "domain broad question")
    assert_contains(replies[2][0], "¿Qué tipo de trabajo haces", "work targeted question")
    assert_contains(replies[2][0], "horarios, pendientes, seguimiento", "work options")
    assert_contains(replies[3][0], "no te voy a vender un flujo de clientes", "cashier avoids irrelevant client flow")
    assert_contains(replies[3][0], "horarios, pendientes, recordatorios, dinero/pagos", "cashier support areas")
    for turn in replies:
        _assert_safe(turn[0], "adaptive work sequence")


def test_too_broad_and_refusal() -> None:
    broad = _runtime_sequence_replies_by_turn(["Val, tengo demasiadas cosas", "sí", "todo me sirve"])
    assert_true([len(turn) for turn in broad] == [1, 1, 1], "broad sequence one reply per turn")
    assert_contains(broad[-1][0], "si empezamos con todo nos ahogamos elegante", "broad answer narrows gently")
    assert_contains(broad[-1][0], "Escogemos uno primero", "broad answer chooses one first")
    _assert_safe(broad[-1][0], "broad answer")

    refusal = _runtime_sequence_replies_by_turn(["Val, estoy perdida", "no quiero responder"])
    assert_true([len(turn) for turn in refusal] == [1, 1], "refusal sequence one reply per turn")
    assert_contains(refusal[-1][0], "Perfecto, no pasa nada", "refusal respected")
    assert_contains(refusal[-1][0], "escoger un flujo manualmente", "refusal gives manual path")
    _assert_safe(refusal[-1][0], "refusal answer")


def test_existing_onboarding_and_contextless_domain() -> None:
    onboarding = _runtime_sequence_replies_by_turn(["Val, ¿cómo me puedes ayudar?"])
    assert_true(len(onboarding) == 1 and len(onboarding[0]) == 1, "existing onboarding sends one reply")
    assert_contains(onboarding[0][0], "Por ahora puedo ayudarte como operadora personal desde Telegram", "existing onboarding still works")
    assert_contains(onboarding[0][0], "Ejemplos concretos", "existing onboarding static menu remains")

    import asyncio

    class Msg:
        replies: list[str]

        def __init__(self) -> None:
            self.replies = []

        async def reply_text(self, text: str, **_kwargs):
            self.replies.append(text)
            return text

    class Ctx:
        def __init__(self) -> None:
            self.chat_data = {}

    async def probe() -> tuple[bool, list[str]]:
        msg = Msg()
        update = type("Update", (), {"message": msg})()
        handled = await maybe_handle_adaptive_intake(update, Ctx(), "trabajo")
        return handled, msg.replies

    handled, replies = asyncio.run(probe())
    assert_true(handled is False, "contextless work is not consumed by adaptive intake")
    assert_true(replies == [], "contextless work does not get adaptive reply")


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
    test_static_classifiers()
    test_runtime_adaptive_intake_work_flow()
    test_too_broad_and_refusal()
    test_existing_onboarding_and_contextless_domain()
    test_protected_not_staged()
    print("PASS: adaptive intake runtime smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
