#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.document_summary_queries import (  # noqa: E402
    _build_ocr_summary_reply,
    _build_specific_doc_summary_reply,
    _generate_specific_doc_summary_text,
    _render_combined_legal_documents_summary,
)


STALE_PHRASES = ("bajar de peso", "task_high", "memoria pura")
FAKE_AUTHORITY = (
    "soy tu abogada",
    "conclusión legal definitiva",
    "dictamen legal",
    "asesoría legal definitiva",
)


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def _legal_doc_meta() -> dict:
    return {
        "filename": "Auto_secuestro_Embargo.pdf",
        "ingest_id": "20260531_000001",
        "caption": "Val, transcribe este documento y hazme un resumen",
        "state": "texto extraído e indexado",
        "text": (
            "Juzgado Primero de Circuito Civil. Finca No. 10082. "
            "Se menciona el Oficio No. 792 dirigido al Registro Público. "
            "Auto No. 629 fechado 29 de abril de 2024. "
            "Carmen Montenegro de Sandino aparece mencionada."
        ),
    }


def _assert_warm_legal_frame(reply: str) -> None:
    assert_contains(reply, "Tany, te lo traduzco a útil", "warm Tany framing")
    assert_contains(reply, "Lo importante", "important section")
    assert_contains(reply, "Qué puede significar", "meaning section")
    assert_contains(reply, "Qué falta confirmar", "confirm section")
    assert_contains(reply, "Preguntas para Nora", "Nora questions section")
    assert_contains(reply, "Próximo paso sugerido", "next step section")
    assert_contains(reply, "no una decisión legal", "legal certainty boundary")
    assert_contains(reply, "Nora/la abogada", "lawyer review framing")
    for phrase in STALE_PHRASES:
        assert_not_contains(reply, phrase, f"no stale contamination: {phrase}")
    for phrase in FAKE_AUTHORITY:
        assert_not_contains(reply, phrase, f"no fake legal authority: {phrase}")


def test_specific_document_summary_warmth() -> None:
    generated = _generate_specific_doc_summary_text(_legal_doc_meta())
    reply = _build_specific_doc_summary_reply({**_legal_doc_meta(), "saved_summary": generated})

    _assert_warm_legal_frame(reply)
    assert_contains(reply, "Finca No. 10082", "grounded finca fact preserved")
    assert_contains(reply, "Oficio No. 792", "grounded oficio fact preserved")
    assert_contains(reply, "Registro Público", "grounded registry fact preserved")
    assert_contains(reply, "Siguientes acciones útiles", "existing next-action block preserved")
    assert_true(reply.count("no sustituye revisión legal o profesional") == 1, "generic legal limit remains single")


def test_legacy_saved_summary_gets_warm_frame() -> None:
    reply = _build_specific_doc_summary_reply({
        **_legal_doc_meta(),
        "saved_summary": "📋 Resumen claro\n- Finca No. 10082.\n- Oficio No. 792.",
    })

    _assert_warm_legal_frame(reply)
    assert_contains(reply, "- Finca No. 10082.", "legacy saved fact preserved")
    assert_contains(reply, "- Oficio No. 792.", "legacy saved fact preserved")


def test_ocr_summary_warmth_keeps_ocr_limits() -> None:
    reply = _build_ocr_summary_reply(_legal_doc_meta(), _legal_doc_meta()["text"], pages=3)

    _assert_warm_legal_frame(reply)
    assert_contains(reply, "Resumen generado con OCR/lectura visual del PDF. Es una primera pasada", "OCR first-pass framing")
    assert_contains(reply, "Nota: por ahora revisé hasta las primeras 3 páginas.", "OCR page limit")
    assert_contains(reply, "Puede tener errores de OCR", "OCR error boundary")
    assert_contains(reply, "no sustituye la revisión de la abogada o del documento original", "OCR legal boundary")


def test_combined_legal_summary_uses_tany_not_legacy_vocative() -> None:
    reply = _render_combined_legal_documents_summary("KAREN-LAND-001", [_legal_doc_meta()])

    assert_contains(reply, "Tany, te lo traduzco a útil", "combined legal summary Tany framing")
    assert_contains(reply, "Lo importante", "combined important section")
    assert_contains(reply, "Qué falta confirmar", "combined confirm section")
    assert_contains(reply, "Preguntas para Nora", "combined Nora section")
    legacy_vocative = "Insan" + "ity"
    assert_not_contains(reply, legacy_vocative, "combined legal summary avoids legacy vocative")
    for phrase in STALE_PHRASES:
        assert_not_contains(reply, phrase, f"combined no stale contamination: {phrase}")


def main() -> int:
    test_specific_document_summary_warmth()
    test_legacy_saved_summary_gets_warm_frame()
    test_ocr_summary_warmth_keeps_ocr_limits()
    test_combined_legal_summary_uses_tany_not_legacy_vocative()
    print("PASS: Karen document summary warmth smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
