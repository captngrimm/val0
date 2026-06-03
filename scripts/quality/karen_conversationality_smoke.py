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
    assert_contains(opening, "agenda", "agenda opening names the surface")
    assert_true(any(word in opening.lower() for word in ("sancocho", "novela")), "agenda opening has controlled warmth")
    assert_true(opening == render_karen_safe_opening("karen", surface="agenda_today"), "safe opening is deterministic")
    assert_true(render_karen_safe_opening("other-client", surface="agenda_today") == "", "safe opening is Karen-scoped")

    task_opening = render_karen_safe_opening("karen", surface="tasks_list")
    reminder_opening = render_karen_safe_opening("karen", surface="reminders_all")
    assert_contains(task_opening, "Tany", "task opening keeps Tany")
    assert_contains(reminder_opening, "Tany", "reminder opening keeps Tany")
    assert_true(any(word in task_opening.lower() for word in ("despachar", "fila")), "task opening has controlled personality")
    assert_true(any(word in reminder_opening.lower() for word in ("circo", "drama")), "reminder opening has controlled personality")
    assert_true(opening != task_opening != reminder_opening, "safe surfaces do not all sound copy-pasted")

    wrapped = add_karen_safe_opening("🗓️ Agenda de hoy\n\n⏰ Recordatorios de Val", "karen", surface="agenda_today")
    assert_contains(wrapped, "Tany", "wrapped agenda includes Tany")
    assert_contains(wrapped, "🗓️ Agenda de hoy", "wrapped agenda keeps required facts")
    assert_contains(wrapped, "⏰ Recordatorios de Val", "wrapped agenda keeps reminder section")

    for banned in KAREN_BANNED_CONVERSATIONALITY_LEAKS:
        assert_not_contains(wrapped.lower(), banned, f"wrapped agenda avoids stale contamination: {banned}")
        assert_not_contains(opening.lower(), banned, f"opening avoids stale contamination: {banned}")
        assert_not_contains(task_opening.lower(), banned, f"task opening avoids stale contamination: {banned}")
        assert_not_contains(reminder_opening.lower(), banned, f"reminder opening avoids stale contamination: {banned}")

    for unsafe_authority in ("soy tu abogada", "asesoría legal", "dictamen legal"):
        assert_not_contains(opening.lower(), unsafe_authority, f"opening avoids fake legal authority: {unsafe_authority}")
        assert_not_contains(task_opening.lower(), unsafe_authority, f"task opening avoids fake legal authority: {unsafe_authority}")
        assert_not_contains(reminder_opening.lower(), unsafe_authority, f"reminder opening avoids fake legal authority: {unsafe_authority}")

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
