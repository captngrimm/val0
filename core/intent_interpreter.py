from __future__ import annotations

import re
import unicodedata
from typing import Any

from core.time_intelligence import parse_spanish_clock_time, parse_spanish_relative_minutes


SUPPORTED_INTENTS = {
    "agenda_query",
    "reminder_list",
    "reminder_create",
    "task_list",
    "task_create",
    "calendar_create",
    "calendar_create_followup",
    "document_list",
    "case_status",
    "next_action",
    "unknown",
}


def _strip_accents(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def _normalize(text: str) -> str:
    value = _strip_accents(str(text or "")).lower()
    value = re.sub(r"[¿?¡!.,;]+", " ", value)
    value = re.sub(r"\b(?:valeria|vale|val|va\s+el|bal|pal)\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _pending_type(pending_state: Any) -> str:
    if not pending_state:
        return ""
    if isinstance(pending_state, str):
        return pending_state
    if isinstance(pending_state, dict):
        return str(
            pending_state.get("intent")
            or pending_state.get("intent_type")
            or pending_state.get("action_type")
            or pending_state.get("type")
            or ""
        )
    return str(type(pending_state).__name__ or "")


def _pending_missing_fields(pending_state: Any) -> list[str]:
    if not isinstance(pending_state, dict):
        return []
    raw = pending_state.get("missing_fields") or pending_state.get("missing") or []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, (list, tuple, set)):
        return [str(item) for item in raw]
    return []


def _result(
    intent: str,
    *,
    confidence: float,
    fields: dict[str, Any] | None = None,
    missing_fields: list[str] | None = None,
    normalized_user_text: str,
    route_hint: str | None = None,
    requires_confirmation: bool = False,
) -> dict[str, Any]:
    selected = intent if intent in SUPPORTED_INTENTS else "unknown"
    return {
        "intent": selected,
        "confidence": float(confidence),
        "fields": fields or {},
        "missing_fields": list(missing_fields or []),
        "normalized_user_text": normalized_user_text,
        "route_hint": route_hint or selected,
        "should_execute": False,
        "requires_confirmation": bool(requires_confirmation),
    }


def _has_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _word_number_hour(token: str) -> int | None:
    return {
        "una": 1,
        "uno": 1,
        "dos": 2,
        "tres": 3,
        "cuatro": 4,
        "cinco": 5,
        "seis": 6,
        "siete": 7,
        "ocho": 8,
        "nueve": 9,
        "diez": 10,
        "once": 11,
        "doce": 12,
    }.get(token)


def _parse_followup_time(text: str) -> str | None:
    parsed = parse_spanish_clock_time(text)
    if parsed:
        return f"{parsed[0]:02d}:{parsed[1]:02d}"

    norm = _normalize(text)
    match = re.search(
        r"\b(?P<hour>una|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|\d{1,2})"
        r"(?:\s+y\s+(?P<minute>media|\d{1,2}))?"
        r"(?:\s+de\s+la\s+(?P<daypart>manana|tarde|noche))?\b",
        norm,
    )
    if not match:
        return None

    hour_token = match.group("hour")
    hour = int(hour_token) if hour_token.isdigit() else _word_number_hour(hour_token)
    if hour is None:
        return None
    minute_token = match.group("minute") or "0"
    minute = 30 if minute_token == "media" else int(minute_token)
    daypart = match.group("daypart") or ""

    if daypart in {"tarde", "noche"} and 1 <= hour <= 11:
        hour += 12
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return f"{hour:02d}:{minute:02d}"
    return None


def _extract_date(text: str) -> str | None:
    norm = _normalize(text)
    for marker in ("hoy", "manana", "pasado manana"):
        if re.search(rf"\b{marker}\b", norm):
            return marker
    weekday = re.search(r"\b(?:proximo\s+)?(lunes|martes|miercoles|jueves|viernes|sabado|domingo)\b", norm)
    if weekday:
        return weekday.group(0)
    explicit = re.search(r"\b\d{1,2}\s+de\s+[a-z]+\b", norm)
    if explicit:
        return explicit.group(0)
    return None


def _extract_time(text: str) -> str | None:
    parsed = parse_spanish_clock_time(text)
    if parsed:
        return f"{parsed[0]:02d}:{parsed[1]:02d}"
    relative = parse_spanish_relative_minutes(text)
    if relative:
        return f"+{int(relative.minutes)}m"
    return _parse_followup_time(text)


def _cleanup_calendar_title(text: str) -> str:
    original = str(text or "")
    title = _strip_accents(original)
    title = re.sub(r"[¿?¡!]+", " ", title)
    title = re.sub(r"\b(?:valeria|vale|val|va\s+el|bal|pal)\b", " ", title, flags=re.IGNORECASE)
    title = re.sub(
        r"\b(?:agenda|agendar|crea\s+evento|crear\s+evento|pon\s+en\s+mi\s+calendario|agrega\s+al\s+calendario|agregala\s+al\s+calendario)\b",
        " ",
        title,
        flags=re.IGNORECASE,
    )
    title = re.sub(r"\b(?:google\s+calendar|calendario)\b", " ", title, flags=re.IGNORECASE)
    title = re.sub(r"\b(?:para|el|la)?\s*(?:hoy|manana|mañana|pasado\s+manana|pasado\s+mañana)\b", " ", title, flags=re.IGNORECASE)
    title = re.sub(r"\b(?:para\s+)?(?:el\s+)?(?:proximo\s+)?(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)\b", " ", title, flags=re.IGNORECASE)
    title = re.sub(r"\b\d{1,2}\s+de\s+[A-Za-záéíóúÁÉÍÓÚñÑ]+\b", " ", title)
    title = re.sub(r"\b(?:a\s+las?|a\s+la|para\s+las?|para\s+la)\s*\d{1,2}(?:(?::|\s+y\s+)\d{1,2})?\s*(?:am|pm|a\s*m|p\s*m)?(?:\s+de\s+la\s+(?:mañana|manana|tarde|noche))?\b", " ", title, flags=re.IGNORECASE)
    title = re.sub(r"\b(?:por|durante)\s+\d{1,3}\s+(?:minutos?|horas?)\b", " ", title, flags=re.IGNORECASE)
    title = re.sub(r"\s+", " ", title).strip(" .,:;")
    return title[:1].lower() + title[1:] if title else ""


def _extract_task_title(text: str) -> str:
    norm = _normalize(text)
    patterns = (
        r"^(?:registra|registrar|agrega|agregar|guarda|guardar|anota|anotar|crea|crear)\s+(?:una\s+)?tarea\s*:?\s+(.+)$",
        r"^(?:tengo\s+que|debo|hay\s+que)\s+(.+)$",
        r"^tarea\s*:?\s+(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, norm)
        if match:
            return re.sub(r"\s+", " ", (match.group(1) or "")).strip()
    return ""


def _extract_duration_minutes(text: str) -> int:
    norm = _normalize(text)
    match = re.search(r"\b(?:por|durante)\s+(?P<num>\d{1,3})\s+minutos?\b", norm)
    if match:
        return max(1, int(match.group("num")))
    match = re.search(r"\b(?:por|durante)\s+(?P<num>\d{1,2})\s+horas?\b", norm)
    if match:
        return max(1, int(match.group("num")) * 60)
    if re.search(r"\b(?:por|durante)\s+media\s+hora\b", norm):
        return 30
    return 60


def _calendar_fields(text: str) -> tuple[dict[str, Any], list[str]]:
    fields: dict[str, Any] = {"duration_minutes": _extract_duration_minutes(text)}
    date = _extract_date(text)
    time_value = _extract_time(text)
    title = _cleanup_calendar_title(text)

    if date:
        fields["date"] = date
    if time_value and not time_value.startswith("+"):
        fields["time"] = time_value
    if title:
        fields["title"] = title

    missing = [name for name in ("title", "date", "time") if name not in fields]
    return fields, missing


def _looks_like_calendar_create(norm: str) -> bool:
    if _has_any(norm, ("crea evento", "crear evento", "pon en mi calendario", "agrega al calendario", "agregala al calendario", "google calendar")):
        return True
    if re.search(r"\bagenda\b", norm) and not _has_any(norm, ("agenda de", "que tengo", "que hay")):
        return True
    return False


def interpret_user_intent(text, client_id, pending_state=None) -> dict[str, Any]:
    """
    Shadow-only Intent Interpreter v1.

    The interpreter returns strict JSON-compatible intent data. It never writes,
    schedules, deletes, confirms, or executes anything; deterministic runtime
    code remains responsible for validation, confirmation, and execution.
    """
    normalized = _normalize(str(text or ""))
    pending_type = _pending_type(pending_state)
    missing = _pending_missing_fields(pending_state)

    if "calendar_create" in pending_type and "time" in missing:
        time_value = _parse_followup_time(str(text or ""))
        fields = {"time": time_value} if time_value else {}
        return _result(
            "calendar_create_followup",
            confidence=0.92 if time_value else 0.55,
            fields=fields,
            missing_fields=[] if time_value else ["time"],
            normalized_user_text=normalized,
            route_hint="gcal_create_followup",
            requires_confirmation=True,
        )

    if _looks_like_calendar_create(normalized):
        fields, missing_fields = _calendar_fields(str(text or ""))
        return _result(
            "calendar_create",
            confidence=0.88 if missing_fields else 0.94,
            fields=fields,
            missing_fields=missing_fields,
            normalized_user_text=normalized,
            route_hint="gcal_create",
            requires_confirmation=True,
        )

    if _has_any(normalized, ("que tengo hoy", "que tengo manana", "que tengo para", "que tengo el lunes", "agenda de", "que hay en mi calendario")):
        return _result("agenda_query", confidence=0.94, normalized_user_text=normalized, route_hint="agenda_query")

    if _has_any(normalized, ("que recordatorios", "recordatorios activos", "mis recordatorios", "recordatorios vencidos")):
        return _result("reminder_list", confidence=0.93, normalized_user_text=normalized, route_hint="reminder_query")

    if re.search(r"\brecuerdame\b", normalized) or re.search(r"\brecordatorio\s+(?:para|de)\b", normalized):
        fields: dict[str, Any] = {}
        time_value = _extract_time(str(text or ""))
        if time_value:
            fields["time"] = time_value
        return _result("reminder_create", confidence=0.92, fields=fields, normalized_user_text=normalized, route_hint="reminder_create")

    if _has_any(normalized, ("que tareas", "tareas activas", "tareas pendientes", "tareas registrada", "tarea activa", "tareas activa")):
        return _result("task_list", confidence=0.94, normalized_user_text=normalized, route_hint="task_query")

    task_title = _extract_task_title(str(text or ""))
    if task_title or re.search(r"\b(registra|registrar|agrega|agregar|guarda|guardar|anota|anotar|crea|crear)\s+(?:una\s+)?tarea\b", normalized):
        fields = {"title": task_title, "action": task_title} if task_title else {}
        missing_fields = [] if task_title else ["title"]
        return _result(
            "task_create",
            confidence=0.92 if task_title else 0.70,
            fields=fields,
            missing_fields=missing_fields,
            normalized_user_text=normalized,
            route_hint="task_create",
        )

    if _has_any(normalized, ("que documentos tengo", "documentos tengo", "lista documentos", "inventario de documentos")):
        return _result("document_list", confidence=0.92, normalized_user_text=normalized, route_hint="document_inventory")

    if _has_any(normalized, ("caso del terreno", "que sabemos del caso", "datos de la finca", "datos de finca", "herederos", "finca")):
        return _result("case_status", confidence=0.88, normalized_user_text=normalized, route_hint="case_status")

    if _has_any(normalized, ("que sigue", "siguiente accion", "proxima accion", "next action", "next")):
        return _result("next_action", confidence=0.78, normalized_user_text=normalized, route_hint="next_action")

    return _result("unknown", confidence=0.25, normalized_user_text=normalized, route_hint="llm_fallback")
