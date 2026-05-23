from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.case_timeline import (
    TimelineEvent,
    filter_timeline_events,
    normalize_confidence,
    normalize_date_precision,
    safe_timeline_event_summary,
    sort_timeline_events,
    timeline_event_from_case_note,
    timeline_event_from_document_record,
)
from core.document_registry import document_record_from_vfms_metadata


def assert_equal(actual, expected, label):
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(value, label):
    if not value:
        raise AssertionError(label)


def build_events() -> list[TimelineEvent]:
    note_event = timeline_event_from_case_note(
        client_id="client-a",
        case_id="CASE-1",
        note_id=101,
        note_text="Evento reciente del caso:\n\nSe revisó el expediente en 2024.",
        created_at="2026-05-23T10:00:00+00:00",
        event_date="2024-04-29",
        date_precision="exact",
        confidence=82,
        tags=("finca:10082", "registro", "registro"),
    )

    record = document_record_from_vfms_metadata(
        client_id="client-a",
        case_id="CASE-1",
        chat_id=111,
        metadata={
            "ingest_id": "20260523_000010",
            "filename": "registro_publico.pdf",
            "caption": "Documento de Registro Publico",
            "status": "texto extraído e indexado",
            "mime_type": "application/pdf",
            "stored_path": "/fixture/raw/20260523_000010__registro_publico.pdf",
            "hash": "secret-hash",
        },
        caption="Documento de Registro Publico",
        source="telegram_attachment_vfms",
        source_message_id=22,
    )
    doc_event = timeline_event_from_document_record(
        record,
        event_date="2026-05",
        date_precision="month",
        tags=("documento", "finca:10082"),
    )

    other_event = timeline_event_from_case_note(
        client_id="client-b",
        case_id="CASE-2",
        note_id="n-2",
        note_text="Otra nota",
        created_at="2025-01-01T00:00:00+00:00",
        confidence=-1,
        tags=("otro",),
    )

    unknown_date_event = timeline_event_from_case_note(
        client_id="client-a",
        case_id="CASE-1",
        note_id="unknown",
        note_text="Nota sin fecha real",
        created_at="",
        event_date="",
        date_precision="unknown",
        tags=("sin-fecha",),
    )

    return [doc_event, unknown_date_event, other_event, note_event]


def main():
    assert_equal(normalize_date_precision("exact"), "day", "exact date precision")
    assert_equal(normalize_date_precision("año"), "year", "year date precision")
    assert_equal(normalize_date_precision("created at"), "created_at_only", "created_at precision")
    assert_equal(normalize_date_precision("weird"), "unknown", "unknown date precision")

    assert_equal(normalize_confidence(82), 0.82, "percentage confidence")
    assert_equal(normalize_confidence(-2), 0.0, "low confidence clamp")
    assert_equal(normalize_confidence(2), 0.02, "small percentage confidence")
    assert_equal(normalize_confidence("bad"), 0.0, "bad confidence")

    events = build_events()
    note_event = events[-1]
    assert_equal(note_event.event_id, "case_note:101", "case note event id")
    assert_equal(note_event.date_precision, "day", "case note precision")
    assert_equal(note_event.confidence, 0.82, "case note confidence")
    assert_equal(note_event.tags, ("finca:10082", "registro"), "deduped tags")

    doc_event = events[0]
    assert_equal(doc_event.source_type, "document", "document source")
    assert_equal(doc_event.document_id, "vfms:20260523_000010", "document id")
    assert_equal(doc_event.ingest_id, "20260523_000010", "ingest id")

    filtered = filter_timeline_events(events, client_id="client-a", case_id="CASE-1")
    assert_equal(len(filtered), 3, "client/case filter")
    assert_equal(len(filter_timeline_events(events, year=2024)), 1, "year filter")
    assert_equal(len(filter_timeline_events(events, tag="finca:10082")), 2, "tag filter")
    assert_equal(len(filter_timeline_events(events, source_type="document")), 1, "source filter")

    sorted_events = sort_timeline_events(events)
    assert_equal(sorted_events[0].event_date, "2024-04-29", "sort first")
    assert_equal(sorted_events[-1].date_precision, "unknown", "sort unknown last")

    summary = safe_timeline_event_summary(doc_event)
    assert_equal(summary["source_type"], "document", "safe source")
    assert_equal(summary["source_id"], "vfms:20260523_000010", "safe source id")
    assert_true("stored_path" not in summary, "safe summary no raw path")
    assert_true("hash" not in summary, "safe summary no hash")
    assert_true("metadata" not in summary, "safe summary no metadata")

    print("PASS: case timeline smoke cases passed.")


if __name__ == "__main__":
    main()
