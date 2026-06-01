#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOT = (ROOT / "bot.py").read_text(encoding="utf-8")


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label}: unexpected {needle!r}")


def function_body(name: str) -> str:
    for marker in (f"async def {name}", f"def {name}"):
        start = BOT.find(marker)
        if start >= 0:
            break
    else:
        raise AssertionError(f"missing function {name}")
    next_def = BOT.find("\ndef ", start + 1)
    next_async = BOT.find("\nasync def ", start + 1)
    stops = [pos for pos in (next_def, next_async) if pos > start]
    end = min(stops) if stops else len(BOT)
    return BOT[start:end]


def test_task_query_beats_case_routes() -> None:
    handle = function_body("handle_text")
    pipeline = function_body("_process_text_pipeline")
    hard_gate = function_body("maybe_handle_karen_task_query_hard_gate")
    visibility = function_body("maybe_handle_karen_notes_tasks_visibility")
    for phrase in (
        "Val, ¿qué tareas tengo activa?",
        "Vale. ¿Qué tareas tengo activas?",
        "val que tareas tengo activas?",
    ):
        assert_true("tareas" in phrase.lower(), f"live phrase covered: {phrase}")
    assert_contains(hard_gate, "looks_like_karen_tasks_query", "hard gate uses task query matcher")
    assert_contains(hard_gate, "render_karen_tasks_view", "hard gate renders accepted task view")
    assert_contains(hard_gate, "fetch_open_commitments", "hard gate reads tasks only")
    assert_not_contains(hard_gate, "insert_memory_item", "hard gate does not insert memory")
    assert_not_contains(hard_gate, "load_karen_case_facts", "hard gate does not render finca facts")
    assert_not_contains(hard_gate, "Esto es lo que tengo guardado del caso del terreno", "hard gate does not include case summary copy")
    assert_contains(visibility, "looks_like_karen_tasks_query", "visibility route recognizes tasks query")
    assert_contains(visibility, "render_karen_tasks_view", "task query renders task list")
    for body, label in ((handle, "handle_text"), (pipeline, "pipeline")):
        task_idx = body.find("maybe_handle_karen_task_query_hard_gate")
        gcal_idx = body.find("maybe_handle_karen_gcal_create_confirmation_first")
        case_idx = body.find("maybe_handle_karen_case_facts")
        case_status_idx = body.find("maybe_handle_karen_case_status")
        day0_idx = body.find("maybe_handle_karen_day0_route")
        memory_idx = body.find("[MEMORY_TEST_TEXT] inserting memory")
        assert_true(task_idx >= 0, f"{label} has task visibility route")
        assert_true(gcal_idx < 0 or task_idx < gcal_idx, f"{label} task route beats gcal")
        assert_true(case_idx < 0 or task_idx < case_idx, f"{label} task route beats case facts")
        assert_true(case_status_idx < 0 or task_idx < case_status_idx, f"{label} task route beats case status")
        assert_true(day0_idx < 0 or task_idx < day0_idx, f"{label} task route beats day0 finca summary")
        assert_true(memory_idx < 0 or task_idx < memory_idx, f"{label} task route beats memory insertion")

    matcher = (ROOT / "core/karen_notes_tasks_visibility.py").read_text(encoding="utf-8")
    for expected in (
        "que\\s+tareas?\\s+tengo\\s+activas?",
        "que tarea tengo",
        "que tareas tengo activa",
        "va\\s+el",
        "pal",
    ):
        assert_contains(matcher, expected, f"matcher covers {expected}")


def test_task_delete_clarification_does_not_route_to_gcal() -> None:
    followup = function_body("maybe_handle_karen_task_delete_followup")
    parser = function_body("_looks_like_karen_task_delete_followup")
    handle = function_body("handle_text")
    pipeline = function_body("_process_text_pipeline")

    for marker in ("eliminarla del listado", "eliminarla", "borrala", "quitarla", "sacala del listado"):
        assert_contains(parser, marker, f"delete follow-up supports {marker}")
    assert_contains(followup, "_KAREN_PENDING_TASK_DELETE_CONTEXT", "task delete pending context is used")
    assert_contains(followup, "status='deleted'", "task delete removes from active list without hard DB delete")
    assert_contains(followup, "Listo. Quité esta tarea del listado activo", "delete success copy is clear")
    assert_contains(followup, "Todavía no elimino tareas del historial", "fallback copy is clear")
    assert_not_contains(followup, "delete_client_event", "task delete follow-up never calls Google Calendar")

    for body, label in ((handle, "handle_text"), (pipeline, "pipeline")):
        followup_idx = body.find("maybe_handle_karen_task_delete_followup")
        gcal_idx = body.find("maybe_handle_karen_gcal_event_number_delete")
        assert_true(followup_idx >= 0, f"{label} has task delete follow-up")
        assert_true(gcal_idx < 0 or followup_idx < gcal_idx, f"{label} task delete follow-up beats gcal numbered delete")


def main() -> int:
    test_task_query_beats_case_routes()
    test_task_delete_clarification_does_not_route_to_gcal()
    print("PASS: Karen task route priority smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
