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


def test_relative_reminders_do_not_ask_for_date() -> None:
    parser = function_body("_parse_karen_natural_reminder_request")
    relative = function_body("_parse_karen_relative_minutes")
    handler = function_body("maybe_handle_karen_natural_weekday_reminder")

    assert_contains(relative, "dentro\\s+de", "relative parser accepts dentro de")
    assert_contains(relative, "diez", "relative parser accepts word numbers")
    assert_contains(parser, "_parse_karen_relative_minutes", "natural reminder parser uses relative minutes")
    assert_contains(parser, "target_date = rel_date", "relative reminder sets date")
    assert_contains(parser, "time_parts = relative_minutes[1]", "relative reminder sets time")
    assert_contains(parser, "minutos?", "relative minute phrase removed from title")
    assert_contains(handler, "insert_reminder", "clear relative reminder creates Val reminder")
    assert_not_contains(handler, "upsert_commitment", "relative reminder does not create task")
    assert_not_contains(handler, "no manejo recordatorios directos", "does not deny direct reminders")


def test_pending_reminder_followups_are_early_and_scoped() -> None:
    pending = function_body("maybe_handle_karen_pending_reminder_context")
    reply_parser = function_body("_parse_karen_pending_reminder_reply")
    handle = function_body("handle_text")
    pipeline = function_body("_process_text_pipeline")

    for token in ("para hoy", "[0-3]?\\d", "mayo", "manana", "lunes", "a\\s+las?", "en|dentro"):
        assert_contains(reply_parser, token, f"pending reply recognizes {token}")
    assert_contains(pending, "_KAREN_PENDING_REMINDER_CONTEXT", "pending reminder context is used")
    assert_contains(pending, "insert_reminder", "complete pending reminder creates Val reminder")
    assert_contains(pending, "¿Para qué fecha lo pongo?", "still asks date when missing")
    assert_contains(pending, "¿A qué hora lo pongo?", "still asks time when missing")
    assert_contains(pending, "¿Qué quieres que te recuerde?", "still asks title when missing")

    for body, label in ((handle, "handle_text"), (pipeline, "pipeline")):
        pending_idx = body.find("maybe_handle_karen_pending_reminder_context")
        doc_idx = body.find("maybe_handle_document_summary_query")
        case_idx = body.find("maybe_handle_karen_case_facts")
        gcal_create_idx = body.find("_looks_like_karen_gcal_event_create_request")
        assert_true(pending_idx >= 0, f"{label} has pending reminder gate")
        assert_true(gcal_create_idx < 0 or pending_idx < gcal_create_idx, f"{label} pending reminder beats gcal create")
        assert_true(doc_idx < 0 or pending_idx < doc_idx, f"{label} pending reminder beats document routes")
        assert_true(case_idx < 0 or pending_idx < case_idx, f"{label} pending reminder beats case routes")


def main() -> int:
    test_relative_reminders_do_not_ask_for_date()
    test_pending_reminder_followups_are_early_and_scoped()
    print("PASS: Karen pending reminder context smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
