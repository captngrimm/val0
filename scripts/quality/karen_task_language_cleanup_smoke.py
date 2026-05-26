#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.document_inventory_queries import render_document_inventory_compact  # noqa: E402
from core.karen_day0_routes import ROUTE_AGENDA_TOMORROW, classify_karen_day0_route  # noqa: E402
from core.karen_notes_tasks_visibility import (  # noqa: E402
    auxiliary_task_items_from_lines,
    render_karen_case_pendientes_view,
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


def test_task_views_use_plain_language() -> None:
    pending_items = auxiliary_task_items_from_lines(["- pedir al topógrafo cotización"])

    tasks = render_karen_tasks_view([], auxiliary_tasks=pending_items)
    assert_contains(tasks, "pedir al topógrafo cotización", "pending task still shown")
    assert_contains(tasks, "sin fecha", "pending task uses plain undated label")
    assert_contains(tasks, "marca como hecha la tarea 1", "task list keeps completion hint")
    assert_contains(tasks, "pon esta tarea para mañana", "task list keeps scheduling hint")
    assert_contains(tasks, "convierta a tarea formal", "read-only limitation uses plain language")
    assert_not_contains(tasks, "pendiente auxiliar", "task list hides internal label")
    assert_not_contains(tasks, "auxiliar", "task list hides auxiliary wording")
    assert_not_contains(tasks, "CLIENT_GROCERY", "task list hides internal file")

    pendientes = render_karen_case_pendientes_view(
        tasks=[],
        auxiliary_tasks=pending_items,
        notes=[
            {
                "note_text": "Nora dijo que hay que revisar el oficio antes de la próxima reunión",
                "source": "karen_explicit_case_note",
                "created_at": "2026-05-26 15:00:00",
            }
        ],
    )
    assert_contains(pendientes, "Tareas", "pendientes keeps tasks section")
    assert_contains(pendientes, "pedir al topógrafo cotización", "pendientes shows pending task")
    assert_not_contains(pendientes, "pendiente auxiliar", "pendientes hides internal label")
    assert_not_contains(pendientes, "auxiliar", "pendientes hides auxiliary wording")


def test_completion_copy_uses_plain_language() -> None:
    completion = _function_body(_bot_source(), "maybe_handle_karen_task_completion")
    assert_contains(completion, "pendiente sin fecha", "completion says pending without date")
    assert_contains(completion, "La puedo mostrar", "completion explains visibility")
    assert_contains(completion, "todavía no puedo marcarla como hecha desde aquí", "completion explains limitation")
    assert_not_contains(completion, "pendiente auxiliar", "completion hides internal label")
    assert_not_contains(completion, "fuente auxiliar", "completion hides internal source wording")
    assert_not_contains(completion, "CLIENT_GROCERY", "completion hides internal file")


def test_tomorrow_agenda_and_document_inventory_stay_clean() -> None:
    route = classify_karen_day0_route("Val, qué tengo mañana?")
    assert_true(route.name == ROUTE_AGENDA_TOMORROW, "tomorrow agenda route still recognized")

    source = _bot_source()
    dashboard = _function_body(source, "build_client_agenda_dashboard")
    tomorrow = _function_body(source, "build_unified_tomorrow_dashboard")
    assert_contains(dashboard, "Google Calendar", "agenda keeps Google Calendar section")
    assert_contains(tomorrow, "⏰ Recordatorios", "agenda keeps reminders section")
    assert_contains(tomorrow, "📌 Tareas", "agenda keeps tasks section")
    assert_contains(tomorrow, "No tienes tareas con fecha para mañana", "agenda keeps dated-task copy")
    assert_not_contains(dashboard, "Agenda interna de Val", "agenda avoids confusing internal label")

    inventory = render_document_inventory_compact([
        {
            "filename": "Escritura_finca_10082.pdf",
            "created_at": "2026-05-26 10:00:00",
            "state": "texto leído; resumen disponible",
            "raw": "resumen disponible",
        }
    ])
    assert_contains(inventory, "📎 Documentos registrados", "document inventory header unchanged")
    assert_contains(inventory, "resumen disponible", "document inventory status unchanged")


def main() -> int:
    test_task_views_use_plain_language()
    test_completion_copy_uses_plain_language()
    test_tomorrow_agenda_and_document_inventory_stay_clean()
    print("PASS: Karen task language cleanup smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
