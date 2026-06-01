from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IntentObservation:
    chat_id: int | None
    message_id: int | str | None
    predicted_intent: str = ""
    actual_intent: str = ""
    confidence: float = 0.0
    handler_name: str = ""
    reason: str = ""
    match: bool | None = None


_OBSERVATIONS: dict[tuple[str, str], dict[str, Any]] = {}


def _key(chat_id, message_id) -> tuple[str, str]:
    return (str(chat_id or "unknown"), str(message_id or "unknown"))


def record_predicted_intent(chat_id, message_id, decision) -> IntentObservation:
    try:
        key = _key(chat_id, message_id)
        item = dict(_OBSERVATIONS.get(key) or {})
        item.update({
            "chat_id": chat_id,
            "message_id": message_id,
            "predicted_intent": str(getattr(decision, "selected_intent", "") or ""),
            "confidence": float(getattr(decision, "confidence", 0.0) or 0.0),
            "predicted_reason": str(getattr(decision, "reason", "") or ""),
            "updated_at": time.time(),
        })
        _OBSERVATIONS[key] = item
        return _observation_from_item(item)
    except Exception:
        return IntentObservation(chat_id=chat_id, message_id=message_id)


def record_actual_intent(chat_id, message_id, actual_intent, handler_name, reason: str = "") -> IntentObservation:
    try:
        key = _key(chat_id, message_id)
        item = dict(_OBSERVATIONS.get(key) or {})
        item.update({
            "chat_id": chat_id,
            "message_id": message_id,
            "actual_intent": str(actual_intent or ""),
            "handler_name": str(handler_name or ""),
            "actual_reason": str(reason or ""),
            "updated_at": time.time(),
        })
        _OBSERVATIONS[key] = item
        return _observation_from_item(item)
    except Exception:
        return IntentObservation(
            chat_id=chat_id,
            message_id=message_id,
            actual_intent=str(actual_intent or ""),
            handler_name=str(handler_name or ""),
            reason=str(reason or ""),
        )


def _observation_from_item(item: dict[str, Any]) -> IntentObservation:
    predicted = str(item.get("predicted_intent") or "")
    actual = str(item.get("actual_intent") or "")
    match = (predicted == actual) if predicted and actual else None
    return IntentObservation(
        chat_id=item.get("chat_id"),
        message_id=item.get("message_id"),
        predicted_intent=predicted,
        actual_intent=actual,
        confidence=float(item.get("confidence") or 0.0),
        handler_name=str(item.get("handler_name") or ""),
        reason=str(item.get("actual_reason") or item.get("predicted_reason") or ""),
        match=match,
    )


def render_intent_observation(observation: IntentObservation) -> str:
    return (
        f"predicted={observation.predicted_intent or '-'} "
        f"actual={observation.actual_intent or '-'} "
        f"match={observation.match} "
        f"confidence={observation.confidence:.2f} "
        f"handler={observation.handler_name or '-'}"
    )


def clear_observations() -> None:
    _OBSERVATIONS.clear()
