#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.karen_notes_tasks_visibility import render_karen_tasks_view  # noqa: E402


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def _bot_source() -> str:
    return (REPO_ROOT / "bot.py").read_text(encoding="utf-8")


def _function_body(source: str, name: str) -> str:
    for marker in (f"async def {name}", f"def {name}"):
        start = source.find(marker)
        if start >= 0:
            break
    else:
        raise AssertionError(f"missing function {name}")
    next_def = source.find("\ndef ", start + 1)
    next_async_def = source.find("\nasync def ", start + 1)
    stops = [pos for pos in (next_def, next_async_def) if pos > start]
    end = min(stops) if stops else len(source)
    return source[start:end]


def test_agenda_task_numbering_uses_single_counter() -> None:
    tomorrow = _function_body(_bot_source(), "build_unified_tomorrow_dashboard")
    assert_contains(tomorrow, "task_display_number = 1", "single task counter initialized")
    assert_contains(tomorrow, "task_display_number += 1", "task counter increments")
    assert_contains(tomorrow, "warning_numbers", "warning task numbers tracked")
    assert_contains(tomorrow, "marca la tarea {first_warning}", "warning action copy matches visible number")
    assert_not_contains(tomorrow, "enumerate(reminder_like_tasks, start=1)", "warning numbering does not reset")
    assert_not_contains(tomorrow, "marca la tarea 2 como hecha", "no hardcoded tarea 2")


def test_task_active_list_numbering_is_consistent() -> None:
    rendered = render_karen_tasks_view([
        {
            "id": 1,
            "raw_input": "pedir al topógrafo cotización",
            "due_date": "2026-05-29",
            "status": "open",
        },
        {
            "id": 2,
            "raw_input": "Val recuérdame llamar al Juzgado a las 9 de la mañana mañana.",
            "due_date": "2026-05-29",
            "status": "open",
        },
    ])
    assert_contains(rendered, "1. pedir al topógrafo cotización", "normal task numbered 1")
    assert_contains(rendered, "2. Val recuérdame llamar", "warning-like task numbered 2")
    assert_contains(rendered, "Posible recordatorio guardado como tarea", "warning label kept")
    assert_not_contains(rendered, "\n1. Val recuérdame", "task list does not reset numbering")


def test_past_reminder_copy_avoids_editing() -> None:
    reminder_list = _function_body(_bot_source(), "_render_karen_reminder_list")
    assert_contains(reminder_list, "elimina el recordatorio vencido 1", "past reminder delete copy")
    assert_contains(reminder_list, "Conserva el historial", "past reminder history copy")
    past_branch = reminder_list.split('if when == "past":', 1)[1].split("else:", 1)[0]
    assert_not_contains(past_branch, "cambia el recordatorio", "past reminders do not suggest edit")


def test_existing_document_routes_remain_present() -> None:
    source = _bot_source()
    assert_contains(source, "maybe_handle_document_query", "document inventory route present")
    assert_contains(source, "maybe_handle_document_summary_query", "document summary route present")


def main() -> int:
    test_agenda_task_numbering_uses_single_counter()
    test_task_active_list_numbering_is_consistent()
    test_past_reminder_copy_avoids_editing()
    test_existing_document_routes_remain_present()
    print("PASS: Karen unified task numbering smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
