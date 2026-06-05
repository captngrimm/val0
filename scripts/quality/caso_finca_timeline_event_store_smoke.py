#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.case_timeline_events import (  # noqa: E402
    CaseTimelineEventJsonStore,
    parse_case_timeline_event_draft,
    render_timeline_event_records_for_user,
    timeline_event_date_label,
)


KAREN_CLIENT_ID = "kar" + "en"
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


def test_store_roundtrip_sorting_and_audit() -> None:
    before_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    before_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None

    with tempfile.TemporaryDirectory(prefix="val0_case_timeline_store_") as tmp:
        store_path = Path(tmp) / "caso_finca_events.json"
        store = CaseTimelineEventJsonStore(store_path)

        exact = store.append_from_draft(
            _draft("Val, anota en Caso Finca que el 12 de mayo de 2024 recibimos respuesta del juzgado"),
            now="2026-06-04T22:10:00+00:00",
        )
        year = store.append_from_draft(
            _draft("Val, registra en Caso Finca que en 2021 se presentó una solicitud al Registro Público"),
            now="2026-06-04T22:11:00+00:00",
        )
        unknown = store.append_from_draft(
            _draft("Val, agrega a la línea de tiempo que falta confirmar la fecha del oficio"),
            now="2026-06-04T22:12:00+00:00",
        )

        records = store.list_events()
        assert_true(len(records) == 3, "three records read back")
        assert_true(exact.event_date == "2024-05-12", "exact event stored")
        assert_true(exact.event_date_precision == "exact", "exact precision stored")
        assert_true(year.event_date == "2021", "year-only event stored")
        assert_true(year.event_date_precision == "year_only", "year-only precision stored")
        assert_true(unknown.event_date_precision == "unknown", "unknown precision stored")
        assert_true(timeline_event_date_label(unknown) == "fecha pendiente", "unknown date label")
        assert_true(exact.audit_trail and exact.audit_trail[0]["action"] == "created_from_draft", "create audit exists")

        sorted_records = store.list_events_sorted()
        assert_true(sorted_records[0].event_date == "2021", "known dates sorted first by date")
        assert_true(sorted_records[1].event_date == "2024-05-12", "exact date follows chronological order")
        assert_true(sorted_records[-1].event_date_precision == "unknown", "unknown date goes to pending bucket")

        rendered = render_timeline_event_records_for_user(sorted_records)
        assert_contains(rendered, "Línea de tiempo de Caso Finca", "renderer title")
        assert_contains(rendered, "Eventos con fecha", "known-date section")
        assert_contains(rendered, "Fecha pendiente", "pending-date section")
        assert_contains(rendered, "Nora/la abogada confirma efecto legal", "legal boundary")
        for needle in FORBIDDEN_USER_FACING:
            assert_not_contains(rendered, needle, f"renderer hides internal {needle}")

        deleted = store.soft_delete(year.event_id, actor="smoke", reason="store spike soft-delete test", now="2026-06-04T22:13:00+00:00")
        assert_true(deleted is not None, "soft-delete returns deleted record")
        assert_true(deleted.deleted_at == "2026-06-04T22:13:00+00:00", "soft-delete marks deleted_at")
        assert_true(deleted.audit_trail[-1]["action"] == "soft_deleted", "soft-delete audit exists")
        assert_true(len(store.list_events()) == 2, "soft-deleted record hidden from active list")
        assert_true(len(store.list_events(include_deleted=True)) == 3, "soft-deleted record retained in full list")

    after_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    after_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None
    assert_true(before_grocery == after_grocery, "CLIENT_GROCERY.md untouched")
    assert_true(before_folders == after_folders, "CLIENT_FOLDERS.json untouched")


def test_protected_live_paths_refused() -> None:
    for path in (
        LIVE_GROCERY,
        LIVE_FOLDERS,
        ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_CASE_TIMELINE_EVENTS.json",
    ):
        try:
            CaseTimelineEventJsonStore(path)
        except ValueError as exc:
            assert_contains(str(exc), "protected live client path", f"protected path refused: {path.name}")
        else:
            raise AssertionError(f"protected path was not refused: {path}")


def main() -> None:
    test_store_roundtrip_sorting_and_audit()
    test_protected_live_paths_refused()
    print("PASS caso_finca_timeline_event_store_smoke")


if __name__ == "__main__":
    main()
