#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOT = (ROOT / "bot.py").read_text(encoding="utf-8")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label}: unexpected {needle!r}")


def function_body(name: str) -> str:
    for marker in (f"async def {name}", f"def {name}"):
        start = BOT.find(marker)
        if start >= 0:
            break
    else:
        raise AssertionError(f"missing function {name}")
    next_def = BOT.find("\ndef ", start + 1)
    next_async = BOT.find("\nasync def ", start + 1)
    stops = [pos for pos in (next_def, next_async) if pos > start]
    end = min(stops) if stops else len(BOT)
    return BOT[start:end]


def main() -> int:
    agenda = function_body("build_client_agenda_dashboard")
    internal = function_body("_build_val_agenda_for_date")
    reminder_query = function_body("_looks_like_karen_reminder_list_query")

    assert_contains(agenda, "_build_val_agenda_for_date", "today agenda uses clean Val agenda sections")
    assert_not_contains(agenda, "_generate_morning_brief_det", "today agenda avoids old morning brief format")
    assert_contains(internal, "⏰ Recordatorios de Val", "Val reminders section remains")
    assert_contains(internal, "📌 Tareas de Val", "Val tasks section remains")
    assert_contains(internal, "status IN ('pending', 'sending')", "agenda shows active reminders only")
    assert_not_contains(internal, "status IN ('pending', 'sending', 'sent')", "agenda no longer mixes sent reminders as active")
    assert_contains(reminder_query, "recordatorios activos", "active reminders wording routes to reminders")
    assert_contains(reminder_query, "recordatorios pendientes", "pending reminders wording routes to reminders")
    assert_contains(BOT, "va\\s+el", "voice/STT wake-prefix normalization covers 'va el'")
    print("PASS: Karen agenda active route smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
