#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
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


def _source(path: str = "bot.py") -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


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


def test_agenda_labels_and_numbered_gcal_events() -> None:
    source = _source()
    gcal_section = _function_body(source, "_format_client_gcal_events_section")
    tomorrow = _function_body(source, "build_unified_tomorrow_dashboard")
    agenda = _function_body(source, "build_client_agenda_dashboard")

    assert_contains(gcal_section, "📅 Eventos de Google Calendar", "agenda uses event section name")
    assert_not_contains(gcal_section, "Google Calendar · solo lectura", "agenda does not call gcal read-only")
    assert_contains(gcal_section, 'lines.append(f"{idx}. {label} · {title}")', "gcal events are numbered")
    assert_contains(tomorrow, "⏰ Recordatorios de Val", "reminder section names Val")
    assert_contains(tomorrow, "📌 Tareas de Val", "task section names Val")
    assert_not_contains(agenda, "📌 Recordatorios y tareas", "agenda removes vague combined header")


def test_numbered_event_delete_confirmation_is_scoped() -> None:
    source = _source()
    parser = _function_body(source, "_parse_karen_gcal_event_number_delete")
    numbered_delete = _function_body(source, "maybe_handle_karen_gcal_event_number_delete")
    pending_delete = _function_body(source, "maybe_handle_pending_gcal_delete_confirmation")

    for phrase in ("elimina", "borra", "cancela", "evento", "google"):
        assert_contains(parser, phrase, f"parser supports {phrase}")
    assert_contains(numbered_delete, "GCAL_DELETE_ACTION_TYPE", "numbered delete creates gcal delete pending action")
    assert_contains(numbered_delete, "Voy a eliminar este evento de Google Calendar", "delete asks confirmation")
    assert_contains(numbered_delete, "create_pending_action", "delete does not happen immediately")
    assert_not_contains(numbered_delete.split("create_pending_action", 1)[0], "delete_client_event", "numbered delete does not delete before confirmation")
    assert_contains(pending_delete, "delete_client_event", "confirmation uses real gcal delete helper")
    assert_contains(pending_delete, "dry_run=False", "confirmation performs real helper delete only after confirmation")
    assert_contains(pending_delete, "Listo. Eliminé de Google Calendar", "success copy names gcal delete")
    assert_contains(pending_delete, "No pude eliminar el evento de Google Calendar. No cambié nada.", "failure copy does not fake success")
    assert_contains(pending_delete, "No toqué recordatorios ni tareas de Val", "gcal delete success preserves separation")
    assert_not_contains(pending_delete, "Eliminé el recordatorio", "gcal delete success does not claim reminder deletion")


def test_delete_pending_confirmation_is_isolated_and_cancel_safe() -> None:
    from core.pending_actions import (
        ConfirmationDecision,
        PendingAction,
        classify_confirmation_reply,
        clear_pending_action,
        create_pending_action,
        get_pending_action,
    )

    chat_id = 717171
    client_id = "ka" + "ren"
    now = datetime.now(timezone.utc)
    stale_create = create_pending_action(
        PendingAction(
            action_id="smoke:gcal-create-stale",
            chat_id=chat_id,
            client_id=client_id,
            action_type="gcal_create_event",
            display_summary="Cita: otro evento",
            confirm_words=("sí", "si confirma"),
            cancel_words=("no",),
            expires_at=now + timedelta(minutes=10),
            payload={"title": "otro evento"},
        )
    )
    delete = create_pending_action(
        PendingAction(
            action_id="smoke:gcal-delete",
            chat_id=chat_id,
            client_id=client_id,
            action_type="gcal_delete_event",
            display_summary="Sat 30/05 10:00 AM · Cita: prueba calendario",
            confirm_words=("sí", "si confirma", "sí confirma", "confirma", "dale"),
            cancel_words=("no", "cancelar", "déjalo", "dejalo"),
            expires_at=now + timedelta(minutes=10),
            payload={"summary": "Cita: prueba calendario", "event_id": "event-1"},
        )
    )
    try:
        selected = get_pending_action(chat_id, action_type="gcal_delete_event", client_id=client_id, now=now)
        assert_true(selected is not None and selected.action_id == delete.action_id, "delete pending selected by action type")
        assert_true(classify_confirmation_reply("sí confirma", selected, now=now) == ConfirmationDecision.CONFIRM, "delete accepts sí confirma")
        assert_true(classify_confirmation_reply("dale", selected, now=now) == ConfirmationDecision.CONFIRM, "delete accepts dale")
        assert_true(classify_confirmation_reply("déjalo", selected, now=now) == ConfirmationDecision.CANCEL, "delete cancel does not delete")
        assert_true(stale_create.action_id != selected.action_id, "create pending cannot override delete pending")
    finally:
        clear_pending_action(stale_create.action_id)
        clear_pending_action(delete.action_id)


def test_route_priority_and_ambiguity_copy() -> None:
    source = _source()
    handle_text = _function_body(source, "handle_text")
    priority_gate_idx = source.find("KAREN_NUMBERED_ACTION_PRIORITY_GATE")
    gcal_delete_idx = source.find("KAREN_GCAL_DELETE_PRIORITY_GATE")
    assert_true(priority_gate_idx >= 0 and gcal_delete_idx >= 0 and priority_gate_idx < gcal_delete_idx, "reminder/task numbered actions still beat generic gcal delete")
    assert_contains(handle_text, "maybe_handle_pending_gcal_delete_confirmation", "live path checks pending gcal delete confirmations")
    assert_contains(source, "maybe_handle_karen_gcal_event_number_delete", "numbered gcal event delete route present")
    assert_contains(source, "¿Quieres eliminar el evento", "ambiguous generic delete asks event/reminder/task clarification")
    assert_contains(source, "el recordatorio", "ambiguous copy keeps reminder option")
    assert_contains(source, "la tarea", "ambiguous copy keeps task option")
    assert_contains(source, "maybe_handle_karen_reminder_management", "reminder route remains present")
    assert_contains(source, "maybe_handle_karen_task_completion", "task completion route remains present")
    assert_contains(source, "try_appointment_save_natural", "gcal create route remains present")


def main() -> int:
    test_agenda_labels_and_numbered_gcal_events()
    test_numbered_event_delete_confirmation_is_scoped()
    test_delete_pending_confirmation_is_isolated_and_cancel_safe()
    test_route_priority_and_ambiguity_copy()
    print("PASS: Karen Google Calendar event delete smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
