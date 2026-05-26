#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.daily_operator import (  # noqa: E402
    build_daily_operator_snapshot_from_sources,
    render_daily_operator_compact,
)


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def test_reminder_time_consistency() -> None:
    client_id = "ka" + "ren"
    snapshot = build_daily_operator_snapshot_from_sources(
        client_id=client_id,
        case_id="KAREN-LAND-001",
        snapshot_date="2026-05-25",
        reminders=[
            {
                "id": "rem-9am",
                "text": "comprar la inyeccion",
                "due_at_utc": "2026-05-26 14:00:00",
                "status": "pending",
                "source": "reminder",
            }
        ],
        document_records=[
            {
                "id": "old-doc",
                "filename": "documento_de_prueba.pdf",
                "status": "requires OCR/revision",
                "created_at": "2026-05-20 10:00:00",
            }
        ],
    )

    reminder = snapshot.reminders[0]
    assert_true(str(reminder.due_at).startswith("2026-05-26T09:00:00"), "reminder localized to Panama 09:00")
    assert_true(snapshot.suggested_next_action == "Próximo pendiente: comprar la inyeccion", "next action prefers reminder")

    rendered = render_daily_operator_compact(snapshot)
    assert_contains(rendered, "9:00 AM", "compact shows 9am")
    assert_not_contains(rendered, "2:00 PM", "compact does not show UTC 2pm")
    assert_not_contains(rendered, "Documentos:", "document noise is not main compact item when reminder exists")

    topographer = build_daily_operator_snapshot_from_sources(
        client_id=client_id,
        case_id="KAREN-LAND-001",
        snapshot_date="2026-05-25",
        reminders=[
            {
                "id": "rem-8am",
                "text": "escribirle al topógrafo",
                "due_at_utc": "2026-05-26 13:00:00",
                "status": "pending",
                "source": "reminder",
            }
        ],
    )
    topographer_rendered = render_daily_operator_compact(topographer)
    assert_contains(topographer_rendered, "8:00 AM", "compact shows Panama 8am")
    assert_not_contains(topographer_rendered, "1:00 PM", "compact does not show UTC 1pm")


def _bot_source() -> str:
    return (REPO_ROOT / "bot.py").read_text(encoding="utf-8")


def _function_body(source: str, name: str) -> str:
    marker = f"async def {name}"
    start = source.find(marker)
    if start < 0:
        marker = f"def {name}"
        start = source.find(marker)
    if start < 0:
        raise AssertionError(f"missing function {name}")
    next_def = source.find("\ndef ", start + 1)
    next_async_def = source.find("\nasync def ", start + 1)
    stops = [pos for pos in (next_def, next_async_def) if pos > start]
    end = min(stops) if stops else len(source)
    return source[start:end]


def test_internal_agenda_wording() -> None:
    body = _function_body(_bot_source(), "build_client_agenda_dashboard")
    assert_contains(body, "📌 Recordatorios y tareas", "agenda uses clear reminder/task label")
    assert_not_contains(body, "📌 Agenda interna de Val", "agenda avoids confusing internal label")


def test_note_save_copy() -> None:
    source = _bot_source()
    body = _function_body(source, "maybe_handle_karen_explicit_case_note")
    assert_contains(body, "nota de finca/caso", "note copy labels note")
    assert_contains(body, "recuérdame", "note copy can suggest reminder")
    assert_contains(body, "guarda|guardar|anota|toma", "note handler matches save-note verbs")
    assert_contains(body, "nota\\s+de\\s+(?:finca|caso)", "note handler matches finca/case note")
    reply_start = body.find("📝 Guardé esta nota de finca/caso")
    reply_end = body.find("return True", reply_start)
    reply_block = body[reply_start:reply_end]
    assert_not_contains(reply_block, "cita", "note copy does not say cita")
    assert_not_contains(reply_block, "agenda", "note copy does not say agenda")

    handle_text_body = _function_body(source, "handle_text")
    note_gate = handle_text_body.find("maybe_handle_karen_explicit_case_note")
    day0_gate = handle_text_body.find("maybe_handle_karen_day0_route")
    appointment_gate = handle_text_body.find("maybe_handle_karen_appointment")
    assert_true(note_gate >= 0, "live handle_text has explicit note gate")
    assert_true(day0_gate < 0 or note_gate < day0_gate, "explicit note gate beats Day0 route")
    assert_true(appointment_gate < 0 or note_gate < appointment_gate, "explicit note gate beats appointment route")


def test_live_daily_operator_uses_utc_key() -> None:
    body = _function_body(_bot_source(), "_build_karen_daily_operator_reply")
    append_start = body.find("reminders.append")
    append_end = body.find("})", append_start)
    append_block = body[append_start:append_end]
    assert_contains(append_block, '"due_at_utc": due', "live Daily Operator passes UTC key for localization")
    assert_not_contains(append_block, '"due_at": due', "live Daily Operator does not bypass localization")


def main() -> int:
    test_reminder_time_consistency()
    test_internal_agenda_wording()
    test_note_save_copy()
    test_live_daily_operator_uses_utc_key()
    print("PASS: Karen agenda/note UX smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
