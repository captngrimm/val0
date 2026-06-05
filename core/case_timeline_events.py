from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any


CASE_ID = "CASE:KAREN-LAND-001"
WORKSPACE_TITLE = "Caso Finca"
LEGAL_BOUNDARY = "Val organiza y resume; Nora/la abogada confirma efecto legal."
PENDING_DRAFT_KEY = "pending_case_timeline_event_draft"

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
