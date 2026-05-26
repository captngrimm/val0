#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.karen_day0_routes import ROUTE_AGENDA_TOMORROW, classify_karen_day0_route  # noqa: E402
from core.karen_notes_tasks_visibility import (  # noqa: E402
    looks_like_karen_case_pendientes_query,
    looks_like_karen_notes_query,
    looks_like_karen_tasks_query,
    render_karen_case_notes_view,
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


def _sample_notes() -> list[dict]:
    return [
        {
            "id": 4,
            "note_text": "Nora dijo que hay que revisar el oficio antes de la próxima reunión",
            "source": "karen_explicit_case_note",
            "created_at": "2026-05-26 12:00:00",
        },
        {
            "id": 3,
            "note_text": "Cita / agenda del caso:\n\nVal, guarda nota de finca: Nora dijo que hay que revisar el oficio antes de la próxima reunión",
            "source": "case_appointment_v0",
            "created_at": "2026-05-26 11:00:00",
        },
        {
            "id": 2,
            "note_text": "Cita / agenda del caso: guarda nota de finca: revisar oficio antes de reunión",
            "source": "case_appointment_v0",
            "created_at": "2026-05-26 10:00:00",
        },
        {
            "id": 1,
            "note_text": "- Archivo: foto_prueba_test.jpg\n- Estado: guardado; requiere revisión",
            "source": "telegram_attachment_vfms",
            "created_at": "2026-05-25 10:00:00",
        },
        {
            "id": 5,
            "note_text": "- Archivo: oficio_nora.pdf\n- Estado: guardado; requiere revisión",
            "source": "telegram_attachment_vfms",
            "created_at": "2026-05-26 13:00:00",
        },
    ]


def test_notes_cleanup() -> None:
    assert_true(looks_like_karen_notes_query("qué notas tengo de finca"), "notes route recognized")
    rendered = render_karen_case_notes_view(_sample_notes())
    assert_contains(rendered, "Notas de finca/caso", "notes heading")
    assert_contains(rendered, "Nora dijo que hay que revisar el oficio", "clean note appears")
    assert_not_contains(rendered, "Cita / agenda del caso", "old appointment label hidden")
    assert_not_contains(rendered, "guarda nota de finca:", "raw note command hidden")
    assert_not_contains(rendered, "Documentos del caso", "notes view is not document inventory")
    first_item = next(line for line in rendered.splitlines() if line.startswith("1."))
    assert_contains(first_item, "Nora dijo", "newest clean note first")


def test_pendientes_view() -> None:
    for prompt in (
        "Val, qué pendientes tengo de finca?",
        "pendientes de finca",
        "pendientes del caso",
        "qué falta revisar de finca",
        "qué falta revisar con Nora",
    ):
        assert_true(looks_like_karen_case_pendientes_query(prompt), f"pending route recognized: {prompt}")

    rendered = render_karen_case_pendientes_view(
        tasks=[
            {
                "id": 7,
                "raw_input": "escribirle al topógrafo",
                "due_date": "2026-05-26T08:00:00",
                "status": "open",
            }
        ],
        notes=_sample_notes(),
    )
    assert_contains(rendered, "Pendientes de finca/caso", "pending heading")
    assert_contains(rendered, "Tareas", "pending includes tasks section")
    assert_contains(rendered, "Notas accionables", "pending includes actionable notes")
    assert_contains(rendered, "Documentos / revisión", "pending includes document review section")
    assert_contains(rendered, "escribirle al topógrafo", "task appears")
    assert_contains(rendered, "revisar el oficio", "actionable note appears")
    assert_contains(rendered, "oficio_nora.pdf", "real document review appears")
    assert_not_contains(rendered, "foto_prueba_test.jpg", "test document noise suppressed")
    assert_not_contains(rendered, "Finca: 10082", "pending view is not static finca facts")
    assert_not_contains(rendered, "Tomo/Rollo", "pending view is not registry facts")
    assert_contains(rendered, "Siguiente paso sugerido", "pending view has concise next action")


def test_tasks_and_agenda_still_ok() -> None:
    assert_true(looks_like_karen_tasks_query("qué tareas tengo"), "tasks route still recognized")
    tasks = render_karen_tasks_view([
        {"id": 1, "raw_input": "revisar oficio", "due_date": "", "status": "open"}
    ])
    assert_contains(tasks, "Tareas pendientes", "tasks heading still clean")
    assert_contains(tasks, "sin fecha", "tasks show no-date label")
    assert_not_contains(tasks, "Siguiente acción sugerida", "tasks not Daily Operator")

    route = classify_karen_day0_route("Val, qué tengo mañana?")
    assert_true(route.name == ROUTE_AGENDA_TOMORROW, "tomorrow agenda route unchanged")


def main() -> int:
    test_notes_cleanup()
    test_pendientes_view()
    test_tasks_and_agenda_still_ok()
    print("PASS: Karen pendientes/notes cleanup smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
