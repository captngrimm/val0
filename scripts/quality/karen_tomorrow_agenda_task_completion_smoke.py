#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.karen_day0_routes import ROUTE_AGENDA_TOMORROW, classify_karen_day0_route  # noqa: E402
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


def test_tomorrow_agenda_copy() -> None:
    source = _bot_source()
    dashboard = _function_body(source, "build_client_agenda_dashboard")
    gcal_section = _function_body(source, "_format_client_gcal_events_section")
    tomorrow = _function_body(source, "build_unified_tomorrow_dashboard")
    assert_contains(dashboard, "Google Calendar", "agenda keeps Google Calendar path")
    assert_contains(gcal_section, "🌐 Eventos de Google Calendar", "agenda names Google Calendar events")
    assert_contains(dashboard, "🗓️ Agenda de mañana", "agenda title uses calendar-page emoji")
    assert_not_contains(gcal_section, "📅 Eventos de Google Calendar", "agenda avoids duplicate calendar emoji in gcal section")
    assert_not_contains(dashboard, "📌 Recordatorios y tareas", "agenda no longer uses vague combined heading")
    assert_not_contains(dashboard, "Agenda interna de Val", "agenda removes confusing internal label")
    assert_contains(tomorrow, "⏰ Recordatorios de Val", "tomorrow keeps Val reminders section")
    assert_contains(tomorrow, "📌 Tareas de Val", "tomorrow keeps Val tasks section")
    assert_contains(tomorrow, "No tienes tareas con fecha para mañana", "tomorrow clarifies dated tasks only")
    route = classify_karen_day0_route("Val, qué tengo mañana?")
    assert_true(route.name == ROUTE_AGENDA_TOMORROW, "tomorrow route still recognized")


def test_tasks_list_hint_and_truncation() -> None:
    rendered = render_karen_tasks_view([
        {
            "id": 1,
            "raw_input": (
                "llevar documentos a Nora con una explicación larguísima heredada de una prueba anterior "
                "que no debe ocupar toda la pantalla de tareas"
            ),
            "due_date": "",
            "status": "open",
        }
    ])
    assert_contains(rendered, "Tareas pendientes", "task list heading")
    assert_contains(rendered, "1.", "task list uses stable numbers")
    assert_contains(rendered, "marca como hecha la tarea 1", "task list includes mark-done hint")
    assert_contains(rendered, "sin fecha", "undated task is labelled")
    numbered = next(line for line in rendered.splitlines() if line.startswith("1."))
    assert_true(len(numbered) < 140, "task item is concise")


def test_task_completion_route_exists() -> None:
    source = _bot_source()
    completion = _function_body(source, "maybe_handle_karen_task_completion")
    assert_contains(completion, "marca como hecha la tarea", "completion handles mark-done phrase")
    assert_contains(completion, "ya hice la tarea", "completion handles done phrase")
    assert_contains(completion, "fetch_open_commitments", "completion reads open tasks")
    assert_contains(completion, "UPDATE commitments", "completion marks commitment done")
    assert_contains(completion, "status='done'", "completion preserves history as done")
    assert_contains(completion, "No borré el historial", "completion explains no silent delete")
    assert_contains(completion, "no toqué Google Calendar", "completion does not touch calendar")
    assert_not_contains(completion, "DELETE", "completion does not delete tasks")

    handle_text = _function_body(source, "handle_text")
    assert_contains(handle_text, "maybe_handle_karen_task_completion", "handle_text wires completion gate")


def main() -> int:
    test_tomorrow_agenda_copy()
    test_tasks_list_hint_and_truncation()
    test_task_completion_route_exists()
    print("PASS: Karen tomorrow agenda/task completion smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
