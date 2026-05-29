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


def test_natural_calendar_phrases_route_to_gcal_creation() -> None:
    source = _bot_source()
    handler = _function_body(source, "try_appointment_save_natural")
    handle_text = _function_body(source, "handle_text")

    for phrase in (
        "agenda cita",
        "crea evento",
        "google calendar",
        "pon en mi calendario",
        "agrega al calendario",
        "agregala al calendario",
    ):
        assert_contains(handler, phrase, f"handler recognizes {phrase}")
        assert_contains(handle_text, phrase, f"route recognizes {phrase}")

    assert_contains(handler, "create_pending_action", "uses pending confirmation framework")
    assert_contains(handler, "GCAL_CREATE_ACTION_TYPE", "creates gcal pending action")
    assert_contains(handler, "weekday_names", "weekday date parser present")
    assert_contains(handler, "America/Panama", "uses Panama timezone")


def test_missing_fields_are_asked_before_creation() -> None:
    handler = _function_body(_bot_source(), "try_appointment_save_natural")
    assert_contains(handler, "¿Para qué fecha lo agendo?", "missing date asks date")
    assert_contains(handler, "¿A qué hora lo agendo?", "missing time asks time")
    assert_contains(handler, "¿Qué título le pongo al evento?", "missing title asks title")


def test_no_val_reminder_created_for_gcal_event() -> None:
    handler = _function_body(_bot_source(), "try_appointment_save_natural")
    pending_confirm = _function_body(_bot_source(), "maybe_handle_pending_gcal_appointment_confirmation")
    assert_not_contains(handler, "insert_reminder", "gcal event route does not create Val reminder")
    assert_not_contains(handler, "upsert_commitment", "gcal event route does not create task")
    assert_not_contains(pending_confirm, "insert_reminder", "confirmation does not create Val reminder")


def test_success_and_failure_copy_are_honest() -> None:
    pending_confirm = _function_body(_bot_source(), "maybe_handle_pending_gcal_appointment_confirmation")
    handler = _function_body(_bot_source(), "try_appointment_save_natural")
    assert_contains(pending_confirm, "Agregué al Google Calendar", "success copy says gcal event added")
    assert_contains(pending_confirm, "Google Calendar se encargará de sus notificaciones", "success mentions gcal notifications")
    assert_contains(handler, "Google Calendar se encargará de sus notificaciones", "confirmation preview mentions notifications")
    assert_contains(pending_confirm, "No se creó ningún evento", "failure does not fake success")
    assert_contains(pending_confirm, "Puedo guardarlo como tarea o recordatorio de Val", "failure offers Val fallback")
    assert_contains(pending_confirm, "create_client_event", "uses real client-scoped gcal writer")


def test_document_and_reminder_routes_remain_present() -> None:
    source = _bot_source()
    assert_contains(source, "maybe_handle_document_summary_query", "document summary route still present")
    assert_contains(source, "maybe_handle_document_query", "document inventory route still present")
    assert_contains(source, "maybe_handle_karen_reminder_management", "reminder management route still present")


def main() -> int:
    test_natural_calendar_phrases_route_to_gcal_creation()
    test_missing_fields_are_asked_before_creation()
    test_no_val_reminder_created_for_gcal_event()
    test_success_and_failure_copy_are_honest()
    test_document_and_reminder_routes_remain_present()
    print("PASS: Karen Google Calendar event creation smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
