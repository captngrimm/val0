from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.case_timeline import (
    TimelineEvent,
    build_timeline_events_from_case_notes,
    build_timeline_events_from_document_records,
    filter_timeline_events,
    merge_timeline_events,
    normalize_confidence,
    normalize_date_precision,
    safe_timeline_event_summary,
    sort_timeline_events,
    timeline_events_for_year,
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


def assert_false(value, label):
    if value:
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


def build_derived_fixture_rows():
    return [
        {
            "id": 201,
            "client_id": "client-a",
            "case_id": "CASE-1",
            "source": "telegram_attachment_vfms",
            "created_at": "2026-05-23T10:00:00+00:00",
            "telegram_message_id": 901,
            "note_text": (
                "Documento recibido vía Telegram y registrado en VFMS.\n"
                "- Archivo: registro_publico.pdf\n"
                "- Tipo: document\n"
                "- VFMS ingest_id: 20260523_000020\n"
                "- Ruta local: /fixture/raw/registro_publico.pdf\n"
                "- Estado: texto extraído e indexado\n"
                "- Nota usuario: Registro Publico Finca 10082\n"
            ),
        },
        {
            "id": 202,
            "client_id": "client-a",
            "case_id": "CASE-1",
            "source": "case_recent_event_v0",
            "created_at": "2026-05-23T11:00:00+00:00",
            "note_text": "Evento reciente del caso:\n\nEl 29 de abril de 2024 se revisó el expediente.",
        },
        {
            "id": 203,
            "client_id": "client-a",
            "case_id": "CASE-1",
            "source": "case_recent_event_v0",
            "created_at": "2026-05-23T11:10:00+00:00",
            "note_text": "Evento reciente del caso:\n\nEl trámite familiar empezó en 1986.",
        },
        {
            "id": 204,
            "client_id": "client-a",
            "case_id": "CASE-1",
            "source": "reminder",
            "due_at_utc": "2026-06-01 14:00:00",
            "created_at": "2026-05-23T12:00:00+00:00",
            "note_text": "RECORDATORIO: llamar a la abogada",
        },
        {
            "id": 205,
            "client_id": "client-a",
            "case_id": "CASE-1",
            "source": "term",
            "deadline_date": "2024-05-15",
            "created_at": "2026-05-23T12:15:00+00:00",
            "event_text": "Término para contestar",
        },
        {
            "id": 206,
            "client_id": "client-a",
            "case_id": "CASE-1",
            "source": "generated_summary",
            "created_at": "2026-05-23T12:30:00+00:00",
            "note_text": "Resumen generado que no debe ser fuente de verdad.",
        },
        {
            "id": 207,
            "client_id": "client-b",
            "case_id": "CASE-OTHER",
            "source": "case_recent_event_v0",
            "created_at": "2026-05-23T12:40:00+00:00",
            "note_text": "Evento de otro cliente en 2024.",
        },
        {
            "id": 208,
            "client_id": "client-a",
            "case_id": "CASE-1",
            "source": "manual_note",
            "created_at": "2026-05-23T12:45:00+00:00",
            "note_text": "Nota sin fecha explícita.",
        },
    ]


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

    derived = build_timeline_events_from_case_notes(
        build_derived_fixture_rows(),
        client_id="client-a",
        case_id="CASE-1",
    )
    assert_equal(len(derived), 6, "derived safe event count")

    upload_events = [event for event in derived if event.source_type == "telegram_attachment_vfms"]
    assert_equal(len(upload_events), 1, "upload event count")
    upload = upload_events[0]
    assert_equal(upload.document_id, "vfms:20260523_000020", "upload document id")
    assert_equal(upload.ingest_id, "20260523_000020", "upload ingest id")
    assert_true("finca:10082" in upload.tags, "upload finca tag")
    upload_summary = safe_timeline_event_summary(upload)
    assert_false("Ruta local" in str(upload_summary), "upload safe summary no raw path line")
    assert_false("/fixture/raw" in str(upload_summary), "upload safe summary no raw path value")

    manual_events = [event for event in derived if event.source_id == "202"]
    assert_equal(len(manual_events), 1, "manual event count")
    assert_equal(manual_events[0].source_type, "manual_note", "manual event source type")
    assert_equal(manual_events[0].event_date, "2024-04-29", "manual exact date")
    assert_equal(manual_events[0].date_precision, "day", "manual exact precision")

    year_only_events = [event for event in derived if event.source_id == "203"]
    assert_equal(year_only_events[0].event_date, "1986", "year-only date")
    assert_equal(year_only_events[0].date_precision, "year", "year-only precision")

    reminder_events = [event for event in derived if event.source_type == "reminder"]
    assert_equal(len(reminder_events), 1, "reminder event count")
    assert_equal(reminder_events[0].event_date, "2026-06-01", "reminder exact date")

    term_events = [event for event in derived if event.source_type == "term"]
    assert_equal(len(term_events), 1, "term event count")
    assert_equal(term_events[0].event_date, "2024-05-15", "term deadline date")

    assert_equal(len(timeline_events_for_year(derived, 2024)), 2, "year query exact dates")
    assert_equal(len(timeline_events_for_year(derived, 1986)), 1, "year query year-only")
    assert_equal(sort_timeline_events(derived)[-1].date_precision, "unknown", "derived unknown sort last")

    merged = merge_timeline_events(derived[:2], derived[1:4])
    assert_equal(len(merged), 4, "merged dedupe count")
    assert_equal(merged[0].source_id, "203", "merged keeps sorted provenance")

    generated = [event for event in derived if event.source_id == "206"]
    assert_equal(generated, [], "generated summary ignored")

    cross_client = build_timeline_events_from_case_notes(
        build_derived_fixture_rows(),
        client_id="client-b",
        case_id="CASE-OTHER",
    )
    assert_equal(len(cross_client), 1, "cross-client explicit scope")
    excluded = build_timeline_events_from_case_notes(
        build_derived_fixture_rows(),
        client_id="client-a",
        case_id="CASE-1",
    )
    assert_true(all(event.client_id == "client-a" and event.case_id == "CASE-1" for event in excluded), "cross-client excluded")

    record_a = document_record_from_vfms_metadata(
        client_id="client-a",
        case_id="CASE-1",
        chat_id=111,
        metadata={
            "ingest_id": "20260523_000030",
            "filename": "foto_finca.jpg",
            "status": "archivo guardado; necesita OCR",
            "mime_type": "image/jpeg",
        },
        source="telegram_attachment_vfms",
        source_message_id=33,
    )
    record_b = document_record_from_vfms_metadata(
        client_id="client-b",
        case_id="CASE-2",
        chat_id=222,
        metadata={"ingest_id": "20260523_000031", "filename": "otro.pdf"},
        source="telegram_attachment_vfms",
    )
    record_ignored = document_record_from_vfms_metadata(
        client_id="client-a",
        case_id="CASE-1",
        chat_id=111,
        metadata={"ingest_id": "20260523_000032", "filename": "summary.md"},
        source="generated_summary",
    )
    doc_derived = build_timeline_events_from_document_records(
        [record_a, record_b, record_ignored],
        client_id="client-a",
        case_id="CASE-1",
    )
    assert_equal(len(doc_derived), 1, "document records scoped and safe")
    assert_equal(doc_derived[0].source_type, "telegram_attachment_vfms", "document record source preserved")
    assert_equal(doc_derived[0].ingest_id, "20260523_000030", "document record ingest")

    print("PASS: case timeline smoke cases passed.")


if __name__ == "__main__":
    main()
