#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
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
        message = Msg(text, 992001 + idx)
        update = SimpleNamespace(message=message, effective_chat=SimpleNamespace(id=bot.KAREN_CHAT_ID))
        await bot.handle_text(update, ctx)
        all_replies.append(message.replies)
    print("===VAL0_ADAPTIVE_RECOMMENDATION_REPLIES===")
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
    marker = "===VAL0_ADAPTIVE_RECOMMENDATION_REPLIES==="
    if marker not in proc.stdout:
        raise AssertionError(f"runtime probe marker missing. stdout={proc.stdout!r} stderr={proc.stderr!r}")
    payload = proc.stdout.split(marker, 1)[1].strip().splitlines()[0]
    return json.loads(payload)


def _final_reply_for(answer: str) -> str:
    replies = _runtime_sequence_replies_by_turn(["Val, no sé qué necesito", "sí", "trabajo", "soy cajera", answer])
    assert_true([len(turn) for turn in replies] == [1, 1, 1, 1, 1], f"{answer} one reply per turn")
    return replies[-1][0]


def _assert_safe(reply: str, label: str) -> None:
    for needle in (
        "guardé",
        "saved",
        "memory persisted",
        "creé tareas",
        "creé recordatorios",
        "creé eventos",
        "Google Calendar",
        "Karen",
        "Caso Finca",
        "Nora",
        "soy consciente",
        "tengo conciencia",
        "diagnóstico",
        "decisión financiera por ti",
        "recomendación financiera personalizada",
        "reemplaza",
        "CLIENT_",
    ):
        assert_not_contains(reply, needle, f"{label} safe output")
    assert_contains(reply, "No guardo nada todavía", f"{label} no saving boundary")
    assert_contains(reply, "no creo tareas, recordatorios ni eventos", f"{label} no action boundary")


def test_work_recommendations() -> None:
    cases = (
        ("horarios", ("Rutina y Turnos", "horarios", "antes/después del turno")),
        ("pendientes", ("Organizar mi día laboral", "pendientes", "revisión pequeña")),
        ("recordatorios", ("Recordatorios básicos", "recordatorio", "confirmación")),
        ("dinero/pagos", ("Pagos y fechas importantes", "sin convertirlo en consejo financiero", "orden y visibilidad")),
        ("cansancio", ("Cierre de turno", "apoyo práctico", "no como lectura clínica")),
        ("todo", ("se vuelve monstruo", "Organizar mi día laboral", "primer piloto")),
    )
    for answer, needles in cases:
        reply = _final_reply_for(answer)
        assert_contains(reply, "Mi recomendación sería empezar", f"{answer} recommendation")
        assert_contains(reply, "Lo probaríamos una semana", f"{answer} one-week test")
        assert_contains(reply, "¿Te parece usar", f"{answer} asks pilot confirmation")
        for needle in needles:
            assert_contains(reply, needle, f"{answer} expected recommendation detail")
        _assert_safe(reply, answer)


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
    test_work_recommendations()
    test_protected_not_staged()
    print("PASS: adaptive intake recommendation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
