#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.case_timeline_events import (  # noqa: E402
    CASE_ID,
    CaseTimelineEventSqliteStore,
    parse_case_timeline_event_draft,
    render_timeline_event_records_for_user,
    timeline_event_date_label,
)


KAREN_CLIENT_ID = "kar" + "en"
OTHER_CLIENT_ID = "other-client"
OTHER_CASE_ID = "CASE:OTHER-001"
LIVE_GROCERY = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_GROCERY.md"
LIVE_FOLDERS = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_FOLDERS.json"
FORBIDDEN_USER_FACING = ("event:", "vfms:", "ID técnico", "source_ref", "source_type")


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def _draft(text: str):
    draft = parse_case_timeline_event_draft(text)
    assert_true(draft is not None, f"draft parsed: {text}")
    return draft


def test_sqlite_schema_insert_read_sort_delete_and_audit() -> None:
    before_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    before_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None

    with tempfile.TemporaryDirectory(prefix="val0_case_timeline_sqlite_") as tmp:
        db_path = Path(tmp) / "case_timeline_events.sqlite3"
        store = CaseTimelineEventSqliteStore(db_path)
        store.initialize_schema()
        tables = store.schema_tables()
        assert_true("case_timeline_events" in tables, "primary table created")
        assert_true("case_timeline_event_audit" in tables, "audit table created")

        exact = store.insert_from_draft(
            _draft("Val, anota en Caso Finca que el 12 de mayo de 2024 recibimos respuesta del juzgado"),
            client_id=KAREN_CLIENT_ID,
            now="2026-06-04T22:50:00+00:00",
        )
        year = store.insert_from_draft(
            _draft("Val, registra en Caso Finca que en 2021 se presentó una solicitud al Registro Público"),
            client_id=KAREN_CLIENT_ID,
            now="2026-06-04T22:51:00+00:00",
        )
        unknown = store.insert_from_draft(
            _draft("Val, agrega a la línea de tiempo que falta confirmar la fecha del oficio"),
            client_id=KAREN_CLIENT_ID,
            now="2026-06-04T22:52:00+00:00",
        )
        other = store.insert_from_draft(
            _draft("Val, registra en Caso Finca que en 2022 pasó algo de otro cliente"),
            client_id=OTHER_CLIENT_ID,
            case_id=OTHER_CASE_ID,
            now="2026-06-04T22:53:00+00:00",
        )

        records = store.list_events(client_id=KAREN_CLIENT_ID, case_id=CASE_ID)
        assert_true(len(records) == 3, "Karen/Caso Finca reads only its three events")
        assert_true(exact.event_date == "2024-05-12", "exact date inserted")
        assert_true(exact.event_date_precision == "exact", "exact precision preserved")
        assert_true(year.event_date == "2021", "year-only date inserted")
        assert_true(year.event_date_precision == "year_only", "year-only precision preserved")
        assert_true(unknown.event_date_precision == "unknown", "unknown precision preserved")
        assert_true(timeline_event_date_label(unknown) == "fecha pendiente", "unknown date label")

        other_records = store.list_events(client_id=OTHER_CLIENT_ID, case_id=OTHER_CASE_ID)
        assert_true(len(other_records) == 1 and other_records[0].event_id == other.event_id, "other client/case reads only its event")
        assert_true(
            store.list_events(client_id=KAREN_CLIENT_ID, case_id=OTHER_CASE_ID) == [],
            "wrong case does not leak Karen records",
        )
        assert_true(
            store.list_events(client_id=OTHER_CLIENT_ID, case_id=CASE_ID) == [],
            "wrong client does not leak Caso Finca records",
        )

        sorted_records = store.list_events_sorted(client_id=KAREN_CLIENT_ID, case_id=CASE_ID)
        assert_true(sorted_records[0].event_date == "2021", "year event sorted by date before later exact date")
        assert_true(sorted_records[1].event_date == "2024-05-12", "exact event sorted after 2021")
        assert_true(sorted_records[-1].event_date_precision == "unknown", "unknown event sorted to pending bucket")

        rendered = render_timeline_event_records_for_user(sorted_records)
        assert_contains(rendered, "Línea de tiempo de Caso Finca", "renderer title")
        assert_contains(rendered, "Eventos con fecha", "known date section")
        assert_contains(rendered, "Fecha pendiente", "pending bucket")
        assert_contains(rendered, "Nora/la abogada confirma efecto legal", "legal boundary")
        for needle in FORBIDDEN_USER_FACING:
            assert_not_contains(rendered, needle, f"renderer hides internal {needle}")

        audit = store.audit_rows(event_id=exact.event_id)
        assert_true(len(audit) == 1, "insert creates audit row")
        assert_true(audit[0]["action"] == "created_from_draft", "insert audit action")
        assert_true(audit[0]["client_id"] == KAREN_CLIENT_ID, "audit client_id")
        assert_true(audit[0]["case_id"] == CASE_ID, "audit case_id")
        assert_contains(audit[0]["after_json"], "2024-05-12", "audit stores after_json")

        deleted = store.soft_delete(
            year.event_id,
            client_id=KAREN_CLIENT_ID,
            case_id=CASE_ID,
            actor="smoke",
            reason="SQLite store spike soft-delete test",
            now="2026-06-04T22:54:00+00:00",
        )
        assert_true(deleted is not None, "soft-delete returns record")
        assert_true(deleted.deleted_at == "2026-06-04T22:54:00+00:00", "soft-delete sets deleted_at")
        assert_true(len(store.list_events(client_id=KAREN_CLIENT_ID, case_id=CASE_ID)) == 2, "deleted excluded by default")
        assert_true(
            len(store.list_events(client_id=KAREN_CLIENT_ID, case_id=CASE_ID, include_deleted=True)) == 3,
            "deleted visible when requested",
        )
        delete_audit = store.audit_rows(event_id=year.event_id)
        assert_true(len(delete_audit) == 2, "soft-delete adds second audit row")
        assert_true(delete_audit[-1]["action"] == "soft_deleted", "soft-delete audit action")
        assert_contains(delete_audit[-1]["before_json"], year.event_id, "soft-delete audit before_json")
        assert_contains(delete_audit[-1]["after_json"], "deleted_at", "soft-delete audit after_json")

    after_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    after_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None
    assert_true(before_grocery == after_grocery, "CLIENT_GROCERY.md untouched")
    assert_true(before_folders == after_folders, "CLIENT_FOLDERS.json untouched")


def test_required_client_case_and_temp_path_guard() -> None:
    with tempfile.TemporaryDirectory(prefix="val0_case_timeline_sqlite_guard_") as tmp:
        store = CaseTimelineEventSqliteStore(Path(tmp) / "events.sqlite3")
        draft = _draft("Val, registra en Caso Finca que en 2021 pasó X")
        for kwargs, label in (
            ({"client_id": ""}, "missing client_id refused"),
            ({"client_id": KAREN_CLIENT_ID, "case_id": ""}, "missing case_id refused"),
        ):
            try:
                store.insert_from_draft(draft, **kwargs)
            except ValueError:
                pass
            else:
                raise AssertionError(label)

    try:
        CaseTimelineEventSqliteStore(ROOT / "val0_memory.enc.db")
    except ValueError as exc:
        assert_contains(str(exc), "outside temp directory", "non-temp DB path refused")
    else:
        raise AssertionError("non-temp DB path was not refused")


def main() -> None:
    test_sqlite_schema_insert_read_sort_delete_and_audit()
    test_required_client_case_and_temp_path_guard()
    print("PASS caso_finca_timeline_event_sqlite_store_smoke")


if __name__ == "__main__":
    main()
