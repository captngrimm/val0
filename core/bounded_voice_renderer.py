from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from core.case_workspace_qa import CasoFincaQAPacket, LEGAL_BOUNDARY, OCR_CAVEAT, render_case_qa_answer


DEFAULT_TONE_PROFILE = "karen_tany_warm_clear"
DEFAULT_MAX_LENGTH = 2200
FORBIDDEN_LEGAL_CLAIMS = (
    "legalmente significa que",
    "prueba definitivamente",
    "caso ganado",
    "caso perdido",
    "no necesitas abogada",
    "no necesitas abogado",
    "nora debe",
    "conclusion legal definitiva",
    "conclusión legal definitiva",
)
FORBIDDEN_INTERNAL_LEAKS = (
    "vfms:",
    "id tecnico",
    "id técnico",
    "source_type",
    "source_name",
    "document_id",
)
FORBIDDEN_QA_ACTION_CLAIMS = (
    "creé",
    "cree ",
    "eliminé",
    "elimine ",
    "agendé",
    "agende ",
    "moví",
    "movi ",
    "guardé",
    "guarde ",
    "borré",
    "borre ",
)


@dataclass(frozen=True)
class VoiceRenderPacket:
    client_id: str
    user_display_name: str
    tone_profile: str
    domain: str
    workspace_id: str
    workspace_title: str
    question_type: str
    user_question: str
    deterministic_answer: str
    facts: tuple[str, ...] = field(default_factory=tuple)
    uncertainty: tuple[str, ...] = field(default_factory=tuple)
    questions_for_nora: tuple[str, ...] = field(default_factory=tuple)
    pending_items: tuple[str, ...] = field(default_factory=tuple)
    next_actions: tuple[str, ...] = field(default_factory=tuple)
    selected_document: dict[str, Any] = field(default_factory=dict)
    required_boundaries: tuple[str, ...] = field(default_factory=lambda: (LEGAL_BOUNDARY,))
    forbidden_claims: tuple[str, ...] = field(default_factory=lambda: FORBIDDEN_LEGAL_CLAIMS)
    forbidden_terms: tuple[str, ...] = field(default_factory=lambda: FORBIDDEN_INTERNAL_LEAKS)
    action_claims_forbidden: bool = True
    ocr_caveat_required: bool = False
    max_length: int = DEFAULT_MAX_LENGTH
    emoji_density: str = "low-medium"


@dataclass(frozen=True)
class VoiceRenderValidation:
    ok: bool
    reasons: tuple[str, ...] = ()


def _norm(text: str) -> str:
    return str(text or "").casefold()


def _compact_items(values: tuple[str, ...] | list[str], *, limit: int = 5) -> tuple[str, ...]:
    return tuple(str(item).strip() for item in values if str(item).strip())[:limit]


def build_voice_packet_from_case_qa(
    packet: CasoFincaQAPacket,
    *,
    deterministic_answer: str | None = None,
    user_display_name: str = "Tany",
    tone_profile: str = DEFAULT_TONE_PROFILE,
    max_length: int = DEFAULT_MAX_LENGTH,
) -> VoiceRenderPacket:
    answer = deterministic_answer if deterministic_answer is not None else render_case_qa_answer(packet)
    selected_doc: dict[str, Any] = {}
    if packet.selected_document:
        selected_doc = {
            "visible_number": packet.selected_document_number,
            "title": packet.selected_document.title,
            "ocr_status": packet.selected_document.ocr_status,
            "summary_status": packet.selected_document.summary_status,
            "relevance": packet.selected_document.relevance,
            "include_internal_id": False,
        }
    return VoiceRenderPacket(
        client_id=packet.client_id,
        user_display_name=user_display_name,
        tone_profile=tone_profile,
        domain="caso_finca",
        workspace_id=packet.workspace_id,
        workspace_title=packet.workspace_title,
        question_type=packet.question_type,
        user_question=packet.user_question,
        deterministic_answer=answer,
        facts=_compact_items(packet.known_facts),
        uncertainty=_compact_items(packet.needs_confirmation),
        questions_for_nora=_compact_items(packet.questions_for_nora),
        pending_items=_compact_items(packet.pending_items),
        next_actions=_compact_items(packet.next_actions),
        selected_document=selected_doc,
        ocr_caveat_required=packet.uses_ocr_backed_reading,
        max_length=max_length,
    )


def build_voice_renderer_prompt(packet: VoiceRenderPacket) -> str:
    facts = "\n".join(f"- {item}" for item in packet.facts) or "- Sin hechos adicionales."
    uncertainty = "\n".join(f"- {item}" for item in packet.uncertainty) or "- Sin incertidumbres adicionales."
    boundaries = "\n".join(f"- {item}" for item in packet.required_boundaries)
    return (
        "You are Val rewriting a deterministic answer for Karen/Tany.\n"
        "Use Spanish.\n"
        "Use only the supplied packet.\n"
        "Do not add facts.\n"
        "Do not remove required boundaries.\n"
        "Do not change uncertainty into certainty.\n"
        "Do not give legal advice.\n"
        "Do not say Nora/la abogada is unnecessary.\n"
        "Do not execute or suggest that you executed any action.\n"
        "Do not mention internal IDs unless include_internal_id is true.\n"
        "If the packet is insufficient, keep the deterministic fallback.\n\n"
        f"tone_profile: {packet.tone_profile}\n"
        f"domain: {packet.domain}\n"
        f"workspace_title: {packet.workspace_title}\n"
        f"question_type: {packet.question_type}\n"
        f"user_question: {packet.user_question}\n\n"
        "facts:\n"
        f"{facts}\n\n"
        "uncertainty:\n"
        f"{uncertainty}\n\n"
        "required_boundaries:\n"
        f"{boundaries}\n\n"
        "deterministic_answer:\n"
        f"{packet.deterministic_answer}"
    )


def validate_voice_render_output(packet: VoiceRenderPacket, rendered_text: str) -> VoiceRenderValidation:
    text = str(rendered_text or "").strip()
    reasons: list[str] = []
    if not text:
        reasons.append("empty_output")
    if len(text) > int(packet.max_length or DEFAULT_MAX_LENGTH):
        reasons.append("too_long")

    lowered = _norm(text)
    for boundary in packet.required_boundaries:
        if boundary and _norm(boundary) not in lowered:
            reasons.append("missing_required_boundary")
            break

    if packet.ocr_caveat_required and _norm(OCR_CAVEAT) not in lowered:
        reasons.append("missing_ocr_caveat")

    for claim in packet.forbidden_claims:
        if claim and _norm(claim) in lowered:
            reasons.append(f"forbidden_claim:{claim}")
            break

    for term in packet.forbidden_terms:
        if term and _norm(term) in lowered:
            reasons.append(f"internal_leak:{term}")
            break

    if packet.action_claims_forbidden:
        for claim in FORBIDDEN_QA_ACTION_CLAIMS:
            if re.search(rf"\b{re.escape(claim)}\b", lowered):
                reasons.append(f"forbidden_action_claim:{claim}")
                break

    return VoiceRenderValidation(ok=not reasons, reasons=tuple(reasons))


def render_with_bounded_voice(
    packet: VoiceRenderPacket,
    *,
    renderer: Callable[[VoiceRenderPacket], str] | None = None,
    enabled: bool = False,
) -> str:
    if not enabled or renderer is None:
        return packet.deterministic_answer
    try:
        candidate = renderer(packet)
    except Exception:
        return packet.deterministic_answer
    validation = validate_voice_render_output(packet, candidate)
    if not validation.ok:
        return packet.deterministic_answer
    return str(candidate).strip()
