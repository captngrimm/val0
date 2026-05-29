#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


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


def test_missing_articles_are_supported() -> None:
    source = _bot_source()
    reminder_parser = _function_body(source, "_parse_karen_reminder_management")
    task_completion = _function_body(source, "maybe_handle_karen_task_completion")
    task_delete = _function_body(source, "_parse_karen_task_delete_request")

    assert_contains(reminder_parser, r"(?:el\s+)?recordatorio", "reminder delete/edit accepts missing article")
    assert_contains(reminder_parser, "recordatorio_number_clarify", "bare recordatorio number is handled before other routes")
    assert_contains(task_completion, "marca tarea", "task completion accepts missing article")
    assert_contains(task_delete, r"(?:la\s+)?tarea", "task delete accepts missing article")


def test_numbered_actions_beat_calendar_and_stale_flows() -> None:
    source = _bot_source()
    handle_text = _function_body(source, "handle_text")
    priority_idx = source.find("KAREN_NUMBERED_ACTION_PRIORITY_GATE")
    gcal_idx = source.find("KAREN_GCAL_DELETE_PRIORITY_GATE")
    pending_next_idx = source.find("KAREN_PENDING_NEXT_ACTION_GATE")
    assert_true(priority_idx >= 0 and gcal_idx >= 0 and priority_idx < gcal_idx, "numbered action gate runs before gcal delete")
    assert_true(priority_idx >= 0 and pending_next_idx >= 0 and priority_idx < pending_next_idx, "numbered action gate runs before pending next action")
    reminder_idx = handle_text.find("maybe_handle_karen_reminder_management")
    intercept_idx = handle_text.find("handle_reminder_action_intercept")
    assert_true(reminder_idx >= 0 and intercept_idx >= 0 and reminder_idx < intercept_idx, "Karen reminder numbers beat generic reminder intercept")


def test_action_copy_uses_visible_numbers_only() -> None:
    tomorrow = _function_body(_bot_source(), "build_unified_tomorrow_dashboard")
    assert_contains(tomorrow, "if reminders:", "reminder actions require visible reminders")
    assert_contains(tomorrow, "edit_number = 2 if len(reminders) >= 2 else 1", "edit hint stays within visible reminder count")
    assert_contains(tomorrow, "cambia el recordatorio {edit_number}", "edit hint uses calculated visible number")
    assert_not_contains(tomorrow, '"- cambia el recordatorio 2 para las 11"', "no hardcoded recordatorio 2")


def test_no_fake_edit_success_and_context_cleared() -> None:
    handler = _function_body(_bot_source(), "maybe_handle_karen_reminder_management")
    assert_contains(handler, "Todavía no puedo editarlo directamente", "edit fallback is honest")
    assert_contains(handler, "eliminarlo y crear uno nuevo", "edit fallback offers safe alternative")
    assert_not_contains(handler, "se ajustó", "no fake adjusted copy")
    assert_not_contains(handler, "ya está cambiado", "no fake changed copy")
    assert_contains(handler, "_clear_karen_numbered_action_context", "numbered action clears stale context")
    assert_contains(handler, "_is_karen_numbered_action_dirty", "repeat numbered action checks changed list when dirty")
    assert_contains(handler, "_render_karen_reminder_updated_list", "delete refreshes visible reminder list")
    assert_contains(handler, "Listo. Eliminé", "delete confirmation remains present")


def test_ambiguous_delete_asks_clarification() -> None:
    parser = _function_body(_bot_source(), "_parse_karen_reminder_management")
    handler = _function_body(_bot_source(), "maybe_handle_karen_reminder_management")
    assert_contains(parser, "context_delete", "context numeric delete is recognized")
    assert_contains(handler, "¿Quieres eliminar el recordatorio", "ambiguous delete asks recordatorio vs tarea")


def test_document_routes_remain_present() -> None:
    source = _bot_source()
    assert_contains(source, "maybe_handle_document_summary_query", "document summary route still present")
    assert_contains(source, "maybe_handle_document_query", "document inventory route still present")


def main() -> int:
    test_missing_articles_are_supported()
    test_numbered_actions_beat_calendar_and_stale_flows()
    test_action_copy_uses_visible_numbers_only()
    test_no_fake_edit_success_and_context_cleared()
    test_ambiguous_delete_asks_clarification()
    test_document_routes_remain_present()
    print("PASS: Karen numbered action context safety smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
