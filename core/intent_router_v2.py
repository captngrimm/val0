from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IntentCandidate:
    intent_type: str
    confidence: float
    source: str
    normalized_text: str
    reason: str
    client_id: str | None
    destructive: bool = False
    needs_confirmation: bool = False


@dataclass(frozen=True)
class IntentDecision:
    selected_intent: str
    confidence: float
    handler_hint: str
    reason: str
    blocked_by: str | None
    needs_confirmation: bool


PRIORITY_ORDER = (
    "pending action",
    "destructive confirmation",
    "direct utilities",
    "documents/OCR",
    "case/finca",
    "memory capture",
    "LLM fallback",
)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text or "").lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[¿?¡!.,:;]+", " ", text)
    text = re.sub(r"\b(?:vale|valeria|val|va\s+el|bal|pal)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _has_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _pending_state_type(pending_state: Any) -> str:
    if not pending_state:
        return ""
    if isinstance(pending_state, str):
        return pending_state
    if isinstance(pending_state, dict):
        return str(
            pending_state.get("intent_type")
            or pending_state.get("action_type")
            or pending_state.get("type")
            or "pending_action"
        )
    return "pending_action"


def _candidate(intent_type: str, confidence: float, source: str, normalized_text: str, reason: str, client_id: str | None, *, destructive: bool = False, needs_confirmation: bool = False) -> IntentCandidate:
    return IntentCandidate(
        intent_type=intent_type,
        confidence=float(confidence),
        source=source,
        normalized_text=normalized_text,
        reason=reason,
        client_id=client_id,
        destructive=destructive,
        needs_confirmation=needs_confirmation,
    )


def _decision(candidate: IntentCandidate, *, blocked_by: str | None = None) -> IntentDecision:
    return IntentDecision(
        selected_intent=candidate.intent_type,
        confidence=candidate.confidence,
        handler_hint=f"shadow:{candidate.intent_type}",
        reason=candidate.reason,
        blocked_by=blocked_by,
        needs_confirmation=candidate.needs_confirmation,
    )


def classify_intent_shadow(text, *, client_id=None, chat_id=None, pending_state=None) -> IntentDecision:
    """
    Shadow-only Intent Router v2 classifier.

    Priority model:
    1. Pending actions
    2. Destructive confirmations
    3. Direct utilities: agenda, Google Calendar, reminders, tasks
    4. Documents / OCR
    5. Case/finca/legal context
    6. Memory capture
    7. LLM fallback

    This function does not import handlers, call APIs, mutate state, or decide runtime routing.
    """
    normalized = _normalize(str(text or ""))
    client = str(client_id) if client_id is not None else None
    pending_type = _pending_state_type(pending_state)

    if pending_type:
        return _decision(_candidate(
            "pending_action_reply",
            0.99,
            "pending_state",
            normalized,
            f"pending action exists: {pending_type}",
            client,
            needs_confirmation="confirm" in pending_type or "delete" in pending_type,
        ))

    confirmation_words = {"si", "si confirma", "confirma", "confirmo", "dale", "correcto", "no", "cancelar", "dejalo"}
    if normalized in confirmation_words:
        return _decision(_candidate(
            "destructive_confirmation",
            0.90,
            "deterministic",
            normalized,
            "short confirmation/cancel phrase; should only be consumed with matching pending action",
            client,
            destructive=True,
            needs_confirmation=False,
        ))

    if _has_any(normalized, ("crea evento", "google calendar", "pon en mi calendario", "agrega al calendario")) or re.search(r"\bagenda\s+.+\b(?:manana|lunes|martes|miercoles|jueves|viernes|sabado|domingo)\b.+\b(?:a las|am|pm|\d)", normalized):
        return _decision(_candidate(
            "gcal_create",
            0.92,
            "deterministic",
            normalized,
            "matched Google Calendar event creation",
            client,
            needs_confirmation=True,
        ))

    if _has_any(normalized, ("que tengo manana", "que tengo hoy", "agenda de manana", "agenda para", "que tengo para el lunes", "que tengo el lunes", "que hay en mi calendario")):
        if not _has_any(normalized, ("agenda prueba", "agenda cita", "crea evento", "pon en mi calendario", "agrega al calendario")):
            return _decision(_candidate("agenda_query", 0.95, "deterministic", normalized, "matched agenda/calendar read query", client))

    if re.search(r"\b(elimina|eliminar|borra|borrar|cancela|cancelar|quita|quitar)\s+(?:el\s+)?(?:evento|evento de google calendar|compromiso)\s+(?:\d+|uno|dos|tres)\b", normalized):
        return _decision(_candidate(
            "gcal_delete",
            0.96,
            "deterministic",
            normalized,
            "matched numbered Google Calendar delete",
            client,
            destructive=True,
            needs_confirmation=True,
        ))

    if re.search(r"\b(elimina|eliminar|borra|borrar|cancela|cancelar|quita|quitar)\s+(?:el\s+)?recordatorio\s+(?:\d+|uno|dos|tres)\b", normalized):
        return _decision(_candidate(
            "reminder_delete",
            0.95,
            "deterministic",
            normalized,
            "matched numbered reminder delete",
            client,
            destructive=True,
            needs_confirmation=True,
        ))

    if re.search(r"\b(cambia|cambiar|mueve|mover)\s+(?:el\s+)?recordatorio\s+(?:\d+|uno|dos|tres)\b", normalized):
        return _decision(_candidate(
            "reminder_update",
            0.90,
            "deterministic",
            normalized,
            "matched numbered reminder update",
            client,
            destructive=False,
            needs_confirmation=True,
        ))

    if re.search(r"\brecuerdame\b", normalized) or re.search(r"\brecordatorio\s+(?:para|de)\b", normalized):
        return _decision(_candidate("reminder_create", 0.94, "deterministic", normalized, "matched reminder creation", client))

    if _has_any(normalized, ("que recordatorios tengo", "recordatorios de manana", "recordatorios vencidos", "recordatorios pasados")):
        return _decision(_candidate("reminder_query", 0.94, "deterministic", normalized, "matched reminder query", client))

    if re.search(r"\b(marca|marcar|completa|completar|cierra|cerrar)\s+(?:la\s+)?tarea\s+(?:\d+|uno|dos|tres)\b", normalized):
        return _decision(_candidate(
            "task_complete",
            0.95,
            "deterministic",
            normalized,
            "matched numbered task completion",
            client,
            destructive=False,
            needs_confirmation=False,
        ))

    if re.search(r"\b(elimina|eliminar|borra|borrar|quita|quitar|cancela|cancelar)\s+(?:la\s+)?tarea\s+(?:\d+|uno|dos|tres)\b", normalized):
        return _decision(_candidate(
            "task_delete",
            0.95,
            "deterministic",
            normalized,
            "matched numbered task delete",
            client,
            destructive=True,
            needs_confirmation=True,
        ))

    if re.search(r"\b(registra|registrar|agrega|agregar|guarda|guardar|anota|anotar|crea|crear)\s+(?:una\s+)?tarea\b", normalized) or re.search(r"\b(?:tengo\s+que|debo|hay\s+que)\b", normalized) or normalized.startswith("tarea "):
        return _decision(_candidate(
            "task_create",
            0.93,
            "deterministic",
            normalized,
            "matched explicit task creation",
            client,
        ))

    if _has_any(normalized, ("que tareas tengo", "tareas activas", "tareas pendientes", "tareas registrada", "tarea activa", "tareas activa")):
        return _decision(_candidate("task_query", 0.95, "deterministic", normalized, "matched task query", client))

    if _has_any(normalized, ("resume con ocr", "resumen con ocr", "haz ocr", "lee visualmente", "lectura visual")):
        return _decision(_candidate("document_ocr", 0.95, "deterministic", normalized, "matched explicit document OCR request", client))

    if _has_any(normalized, ("resume el ultimo documento", "resume documento", "resume el documento", "resumen del documento", "dame el resumen", "resume este documento", "que documentos tengo", "inventario de documentos")):
        return _decision(_candidate("document_summary", 0.90, "deterministic", normalized, "matched document summary/inventory request", client))

    if _has_any(normalized, ("caso del terreno", "finca", "herederos", "nora", "abogada", "estatus del caso", "que tengo del caso")):
        return _decision(_candidate("case_status", 0.86, "deterministic", normalized, "matched case/finca/legal context", client))

    if _has_any(normalized, ("guarda", "recuerda que", "anota", "nota")) and len(normalized) >= 12:
        return _decision(_candidate("memory_capture_candidate", 0.65, "deterministic", normalized, "possible memory capture after direct intents", client))

    return _decision(_candidate("llm_fallback", 0.30, "fallback", normalized, "no deterministic route matched; LLM fallback last", client))
