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


def test_monday_reminder_parser_covers_live_variants() -> None:
    parser = function_body("_parse_karen_natural_reminder_request")
    handler = function_body("maybe_handle_karen_natural_weekday_reminder")
    for token in ("recuerdame", "registrar un recordatorio", "proximo", "lunes", "junio"):
        assert_contains(parser, token, f"parser covers {token}")
    assert_contains(parser, "lo puedes hacer", "parser removes voice-style filler")
    assert_contains(parser, "a\\s+las?", "parser looks for natural hour")
    assert_contains(parser, "title = re.sub", "parser cleans title with regex substitution")
    assert_contains(parser, r"\ba\s+las?", "parser strips trailing natural time from title")
    assert_contains(handler, "insert_reminder", "clear reminder creates Val reminder")
    assert_contains(handler, "¿A qué hora lo pongo?", "date/title without hour asks hour")
    assert_contains(handler, "¿Qué quieres que te recuerde?", "date without title asks title")
    assert_contains(handler, "Guardé el recordatorio", "success copy creates Val reminder")
    assert_not_contains(handler, "upsert_commitment", "reminder handler does not create task")
    assert_not_contains(handler, "no manejo recordatorios directos", "does not deny direct reminders")
    assert_not_contains(handler, "Esa hora ya pasó hoy", "future Monday variants do not hit today-past copy")
    assert_not_contains(parser, "Esa hora ya pasó hoy", "parser does not use today-past copy")
    assert_not_contains(handler, "/rmd", "success/missing-field copy does not mention slash cancel")
    assert_not_contains(parser, "title[:time_match.start()]", "title cleanup does not use stale raw indexes")


def test_weekday_agenda_uses_current_dashboard_sections() -> None:
    parser = function_body("_parse_karen_weekday_agenda_target")
    dashboard = function_body("build_client_weekday_agenda_dashboard")
    internal = function_body("_build_val_agenda_for_date")
    handler = function_body("maybe_handle_karen_weekday_agenda_query")

    assert_contains(parser, "que tengo", "weekday agenda parser catches qué tengo")
    assert_contains(parser, "lunes", "weekday agenda parser catches Monday")
    assert_contains(dashboard, "📅 Agenda para", "weekday dashboard title")
    assert_contains(dashboard, "_format_client_gcal_events_section", "weekday dashboard includes Google Calendar events")
    assert_contains(internal, "⏰ Recordatorios de Val", "weekday dashboard uses Val reminders section")
    assert_contains(internal, "📌 Tareas de Val", "weekday dashboard uses Val tasks section")
    assert_contains(handler, "build_client_weekday_agenda_dashboard", "weekday query uses current dashboard")
    for body, label in ((dashboard, "dashboard"), (internal, "internal"), (handler, "handler")):
        assert_not_contains(body, "/rmd", f"{label} does not use legacy slash copy")
        assert_not_contains(body, "Tienes {len(rows)} recordatorio", f"{label} does not use old reminder list copy")


def test_route_order_beats_legacy_reminder_and_task_routes() -> None:
    handle = function_body("handle_text")
    pipeline = function_body("_process_text_pipeline")
    for body, label in ((handle, "handle_text"), (pipeline, "pipeline")):
        agenda_idx = body.find("maybe_handle_karen_weekday_agenda_query")
        reminder_idx = body.find("maybe_handle_karen_natural_weekday_reminder")
        task_idx = body.find("maybe_handle_karen_task_creation")
        old_reminders_idx = body.find("reminders_cmd")
        assert_true(agenda_idx >= 0, f"{label} has weekday agenda guard")
        assert_true(reminder_idx >= 0, f"{label} has natural weekday reminder guard")
        assert_true(task_idx < 0 or reminder_idx < task_idx, f"{label} reminder guard beats task creation")
        assert_true(old_reminders_idx < 0 or agenda_idx < old_reminders_idx, f"{label} weekday agenda beats old reminders command")
    assert_true(
        BOT.find("maybe_handle_karen_natural_weekday_reminder") < BOT.find("NATURAL REMINDER DETECTION"),
        "new reminder guard appears before legacy natural reminder detector",
    )


def main() -> int:
    test_monday_reminder_parser_covers_live_variants()
    test_weekday_agenda_uses_current_dashboard_sections()
    test_route_order_beats_legacy_reminder_and_task_routes()
    print("PASS: Karen natural Monday reminder/agenda smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
