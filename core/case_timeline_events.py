from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CASE_ID = "CASE:KAREN-LAND-001"
WORKSPACE_TITLE = "Caso Finca"
LEGAL_BOUNDARY = "Val organiza y resume; Nora/la abogada confirma efecto legal."
PENDING_DRAFT_KEY = "pending_case_timeline_event_draft"
PROTECTED_LIVE_FILENAMES = {"CLIENT_GROCERY.md", "CLIENT_FOLDERS.json", "CLIENT_CASE_TIMELINE_EVENTS.json"}

SPANISH_MONTHS = {
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

UNCERTAINTY_MARKERS = (
    "parece",
    "creo",
    "puede ser",
    "podria ser",
    "podría ser",
    "posible",
    "tal vez",
    "quizas",
    "quizás",
    "falta confirmar",
    "pendiente de confirmar",
)


@dataclass(frozen=True)
class CaseTimelineEventDraft:
    case_id: str
    workspace_title: str
    title: str
    description: str
    event_date: str
    event_date_precision: str
    source_type: str
    source_ref: str
    confirmation_status: str
    confidence: str
    legal_effect_status: str = "unknown"
    created_by: str = "user"


@dataclass(frozen=True)
class CaseTimelineEventRecord:
    event_id: str
    case_id: str
    title: str
    description: str
    event_date: str
    event_date_precision: str
    recorded_at: str
    source_type: str
    source_ref: str
    confirmation_status: str
    confidence: str
    legal_effect_status: str
    created_by: str
    created_at: str
    updated_at: str
    deleted_at: str = ""
    audit_trail: tuple[dict[str, Any], ...] = field(default_factory=tuple)


def _strip_accents(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def normalize_timeline_event_text(text: str) -> str:
    value = _strip_accents(text).lower()
    value = re.sub(r"[¿?¡!.,:;]+", " ", value)
    value = re.sub(r"\b(?:valeria|vale|val|va\s+el|bal|pal)\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def looks_like_case_timeline_event_registration(text: str) -> bool:
    norm = normalize_timeline_event_text(text)
    if not norm:
        return False

    action_markers = (
        "registra",
        "registrar",
        "anota",
        "apunta",
        "agrega",
        "añade",
        "anade",
        "mete",
    )
    if not any(marker in norm for marker in action_markers):
        return False

    case_markers = (
        "caso finca",
        "caso del terreno",
        "linea de tiempo",
        "timeline",
        "finca",
        "terreno",
    )
    document_reference = bool(re.search(r"\bdocumento\s+\d{1,2}\b", norm))
    return any(marker in norm for marker in case_markers) or document_reference


def _month_number(month_name: str) -> int:
    return SPANISH_MONTHS.get(_strip_accents(month_name).lower().strip(), 0)


def _detect_date(text: str) -> tuple[str, str]:
    norm = normalize_timeline_event_text(text)
    month_names = "|".join(SPANISH_MONTHS)

    exact = re.search(
        rf"\b(?:el\s+)?(?P<day>\d{{1,2}})\s+de\s+(?P<month>{month_names})\s+de\s+(?P<year>19\d{{2}}|20\d{{2}})\b",
        norm,
    )
    if exact:
        month = _month_number(exact.group("month"))
        day = int(exact.group("day"))
        year = int(exact.group("year"))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{year:04d}-{month:02d}-{day:02d}", "exact"

    month_only = re.search(
        rf"\b(?:en\s+)?(?P<month>{month_names})\s+de\s+(?P<year>19\d{{2}}|20\d{{2}})\b",
        norm,
    )
    if month_only:
        month = _month_number(month_only.group("month"))
        year = int(month_only.group("year"))
        if 1 <= month <= 12:
            return f"{year:04d}-{month:02d}", "month_only"

    year_only = re.search(r"\b(?:en|de|del)?\s*(?P<year>19\d{2}|20\d{2})\b", norm)
    if year_only:
        return year_only.group("year"), "year_only"

    return "", "unknown"


def _extract_description(text: str) -> str:
    value = str(text or "").strip()
    value = re.sub(r"(?is)^\s*(?:valeria|vale|val|va\s+el|bal|pal)[,:]?\s+", "", value).strip()
    patterns = (
        r"(?is)^(?:registra|registrar|anota|apunta)\s+en\s+caso\s+finca\s+que\s+",
        r"(?is)^(?:registra|registrar|anota|apunta)\s+en\s+el\s+caso\s+finca\s+que\s+",
        r"(?is)^(?:agrega|añade|anade)\s+a\s+la\s+l[ií]nea\s+de\s+tiempo\s+que\s+",
        r"(?is)^(?:agrega|añade|anade)\s+en\s+caso\s+finca\s+que\s+",
        r"(?is)^(?:registra|registrar|anota|apunta|agrega|añade|anade)\s+que\s+",
    )
    for pattern in patterns:
        value = re.sub(pattern, "", value).strip()
    return re.sub(r"\s+", " ", value).strip()


def _capitalize_first(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    return value[0].upper() + value[1:]


def _short_title(description: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(description or "")).strip()
    if not cleaned:
        return "Evento pendiente de describir"
    cleaned = re.sub(r"(?is)^(?:en\s+)?(?:el\s+)?", "", cleaned).strip()
    title = cleaned[:90].strip()
    if len(cleaned) > len(title):
        title = title.rstrip(" .,;:") + "..."
    return _capitalize_first(title)


def _document_source_ref(text: str) -> str:
    norm = normalize_timeline_event_text(text)
    match = re.search(r"\bdocumento\s+(\d{1,2})\b", norm)
    if match:
        return f"documento {int(match.group(1))}"
    return ""


def parse_case_timeline_event_draft(text: str) -> CaseTimelineEventDraft | None:
    if not looks_like_case_timeline_event_registration(text):
        return None

    description = _extract_description(text)
    event_date, precision = _detect_date(text)
    norm = normalize_timeline_event_text(text)
    source_ref = _document_source_ref(text)
    source_type = "document_metadata" if source_ref else "user_note"
    uncertain = any(marker in norm for marker in UNCERTAINTY_MARKERS)
    confirmation_status = "candidate" if uncertain else "pending_confirmation"
    confidence = "low" if uncertain else "medium"

    return CaseTimelineEventDraft(
        case_id=CASE_ID,
        workspace_title=WORKSPACE_TITLE,
        title=_short_title(description),
        description=description or "Evento pendiente de describir",
        event_date=event_date,
        event_date_precision=precision,
        source_type=source_type,
        source_ref=source_ref,
        confirmation_status=confirmation_status,
        confidence=confidence,
    )


def _date_label(draft: CaseTimelineEventDraft) -> str:
    if draft.event_date_precision == "exact":
        return draft.event_date
    if draft.event_date_precision == "month_only":
        return draft.event_date
    if draft.event_date_precision == "year_only":
        return draft.event_date
    return "fecha pendiente"


def _precision_label(precision: str) -> str:
    labels = {
        "exact": "fecha exacta",
        "month_only": "mes y año",
        "year_only": "solo año",
        "unknown": "sin fecha todavía",
    }
    return labels.get(precision, "sin fecha todavía")


def _status_label(status: str) -> str:
    if status == "candidate":
        return "candidato / pendiente de confirmar"
    return "pendiente de confirmar"


def _source_label(draft: CaseTimelineEventDraft) -> str:
    if draft.source_type == "document_metadata":
        return f"referencia a {draft.source_ref or 'documento registrado'}"
    return "nota tuya"


def render_case_timeline_event_draft_preview(draft: CaseTimelineEventDraft) -> str:
    lines = [
        "Tany, tengo este borrador de evento para Caso Finca. No lo he guardado todavía.",
        "",
        f"Evento: {draft.title}",
        f"Fecha: {_date_label(draft)}",
        f"Precisión: {_precision_label(draft.event_date_precision)}",
        f"Estado: {_status_label(draft.confirmation_status)}",
        f"Fuente: {_source_label(draft)}",
        "Efecto legal: desconocido; Nora/la abogada confirma.",
    ]

    if draft.confirmation_status == "candidate":
        lines.extend(
            [
                "",
                "Cuidado: lo marco como candidato porque la frase suena a dato por confirmar.",
            ]
        )

    lines.extend(
        [
            "",
            "¿Lo guardo en Caso Finca?",
            "",
            f"Límite legal: {LEGAL_BOUNDARY}",
            "Nota de seguridad: esta versión prepara el borrador y la confirmación; todavía no persiste eventos.",
        ]
    )
    return "\n".join(lines)


async def maybe_handle_case_timeline_event_draft(
    update: Any,
    context: Any,
    chat_id: int,
    client_id: str,
    text: str,
) -> bool:
    if not update or not getattr(update, "message", None):
        return False
    if str(client_id or "").strip().lower() not in {"karen", "client-zero"}:
        return False

    draft = parse_case_timeline_event_draft(text)
    if not draft:
        return False

    chat_data = getattr(context, "chat_data", None)
    if isinstance(chat_data, dict):
        chat_data[PENDING_DRAFT_KEY] = asdict(draft)

    await update.message.reply_text(render_case_timeline_event_draft_preview(draft), disable_web_page_preview=True)
    return True


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_event_id(*, case_id: str, sequence: int, created_at: str) -> str:
    stamp = re.sub(r"\D+", "", created_at)[:14] or "00000000000000"
    case_slug = re.sub(r"[^a-z0-9]+", "-", _strip_accents(case_id).lower()).strip("-")
    return f"event:{case_slug}:{stamp}-{sequence:04d}"


def _record_from_mapping(data: dict[str, Any]) -> CaseTimelineEventRecord:
    audit = data.get("audit_trail") if isinstance(data.get("audit_trail"), list) else []
    return CaseTimelineEventRecord(
        event_id=str(data.get("event_id") or "").strip(),
        case_id=str(data.get("case_id") or CASE_ID).strip(),
        title=str(data.get("title") or "").strip(),
        description=str(data.get("description") or "").strip(),
        event_date=str(data.get("event_date") or "").strip(),
        event_date_precision=str(data.get("event_date_precision") or "unknown").strip(),
        recorded_at=str(data.get("recorded_at") or "").strip(),
        source_type=str(data.get("source_type") or "user_note").strip(),
        source_ref=str(data.get("source_ref") or "").strip(),
        confirmation_status=str(data.get("confirmation_status") or "pending_confirmation").strip(),
        confidence=str(data.get("confidence") or "unknown").strip(),
        legal_effect_status=str(data.get("legal_effect_status") or "unknown").strip(),
        created_by=str(data.get("created_by") or "user").strip(),
        created_at=str(data.get("created_at") or "").strip(),
        updated_at=str(data.get("updated_at") or "").strip(),
        deleted_at=str(data.get("deleted_at") or "").strip(),
        audit_trail=tuple(item for item in audit if isinstance(item, dict)),
    )


def event_record_from_draft(
    draft: CaseTimelineEventDraft,
    *,
    event_id: str = "",
    now: str = "",
    sequence: int = 1,
) -> CaseTimelineEventRecord:
    created_at = now or _utc_now_iso()
    record_id = event_id or _safe_event_id(case_id=draft.case_id, sequence=sequence, created_at=created_at)
    audit = (
        {
            "action": "created_from_draft",
            "at": created_at,
            "actor": draft.created_by,
            "note": "Fixture/temp storage spike; no live client event file.",
        },
    )
    return CaseTimelineEventRecord(
        event_id=record_id,
        case_id=draft.case_id,
        title=draft.title,
        description=draft.description,
        event_date=draft.event_date,
        event_date_precision=draft.event_date_precision,
        recorded_at=created_at,
        source_type=draft.source_type,
        source_ref=draft.source_ref,
        confirmation_status=draft.confirmation_status,
        confidence=draft.confidence,
        legal_effect_status=draft.legal_effect_status,
        created_by=draft.created_by,
        created_at=created_at,
        updated_at=created_at,
        audit_trail=audit,
    )


def _guard_fixture_store_path(path: Path) -> None:
    resolved = path.resolve()
    parts = set(resolved.parts)
    if path.name in PROTECTED_LIVE_FILENAMES or ("clients" in parts and "karen" in parts):
        raise ValueError(f"Refusing timeline event spike store under protected live client path: {path}")


def _event_sort_key(record: CaseTimelineEventRecord) -> tuple[int, str, int, str]:
    precision = record.event_date_precision
    if precision == "unknown" or not record.event_date:
        return (1, "9999-99-99", 9, record.title.lower())
    precision_rank = {"exact": 0, "month_only": 1, "year_only": 2}.get(precision, 8)
    date_value = record.event_date
    if precision == "month_only":
        date_value = f"{record.event_date}-99"
    elif precision == "year_only":
        date_value = f"{record.event_date}-99-99"
    return (0, date_value, precision_rank, record.title.lower())


def sorted_timeline_event_records(records: list[CaseTimelineEventRecord] | tuple[CaseTimelineEventRecord, ...]) -> list[CaseTimelineEventRecord]:
    return sorted((record for record in records if not record.deleted_at), key=_event_sort_key)


def timeline_event_date_label(record: CaseTimelineEventRecord) -> str:
    if record.event_date_precision == "unknown" or not record.event_date:
        return "fecha pendiente"
    return record.event_date


def render_timeline_event_records_for_user(records: list[CaseTimelineEventRecord] | tuple[CaseTimelineEventRecord, ...]) -> str:
    active = sorted_timeline_event_records(records)
    known = [record for record in active if record.event_date_precision != "unknown" and record.event_date]
    pending = [record for record in active if record.event_date_precision == "unknown" or not record.event_date]
    lines = ["🧭 Línea de tiempo de Caso Finca", ""]
    if known:
        lines.append("Eventos con fecha")
        for idx, record in enumerate(known, start=1):
            status = "candidato" if record.confirmation_status == "candidate" else "pendiente de confirmar"
            lines.append(f"{idx}. {timeline_event_date_label(record)} · {record.title} ({status})")
        lines.append("")
    if pending:
        lines.append("Fecha pendiente")
        for idx, record in enumerate(pending, start=1):
            status = "candidato" if record.confirmation_status == "candidate" else "pendiente de confirmar"
            lines.append(f"{idx}. {record.title} ({status})")
        lines.append("")
    lines.append(f"Límite legal: {LEGAL_BOUNDARY}")
    return "\n".join(lines).strip()


class CaseTimelineEventJsonStore:
    """Fixture/temp JSON store for timeline event storage spikes."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        _guard_fixture_store_path(self.path)

    def _read_payload(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "events": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid timeline event JSON store: {self.path}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"Timeline event JSON store must be an object: {self.path}")
        events = data.get("events")
        if not isinstance(events, list):
            data["events"] = []
        data["version"] = int(data.get("version") or 1)
        return data

    def _write_payload(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def list_events(self, *, include_deleted: bool = False) -> list[CaseTimelineEventRecord]:
        payload = self._read_payload()
        records = [_record_from_mapping(item) for item in payload.get("events", []) if isinstance(item, dict)]
        if include_deleted:
            return records
        return [record for record in records if not record.deleted_at]

    def list_events_sorted(self, *, include_deleted: bool = False) -> list[CaseTimelineEventRecord]:
        records = self.list_events(include_deleted=include_deleted)
        if include_deleted:
            return sorted(records, key=_event_sort_key)
        return sorted_timeline_event_records(records)

    def append_from_draft(self, draft: CaseTimelineEventDraft, *, now: str = "") -> CaseTimelineEventRecord:
        payload = self._read_payload()
        existing = [_record_from_mapping(item) for item in payload.get("events", []) if isinstance(item, dict)]
        record = event_record_from_draft(draft, now=now, sequence=len(existing) + 1)
        payload["events"] = [asdict(item) for item in existing] + [asdict(record)]
        self._write_payload(payload)
        return record

    def soft_delete(self, event_id: str, *, actor: str = "user", reason: str = "", now: str = "") -> CaseTimelineEventRecord | None:
        deleted_at = now or _utc_now_iso()
        payload = self._read_payload()
        records = [_record_from_mapping(item) for item in payload.get("events", []) if isinstance(item, dict)]
        updated: list[CaseTimelineEventRecord] = []
        deleted: CaseTimelineEventRecord | None = None
        for record in records:
            if record.event_id == event_id:
                audit = list(record.audit_trail)
                audit.append(
                    {
                        "action": "soft_deleted",
                        "at": deleted_at,
                        "actor": actor,
                        "reason": reason,
                    }
                )
                deleted = CaseTimelineEventRecord(
                    event_id=record.event_id,
                    case_id=record.case_id,
                    title=record.title,
                    description=record.description,
                    event_date=record.event_date,
                    event_date_precision=record.event_date_precision,
                    recorded_at=record.recorded_at,
                    source_type=record.source_type,
                    source_ref=record.source_ref,
                    confirmation_status=record.confirmation_status,
                    confidence=record.confidence,
                    legal_effect_status=record.legal_effect_status,
                    created_by=record.created_by,
                    created_at=record.created_at,
                    updated_at=deleted_at,
                    deleted_at=deleted_at,
                    audit_trail=tuple(audit),
                )
                updated.append(deleted)
            else:
                updated.append(record)
        payload["events"] = [asdict(item) for item in updated]
        self._write_payload(payload)
        return deleted
