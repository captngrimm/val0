from __future__ import annotations

import re
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
    "manual_note",
    "term",
    "case_event",
    "telegram_attachment_vfms",
}

SAFE_DERIVED_SOURCE_TYPES = {
    "telegram_attachment_vfms",
    "case_event",
    "reminder",
    "term",
    "manual_note",
}

IGNORED_DERIVED_SOURCES = {
    "generated_summary",
    "document_summary",
    "vfms_query",
    "global_vfms_query",
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
    precision = normalize_date_precision(date_precision or ("created_at_only" if not event_date else "day"))
    if event_date:
        timeline_date = str(event_date).strip()
    elif precision == "created_at_only":
        timeline_date = created
    else:
        timeline_date = ""

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
    source_type: str = "document",
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
        source_type=_source_type(source_type),
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


def _row_get(row: Any, key: str, default: Any = "") -> Any:
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


def _matches_scope(row: Any, *, client_id: str | None, case_id: str | None) -> bool:
    row_client_id = str(_row_get(row, "client_id", "") or "").strip()
    row_case_id = str(_row_get(row, "case_id", "") or "").strip()
    if client_id is not None and row_client_id and row_client_id != str(client_id):
        return False
    if case_id is not None and row_case_id and row_case_id != str(case_id):
        return False
    return True


def _normalize_source_for_timeline(source: str, row: Any) -> str:
    raw = (source or "").strip().lower()
    if raw in IGNORED_DERIVED_SOURCES:
        return ""
    if raw == "telegram_attachment_vfms":
        return "telegram_attachment_vfms"
    if raw in {"case_recent_event_v0", "manual_note", "text"}:
        return "manual_note"
    if raw in {"reminder", "case_reminder"}:
        return "reminder"
    if raw in {"term", "deadline"}:
        return "term"
    if raw in {"case_event", "legal_event"}:
        event_text = str(_row_get(row, "event_text", "") or _row_get(row, "note_text", "") or "")
        if event_text.strip().upper().startswith("RECORDATORIO:"):
            return "reminder"
        if _row_get(row, "deadline_date", None):
            return "term"
        return "case_event"
    return ""


def _strip_iso_date(value: Any) -> str:
    raw = str(value or "").strip()
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", raw)
    return m.group(1) if m else ""


def _infer_date_from_text(text: str) -> tuple[str, str]:
    raw = text or ""
    iso = _strip_iso_date(raw)
    if iso:
        return iso, "day"

    month_map = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "setiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }
    month_names = "|".join(month_map)
    m = re.search(
        rf"\b([0-3]?\d)\s+de\s+({month_names})\s+de\s+(\d{{4}})\b",
        raw,
        flags=re.IGNORECASE,
    )
    if m:
        day = int(m.group(1))
        month = month_map[m.group(2).lower()]
        year = int(m.group(3))
        if 1 <= day <= 31:
            return f"{year:04d}-{month:02d}-{day:02d}", "day"

    years = re.findall(r"\b(19\d{2}|20\d{2})\b", raw)
    unique_years = []
    for year in years:
        if year not in unique_years:
            unique_years.append(year)
    if len(unique_years) == 1:
        return unique_years[0], "year"

    return "", "unknown"


def _date_from_row(row: Any, text: str) -> tuple[str, str]:
    for key in ("event_date", "deadline_date", "due_date", "due_at_utc", "start_date"):
        value = _row_get(row, key, "")
        exact = _strip_iso_date(value)
        if exact:
            return exact, "day"

    inferred_date, inferred_precision = _infer_date_from_text(text)
    if inferred_date:
        return inferred_date, inferred_precision

    if _row_get(row, "created_at", None):
        return "", "unknown"
    return "", "unknown"


def _parse_attachment_note(note_text: str) -> dict[str, str]:
    note = note_text or ""

    def first(pattern: str) -> str:
        m = re.search(pattern, note, flags=re.IGNORECASE)
        return (m.group(1).strip() if m else "")

    return {
        "filename": first(r"- Archivo:\s*(.+)"),
        "kind": first(r"- Tipo:\s*(.+)"),
        "ingest_id": first(r"- VFMS ingest_id:\s*(.+)"),
        "status": first(r"- Estado:\s*(.+)"),
        "caption": first(r"- Nota usuario:\s*(.+)"),
    }


def _tags_from_text(text: str, extra: Iterable[Any] | None = None) -> tuple[str, ...]:
    tags = list(extra or ())
    low = (text or "").lower()
    finca = re.search(r"\bfinca\s*[:#]?\s*(\d{3,})\b", low, flags=re.IGNORECASE)
    if finca:
        tags.append(f"finca:{finca.group(1)}")
    if "documento" in low or "vfms" in low:
        tags.append("documento")
    if "recordatorio" in low:
        tags.append("recordatorio")
    if "termino" in low or "término" in low or "deadline" in low or "vence" in low:
        tags.append("termino")
    return _clean_tags(tags)


def build_timeline_events_from_case_notes(
    case_notes: Iterable[Any],
    *,
    client_id: str | None = None,
    case_id: str | None = None,
) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    for row in case_notes or ():
        if not _matches_scope(row, client_id=client_id, case_id=case_id):
            continue

        row_source = str(_row_get(row, "source", "") or "").strip()
        source_type = _normalize_source_for_timeline(row_source, row)
        if source_type not in SAFE_DERIVED_SOURCE_TYPES:
            continue

        note_text = str(_row_get(row, "note_text", "") or _row_get(row, "event_text", "") or _row_get(row, "text", "") or "").strip()
        if not note_text:
            continue

        note_id = str(_row_get(row, "id", "") or _row_get(row, "source_id", "") or len(events) + 1)
        row_client_id = str(client_id if client_id is not None else _row_get(row, "client_id", "") or "").strip()
        row_case_id = str(case_id if case_id is not None else _row_get(row, "case_id", "") or "").strip()
        created_at = str(_row_get(row, "created_at", "") or "").strip()
        event_date, precision = _date_from_row(row, note_text)
        metadata = {
            "source": row_source,
            "telegram_message_id": _row_get(row, "telegram_message_id", None),
            "parent_ref": _row_get(row, "parent_ref", ""),
        }

        if source_type == "telegram_attachment_vfms":
            parsed = _parse_attachment_note(note_text)
            ingest_id = parsed.get("ingest_id") or ""
            filename = parsed.get("filename") or "documento"
            metadata.update(parsed)
            events.append(
                TimelineEvent(
                    event_id=f"case_note:{note_id}:document",
                    client_id=row_client_id,
                    case_id=row_case_id,
                    event_date=created_at if created_at else "",
                    date_precision="created_at_only" if created_at else "unknown",
                    title=f"Documento registrado: {filename}",
                    description=parsed.get("caption") or note_text,
                    source_type=source_type,
                    source_id=note_id,
                    document_id=f"vfms:{ingest_id}" if ingest_id else None,
                    ingest_id=ingest_id or None,
                    confidence=normalize_confidence(_row_get(row, "confidence", 0.75)),
                    tags=_tags_from_text(note_text, ("documento",)),
                    created_at=created_at or _utc_now(),
                    metadata=metadata,
                )
            )
            continue

        title = note_text.splitlines()[0].strip() or "Evento del caso"
        confidence_default = 0.8 if source_type in {"term", "reminder", "case_event"} and event_date else 0.6
        events.append(
            timeline_event_from_case_note(
                client_id=row_client_id,
                case_id=row_case_id,
                note_id=note_id,
                note_text=note_text,
                created_at=created_at,
                event_date=event_date,
                date_precision=precision,
                title=title,
                source_type=source_type,
                confidence=_row_get(row, "confidence", confidence_default),
                tags=_tags_from_text(note_text, _row_get(row, "tags", ())),
                metadata=metadata,
            )
        )
    return sort_timeline_events(events)


def build_timeline_events_from_document_records(
    records: Iterable[DocumentRecord],
    *,
    client_id: str | None = None,
    case_id: str | None = None,
) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    for record in records or ():
        if client_id is not None and record.client_id != str(client_id):
            continue
        if case_id is not None and record.case_id != str(case_id):
            continue
        if (record.source or "").strip().lower() not in SAFE_DERIVED_SOURCE_TYPES:
            continue

        created_at = (record.created_at or "").strip()
        event = timeline_event_from_document_record(
            record,
            event_date=created_at,
            date_precision="created_at_only" if created_at else "unknown",
            source_type=record.source,
            confidence=0.75,
            tags=_tags_from_text(f"{record.filename}\n{record.caption}", ("documento",)),
            metadata={"source": record.source, "status": record.status},
        )
        events.append(event)
    return sort_timeline_events(events)


def merge_timeline_events(*event_lists: Iterable[TimelineEvent]) -> list[TimelineEvent]:
    merged: dict[str, TimelineEvent] = {}
    for events in event_lists:
        for event in events or ():
            if event.event_id not in merged:
                merged[event.event_id] = event
                continue
            existing = merged[event.event_id]
            if normalize_confidence(event.confidence) > normalize_confidence(existing.confidence):
                merged[event.event_id] = event
    return sort_timeline_events(merged.values())


def timeline_events_for_year(events: Iterable[TimelineEvent], year: int | str) -> list[TimelineEvent]:
    return filter_timeline_events(events, year=str(year).strip())
