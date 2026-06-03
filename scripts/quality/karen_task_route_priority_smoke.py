#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
BOT = (ROOT / "bot.py").read_text(encoding="utf-8")

from core.intent_interpreter import interpret_user_intent  # noqa: E402
from core.intent_router_v2 import classify_intent_shadow  # noqa: E402
from core.karen_notes_tasks_visibility import looks_like_karen_tasks_query  # noqa: E402


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
        "Val, qué tareas activas tengo pendientes?",
        "Qué tareas activas tengo pendientes?",
        "Val, qué tareas pendientes tengo?",
    ):
        assert_true("tareas" in phrase.lower(), f"live phrase covered: {phrase}")
        assert_true(looks_like_karen_tasks_query(phrase), f"hard matcher catches task list: {phrase}")
        interpreted = interpret_user_intent(phrase, client_id="client-zero")
        assert_true(interpreted["intent"] == "task_list", f"interpreter task_list: {phrase}")
        assert_true(interpreted["confidence"] >= 0.90, f"interpreter high confidence: {phrase}")
        shadow = classify_intent_shadow(phrase, client_id="client-zero")
        assert_true(shadow.selected_intent == "task_query", f"shadow router task_query: {phrase}")
    assert_contains(hard_gate, "looks_like_karen_tasks_query", "hard gate uses task query matcher")
    assert_contains(hard_gate, "render_karen_tasks_view", "hard gate renders accepted task view")
    assert_contains(hard_gate, "fetch_open_commitments", "hard gate reads tasks only")
    assert_contains(hard_gate, "[KAREN_TASK_QUERY_HARD_GATE] handled=True", "hard gate logs terminal handling")
    assert_not_contains(hard_gate, "insert_memory_item", "hard gate does not insert memory")
    assert_not_contains(hard_gate, "load_karen_case_facts", "hard gate does not render finca facts")
    assert_not_contains(hard_gate, "Esto es lo que tengo guardado del caso del terreno", "hard gate does not include case summary copy")
    assert_contains(visibility, "looks_like_karen_tasks_query", "visibility route recognizes tasks query")
    assert_contains(visibility, "render_karen_tasks_view", "task query renders task list")
    for body, label in ((handle, "handle_text"), (pipeline, "pipeline")):
        task_idx = body.find("maybe_handle_karen_task_query_hard_gate")
        task_call_block = body[task_idx:task_idx + 360] if task_idx >= 0 else ""
        gcal_idx = body.find("maybe_handle_karen_gcal_create_confirmation_first")
        case_idx = body.find("maybe_handle_karen_case_facts")
        case_status_idx = body.find("maybe_handle_karen_case_status")
        day0_idx = body.find("maybe_handle_karen_day0_route")
        memory_idx = body.find("[MEMORY_TEST_TEXT] inserting memory")
        assert_true(task_idx >= 0, f"{label} has task visibility route")
        assert_contains(task_call_block, "return", f"{label} hard gate returns immediately")
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
        "que\\s+tareas?\\s+activas?\\s+tengo\\s+pendientes?",
        "que tareas activas tengo pendientes",
        "va\\s+el",
        "pal",
    ):
        assert_contains(matcher, expected, f"matcher covers {expected}")


def test_task_delete_clarification_does_not_route_to_gcal() -> None:
    followup = function_body("maybe_handle_karen_task_delete_followup")
    parser = function_body("_looks_like_karen_task_delete_followup")
    request_parser = function_body("_parse_karen_task_delete_request")
    request_handler = function_body("maybe_handle_karen_task_delete_request")
    completion = function_body("maybe_handle_karen_task_completion")
    handle = function_body("handle_text")
    pipeline = function_body("_process_text_pipeline")

    for marker in ("borra|borrar|elimina|eliminar|quita|quitar", "_karen_extract_number_after"):
        assert_contains(request_parser, marker, f"task delete request parser supports {marker}")
    for phrase in ("Val elimina la tarea 1", "Elimina la tarea 1", "borra la tarea 1", "quita la tarea 1"):
        shadow = classify_intent_shadow(phrase, client_id="client-zero")
        assert_true(shadow.selected_intent == "task_delete", f"shadow router task_delete: {phrase}")
    done_shadow = classify_intent_shadow("marca la tarea 1 como hecha", client_id="client-zero")
    assert_true(done_shadow.selected_intent == "task_complete", "mark-done stays task_complete")
    assert_contains(request_handler, "status='deleted'", "explicit task delete marks status deleted")
    assert_contains(request_handler, "Listo. Quité esta tarea del listado activo", "explicit task delete removes from active list")
    assert_not_contains(request_handler, "DELETE FROM commitments", "explicit task delete does not hard-delete DB rows")
    assert_contains(completion, "status='done'", "mark-done route still marks done")

    for marker in ("eliminarla del listado", "eliminarla", "borrala", "quitarla", "sacala del listado"):
        assert_contains(parser, marker, f"delete follow-up supports {marker}")
    assert_contains(followup, "_KAREN_PENDING_TASK_DELETE_CONTEXT", "task delete pending context is used")
    assert_contains(followup, "status='deleted'", "task delete removes from active list without hard DB delete")
    assert_contains(followup, "Listo. Quité esta tarea del listado activo", "delete success copy is clear")
    assert_contains(followup, "Todavía no elimino tareas del historial", "fallback copy is clear")
    assert_not_contains(followup, "delete_client_event", "task delete follow-up never calls Google Calendar")

    for body, label in ((handle, "handle_text"), (pipeline, "pipeline")):
        direct_delete_idx = body.find("maybe_handle_karen_task_delete_request")
        followup_idx = body.find("maybe_handle_karen_task_delete_followup")
        gcal_idx = body.find("maybe_handle_karen_gcal_event_number_delete")
        case_status_idx = body.find("maybe_handle_karen_case_status")
        assert_true(direct_delete_idx >= 0, f"{label} has direct task delete")
        assert_true(followup_idx >= 0, f"{label} has task delete follow-up")
        assert_true(gcal_idx < 0 or direct_delete_idx < gcal_idx, f"{label} direct task delete beats gcal numbered delete")
        assert_true(gcal_idx < 0 or followup_idx < gcal_idx, f"{label} task delete follow-up beats gcal numbered delete")
        assert_true(case_status_idx < 0 or direct_delete_idx < case_status_idx, f"{label} direct task delete beats case/finca")


def main() -> int:
    test_task_query_beats_case_routes()
    test_task_delete_clarification_does_not_route_to_gcal()
    print("PASS: Karen task route priority smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
