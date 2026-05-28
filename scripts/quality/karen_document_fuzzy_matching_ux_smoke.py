#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.document_summary_queries import (  # noqa: E402
    _build_specific_doc_summary_reply,
    _doc_match_score,
    _doc_match_keys,
    _normalize_doc_name,
    _render_ambiguous_document_matches,
    render_document_naming_metadata_suggestion,
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


def _agi_doc() -> dict:
    return {
        "filename": "Agi.pdf",
        "ingest_id": "20260528_000002",
        "state": "texto extraído e indexado; resumen disponible",
        "saved_summary": "📋 Resumen claro\n- El documento habla de AGI, predicciones y timelines para 2028 y 2030.",
        "text": (
            "AGI predictions and AI timeline. "
            "The document discusses artificial general intelligence, forecasts, 2028, and 2030."
        ),
    }


def _six_doc() -> dict:
    return {
        "filename": "six_pdf.pdf",
        "ingest_id": "20260528_000001",
        "state": "texto extraído e indexado; resumen disponible",
        "saved_summary": "📋 Resumen claro\n- Se menciona Finca No. 10082.",
        "text": "Finca No. 10082. Auto No. 629 fechado 29 de abril de 2024.",
    }


def test_fuzzy_doc_name_keys_match_human_phrases() -> None:
    agi = _agi_doc()
    six = _six_doc()

    for query in ("agi.pdf", "agi pdf", "Agi.pdf", "AGI PDF", "agi", "Agi"):
        assert_true(_doc_match_score(_doc_match_keys(query), agi) > 0, f"{query} matches Agi.pdf")

    for query in ("six_pdf.pdf", "six pdf", "six-pdf", "sixpdf"):
        assert_true(_doc_match_score(_doc_match_keys(query), six) > 0, f"{query} matches six_pdf.pdf")

    assert_true(_normalize_doc_name("agi pdf") == _normalize_doc_name("Agi.pdf"), "agi pdf normalizes to Agi.pdf")


def test_summary_response_is_clean_not_inventory() -> None:
    reply = _build_specific_doc_summary_reply(_agi_doc())
    assert_not_contains(reply, "📎 Documentos registrados", "summary is not inventory")
    assert_contains(reply, "📋 Resumen claro", "summary header kept")
    assert_true(reply.count("- ") <= 8, "summary is not a data wall")


def test_naming_response_for_agi_is_general_not_finca() -> None:
    rendered = render_document_naming_metadata_suggestion(_agi_doc(), case_id="KAREN-LAND-001")
    assert_contains(rendered, "AGI_Predicciones_y_Timeline_2028_2030", "AGI suggested name")
    assert_contains(rendered, "AGI", "AGI tag")
    assert_contains(rendered, "inteligencia artificial", "AI tag")
    assert_contains(rendered, "predicciones", "prediction tag")
    assert_contains(rendered, "2028", "2028 tag/date")
    assert_contains(rendered, "2030", "2030 tag/date")
    assert_contains(rendered, "General / Investigación", "general folder for non-finca")
    assert_contains(rendered, "parece no ser de finca", "does not force current finca case")
    assert_not_contains(rendered, "Ayuda a ubicar datos de la finca", "does not claim finca importance")
    assert_not_contains(rendered, "renombré", "does not claim destructive rename")
    assert_not_contains(rendered, "/opt/val0", "no internal path")


def test_ambiguous_matches_ask_for_clarification() -> None:
    rendered = _render_ambiguous_document_matches([
        {"filename": "Agi.pdf", "ingest_id": "20260528_000002"},
        {"filename": "AGI_notes.pdf", "ingest_id": "20260528_000003"},
    ])
    assert_contains(rendered, "Encontré varios documentos parecidos", "ambiguous asks clarification")
    assert_contains(rendered, "Agi.pdf", "first match listed")
    assert_contains(rendered, "AGI_notes.pdf", "second match listed")


def test_no_match_copy_exists_in_route_source() -> None:
    source = (REPO_ROOT / "core" / "document_summary_queries.py").read_text(encoding="utf-8")
    assert_contains(source, "No encontré un documento que coincida", "helpful no-match copy")
    assert_contains(source, "Encontré varios documentos parecidos", "ambiguous copy wired")


def main() -> int:
    test_fuzzy_doc_name_keys_match_human_phrases()
    test_summary_response_is_clean_not_inventory()
    test_naming_response_for_agi_is_general_not_finca()
    test_ambiguous_matches_ask_for_clarification()
    test_no_match_copy_exists_in_route_source()
    print("PASS: Karen document fuzzy matching UX smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
