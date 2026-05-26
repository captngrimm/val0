#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.karen_notes_tasks_visibility import (  # noqa: E402
    auxiliary_task_items_from_lines,
    is_auxiliary_task_row,
    merge_karen_task_items,
    parse_karen_task_schedule_for_tomorrow,
    render_karen_tasks_view,
    select_karen_task_for_schedule,
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


def test_schedule_phrases_parse() -> None:
    numbered = (
        "Val, pon la tarea 1 para mañana",
        "pon la tarea 1 para mañana",
        "registra la tarea 1 para mañana",
        "agenda la tarea 1 para mañana",
        "programa la tarea 1 para mañana",
    )
    for phrase in numbered:
        parsed = parse_karen_task_schedule_for_tomorrow(phrase)
        assert_true(parsed is not None, f"schedule phrase recognized: {phrase}")
        assert_true(parsed["number"] == 1, f"schedule phrase number extracted: {phrase}")

    current = parse_karen_task_schedule_for_tomorrow("pon esta tarea para mañana")
    assert_true(current is not None and current["current"], "current task phrase recognized")

    target = parse_karen_task_schedule_for_tomorrow("pon la tarea de topógrafo para mañana")
    assert_true(target is not None, "target task phrase recognized")
    assert_contains(target["target"], "topografo", "target keeps topographer term")

    raw = parse_karen_task_schedule_for_tomorrow("pon pedir al topógrafo cotización para mañana")
    assert_true(raw is not None, "raw task text phrase recognized")
    assert_contains(raw["target"], "pedir al topografo cotizacion", "raw target extracted")


def test_read_only_pending_item_can_be_selected_for_conversion() -> None:
    auxiliary = auxiliary_task_items_from_lines(["- pedir al topógrafo cotización"])
    rows = merge_karen_task_items([], auxiliary)
    request = parse_karen_task_schedule_for_tomorrow("Val, pon la tarea 1 para mañana")
    selected, status = select_karen_task_for_schedule(rows, request or {})
    assert_true(status == "ok", "numbered read-only task selected")
    assert_true(is_auxiliary_task_row(selected), "selected row is read-only pending item")

    target_request = parse_karen_task_schedule_for_tomorrow("pon la tarea de topógrafo para mañana")
    selected_by_target, target_status = select_karen_task_for_schedule(rows, target_request or {})
    assert_true(target_status == "ok", "target read-only task selected")
    assert_true(is_auxiliary_task_row(selected_by_target), "target selected row is read-only pending item")

    rendered = render_karen_tasks_view([], auxiliary_tasks=auxiliary)
    assert_contains(rendered, "pedir al topógrafo cotización", "task view includes pending item")
    assert_not_contains(rendered, "auxiliar", "task view hides internal source language")
    assert_not_contains(rendered, "CLIENT_GROCERY", "task view hides internal file")


def test_runtime_path_updates_or_converts_without_draft_or_calendar() -> None:
    source = _bot_source()
    schedule = _function_body(source, "maybe_handle_karen_task_schedule_for_tomorrow")
    assert_contains(schedule, "parse_karen_task_schedule_for_tomorrow", "runtime uses schedule parser")
    assert_contains(schedule, "select_karen_task_for_schedule", "runtime selects from visible task list")
    assert_contains(schedule, "UPDATE commitments", "normal commitment path updates due date")
    assert_contains(schedule, "upsert_commitment", "read-only pending item path converts to formal commitment")
    assert_contains(schedule, "Ya tengo esa tarea para mañana", "duplicate scheduling response exists")
    assert_contains(schedule, "Listo. Puse esta tarea para mañana", "successful scheduling response exists")
    assert_not_contains(schedule, "draftfollowup_cmd", "schedule path does not draft follow-up")
    assert_not_contains(schedule, "Google Calendar", "schedule path does not claim calendar change")
    assert_not_contains(schedule, "CLIENT_GROCERY", "schedule path does not expose internal file")
    assert_not_contains(schedule, "pendiente auxiliar", "schedule path does not expose internal label")

    for function_name in ("handle_text", "_process_text_pipeline"):
        body = _function_body(source, function_name)
        schedule_gate = body.find("maybe_handle_karen_task_schedule_for_tomorrow")
        draft_call = body.find("draftfollowup_cmd")
        day0_gate = body.find("maybe_handle_karen_day0_route")
        assert_true(schedule_gate >= 0, f"{function_name} has schedule gate")
        assert_true(day0_gate < 0 or schedule_gate < day0_gate, f"{function_name} schedules before Day0 route")
        if draft_call >= 0:
            assert_true(schedule_gate < draft_call, f"{function_name} schedules before draft follow-up")


def test_duplicate_merge_fixture_shows_once() -> None:
    auxiliary = auxiliary_task_items_from_lines(["- pedir al topógrafo cotización"])
    formal = [{
        "id": 7,
        "raw_input": "pedir al topógrafo cotización",
        "action": "pedir al topógrafo cotización",
        "target": "",
        "due_date": "2026-05-26",
        "status": "open",
    }]
    merged = merge_karen_task_items(formal, auxiliary)
    assert_true(len(merged) == 1, "formal task and pending item dedupe in visible list")


def main() -> int:
    test_schedule_phrases_parse()
    test_read_only_pending_item_can_be_selected_for_conversion()
    test_runtime_path_updates_or_converts_without_draft_or_calendar()
    test_duplicate_merge_fixture_shows_once()
    print("PASS: Karen schedule undated task smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
