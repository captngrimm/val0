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


def test_vencidos_delete_variants_are_parsed() -> None:
    parser = _function_body(_bot_source(), "_parse_karen_reminder_management")
    assert_contains(parser, "vencido|vencidos|pasado|pasados", "expired reminder words parsed")
    assert_contains(parser, "elimina|eliminar|borra|borrar|cancela|cancelar|quita|quitar", "delete verb variants parsed")
    assert_contains(parser, '"when": "past"', "expired delete targets past list")
    assert_contains(parser, "recordatorio\\s+(?:vencido|vencidos|pasado|pasados)", "recordatorio vencido number pattern")
    assert_contains(parser, "primer|primero", "word-number first supported")


def test_active_delete_variants_are_parsed() -> None:
    parser = _function_body(_bot_source(), "_parse_karen_reminder_management")
    assert_contains(parser, r"(?:el\s+)?recordatorio", "missing article supported")
    assert_contains(parser, '"when": "active"', "plain reminder delete targets active list")
    assert_contains(parser, "context_delete", "bare numeric delete can use last-list context")


def test_last_list_context_and_updated_list_response() -> None:
    source = _bot_source()
    list_view = _function_body(source, "_render_karen_reminder_list")
    updated = _function_body(source, "_render_karen_reminder_updated_list")
    handler = _function_body(source, "maybe_handle_karen_reminder_management")
    dashboard = _function_body(source, "build_unified_tomorrow_dashboard")

    assert_contains(source, "_KAREN_REMINDER_LIST_CONTEXT", "last reminder list context tracked")
    assert_contains(list_view, '"past" if when == "past" else "active"', "list view stores past/active context")
    assert_contains(dashboard, '"agenda"', "agenda marks mixed reminder/task context")
    assert_contains(handler, 'last_context == "past"', "generic delete can use past context")
    assert_contains(handler, 'last_context == "active"', "generic delete can use active context")
    assert_contains(handler, "¿Quieres eliminar el recordatorio", "ambiguous mixed context asks")
    assert_contains(handler, "_render_karen_reminder_updated_list", "delete returns updated list")
    assert_contains(updated, "Recordatorios actualizados", "active updated heading")
    assert_contains(updated, "Recordatorios vencidos actualizados", "expired updated heading")
    assert_contains(updated, "No tienes recordatorios vencidos", "expired empty state")
    assert_not_contains(handler, "Pide “Val, qué recordatorios tengo” antes de borrar otro", "valid delete no longer tells user to ask again")


def test_expired_copy_only_suggests_supported_command() -> None:
    list_view = _function_body(_bot_source(), "_render_karen_reminder_list")
    assert_contains(list_view, "elimina el recordatorio vencido 1", "expired list suggests supported command")
    assert_contains(list_view, "Conserva el historial", "expired list history caution")
    past_action_branch = list_view.split('if when == "past":', 2)[2].split("else:", 1)[0]
    assert_not_contains(past_action_branch, "cambia el recordatorio", "expired list does not suggest edit")


def test_google_calendar_and_document_routes_not_touched() -> None:
    source = _bot_source()
    handler = _function_body(source, "maybe_handle_karen_reminder_management")
    assert_not_contains(handler, "try_gcal", "reminder delete does not touch Google Calendar")
    assert_not_contains(handler, "Google Calendar", "reminder delete does not mention Google Calendar")
    assert_contains(source, "maybe_handle_document_summary_query", "document summary route still present")
    assert_contains(source, "maybe_handle_document_query", "document inventory route still present")


def main() -> int:
    test_vencidos_delete_variants_are_parsed()
    test_active_delete_variants_are_parsed()
    test_last_list_context_and_updated_list_response()
    test_expired_copy_only_suggests_supported_command()
    test_google_calendar_and_document_routes_not_touched()
    print("PASS: Karen reminder vencidos action variants smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
