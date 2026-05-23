from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from core.document_registry import DocumentRecord


DATE_PRECISIONS = {
    "day",
    "month",
    "year",
    "approximate",
    "created_at_only",
    "unknown",
}

SOURCE_TYPES = {
    "case_note",
    "document",
    "vfms_chunk",
    "reminder",
    "calendar",
    "legal_note",
    "manual",
}


@dataclass(frozen=True)
class TimelineEvent:
    event_id: str
    client_id: str
    case_id: str
    event_date: str
    date_precision: str
    title: str
    description: str
    source_type: str
    source_id: str
    document_id: str | None = None
    ingest_id: str | None = None
    confidence: float = 0.0
    tags: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


def normalize_date_precision(value: str | None) -> str:
    raw = (value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if not raw:
        return "unknown"

    aliases = {
        "exact": "day",
        "exact_day": "day",
        "date": "day",
        "daily": "day",
        "yyyy_mm_dd": "day",
        "mes": "month",
        "monthly": "month",
        "yyyy_mm": "month",
        "ano": "year",
        "año": "year",
        "annual": "year",
        "yyyy": "year",
        "approx": "approximate",
        "aprox": "approximate",
        "aproximado": "approximate",
        "created": "created_at_only",
        "created_at": "created_at_only",
        "created_only": "created_at_only",
        "none": "unknown",
        "sin_fecha": "unknown",
        "unknown_date": "unknown",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in DATE_PRECISIONS else "unknown"


def normalize_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0

    if confidence > 1.0 and confidence <= 100.0:
        confidence = confidence / 100.0
    if confidence < 0.0:
        return 0.0
    if confidence > 1.0:
        return 1.0
    return round(confidence, 4)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_tags(tags: Iterable[Any] | None) -> tuple[str, ...]:
    seen = set()
    cleaned = []
    for tag in tags or ():
        item = str(tag or "").strip().lower()
        if not item or item in seen:
            continue
        seen.add(item)
        cleaned.append(item)
    return tuple(cleaned)


def _source_type(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return raw if raw in SOURCE_TYPES else "manual"


def timeline_event_from_case_note(
    *,
    client_id: str,
    case_id: str,
    note_id: str | int,
    note_text: str,
    created_at: str | None = None,
    event_date: str | None = None,
    date_precision: str | None = None,
    title: str | None = None,
    source_type: str = "case_note",
    confidence: Any = 0.65,
    tags: Iterable[Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> TimelineEvent:
    clean_note = (note_text or "").strip()
    clean_title = (title or clean_note.splitlines()[0] if clean_note else "Nota del caso").strip()
    source_id = str(note_id).strip()
    created = (created_at or _utc_now()).strip()
    timeline_date = (event_date or created).strip()
    precision = normalize_date_precision(date_precision or ("created_at_only" if not event_date else "day"))

    return TimelineEvent(
        event_id=f"case_note:{source_id}",
        client_id=str(client_id).strip(),
        case_id=str(case_id).strip(),
        event_date=timeline_date,
        date_precision=precision,
        title=clean_title or "Nota del caso",
        description=clean_note,
        source_type=_source_type(source_type),
        source_id=source_id,
        confidence=normalize_confidence(confidence),
        tags=_clean_tags(tags),
        created_at=created,
        metadata=dict(metadata or {}),
    )


def timeline_event_from_document_record(
    record: DocumentRecord,
    *,
    event_date: str | None = None,
    date_precision: str | None = None,
    title: str | None = None,
    description: str | None = None,
    confidence: Any = 0.7,
    tags: Iterable[Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> TimelineEvent:
    event_id = f"document:{record.document_id}"
    doc_title = title or f"Documento registrado: {record.filename}"
    doc_description = description or (record.caption or f"Documento {record.filename} registrado para el caso.")
    timeline_date = (event_date or record.created_at or "").strip()
    precision = normalize_date_precision(date_precision or ("created_at_only" if not event_date else "day"))
    combined_metadata = dict(metadata or {})
    combined_metadata.update(
        {
            "filename": record.filename,
            "mime_type": record.mime_type,
            "status": record.status,
            "source": record.source,
            "source_message_id": record.source_message_id,
        }
    )

    return TimelineEvent(
        event_id=event_id,
        client_id=str(record.client_id).strip(),
        case_id=str(record.case_id).strip(),
        event_date=timeline_date,
        date_precision=precision,
        title=str(doc_title).strip(),
        description=str(doc_description).strip(),
        source_type="document",
        source_id=record.document_id,
        document_id=record.document_id,
        ingest_id=record.ingest_id or None,
        confidence=normalize_confidence(confidence),
        tags=_clean_tags(tags),
        created_at=record.created_at,
        metadata=combined_metadata,
    )


def filter_timeline_events(
    events: Iterable[TimelineEvent],
    *,
    client_id: str | None = None,
    case_id: str | None = None,
    year: int | str | None = None,
    tag: str | None = None,
    source_type: str | None = None,
) -> list[TimelineEvent]:
    year_text = str(year).strip() if year is not None else ""
    tag_text = str(tag or "").strip().lower()
    source_text = str(source_type or "").strip().lower()

    out = []
    for event in events:
        if client_id is not None and event.client_id != str(client_id):
            continue
        if case_id is not None and event.case_id != str(case_id):
            continue
        if year_text and not str(event.event_date or "").startswith(year_text):
            continue
        if tag_text and tag_text not in event.tags:
            continue
        if source_text and event.source_type != source_text:
            continue
        out.append(event)
    return out


def _sort_key(event: TimelineEvent) -> tuple[int, str, str]:
    date_text = (event.event_date or "").strip()
    precision = normalize_date_precision(event.date_precision)
    if not date_text or precision == "unknown":
        return (1, "9999-99-99", event.event_id)

    padded = date_text
    if precision == "year" and len(padded) == 4:
        padded = f"{padded}-12-31"
    elif precision == "month" and len(padded) == 7:
        padded = f"{padded}-31"
    return (0, padded, event.event_id)


def sort_timeline_events(events: Iterable[TimelineEvent]) -> list[TimelineEvent]:
    return sorted(list(events), key=_sort_key)


def safe_timeline_event_summary(event: TimelineEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "client_id": event.client_id,
        "case_id": event.case_id,
        "event_date": event.event_date,
        "date_precision": normalize_date_precision(event.date_precision),
        "title": event.title,
        "description": event.description,
        "source_type": event.source_type,
        "source_id": event.source_id,
        "document_id": event.document_id,
        "ingest_id": event.ingest_id,
        "confidence": normalize_confidence(event.confidence),
        "tags": list(event.tags),
        "created_at": event.created_at,
    }
