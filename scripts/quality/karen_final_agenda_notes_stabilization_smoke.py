#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.karen_day0_routes import ROUTE_AGENDA_TOMORROW, classify_karen_day0_route  # noqa: E402
from core.karen_notes_tasks_visibility import (  # noqa: E402
    render_karen_case_notes_view,
    render_karen_case_pendientes_view,
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


def _notes_fixture() -> list[dict]:
    clean = {
        "id": 10,
        "note_text": "Nora dijo que hay que revisar el oficio antes de la próxima reunión",
        "source": "karen_explicit_case_note",
        "created_at": "2026-05-26 15:00:00",
    }
    noisy = [
        {
            "id": 9,
            "note_text": "Cita / agenda del caso: guarda nota de finca: Nora dijo que hay que revisar el oficio antes de la próxima reunión",
            "source": "case_appointment_v0",
            "created_at": "2026-05-26 14:00:00",
        },
        {
            "id": 8,
            "note_text": "Inventario inicial: historia larga vieja de contexto con detalles no accionables",
            "source": "manual_note",
            "created_at": "2026-05-20 09:00:00",
        },
        {
            "id": 7,
            "note_text": "nota de prueba test antigua",
            "source": "manual_note",
            "created_at": "2026-05-19 09:00:00",
        },
        {
            "id": 6,
            "note_text": "- Archivo: foto_prueba_test.jpg\n- Estado: guardado; requiere revisión",
            "source": "telegram_attachment_vfms",
            "created_at": "2026-05-18 09:00:00",
        },
        {
            "id": 5,
            "note_text": "- Archivo: oficio_nora.pdf\n- Estado: guardado; requiere revisión",
            "source": "telegram_attachment_vfms",
            "created_at": "2026-05-26 13:00:00",
        },
    ]
    return [clean, *noisy]


def _source(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_appointment_gate_re_available() -> None:
    source = _source("core/karen_appointments.py")
    assert_contains(source, "import re", "karen_appointments imports re")
    assert_contains(source, "re.match", "appointment guard still exercises re")
    assert_contains(source, "(?:guarda|guardar|anota|toma)", "appointment guard excludes note commands")
    assert_contains(source, "return False", "appointment guard can reject note commands")


def test_notes_are_concise_and_clean_first() -> None:
    rendered = render_karen_case_notes_view(_notes_fixture())
    assert_contains(rendered, "Notas de finca/caso", "notes heading")
    first_item = next(line for line in rendered.splitlines() if line.startswith("1."))
    assert_contains(first_item, "Nora dijo que hay que revisar el oficio", "clean note first")
    assert_not_contains(first_item, "Cita / agenda del caso", "appointment label not primary")
    assert_not_contains(first_item, "guarda nota de finca", "raw command not primary")
    assert_not_contains(rendered, "Cita / agenda del caso", "appointment label hidden from notes")
    assert_contains(rendered, "Oculté", "historical/test noise summarized")
    note_lines = [line for line in rendered.splitlines() if line[:2] in {"1.", "2.", "3.", "4.", "5.", "6."}]
    assert_true(len(note_lines) <= 5, "notes view capped")


def test_pendientes_sections_and_next_action() -> None:
    long_task = (
        "hacer una estrategia larguísima para convencer a Guillermo con una narrativa de muchas líneas "
        "y detalles heredados que no debe dominar el próximo paso"
    )
    rendered = render_karen_case_pendientes_view(
        tasks=[
            {"id": 1, "raw_input": long_task, "due_date": "", "status": "open"},
            {"id": 2, "raw_input": "escribirle al topógrafo", "due_date": "2026-05-26T08:00:00", "status": "open"},
        ],
        notes=_notes_fixture(),
    )
    assert_contains(rendered, "Tareas", "pending has tasks section")
    assert_contains(rendered, "Notas accionables", "pending has actionable notes section")
    assert_contains(rendered, "Documentos / revisión", "pending has documents section")
    assert_contains(rendered, "oficio_nora.pdf", "real document appears")
    assert_not_contains(rendered, "foto_prueba_test.jpg", "test document suppressed")
    next_line = next(line for line in rendered.splitlines() if line.startswith("Siguiente paso sugerido:"))
    assert_contains(next_line, "revisar el oficio", "next action prefers clean actionable note")
    assert_true(len(next_line) <= 140, "next action concise")
    assert_not_contains(next_line, "convencer a Guillermo", "next action avoids long legacy task blob")


def test_agenda_route_still_passes() -> None:
    route = classify_karen_day0_route("Val, qué tengo mañana?")
    assert_true(route.name == ROUTE_AGENDA_TOMORROW, "tomorrow agenda route unchanged")


def main() -> int:
    test_appointment_gate_re_available()
    test_notes_are_concise_and_clean_first()
    test_pendientes_sections_and_next_action()
    test_agenda_route_still_passes()
    print("PASS: Karen final agenda/notes stabilization smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
