from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Iterable


class ResponseType(str, Enum):
    INFO = "info"
    DAILY_OPERATOR = "daily_operator"
    TIMELINE = "timeline"
    DOCUMENT_INVENTORY = "document_inventory"
    DOCUMENT_SUMMARY = "document_summary"
    CONFIRMATION = "confirmation"
    CALENDAR = "calendar"
    REMINDER = "reminder"
    TECHNICAL = "technical"
    ERROR = "error"


class StyleMode(str, Enum):
    NONE = "none"
    LIGHT = "light"
    WARM = "warm"
    PLAYFUL = "playful"


class SafetyFlag(str, Enum):
    NO_POLISH = "no_polish"
    LEGAL_SENSITIVE = "legal_sensitive"
    CONFIRMATION_REQUIRED = "confirmation_required"
    SOURCE_REQUIRED = "source_required"
    TECHNICAL_CONTENT = "technical_content"
    ACTION_SENSITIVE = "action_sensitive"


RESPONSE_TYPES = {item.value for item in ResponseType}
STYLE_MODES = {item.value for item in StyleMode}
SAFETY_FLAGS = {item.value for item in SafetyFlag}

ALWAYS_DENY_FLAGS = {
    SafetyFlag.NO_POLISH.value,
    SafetyFlag.TECHNICAL_CONTENT.value,
    SafetyFlag.CONFIRMATION_REQUIRED.value,
    SafetyFlag.ACTION_SENSITIVE.value,
}

POLISHABLE_TYPES = {
    ResponseType.DAILY_OPERATOR.value,
    ResponseType.INFO.value,
}


@dataclass(frozen=True)
class ResponseEnvelope:
    response_id: str
    client_id: str
    source_route: str
    response_type: str
    factual_payload: dict[str, Any] = field(default_factory=dict)
    rendered_text: str = ""
    allowed_style_mode: str = StyleMode.NONE.value
    legal_boundary: str = ""
    safety_flags: tuple[str, ...] = ()
    provenance: tuple[dict[str, Any], ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


def safe_response_type(value: str | None) -> str:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return raw if raw in RESPONSE_TYPES else ResponseType.INFO.value


def safe_style_mode(value: str | None) -> str:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return raw if raw in STYLE_MODES else StyleMode.NONE.value


def _safe_flags(values: Iterable[Any] | None) -> tuple[str, ...]:
    seen = set()
    out = []
    for value in values or ():
        raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
        if raw not in SAFETY_FLAGS or raw in seen:
            continue
        seen.add(raw)
        out.append(raw)
    return tuple(out)


def _safe_provenance(values: Iterable[Any] | None) -> tuple[dict[str, Any], ...]:
    out = []
    for value in values or ():
        if not isinstance(value, dict):
            continue
        item = {}
        for key in ("source_type", "source_id", "document_id", "ingest_id", "confidence"):
            if key in value and value.get(key) is not None:
                item[key] = value.get(key)
        if item:
            out.append(item)
    return tuple(out)


def _utc_now_text() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_response_envelope(
    *,
    response_id: str = "",
    client_id: str = "",
    source_route: str = "",
    response_type: str = ResponseType.INFO.value,
    factual_payload: dict[str, Any] | None = None,
    rendered_text: str = "",
    allowed_style_mode: str = StyleMode.NONE.value,
    legal_boundary: str = "",
    safety_flags: Iterable[Any] | None = None,
    provenance: Iterable[Any] | None = None,
    created_at: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ResponseEnvelope:
    rid = str(response_id or "").strip()
    if not rid:
        rid = f"response:{_utc_now_text()}"

    return ResponseEnvelope(
        response_id=rid,
        client_id=str(client_id or "").strip(),
        source_route=str(source_route or "").strip(),
        response_type=safe_response_type(response_type),
        factual_payload=dict(factual_payload or {}),
        rendered_text=str(rendered_text or ""),
        allowed_style_mode=safe_style_mode(allowed_style_mode),
        legal_boundary=str(legal_boundary or "").strip(),
        safety_flags=_safe_flags(safety_flags),
        provenance=_safe_provenance(provenance),
        created_at=str(created_at or _utc_now_text()),
        metadata=dict(metadata or {}),
    )


def add_safety_flag(envelope: ResponseEnvelope, flag: str) -> ResponseEnvelope:
    new_flags = _safe_flags((*envelope.safety_flags, flag))
    return replace(envelope, safety_flags=new_flags)


def _operation_text(envelope: ResponseEnvelope) -> str:
    operation = str(envelope.metadata.get("operation") or "").strip().lower()
    action_type = str(envelope.metadata.get("action_type") or "").strip().lower()
    route = str(envelope.source_route or "").strip().lower()
    payload_action = str(envelope.factual_payload.get("action") or "").strip().lower()
    return " ".join([operation, action_type, route, payload_action])


def _has_provenance(envelope: ResponseEnvelope) -> bool:
    return bool(envelope.provenance)


def should_allow_polish(envelope: ResponseEnvelope) -> bool:
    style = safe_style_mode(envelope.allowed_style_mode)
    if style == StyleMode.NONE.value:
        return False

    response_type = safe_response_type(envelope.response_type)
    flags = set(_safe_flags(envelope.safety_flags))
    if flags & ALWAYS_DENY_FLAGS:
        return False

    op_text = _operation_text(envelope)
    if response_type == ResponseType.CONFIRMATION.value:
        return False
    if response_type == ResponseType.TECHNICAL.value:
        return False
    if response_type == ResponseType.CALENDAR.value and any(word in op_text for word in ("create", "delete", "crear", "borrar", "eliminar")):
        return False
    if response_type == ResponseType.REMINDER.value and any(word in op_text for word in ("create", "delete", "update", "cancel", "crear", "borrar", "actualizar", "cancelar")):
        return False
    if response_type == ResponseType.DOCUMENT_SUMMARY.value and not _has_provenance(envelope):
        return False

    requires_source = (
        SafetyFlag.SOURCE_REQUIRED.value in flags
        or SafetyFlag.LEGAL_SENSITIVE.value in flags
        or response_type in {ResponseType.DOCUMENT_SUMMARY.value, ResponseType.TIMELINE.value}
    )
    if requires_source and not _has_provenance(envelope):
        return False

    if SafetyFlag.LEGAL_SENSITIVE.value in flags and style not in {StyleMode.LIGHT.value}:
        return False

    if response_type not in POLISHABLE_TYPES and not (
        SafetyFlag.LEGAL_SENSITIVE.value in flags and style == StyleMode.LIGHT.value
    ):
        return False

    return True


def render_envelope_text(envelope: ResponseEnvelope) -> str:
    text = str(envelope.rendered_text or "")
    boundary = str(envelope.legal_boundary or "").strip()
    if boundary and boundary not in text:
        text = (text.rstrip() + "\n\n" + boundary).strip()
    return text


def envelope_summary(envelope: ResponseEnvelope) -> dict[str, Any]:
    return {
        "response_id": envelope.response_id,
        "client_id": envelope.client_id,
        "source_route": envelope.source_route,
        "response_type": safe_response_type(envelope.response_type),
        "allowed_style_mode": safe_style_mode(envelope.allowed_style_mode),
        "safety_flags": list(envelope.safety_flags),
        "provenance_count": len(envelope.provenance),
        "has_factual_payload": bool(envelope.factual_payload),
        "rendered_text_length": len(envelope.rendered_text or ""),
        "created_at": envelope.created_at,
        "polish_allowed": should_allow_polish(envelope),
    }


def _line_set(text: str) -> set[str]:
    return {line.strip() for line in str(text or "").splitlines() if line.strip()}


def _protected_lines(text: str) -> tuple[str, ...]:
    protected = []
    markers = (
        "vfms",
        "fuente",
        "source",
        "case:",
        "id:",
        "fecha",
        "date",
        "creé",
        "cree",
        "borré",
        "borre",
        "guardé",
        "guarde",
        "confirm",
        "cancel",
        "no sustituye",
        "lectura solamente",
    )
    for line in str(text or "").splitlines():
        clean = line.strip()
        low = clean.lower()
        if clean and any(marker in low for marker in markers):
            protected.append(clean)
    return tuple(protected)


def _fact_strings(payload: dict[str, Any]) -> tuple[str, ...]:
    facts = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for child in value.values():
                walk(child)
            return
        if isinstance(value, (list, tuple, set)):
            for child in value:
                walk(child)
            return
        if value is None or isinstance(value, bool):
            return
        text = str(value).strip()
        if len(text) >= 4:
            facts.append(text)

    walk(payload or {})
    seen = set()
    out = []
    for fact in facts:
        if fact in seen:
            continue
        seen.add(fact)
        out.append(fact)
    return tuple(out)


def _has_new_action_claim(original: str, polished: str) -> bool:
    original_low = str(original or "").lower()
    polished_low = str(polished or "").lower()
    action_claims = (
        "creé",
        "cree",
        "he creado",
        "borré",
        "borre",
        "he borrado",
        "eliminé",
        "elimine",
        "guardé",
        "guarde",
        "envié",
        "envie",
        "mandé",
        "mande",
        "actualicé",
        "actualice",
        "cancelé",
        "cancele",
    )
    return any(claim in polished_low and claim not in original_low for claim in action_claims)


def _has_new_source_claim(original: str, polished: str) -> bool:
    original_low = str(original or "").lower()
    polished_low = str(polished or "").lower()
    source_claims = (
        "según",
        "segun",
        "fuente:",
        "source:",
        "vfms",
        "documento",
        "expediente",
        "registro público",
        "registro publico",
    )
    return any(claim in polished_low and claim not in original_low for claim in source_claims)


def compare_factual_payload_preserved(original: ResponseEnvelope | str, polished: str) -> bool:
    if isinstance(original, ResponseEnvelope):
        original_text = render_envelope_text(original)
        facts = _fact_strings(original.factual_payload)
    else:
        original_text = str(original or "")
        facts = ()

    polished_text = str(polished or "")
    if not original_text.strip():
        return True

    for fact in facts:
        if fact not in original_text:
            continue
        if fact not in polished_text:
            return False

    for line in _protected_lines(original_text):
        if line not in _line_set(polished_text):
            return False

    return True


def apply_safe_warmth(envelope: ResponseEnvelope, text: str) -> str:
    deterministic = str(text or "")
    if not should_allow_polish(envelope):
        return deterministic

    intro, closing = _warmth_lines(envelope)
    parts = []
    if intro and intro not in deterministic:
        parts.append(intro)
        parts.append("")
    parts.append(deterministic.strip())
    if closing and closing not in deterministic:
        parts.append("")
        parts.append(closing)
    return "\n".join(parts).strip()


def _warmth_lines(envelope: ResponseEnvelope) -> tuple[str, str]:
    style = safe_style_mode(envelope.allowed_style_mode)
    response_type = safe_response_type(envelope.response_type)

    intro = ""
    closing = ""
    if response_type == ResponseType.DAILY_OPERATOR.value:
        intro = "Te lo ordeno en corto."
        if str(envelope.metadata.get("mode") or "").strip().lower() == "compact":
            closing = "Siguiente paso: empieza por el pendiente próximo o pide el resumen completo si quieres más contexto."
        else:
            closing = "Siguiente paso: toma primero lo que aparece como sugerido."
    elif response_type == ResponseType.INFO.value:
        if style in {StyleMode.LIGHT.value, StyleMode.WARM.value, StyleMode.PLAYFUL.value}:
            intro = "Claro. Esto es lo que tengo."
            closing = "Lo mantengo simple para no mezclar cosas."
    return intro, closing


def validate_polished_text(envelope: ResponseEnvelope, text: str) -> bool:
    deterministic = render_envelope_text(envelope)
    polished = str(text or "")

    if not should_allow_polish(envelope):
        return polished == deterministic
    if not deterministic.strip():
        return polished == deterministic
    if deterministic.strip() not in polished:
        return False
    if not compare_factual_payload_preserved(envelope, polished):
        return False
    if envelope.legal_boundary and envelope.legal_boundary not in polished:
        return False
    allowed_added = {line for line in _warmth_lines(envelope) if line}
    original_lines = _line_set(deterministic)
    for line in _line_set(polished):
        if line not in original_lines and line not in allowed_added:
            return False
    if _has_new_action_claim(deterministic, polished):
        return False
    if SafetyFlag.LEGAL_SENSITIVE.value in envelope.safety_flags or envelope.response_type == ResponseType.DOCUMENT_SUMMARY.value:
        if _has_new_source_claim(deterministic, polished):
            return False

    date_tokens = re.findall(r"\b(?:19|20)\d{2}(?:-\d{2}(?:-\d{2})?)?\b", deterministic)
    for token in date_tokens:
        if token not in polished:
            return False

    return True


def render_polished_fixture_response(envelope: ResponseEnvelope) -> str:
    deterministic = render_envelope_text(envelope)
    if not should_allow_polish(envelope):
        return deterministic

    polished = apply_safe_warmth(envelope, deterministic)
    if validate_polished_text(envelope, polished):
        return polished
    return deterministic
