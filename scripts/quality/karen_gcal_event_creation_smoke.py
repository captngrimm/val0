#!/usr/bin/env python3
from __future__ import annotations

import sys
import subprocess
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


def _source_contains_order(source: str, first: str, second: str) -> bool:
    first_idx = source.find(first)
    second_idx = source.find(second)
    return first_idx >= 0 and second_idx >= 0 and first_idx < second_idx


def test_natural_calendar_phrases_route_to_gcal_creation() -> None:
    source = _bot_source()
    intent_helper = _function_body(source, "_looks_like_karen_gcal_event_create_request")
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

    assert_contains(source, "create_pending_action", "uses pending confirmation framework")
    assert_contains(source, "GCAL_CREATE_ACTION_TYPE", "creates gcal pending action")
    assert_contains(handler, "_store_gcal_create_confirmation_pending", "handler stores gcal pending through helper")
    assert_contains(handler, "weekday_names", "weekday date parser present")
    assert_contains(handler, "America/Panama", "uses Panama timezone")
    assert_contains(intent_helper, 'norm.startswith("agenda ") and has_date and has_time', "agenda date/time create intent supported")
    assert_contains(handler, "agenda para", "voice/natural agenda para phrase supported")


def test_voice_title_cleanup_for_gcal_create() -> None:
    source = _bot_source()
    normalizer = _function_body(source, "_norm_gcal_confirm_text")
    cleanup = _function_body(source, "_cleanup_karen_gcal_event_title")
    handler = _function_body(source, "try_appointment_save_natural")

    for token in ("bal", "pal", "va\\s+el"):
        assert_contains(normalizer, token, f"voice assistant prefix normalized: {token}")
    assert_contains(cleanup, "de\\s+la", "cleanup removes dangling de la")
    assert_contains(cleanup, "llamar", "cleanup only strips filler before meaningful verbs")
    assert_contains(handler, "_cleanup_karen_gcal_event_title", "create handler applies title cleanup")
    assert_contains(handler, "Cita: ", "valid cleaned title still becomes calendar event title")


def test_gcal_creation_priority_beats_draft_followup() -> None:
    source = _bot_source()
    handle_text = _function_body(source, "handle_text")
    pipeline = _function_body(source, "_process_text_pipeline")
    helper = _function_body(source, "_looks_like_karen_gcal_event_create_request")

    assert_contains(helper, "agenda ", "agenda prueba calendario can be classified")
    assert_contains(handle_text, "[GCAL_CREATE_ROUTE] matched live text", "live route logging present")
    assert_contains(pipeline, "[GCAL_CREATE_ROUTE] matched live text", "pipeline route logging present")
    assert_contains(handle_text, "if _looks_like_karen_gcal_event_create_request(text)", "live handler uses actual intent helper")
    assert_contains(handle_text, "KAREN_GCAL_CREATE_EARLY_HANDLE_TEXT", "early handle_text gcal create gate")
    assert_contains(pipeline, "KAREN_GCAL_CREATE_EARLY_PIPELINE", "early pipeline gcal create gate")

    live_gate_idx = handle_text.find("[GCAL_CREATE_ROUTE] matched live text")
    shadow_idx = handle_text.find("_log_conversation_router_shadow")
    assert_true(live_gate_idx >= 0 and shadow_idx >= 0 and live_gate_idx < shadow_idx, "live gcal gate beats router shadow")

    pipeline_early_idx = source.find("KAREN_GCAL_CREATE_EARLY_PIPELINE")
    draft_idx = source.find("operator_route == \"draft_followup\"")
    assert_true(pipeline_early_idx >= 0 and draft_idx >= 0 and pipeline_early_idx < draft_idx, "pipeline gcal create beats draft follow-up")

    handle_early_idx = handle_text.find("KAREN_GCAL_CREATE_EARLY_HANDLE_TEXT")
    pipeline_call_idx = handle_text.find("_process_text_pipeline")
    assert_true(handle_early_idx >= 0 and pipeline_call_idx >= 0 and handle_early_idx < pipeline_call_idx, "handle_text gcal create beats pipeline fallback")

    assert_not_contains(handle_text.split("KAREN_GCAL_CREATE_EARLY_PIPELINE", 1)[0], "Draft follow-up", "no draft copy before gcal create gate")
    handler = _function_body(source, "try_appointment_save_natural")
    prompt_helper = _function_body(source, "_render_gcal_create_confirmation_prompt")
    assert_contains(prompt_helper, "Google Calendar se encargará de sus notificaciones", "create route notification copy")

    assert_true(_source_contains_order(source, "_looks_like_karen_gcal_event_create_request", "operator_route == \"draft_followup\""), "intent helper appears before draft router")


def test_gcal_confirmation_priority_beats_stale_pending_actions() -> None:
    source = _bot_source()
    handle_text = _function_body(source, "handle_text")
    pipeline = _function_body(source, "_process_text_pipeline")
    pending_confirm = _function_body(source, "maybe_handle_pending_gcal_appointment_confirmation")
    early_confirm = _function_body(source, "maybe_handle_karen_gcal_create_confirmation_first")
    any_state = _function_body(source, "_get_gcal_pending_action_any_state")

    assert_contains(any_state, "GCAL_CREATE_ACTION_TYPE", "early confirmation lookup is scoped to gcal create")
    assert_contains(early_confirm, "[GCAL_CONFIRM_ROUTE] matched pending gcal_create_event reply", "early confirmation route logging present")
    assert_contains(handle_text, "maybe_handle_karen_gcal_create_confirmation_first", "handle_text checks gcal confirmation first")
    assert_contains(pipeline, "maybe_handle_karen_gcal_create_confirmation_first", "pipeline checks gcal confirmation first")
    assert_true(
        handle_text.find("maybe_handle_karen_gcal_create_confirmation_first") < handle_text.find("_looks_like_karen_gcal_event_create_request"),
        "handle_text confirmation beats create/draft routes",
    )
    assert_true(
        pipeline.find("maybe_handle_karen_gcal_create_confirmation_first") < pipeline.find("_looks_like_karen_gcal_event_create_request"),
        "pipeline confirmation beats create/draft routes",
    )

    assert_contains(pending_confirm, "Esa confirmación ya venció", "expired pending has explicit copy")
    assert_contains(pending_confirm, "Listo, no creé el evento en Google Calendar", "cancel copy is scoped to gcal")
    assert_contains(pending_confirm, "No pude crear el evento en Google Calendar por un problema de autorización/conexión", "failure copy is scoped")
    assert_not_contains(pending_confirm, "Tany", "gcal confirmation does not leak stale user name")
    assert_not_contains(pending_confirm, "jardinero", "gcal confirmation does not leak stale event title")
    assert_not_contains(pending_confirm, "Draft follow-up", "gcal confirmation does not draft-followup")
    assert_not_contains(pending_confirm, "/journal", "gcal confirmation does not suggest journal")


def test_gcal_pending_action_classifier_is_isolated() -> None:
    from core.pending_actions import (
        ConfirmationDecision,
        PendingAction,
        classify_confirmation_reply,
        clear_pending_action,
        create_pending_action,
        get_pending_action,
    )

    chat_id = 707070
    client_id = "ka" + "ren"
    now = datetime.now(timezone.utc)
    stale = create_pending_action(
        PendingAction(
            action_id="smoke:stale-reminder",
            chat_id=chat_id,
            client_id=client_id,
            action_type="reminder_create",
            display_summary="Tany, confirmado: escribirle al jardinero mañana a las 9 am",
            confirm_words=("sí", "si confirma"),
            cancel_words=("no",),
            expires_at=now + timedelta(minutes=10),
            payload={"title": "escribirle al jardinero"},
        )
    )
    gcal = create_pending_action(
        PendingAction(
            action_id="smoke:gcal-create",
            chat_id=chat_id,
            client_id=client_id,
            action_type="gcal_create_event",
            display_summary="sábado 30 de mayo · 10:00 AM · Cita: prueba calendario",
            confirm_words=("sí", "si confirma", "sí confirma", "confirma", "dale", "correcto"),
            cancel_words=("no", "cancelar", "déjalo", "dejalo"),
            expires_at=now + timedelta(minutes=10),
            payload={"title": "Cita: prueba calendario"},
        )
    )
    try:
        selected = get_pending_action(chat_id, action_type="gcal_create_event", client_id=client_id, now=now)
        assert_true(selected is not None, "gcal pending action selected")
        assert_true(selected.action_id == gcal.action_id, "stale generic pending cannot override gcal pending")
        assert_true(classify_confirmation_reply("Sí, confirma", selected, now=now) == ConfirmationDecision.CONFIRM, "sí confirma confirms gcal")
        assert_true(classify_confirmation_reply("correcto", selected, now=now) == ConfirmationDecision.CONFIRM, "correcto confirms gcal")
        assert_true(classify_confirmation_reply("déjalo", selected, now=now) == ConfirmationDecision.CANCEL, "déjalo cancels gcal")

        expired = PendingAction(
            action_id="smoke:gcal-expired",
            chat_id=chat_id,
            client_id=client_id,
            action_type="gcal_create_event",
            display_summary="expired gcal",
            confirm_words=("sí",),
            cancel_words=("no",),
            expires_at=now - timedelta(seconds=1),
        )
        assert_true(classify_confirmation_reply("sí", expired, now=now) == ConfirmationDecision.EXPIRED, "expired gcal pending is detected")
        assert_not_contains(stale.display_summary, "prueba calendario", "fixture separates stale action from gcal action")
    finally:
        clear_pending_action(stale.action_id)
        clear_pending_action(gcal.action_id)


def test_missing_fields_are_asked_before_creation() -> None:
    handler = _function_body(_bot_source(), "try_appointment_save_natural")
    assert_contains(handler, "¿Para qué fecha lo agendo?", "missing date asks date")
    assert_contains(handler, "¿A qué hora lo agendo?", "missing time asks time")
    assert_contains(handler, "¿Qué título le pongo al evento?", "missing title asks title")
    assert_contains(handler, "_store_gcal_create_missing_time_pending", "missing time stores calendar draft for follow-up")


def test_missing_time_followup_runtime_bridge() -> None:
    code = r'''
import asyncio
import bot
from core.pending_actions import clear_pending_action

def check(value, label):
    if not value:
        raise AssertionError(label)

class FakeMessage:
    def __init__(self):
        self.replies = []
    async def reply_text(self, text):
        self.replies.append(text)

class FakeUpdate:
    def __init__(self):
        self.message = FakeMessage()

async def run_case():
    chat_id = bot.KAREN_CHAT_ID
    client_id = bot.resolve_client_id(chat_id)
    existing = bot._get_gcal_pending_action_any_state(chat_id, client_id)
    if existing:
        clear_pending_action(existing.action_id)

    first = FakeUpdate()
    handled = await bot.try_appointment_save_natural(first, chat_id, "Val, agenda para mañana cita con la bróker y mi mamá")
    check(handled, "missing-time calendar create handled")
    check(first.message.replies and "¿A qué hora lo agendo?" in first.message.replies[-1], "missing-time asks for hour")

    partial = bot._get_gcal_pending_action_any_state(chat_id, client_id)
    check(partial is not None, "partial gcal pending stored")
    check("time" in (partial.payload.get("missing_fields") or []), "partial pending marks missing time")
    check("start_iso" not in partial.payload, "partial pending does not pretend complete event")

    second = FakeUpdate()
    followup_handled = await bot.maybe_handle_pending_gcal_create_followup(second, chat_id, "a la 1:30 PM")
    check(followup_handled, "time follow-up handled")
    reply = second.message.replies[-1] if second.message.replies else ""
    check("¿Confirmas que la cree en Google Calendar?" in reply, "follow-up shows confirmation preview")
    check("1:30 PM" in reply, "follow-up confirmation includes parsed time")
    check("Cita con la broker y mi mama" in reply, "follow-up confirmation keeps title")

    complete = bot._get_gcal_pending_action_any_state(chat_id, client_id)
    try:
        check(complete is not None, "complete gcal pending stored")
        check("missing_fields" not in complete.payload, "complete pending no longer missing time")
        check("T13:30:00" in (complete.payload.get("start_iso") or ""), "complete pending stores parsed time")
        check(bool(complete.confirm_words), "complete pending requires explicit confirmation before write")
    finally:
        if complete:
            clear_pending_action(complete.action_id)

asyncio.run(run_case())
print("PASS runtime bridge")
'''
    result = subprocess.run(
        ["./scripts/val0py", "-c", code],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"runtime bridge subprocess failed: stdout={result.stdout!r} stderr={result.stderr!r}")
    assert_contains(result.stdout, "PASS runtime bridge", "runtime bridge subprocess passed")


def test_missing_date_followup_runtime_bridge() -> None:
    code = r'''
import asyncio
import bot
from core.pending_actions import clear_pending_action

def check(value, label):
    if not value:
        raise AssertionError(label)

class FakeMessage:
    def __init__(self):
        self.replies = []
    async def reply_text(self, text):
        self.replies.append(text)

class FakeUpdate:
    def __init__(self):
        self.message = FakeMessage()

async def run_case():
    chat_id = bot.KAREN_CHAT_ID
    client_id = bot.resolve_client_id(chat_id)
    existing = bot._get_gcal_pending_action_any_state(chat_id, client_id)
    if existing:
        clear_pending_action(existing.action_id)

    first = FakeUpdate()
    handled = await bot.try_appointment_save_natural(first, chat_id, "Val, agenda cita con la bróker y mi mamá a la 1:30 PM")
    check(handled, "missing-date calendar create handled")
    check(first.message.replies and "¿Para qué fecha lo agendo?" in first.message.replies[-1], "missing-date asks for date")

    partial = bot._get_gcal_pending_action_any_state(chat_id, client_id)
    check(partial is not None, "partial gcal pending stored")
    check("date" in (partial.payload.get("missing_fields") or []), "partial pending marks missing date")
    check("start_iso" not in partial.payload, "partial pending does not pretend complete event")
    check(partial.payload.get("time_hour") == 13 and partial.payload.get("time_minute") == 30, "partial pending stores parsed time")

    second = FakeUpdate()
    followup_handled = await bot.maybe_handle_pending_gcal_create_followup(second, chat_id, "mañana")
    check(followup_handled, "date follow-up handled")
    reply = second.message.replies[-1] if second.message.replies else ""
    check("¿Confirmas que la cree en Google Calendar?" in reply, "follow-up shows confirmation preview")
    check("1:30 PM" in reply, "follow-up confirmation includes retained time")
    check("Cita con la broker y mi mama" in reply, "follow-up confirmation keeps title")

    complete = bot._get_gcal_pending_action_any_state(chat_id, client_id)
    try:
        check(complete is not None, "complete gcal pending stored")
        check("missing_fields" not in complete.payload, "complete pending no longer missing date")
        check("T13:30:00" in (complete.payload.get("start_iso") or ""), "complete pending stores retained time")
        check(bool(complete.confirm_words), "complete pending requires explicit confirmation before write")
    finally:
        if complete:
            clear_pending_action(complete.action_id)

asyncio.run(run_case())
print("PASS missing-date runtime bridge")
'''
    result = subprocess.run(
        ["./scripts/val0py", "-c", code],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"missing-date runtime bridge subprocess failed: stdout={result.stdout!r} stderr={result.stderr!r}")
    assert_contains(result.stdout, "PASS missing-date runtime bridge", "missing-date runtime bridge subprocess passed")


def test_pending_expiration_datetime_collision_regression() -> None:
    helper = _function_body(_bot_source(), "_gcal_pending_expires_at")
    assert_not_contains(helper, "datetime.datetime.now", "pending expiration avoids datetime.datetime collision")
    assert_contains(helper, "import datetime as dt", "pending expiration uses local datetime module alias")
    namespace = {
        "timezone": timezone,
        "GCAL_PENDING_TTL": timedelta(days=365),
    }
    exec(helper, namespace)
    expires_at = namespace["_gcal_pending_expires_at"]()
    assert_true(hasattr(expires_at, "tzinfo") and expires_at.tzinfo is not None, "pending expiration returns aware datetime")


def test_no_val_reminder_created_for_gcal_event() -> None:
    handler = _function_body(_bot_source(), "try_appointment_save_natural")
    pending_confirm = _function_body(_bot_source(), "maybe_handle_pending_gcal_appointment_confirmation")
    assert_not_contains(handler, "insert_reminder", "gcal event route does not create Val reminder")
    assert_not_contains(handler, "upsert_commitment", "gcal event route does not create task")
    assert_not_contains(pending_confirm, "insert_reminder", "confirmation does not create Val reminder")


def test_success_and_failure_copy_are_honest() -> None:
    pending_confirm = _function_body(_bot_source(), "maybe_handle_pending_gcal_appointment_confirmation")
    prompt_helper = _function_body(_bot_source(), "_render_gcal_create_confirmation_prompt")
    assert_contains(pending_confirm, "Agregué al Google Calendar", "success copy says gcal event added")
    assert_contains(pending_confirm, "Google Calendar se encargará de sus notificaciones", "success mentions gcal notifications")
    assert_contains(prompt_helper, "Google Calendar se encargará de sus notificaciones", "confirmation preview mentions notifications")
    assert_contains(pending_confirm, "No lo marqué como creado", "failure does not fake success")
    assert_contains(pending_confirm, "clear_pending_action(action.action_id)", "terminal confirmation paths clear gcal pending")
    assert_contains(pending_confirm, "create_client_event", "uses real client-scoped gcal writer")


def test_document_and_reminder_routes_remain_present() -> None:
    source = _bot_source()
    assert_contains(source, "maybe_handle_document_summary_query", "document summary route still present")
    assert_contains(source, "maybe_handle_document_query", "document inventory route still present")
    assert_contains(source, "maybe_handle_karen_reminder_management", "reminder management route still present")


def main() -> int:
    test_natural_calendar_phrases_route_to_gcal_creation()
    test_voice_title_cleanup_for_gcal_create()
    test_gcal_creation_priority_beats_draft_followup()
    test_gcal_confirmation_priority_beats_stale_pending_actions()
    test_gcal_pending_action_classifier_is_isolated()
    test_missing_fields_are_asked_before_creation()
    test_missing_time_followup_runtime_bridge()
    test_missing_date_followup_runtime_bridge()
    test_pending_expiration_datetime_collision_regression()
    test_no_val_reminder_created_for_gcal_event()
    test_success_and_failure_copy_are_honest()
    test_document_and_reminder_routes_remain_present()
    print("PASS: Karen Google Calendar event creation smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
