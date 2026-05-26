#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.karen_notes_tasks_visibility import parse_karen_task_schedule_for_tomorrow  # noqa: E402


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


def test_schedule_phrases_are_task_schedule_intent() -> None:
    for phrase in (
        "Val, pon la tarea 1 para mañana",
        "pon la tarea 1 para mañana",
        "registra la tarea 1 para mañana",
        "agenda la tarea 1 para mañana",
        "programa la tarea 1 para mañana",
        "pon la tarea de topógrafo para mañana",
        "pon pedir al topógrafo cotización para mañana",
    ):
        assert_true(parse_karen_task_schedule_for_tomorrow(phrase), f"schedule phrase recognized: {phrase}")


def test_schedule_priority_over_deadline_routes() -> None:
    source = _bot_source()
    for function_name in ("handle_text", "_process_text_pipeline"):
        body = _function_body(source, function_name)
        early_gate = body.find("KAREN_TASK_SCHEDULE_EARLY")
        schedule_call = body.find("maybe_handle_karen_task_schedule_for_tomorrow")
        due_call = body.find("try_due_tomorrow")
        assert_true(schedule_call >= 0, f"{function_name} has task schedule gate")
        assert_true(early_gate >= 0, f"{function_name} has early schedule priority gate")
        if due_call >= 0:
            assert_true(schedule_call < due_call, f"{function_name} schedules before due tomorrow")

    pipeline = _function_body(source, "_process_text_pipeline")
    assert_contains(pipeline, "schedule_tomorrow_intent", "pipeline records schedule intent before handler loop")
    assert_contains(pipeline, "try_due_tomorrow_natural", "pipeline still keeps natural deadline handler")
    assert_contains(pipeline, "try_due_tomorrow", "pipeline still keeps true deadline handler")
    assert_contains(pipeline, "continue", "pipeline can skip due handlers for schedule intent")


def test_deadline_gate_excludes_schedule_intent_but_keeps_true_deadline_queries() -> None:
    source = _bot_source()
    due_natural = _function_body(source, "try_due_tomorrow_natural")
    assert_contains(due_natural, "parse_karen_task_schedule_for_tomorrow", "due gate excludes task scheduling")
    assert_contains(due_natural, "que\\s+vence\\s+manana", "true due tomorrow query still recognized")
    assert_contains(due_natural, "que\\s+terminos\\s+vencen\\s+manana", "true terms due tomorrow query still recognized")

    schedule = _function_body(source, "maybe_handle_karen_task_schedule_for_tomorrow")
    assert_contains(schedule, "Listo. Puse esta tarea para mañana", "schedule success response exists")
    assert_contains(schedule, "Ya tengo esa tarea para mañana", "schedule duplicate response exists")
    assert_not_contains(schedule, "Mañana no tengo vencimientos registrados", "schedule path does not return deadline empty state")
    assert_not_contains(schedule, "Draft follow-up", "schedule path does not draft follow-up")
    assert_not_contains(schedule, "Documentos registrados", "schedule path does not route documents")
    assert_not_contains(schedule, "pendiente auxiliar", "schedule path does not expose internal task label")


def main() -> int:
    test_schedule_phrases_are_task_schedule_intent()
    test_schedule_priority_over_deadline_routes()
    test_deadline_gate_excludes_schedule_intent_but_keeps_true_deadline_queries()
    print("PASS: Karen task schedule priority smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
