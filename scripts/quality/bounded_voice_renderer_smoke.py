#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.bounded_voice_renderer import (  # noqa: E402
    OCR_CAVEAT,
    build_voice_packet_from_case_qa,
    build_voice_renderer_prompt,
    generate_shadow_voice_candidate,
    render_with_bounded_voice,
    validate_voice_render_output,
)
from core.case_workspace_qa import (  # noqa: E402
    LEGAL_BOUNDARY,
    build_case_qa_packet,
    render_case_qa_answer,
)


KAREN_CLIENT_ID = "kar" + "en"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_equal(left: str, right: str, label: str) -> None:
    if left != right:
        raise AssertionError(f"{label}: expected {right!r}, got {left!r}")


def _base_packet():
    case_packet = build_case_qa_packet("Val, qué sabes del caso?", client_id=KAREN_CLIENT_ID)
    assert_true(case_packet is not None, "base case packet exists")
    deterministic = render_case_qa_answer(case_packet)
    return build_voice_packet_from_case_qa(case_packet, deterministic_answer=deterministic)


def _ocr_packet():
    case_packet = build_case_qa_packet("Val, ese primer documento, por qué importa?", client_id=KAREN_CLIENT_ID)
    assert_true(case_packet is not None and case_packet.uses_ocr_backed_reading, "OCR case packet exists")
    deterministic = render_case_qa_answer(case_packet)
    return build_voice_packet_from_case_qa(case_packet, deterministic_answer=deterministic)


def test_prompt_contract() -> None:
    packet = _base_packet()
    prompt = build_voice_renderer_prompt(packet)
    assert_contains(prompt, "Use only the supplied packet", "prompt forbids extra facts")
    assert_contains(prompt, "Do not execute", "prompt forbids execution")
    assert_contains(prompt, "Do not give legal advice", "prompt forbids legal advice")
    assert_contains(prompt, "deterministic_answer", "prompt includes deterministic fallback")


def test_validation_and_fallbacks() -> None:
    packet = _base_packet()
    deterministic = packet.deterministic_answer
    safe = (
        "Tany, te lo pongo en limpio sobre Caso Finca.\n\n"
        "Lo que sé\n"
        "1. Hay documentos registrados y puntos por confirmar.\n\n"
        f"{LEGAL_BOUNDARY}"
    )
    assert_true(validate_voice_render_output(packet, safe).ok, "safe rendered output passes")
    assert_equal(
        render_with_bounded_voice(packet, renderer=lambda _packet: safe, enabled=True),
        safe,
        "safe rendered output returned",
    )

    missing_boundary = "Tany, te lo pongo en limpio sobre Caso Finca."
    assert_true(not validate_voice_render_output(packet, missing_boundary).ok, "missing legal boundary fails")
    assert_equal(
        render_with_bounded_voice(packet, renderer=lambda _packet: missing_boundary, enabled=True),
        deterministic,
        "missing boundary falls back",
    )

    legal_certainty = f"Esto prueba definitivamente el caso.\n\n{LEGAL_BOUNDARY}"
    assert_true(not validate_voice_render_output(packet, legal_certainty).ok, "legal certainty fails")
    assert_equal(
        render_with_bounded_voice(packet, renderer=lambda _packet: legal_certainty, enabled=True),
        deterministic,
        "legal certainty falls back",
    )

    internal_leak = f"El documento vfms:20260531_000001 tiene ID técnico del documento.\n\n{LEGAL_BOUNDARY}"
    assert_true(not validate_voice_render_output(packet, internal_leak).ok, "internal leak fails")
    assert_equal(
        render_with_bounded_voice(packet, renderer=lambda _packet: internal_leak, enabled=True),
        deterministic,
        "internal leak falls back",
    )

    action_claim = f"Listo, agendé y guardé cambios del Caso Finca.\n\n{LEGAL_BOUNDARY}"
    assert_true(not validate_voice_render_output(packet, action_claim).ok, "action claim fails")
    assert_equal(
        render_with_bounded_voice(packet, renderer=lambda _packet: action_claim, enabled=True),
        deterministic,
        "action claim falls back",
    )

    assert_equal(render_with_bounded_voice(packet, renderer=lambda _packet: safe, enabled=False), deterministic, "disabled renderer falls back")
    assert_equal(render_with_bounded_voice(packet, renderer=lambda _packet: (_ for _ in ()).throw(RuntimeError("nope")), enabled=True), deterministic, "renderer exception falls back")


def test_shadow_candidate_generation() -> None:
    packet = _base_packet()
    deterministic = packet.deterministic_answer
    safe = (
        "Tany, va en limpio y sin drama mágico: Caso Finca tiene piezas útiles, "
        "pero hay cosas que confirmar.\n\n"
        f"{LEGAL_BOUNDARY}"
    )
    result = generate_shadow_voice_candidate(packet, renderer=lambda _packet: safe)
    assert_equal(result.validation_status, "accepted_shadow_only", "safe shadow status")
    assert_equal(result.candidate_answer or "", safe, "safe shadow candidate recorded")
    assert_equal(result.user_facing_answer, deterministic, "safe shadow remains deterministic-facing")

    unsafe = f"Esto prueba definitivamente el caso.\n\n{LEGAL_BOUNDARY}"
    rejected = generate_shadow_voice_candidate(packet, renderer=lambda _packet: unsafe)
    assert_equal(rejected.validation_status, "rejected", "unsafe shadow rejected")
    assert_contains(rejected.rejection_reason or "", "forbidden_claim", "unsafe shadow reason")
    assert_equal(rejected.user_facing_answer, deterministic, "unsafe shadow remains deterministic-facing")

    missing_boundary = generate_shadow_voice_candidate(packet, renderer=lambda _packet: "Tany, te lo resumo.")
    assert_equal(missing_boundary.validation_status, "rejected", "missing boundary rejected")
    assert_contains(missing_boundary.rejection_reason or "", "missing_required_boundary", "missing boundary reason")

    leak = generate_shadow_voice_candidate(
        packet,
        renderer=lambda _packet: f"Documento vfms:20260531_000001.\n\n{LEGAL_BOUNDARY}",
    )
    assert_equal(leak.validation_status, "rejected", "internal leak rejected")
    assert_contains(leak.rejection_reason or "", "internal_leak", "internal leak reason")

    action = generate_shadow_voice_candidate(
        packet,
        renderer=lambda _packet: f"Tany, guardé el resumen y agendé la revisión.\n\n{LEGAL_BOUNDARY}",
    )
    assert_equal(action.validation_status, "rejected", "action claim rejected")
    assert_contains(action.rejection_reason or "", "forbidden_action_claim", "action claim reason")

    no_renderer = generate_shadow_voice_candidate(packet)
    assert_equal(no_renderer.validation_status, "renderer_unavailable", "missing renderer status")
    assert_equal(no_renderer.user_facing_answer, deterministic, "missing renderer deterministic-facing")

    exception = generate_shadow_voice_candidate(
        packet,
        renderer=lambda _packet: (_ for _ in ()).throw(RuntimeError("fake renderer down")),
    )
    assert_equal(exception.validation_status, "renderer_exception", "renderer exception status")
    assert_contains(exception.rejection_reason or "", "RuntimeError", "renderer exception reason")
    assert_equal(exception.user_facing_answer, deterministic, "exception deterministic-facing")


def test_ocr_caveat_required() -> None:
    packet = _ocr_packet()
    deterministic = packet.deterministic_answer
    missing_ocr = (
        "Tany, el documento 1 importa porque tiene lectura disponible.\n\n"
        f"{LEGAL_BOUNDARY}"
    )
    assert_true(not validate_voice_render_output(packet, missing_ocr).ok, "missing OCR caveat fails")
    assert_equal(
        render_with_bounded_voice(packet, renderer=lambda _packet: missing_ocr, enabled=True),
        deterministic,
        "missing OCR caveat falls back",
    )
    safe_ocr = (
        "Tany, el documento 1 importa como punto de partida de Caso Finca.\n\n"
        f"{OCR_CAVEAT}\n"
        f"{LEGAL_BOUNDARY}"
    )
    assert_true(validate_voice_render_output(packet, safe_ocr).ok, "OCR-safe output passes")
    result = generate_shadow_voice_candidate(packet, renderer=lambda _packet: missing_ocr)
    assert_equal(result.validation_status, "rejected", "OCR shadow missing caveat rejected")
    assert_contains(result.rejection_reason or "", "missing_ocr_caveat", "OCR missing caveat reason")
    assert_equal(result.user_facing_answer, deterministic, "OCR missing caveat deterministic-facing")


def main() -> int:
    test_prompt_contract()
    test_validation_and_fallbacks()
    test_shadow_candidate_generation()
    test_ocr_caveat_required()
    print("PASS: bounded voice renderer smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
