#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.karen_notes_tasks_visibility import (  # noqa: E402
    looks_like_karen_tasks_query,
    looks_like_reminder_command_task,
    render_karen_tasks_view,
)


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


def test_tomorrow_agenda_hygiene_copy() -> None:
    source = _bot_source()
    dashboard = _function_body(source, "build_client_agenda_dashboard")
    gcal_section = _function_body(source, "_format_client_gcal_events_section")
    tomorrow = _function_body(source, "build_unified_tomorrow_dashboard")
    assert_contains(dashboard, "🗓️ Agenda de mañana", "agenda title uses calendar-page emoji")
    assert_contains(gcal_section, "🌐 Eventos de Google Calendar", "gcal section uses globe emoji")
    assert_not_contains(gcal_section, "📅 Eventos de Google Calendar", "gcal section avoids duplicate calendar emoji")
    assert_contains(tomorrow, "enumerate(reminders, start=1)", "reminders remain numbered")
    assert_contains(tomorrow, "task_display_number = 1", "tasks use unified visible numbering")
    assert_contains(tomorrow, "Elimina el recordatorio 1", "reminder delete action")
    assert_contains(tomorrow, "edit_number = 2 if len(reminders) >= 2 else 1", "reminder edit action uses visible count")
    assert_contains(tomorrow, "Cambia el recordatorio {edit_number} para las 11", "reminder edit action matches visible number")
    assert_contains(tomorrow, "Marca la tarea 1 como hecha", "task done action")
    assert_contains(tomorrow, "Elimina la tarea 1", "task cleanup action")
    assert_not_contains(tomorrow, "pon la tarea 1 para mañana", "no tomorrow reschedule hint")
    assert_not_contains(tomorrow, "/rmd", "no slash command")


def test_reminder_time_mismatch_and_past_routes() -> None:
    source = _bot_source()
    note = _function_body(source, "_karen_reminder_time_note")
    list_helper = _function_body(source, "_looks_like_karen_reminder_list_query")
    row_helper = _function_body(source, "_karen_reminder_rows")
    render_helper = _function_body(source, "_render_karen_reminder_list")
    handler = _function_body(source, "maybe_handle_karen_reminder_management")

    assert_contains(note, "texto menciona otra hora", "time mismatch warning exists")
    assert_contains(row_helper, 'when in {"all", "active"} and due_dt < now', "active list hides past reminders")
    assert_contains(row_helper, 'when == "past" and due_dt >= now', "past route filters future reminders")
    assert_contains(list_helper, "recordatorios vencidos", "past reminder route")
    assert_contains(list_helper, "recordatorios pasados", "past reminder variants")
    assert_contains(render_helper, "Hay recordatorios vencidos ocultos", "active list mentions hidden past reminders")
    assert_contains(handler, "no los elimino en bloque sin confirmación", "bulk delete asks confirmation")


def test_reminder_like_tasks_are_labeled() -> None:
    rendered = render_karen_tasks_view([
        {
            "id": 2,
            "raw_input": "Val recuérdame llamar al. Juzgado a las 9 de la mañana mañana.",
            "due_date": "2026-05-29",
            "status": "open",
        }
    ])
    assert_true(looks_like_reminder_command_task("Val recuérdame llamar al juzgado mañana a las 9"), "reminder-like task detected")
    assert_contains(rendered, "Posible recordatorio guardado como tarea", "task list labels reminder pollution")
    assert_contains(rendered, "marca como hecha la tarea 1", "cleanup action still available")
    assert_not_contains(rendered, "auxiliar", "no internal jargon")

    source = _bot_source()
    tomorrow = _function_body(source, "build_unified_tomorrow_dashboard")
    assert_contains(tomorrow, "Posible recordatorio guardado como tarea", "agenda labels reminder-like tasks")
    assert_contains(tomorrow, "Todavía no convierto tareas a recordatorios automáticamente", "conversion fallback honest")


def test_task_routes_still_plain_task_list() -> None:
    assert_true(looks_like_karen_tasks_query("Val, qué tareas activas tengo?"), "active tasks route")
    assert_true(looks_like_karen_tasks_query("Val, qué tareas pendientes tengo?"), "pending tasks route")
    assert_true(looks_like_karen_tasks_query("Val, cuáles son mis tareas registradas?"), "registered tasks route")


def test_document_routes_untouched() -> None:
    source = _bot_source()
    assert_contains(source, "maybe_handle_document_summary_query", "document summary route remains")
    assert_contains(source, "maybe_handle_document_query", "document inventory route remains")


def main() -> int:
    test_tomorrow_agenda_hygiene_copy()
    test_reminder_time_mismatch_and_past_routes()
    test_reminder_like_tasks_are_labeled()
    test_task_routes_still_plain_task_list()
    test_document_routes_untouched()
    print("PASS: Karen agenda hygiene smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
