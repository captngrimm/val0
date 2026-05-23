from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
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
