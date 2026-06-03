#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.karen_conversationality import (  # noqa: E402
    KAREN_BANNED_CONVERSATIONALITY_LEAKS,
    add_karen_safe_opening,
    render_karen_safe_opening,
)


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label}: unexpected {needle!r}")


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    opening = render_karen_safe_opening("karen", surface="agenda_today")
    assert_contains(opening, "Tany", "safe opening keeps Karen vocative")
    assert_true(opening == render_karen_safe_opening("karen", surface="agenda_today"), "safe opening is deterministic")
    assert_true(render_karen_safe_opening("other-client", surface="agenda_today") == "", "safe opening is Karen-scoped")

    wrapped = add_karen_safe_opening("🗓️ Agenda de hoy\n\n⏰ Recordatorios de Val", "karen", surface="agenda_today")
    assert_contains(wrapped, "Tany", "wrapped agenda includes Tany")
    assert_contains(wrapped, "🗓️ Agenda de hoy", "wrapped agenda keeps required facts")
    assert_contains(wrapped, "⏰ Recordatorios de Val", "wrapped agenda keeps reminder section")

    for banned in KAREN_BANNED_CONVERSATIONALITY_LEAKS:
        assert_not_contains(wrapped.lower(), banned, f"wrapped agenda avoids stale contamination: {banned}")
        assert_not_contains(opening.lower(), banned, f"opening avoids stale contamination: {banned}")

    bot = _read("bot.py")
    tasks = _read("core/karen_notes_tasks_visibility.py")
    assert_contains(bot, "add_karen_safe_opening", "bot wires safe opening helper")
    assert_contains(bot, "surface=f\"agenda_{window}\"", "agenda dashboard has conversationality surface")
    assert_contains(bot, "surface=f\"reminders_{when}\"", "reminder list has conversationality surface")
    assert_contains(tasks, "add_karen_safe_opening", "task list wires safe opening helper")
    assert_contains(tasks, "surface=\"tasks_list\"", "task list has conversationality surface")

    assert_contains(bot, "maybe_handle_pending_gcal_appointment_confirmation", "gcal confirmation route remains present")
    assert_contains(bot, "maybe_handle_karen_task_delete_request", "task delete route remains present")
    assert_contains(bot, "maybe_handle_karen_reminder_management", "reminder management route remains present")

    print("PASS: Karen conversationality smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
