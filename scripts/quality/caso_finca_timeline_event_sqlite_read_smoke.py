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
    render_sqlite_timeline_for_case,
    render_sqlite_timeline_events_for_user,
)


KAREN_CLIENT_ID = "kar" + "en"
OTHER_CLIENT_ID = "other-client"
OTHER_CASE_ID = "CASE:OTHER-001"
LIVE_GROCERY = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_GROCERY.md"
LIVE_FOLDERS = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_FOLDERS.json"
FORBIDDEN_USER_FACING = ("event:", "vfms:", "ID técnico", "source_ref", "source_type", "case_timeline_events")


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


def _assert_timeline_render_safe(rendered: str, *, label: str) -> None:
    assert_contains(rendered, "Línea de tiempo de Caso Finca", f"{label} title")
    assert_contains(rendered, "Fuente: SQLite fixture/test temporal", f"{label} fixture source")
    assert_contains(rendered, "Estado:", f"{label} status labels")
    assert_contains(rendered, "Fuente:", f"{label} source labels")
    assert_contains(rendered, "Efecto legal: desconocido", f"{label} legal effect unknown")
    assert_contains(rendered, "Nora/la abogada confirma efecto legal", f"{label} legal boundary")
    for phrase in FORBIDDEN_USER_FACING:
        assert_not_contains(rendered, phrase, f"{label} avoids forbidden user-facing copy {phrase}")


def test_sqlite_read_renderer_filters_sorts_and_hides_deleted() -> None:
    before_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    before_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None

    with tempfile.TemporaryDirectory(prefix="val0_case_timeline_sqlite_read_") as tmp:
        db_path = Path(tmp) / "case_timeline_events.sqlite3"
        store = CaseTimelineEventSqliteStore(db_path)
        exact = store.insert_from_draft(
            _draft("Val, anota en Caso Finca que el 12 de mayo de 2024 recibimos respuesta del juzgado"),
            client_id=KAREN_CLIENT_ID,
            now="2026-06-04T23:01:00+00:00",
        )
        year = store.insert_from_draft(
            _draft("Val, registra en Caso Finca que en 2021 se presentó una solicitud al Registro Público"),
            client_id=KAREN_CLIENT_ID,
            now="2026-06-04T23:02:00+00:00",
        )
        unknown = store.insert_from_draft(
            _draft("Val, agrega a la línea de tiempo que falta confirmar la fecha del oficio"),
            client_id=KAREN_CLIENT_ID,
            now="2026-06-04T23:03:00+00:00",
        )
        other = store.insert_from_draft(
            _draft("Val, registra en Caso Finca que en 2022 pasó algo de otro cliente"),
            client_id=OTHER_CLIENT_ID,
            case_id=OTHER_CASE_ID,
            now="2026-06-04T23:04:00+00:00",
        )

        deleted = store.soft_delete(
            exact.event_id,
            client_id=KAREN_CLIENT_ID,
            case_id=CASE_ID,
            actor="smoke",
            reason="SQLite read smoke delete filter",
            now="2026-06-04T23:05:00+00:00",
        )
        assert_true(deleted is not None, "soft-delete test fixture event")

        active_records = store.list_events_sorted(client_id=KAREN_CLIENT_ID, case_id=CASE_ID)
        assert_true(len(active_records) == 2, "deleted event excluded by default")
        assert_true(active_records[0].event_id == year.event_id, "year-known date first")
        assert_true(active_records[-1].event_id == unknown.event_id, "unknown date pending bucket last")

        rendered = render_sqlite_timeline_for_case(db_path, client_id=KAREN_CLIENT_ID, case_id=CASE_ID)
        _assert_timeline_render_safe(rendered, label="default render")
        assert_contains(rendered, "2021 (solo año)", "year-only rendered with precision")
        assert_contains(rendered, "Fecha pendiente", "unknown-date section rendered")
        assert_contains(rendered, "fecha pendiente", "unknown-date label rendered")
        assert_not_contains(rendered, exact.title, "deleted event hidden by default")
        assert_not_contains(rendered, other.title, "other client/case hidden")
        assert_true(rendered.find("2021 (solo año)") < rendered.find("Fecha pendiente"), "known dates render before unknown bucket")

        diagnostic_records = store.list_events_sorted(client_id=KAREN_CLIENT_ID, case_id=CASE_ID, include_deleted=True)
        diagnostic = render_sqlite_timeline_events_for_user(diagnostic_records, include_deleted=True)
        _assert_timeline_render_safe(diagnostic, label="include-deleted render")
        assert_contains(diagnostic, "Eliminados / ocultos", "deleted diagnostic section")
        assert_contains(diagnostic, exact.title, "deleted event visible in diagnostic mode")
        assert_not_contains(diagnostic, other.title, "other client still hidden in diagnostic mode")

        wrong_client = render_sqlite_timeline_for_case(db_path, client_id=OTHER_CLIENT_ID, case_id=CASE_ID)
        assert_contains(wrong_client, "Todavía no hay eventos", "wrong client/case no events")
        assert_not_contains(wrong_client, year.title, "wrong client/case does not leak Karen event")

    after_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    after_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None
    assert_true(before_grocery == after_grocery, "CLIENT_GROCERY.md untouched")
    assert_true(before_folders == after_folders, "CLIENT_FOLDERS.json untouched")


def main() -> None:
    test_sqlite_read_renderer_filters_sorts_and_hides_deleted()
    print("PASS caso_finca_timeline_event_sqlite_read_smoke")


if __name__ == "__main__":
    main()
