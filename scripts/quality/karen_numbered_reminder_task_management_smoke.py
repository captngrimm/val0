#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.karen_notes_tasks_visibility import (  # noqa: E402
    looks_like_karen_tasks_query,
    parse_karen_task_schedule_for_tomorrow,
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


def test_agenda_has_numbered_reminders_tasks_and_natural_actions() -> None:
    source = _bot_source()
    tomorrow = _function_body(source, "build_unified_tomorrow_dashboard")
    dashboard = _function_body(source, "build_client_agenda_dashboard")
    assert_contains(dashboard, "Google Calendar", "agenda keeps Google Calendar")
    assert_contains(tomorrow, "⏰ Recordatorios", "reminder section")
    assert_contains(tomorrow, "📌 Tareas", "task section")
    assert_contains(tomorrow, "enumerate(reminders, start=1)", "reminders numbered")
    assert_contains(tomorrow, "task_display_number = 1", "tasks numbered with unified visible counter")
    assert_contains(tomorrow, "elimina el recordatorio 1", "natural delete hint")
    assert_contains(tomorrow, "edit_number = 2 if len(reminders) >= 2 else 1", "natural edit hint uses visible count")
    assert_contains(tomorrow, "cambia el recordatorio {edit_number} para las 11", "natural edit hint matches visible number")
    assert_contains(tomorrow, "marca la tarea 1 como hecha", "natural done hint")
    assert_contains(tomorrow, "elimina la tarea 1", "natural task delete hint")
    assert_not_contains(tomorrow, "pon la tarea 1 para mañana", "tomorrow agenda avoids rescheduling already-dated tasks")
    assert_not_contains(tomorrow, "/rmd", "no slash command in agenda")
    assert_not_contains(dashboard, "/rmd", "no slash command in dashboard")


def test_reminder_management_routes_and_copy() -> None:
    source = _bot_source()
    helper = _function_body(source, "_parse_karen_reminder_management")
    handler = _function_body(source, "maybe_handle_karen_reminder_management")
    list_helper = _function_body(source, "_render_karen_reminder_list")
    handle_text = _function_body(source, "handle_text")

    assert_contains(list_helper, "⏰ Recordatorios de mañana", "tomorrow reminders list")
    assert_contains(list_helper, "elimina el recordatorio 1", "list delete hint")
    assert_contains(list_helper, "cambia el recordatorio 1 para las 10", "list edit hint")
    assert_not_contains(list_helper, "/rmd", "natural list hides slash commands")

    assert_contains(helper, "elimina|eliminar|borra|borrar|cancela|cancelar|quita|quitar", "delete verbs parsed")
    assert_contains(helper, "cambia|mueve", "edit verbs parsed")
    assert_contains(handler, "cancel_reminder", "delete uses reminder cancellation")
    assert_contains(handler, "Listo. Eliminé el recordatorio", "delete confirmation")
    assert_contains(handler, "Todavía no puedo editarlo directamente", "honest edit fallback")
    assert_contains(handler, "eliminarlo y crear uno nuevo", "honest edit alternative")
    assert_contains(handler, "¿Quieres eliminar el recordatorio", "ambiguous delete asks clarification")
    assert_contains(handle_text, "maybe_handle_karen_reminder_management", "reminder management wired")


def test_task_query_creation_delete_schedule_completion_routes() -> None:
    source = _bot_source()
    creation = _function_body(source, "_extract_karen_task_creation_text")
    create_handler = _function_body(source, "maybe_handle_karen_task_creation")
    delete_handler = _function_body(source, "maybe_handle_karen_task_delete_request")
    completion = _function_body(source, "maybe_handle_karen_task_completion")
    handle_text = _function_body(source, "handle_text")

    assert_true(looks_like_karen_tasks_query("Val, qué tareas activas tengo?"), "active task query")
    assert_true(looks_like_karen_tasks_query("Val, qué tareas pendientes tengo?"), "pending task query")
    assert_true(looks_like_karen_tasks_query("Val, cuáles son mis tareas registradas?"), "registered task query")
    assert_contains(creation, "registra|agrega|anota", "task creation verbs")
    assert_contains(creation, "recuerdame", "task creation does not steal reminders")
    assert_contains(create_handler, "upsert_commitment", "task creation stores commitment")
    assert_contains(delete_handler, "status='deleted'", "explicit task delete removes from active list")
    assert_contains(delete_handler, "Listo. Quité esta tarea del listado activo", "explicit task delete success copy")
    assert_contains(completion, "status='done'", "mark done still supported")
    assert_contains(handle_text, "maybe_handle_karen_task_creation", "task creation wired")
    assert_contains(handle_text, "maybe_handle_karen_task_delete_request", "task delete wired")
    assert_contains(handle_text, "maybe_handle_karen_task_schedule_for_tomorrow", "task schedule still wired")
    assert_contains(handle_text, "maybe_handle_karen_task_completion", "task completion still wired")

    scheduled = parse_karen_task_schedule_for_tomorrow("Val, cambia la tarea uno para mañana")
    assert_true(bool(scheduled and scheduled.get("number") == 1), "word-number task schedule")


def test_task_list_numbered_and_plain_language() -> None:
    rendered = render_karen_tasks_view([
        {
            "id": 1,
            "raw_input": "pedir cotización al topógrafo",
            "due_date": "",
            "status": "open",
        }
    ])
    assert_contains(rendered, "1. pedir cotización al topógrafo", "numbered task")
    assert_contains(rendered, "sin fecha", "plain date label")
    assert_contains(rendered, "marca como hecha la tarea 1", "done hint")
    assert_not_contains(rendered, "auxiliar", "no auxiliary jargon")
    assert_not_contains(rendered, "/rmd", "no slash command")


def test_document_routes_not_touched() -> None:
    source = _bot_source()
    assert_contains(source, "maybe_handle_document_summary_query", "document summary route still present")
    assert_contains(source, "maybe_handle_document_query", "document inventory route still present")


def main() -> int:
    test_agenda_has_numbered_reminders_tasks_and_natural_actions()
    test_reminder_management_routes_and_copy()
    test_task_query_creation_delete_schedule_completion_routes()
    test_task_list_numbered_and_plain_language()
    test_document_routes_not_touched()
    print("PASS: Karen numbered reminder/task management smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
