from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
import unicodedata


class ConfirmationDecision(str, Enum):
    CONFIRM = "confirm"
    CANCEL = "cancel"
    UNKNOWN = "unknown"
    EXPIRED = "expired"


@dataclass(frozen=True)
class PendingAction:
    action_id: str
    chat_id: int
    client_id: str
    action_type: str
    display_summary: str
    confirm_words: tuple[str, ...]
    cancel_words: tuple[str, ...]
    expires_at: datetime
    payload: dict = field(default_factory=dict)
    audit_metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "val0"
    sensitive_payload_keys: tuple[str, ...] = ()


_PENDING_ACTIONS: dict[str, PendingAction] = {}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def normalize_confirmation_text(text: str) -> str:
    normalized = (text or "").strip().lower()
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"[¿?¡!.,:;]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = re.sub(r"^(val|valeria|vale)\s+", "", normalized).strip()
    return normalized


def classify_confirmation_reply(
    text: str,
    action: PendingAction,
    now: datetime | None = None,
) -> ConfirmationDecision:
    current = _as_aware_utc(now or _now_utc())
    if _as_aware_utc(action.expires_at) <= current:
        return ConfirmationDecision.EXPIRED

    normalized = normalize_confirmation_text(text)
    confirm_words = {normalize_confirmation_text(word) for word in action.confirm_words}
    cancel_words = {normalize_confirmation_text(word) for word in action.cancel_words}

    if normalized in confirm_words:
        return ConfirmationDecision.CONFIRM
    if normalized in cancel_words:
        return ConfirmationDecision.CANCEL
    return ConfirmationDecision.UNKNOWN


def create_pending_action(action: PendingAction) -> PendingAction:
    _PENDING_ACTIONS[action.action_id] = action
    return action


def get_pending_action(
    chat_id: int,
    action_type: str | None = None,
    client_id: str | None = None,
    now: datetime | None = None,
) -> PendingAction | None:
    current = _as_aware_utc(now or _now_utc())
    matches = []

    for action in _PENDING_ACTIONS.values():
        if int(action.chat_id) != int(chat_id):
            continue
        if action_type is not None and action.action_type != action_type:
            continue
        if client_id is not None and action.client_id != client_id:
            continue
        if _as_aware_utc(action.expires_at) <= current:
            continue
        matches.append(action)

    if not matches:
        return None

    matches.sort(key=lambda action: _as_aware_utc(action.created_at), reverse=True)
    return matches[0]


def clear_pending_action(action_id: str) -> None:
    _PENDING_ACTIONS.pop(action_id, None)


def expire_pending_actions(now: datetime | None = None) -> int:
    current = _as_aware_utc(now or _now_utc())
    expired_ids = [
        action_id
        for action_id, action in _PENDING_ACTIONS.items()
        if _as_aware_utc(action.expires_at) <= current
    ]
    for action_id in expired_ids:
        _PENDING_ACTIONS.pop(action_id, None)
    return len(expired_ids)


def safe_audit_payload(action: PendingAction) -> dict:
    sensitive = set(action.sensitive_payload_keys or ())
    safe_payload = {
        key: ("[redacted]" if key in sensitive else value)
        for key, value in (action.payload or {}).items()
    }
    return {
        "action_id": action.action_id,
        "chat_id": int(action.chat_id),
        "client_id": action.client_id,
        "action_type": action.action_type,
        "display_summary": action.display_summary,
        "expires_at": _as_aware_utc(action.expires_at).isoformat(),
        "created_at": _as_aware_utc(action.created_at).isoformat(),
        "created_by": action.created_by,
        "payload": safe_payload,
        "audit_metadata": dict(action.audit_metadata or {}),
    }


def render_confirmation_prompt(action: PendingAction) -> str:
    confirm_hint = action.confirm_words[0] if action.confirm_words else "sí"
    cancel_hint = action.cancel_words[0] if action.cancel_words else "cancelar"
    return (
        f"{action.display_summary}\n\n"
        "¿Confirmas?\n"
        f"Respóndeme: “{confirm_hint}” o “{cancel_hint}”."
    )
