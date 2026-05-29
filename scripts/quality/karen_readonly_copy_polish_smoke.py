#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROUTINE_FOOTER = "Modo: lectura solamente"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def _source(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


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


def test_agenda_and_daily_operator_copy_are_not_footered() -> None:
    bot_source = _source("bot.py")
    agenda = _function_body(bot_source, "build_client_agenda_dashboard")
    daily = _function_body(bot_source, "_build_karen_daily_operator_reply")

    assert_not_contains(agenda, ROUTINE_FOOTER, "agenda dashboard no longer ends with routine read-only mode footer")
    assert_not_contains(agenda, "No creé, cambié ni borré eventos", "agenda dashboard removes robotic event footer")
    assert_not_contains(daily, ROUTINE_FOOTER, "Karen daily operator no longer has routine read-only footer")
    assert_contains(daily, "no sustituye revisión legal", "Karen daily operator keeps legal boundary")


def test_notes_tasks_and_pendientes_views_are_not_footered() -> None:
    from core.karen_notes_tasks_visibility import (
        render_karen_case_notes_view,
        render_karen_case_pendientes_view,
        render_karen_tasks_view,
    )

    task = {
        "raw_input": "pedir al topógrafo cotización",
        "due_date": "",
        "source_type": "commitment",
    }
    note = {
        "note_text": "Nora dijo que hay que revisar el oficio antes de la próxima reunión",
        "created_at": "2026-05-28T10:00:00",
        "source": "manual_note",
    }

    notes_view = render_karen_case_notes_view([note])
    empty_notes_view = render_karen_case_notes_view([])
    tasks_view = render_karen_tasks_view([task])
    empty_tasks_view = render_karen_tasks_view([])
    pendientes_view = render_karen_case_pendientes_view(tasks=[task], notes=[note])

    for label, rendered in (
        ("notes", notes_view),
        ("empty notes", empty_notes_view),
        ("tasks", tasks_view),
        ("empty tasks", empty_tasks_view),
        ("pendientes", pendientes_view),
    ):
        assert_not_contains(rendered, ROUTINE_FOOTER, f"{label} view removes routine read-only footer")
        assert_not_contains(rendered, "No creé, cambié ni borré nada", f"{label} view removes robotic safety footer")

    assert_contains(tasks_view, "marca como hecha la tarea 1", "task list keeps useful action hint")
    assert_contains(pendientes_view, "Siguiente paso sugerido", "pendientes keeps next action")


def test_document_inventory_keeps_legal_boundary_without_mode_footer() -> None:
    from core.document_inventory_queries import render_document_inventory_compact

    rendered = render_document_inventory_compact([
        {
            "id": 1,
            "filename": "Agi.pdf",
            "created_at": "2026-05-28T10:00:00",
            "summary_available": True,
            "state": "texto extraído e indexado",
        }
    ])

    assert_contains(rendered, "📎 Documentos registrados", "document inventory still renders")
    assert_contains(rendered, "no sustituye revisión legal o profesional", "document inventory keeps legal/professional boundary")
    assert_not_contains(rendered, ROUTINE_FOOTER, "document inventory has no routine read-only footer")


def test_write_confirmations_and_failures_keep_safety_copy() -> None:
    pending_confirm = _function_body(_source("bot.py"), "maybe_handle_pending_gcal_appointment_confirmation")
    assert_contains(pending_confirm, "Listo. Agregué al Google Calendar", "gcal success still confirms write")
    assert_contains(pending_confirm, "Google Calendar se encargará de sus notificaciones", "gcal success keeps notification boundary")
    assert_contains(pending_confirm, "Solo creé este evento. No creé recordatorios de Val", "gcal success keeps write scope")
    assert_contains(pending_confirm, "No lo marqué como creado", "gcal failure keeps no-fake-success copy")


def main() -> int:
    test_agenda_and_daily_operator_copy_are_not_footered()
    test_notes_tasks_and_pendientes_views_are_not_footered()
    test_document_inventory_keeps_legal_boundary_without_mode_footer()
    test_write_confirmations_and_failures_keep_safety_copy()
    print("PASS: Karen read-only copy polish smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
