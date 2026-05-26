#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.karen_day0_routes import ROUTE_AGENDA_TOMORROW, classify_karen_day0_route  # noqa: E402
from core.karen_notes_tasks_visibility import (  # noqa: E402
    looks_like_karen_notes_query,
    looks_like_karen_tasks_query,
    render_karen_case_notes_view,
    render_karen_tasks_view,
)


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_false(value, label: str) -> None:
    if value:
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


def test_notes_route_and_render() -> None:
    for prompt in (
        "Val, qué notas tengo de finca?",
        "qué notas tengo de finca",
        "notas de finca",
        "notas del caso",
    ):
        assert_true(looks_like_karen_notes_query(prompt), f"notes query recognized: {prompt}")

    rendered = render_karen_case_notes_view([
        {
            "id": 1,
            "note_text": "Nora dijo que hay que revisar el oficio antes de la próxima reunión",
            "source": "karen_explicit_case_note",
            "created_at": "2026-05-26 09:15:00",
        }
    ])
    assert_contains(rendered, "Notas de finca/caso", "notes heading")
    assert_contains(rendered, "Nora dijo", "saved note appears")
    assert_not_contains(rendered, "Documentos del caso", "notes view is not document inventory")

    empty = render_karen_case_notes_view([])
    assert_contains(empty, "No encontré notas", "empty notes says none found")
    assert_contains(empty, "guarda nota de finca", "empty notes suggests note command")
    assert_not_contains(empty, "Documentos del caso", "empty notes is not document inventory")


def test_tasks_route_and_render() -> None:
    for prompt in (
        "Val, qué tareas tengo?",
        "qué tareas tengo",
        "tareas pendientes",
        "pendientes",
    ):
        assert_true(looks_like_karen_tasks_query(prompt), f"tasks query recognized: {prompt}")

    rendered = render_karen_tasks_view([
        {
            "id": 7,
            "raw_input": "escribirle al topógrafo",
            "action": "escribir",
            "target": "topógrafo",
            "due_date": "2026-05-26T08:00:00",
            "status": "open",
        },
        {
            "id": 8,
            "raw_input": "revisar oficio",
            "due_date": "",
            "status": "open",
        },
    ])
    assert_contains(rendered, "Tareas pendientes", "tasks heading")
    assert_contains(rendered, "escribirle al topógrafo", "task with date appears")
    assert_contains(rendered, "2026-05-26 08:00", "task date appears")
    assert_contains(rendered, "sin fecha", "task without date is labelled")
    assert_not_contains(rendered, "convencer a Guillermo", "tasks view does not invent strategy")
    assert_not_contains(rendered, "Siguiente acción sugerida", "tasks view is not Daily Operator")
    assert_contains(rendered, "márcala como hecha", "tasks view offers simple command")


def test_agenda_route_unchanged_and_gate_order() -> None:
    route = classify_karen_day0_route("Val, qué tengo mañana?")
    assert_true(route.name == ROUTE_AGENDA_TOMORROW, "tomorrow agenda route still recognized")

    source = _bot_source()
    handle_text = _function_body(source, "handle_text")
    visibility_gate = handle_text.find("maybe_handle_karen_notes_tasks_visibility")
    day0_gate = handle_text.find("maybe_handle_karen_day0_route")
    daily_gate = handle_text.find("maybe_handle_karen_daily_operator_query")
    document_gate = handle_text.find("maybe_handle_document_query")
    assert_true(visibility_gate >= 0, "handle_text has visibility gate")
    assert_true(day0_gate < 0 or visibility_gate < day0_gate, "visibility beats Day0")
    assert_true(daily_gate < 0 or visibility_gate < daily_gate, "visibility beats Daily Operator")
    assert_true(document_gate < 0 or visibility_gate < document_gate, "visibility beats document inventory")

    process = _function_body(source, "_process_text_pipeline")
    visibility_gate = process.find("maybe_handle_karen_notes_tasks_visibility")
    day0_gate = process.find("maybe_handle_karen_day0_route")
    daily_gate = process.find("maybe_handle_karen_daily_operator_query")
    assert_true(visibility_gate >= 0, "pipeline has visibility gate")
    assert_true(day0_gate < 0 or visibility_gate < day0_gate, "pipeline visibility beats Day0")
    assert_true(daily_gate < 0 or visibility_gate < daily_gate, "pipeline visibility beats Daily Operator")


def main() -> int:
    test_notes_route_and_render()
    test_tasks_route_and_render()
    test_agenda_route_unchanged_and_gate_order()
    print("PASS: Karen notes/tasks visibility smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
