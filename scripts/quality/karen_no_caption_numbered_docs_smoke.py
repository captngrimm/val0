#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.document_inventory_queries import render_document_inventory_compact  # noqa: E402
from core.document_summary_queries import (  # noqa: E402
    _build_specific_doc_summary_reply,
    _doc_match_keys,
    _doc_match_score,
    _extract_document_naming_target,
    _extract_document_number_ref,
    _extract_specific_doc_name,
    _recent_documents_need_clarification,
    _render_recent_documents_clarification,
    render_document_naming_metadata_suggestion,
)


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_equals(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: {actual!r} != {expected!r}")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def _bot_source() -> str:
    return (REPO_ROOT / "bot.py").read_text(encoding="utf-8")


def _function_body(source: str, name: str) -> str:
    for marker in (f"async def {name}", f"def {name}"):
        start = source.find(marker)
        if start >= 0:
            break
    else:
        raise AssertionError(f"missing function {name}")
    next_def = source.find("\ndef ", start + 1)
    next_async_def = source.find("\nasync def ", start + 1)
    stops = [pos for pos in (next_def, next_async_def) if pos > start]
    end = min(stops) if stops else len(source)
    return source[start:end]


def _items() -> list[dict]:
    return [
        {
            "id": 30,
            "created_at": "2026-05-28 15:05:00",
            "filename": "A0x259_scan_final.pdf",
            "alias": "Auto_secuestro_Embargo_o_Medidas_Cautelares_Juncá",
            "vfms_id": "20260528_000003",
            "ingest_id": "20260528_000003",
            "caption": "",
            "state": "texto leído",
            "raw": "- Estado: texto leído",
            "text": "Ricardo Juncá. Auto secuestro embargo medidas cautelares.",
        },
        {
            "id": 29,
            "created_at": "2026-05-28 14:30:00",
            "filename": "Agi.pdf",
            "alias": "AGI_Predicciones_y_Timeline_2028_2030",
            "vfms_id": "20260528_000002",
            "ingest_id": "20260528_000002",
            "caption": "",
            "state": "texto extraído e indexado; resumen disponible",
            "raw": "- Estado: texto extraído e indexado; resumen disponible",
            "saved_summary": "📋 Resumen claro\n- El documento habla de AGI.",
            "text": "AGI predictions and AI timeline.",
        },
        {
            "id": 28,
            "created_at": "2026-05-27 10:00:00",
            "filename": "foto_lote.png",
            "alias": "",
            "vfms_id": "20260527_000001",
            "ingest_id": "20260527_000001",
            "caption": "",
            "state": "",
            "raw": "",
            "text": "",
        },
    ]


def test_no_caption_followup_phrases_resolve_current_or_latest() -> None:
    cases = {
        "Val, resume este documento": "__current__",
        "Val, transcribe este documento y haz un resumen": "__current__",
        "Val, dame el resumen del documento que acabo de subir": "__current__",
        "Val, resume el último documento": "__latest__",
    }
    for phrase, expected in cases.items():
        assert_equals(_extract_specific_doc_name(phrase), expected, f"extract latest/current: {phrase}")

    assert_equals(_extract_document_naming_target("Val, sugiere nombre para este documento"), "", "naming current doc")
    assert_equals(_extract_document_naming_target("Val, ponle nombre a este documento"), "", "ponle nombre current doc")


def test_inventory_is_newest_first_numbered_and_preserves_accents() -> None:
    rendered = render_document_inventory_compact(_items(), visible_limit=3)
    assert_contains(rendered, "📎 Documentos registrados", "inventory header")
    assert_contains(rendered, "3 de 3 documento(s) mostrado(s)", "total shown kept")
    assert_contains(rendered, "2 con texto leído", "text read count kept")
    assert_contains(rendered, "1 con resumen disponible", "summary count kept")
    assert_contains(rendered, "1. Auto_secuestro_Embargo_o_Medidas_Cautelares_Juncá — 2026-05-28 · PDF · texto leído", "newest first item")
    assert_contains(rendered, "2. AGI_Predicciones_y_Timeline_2028_2030 — 2026-05-28 · PDF · resumen disponible", "second item")
    assert_contains(rendered, "Original: Agi.pdf", "original filename shown")
    assert_true(rendered.find("1. Auto_secuestro") < rendered.find("2. AGI"), "inventory ordering newest first")
    assert_not_contains(rendered, "Junc —", "accent not stripped in display")
    assert_not_contains(rendered, "/opt/val0", "no internal path exposed")
    assert_not_contains(rendered, "renombré", "no destructive rename language")


def test_numbered_references_are_parsed() -> None:
    assert_equals(_extract_document_number_ref("resume el documento 1"), 1, "summary doc 1")
    assert_equals(_extract_document_number_ref("Val, dame el resumen del documento 2"), 2, "summary doc 2")
    assert_equals(_extract_document_number_ref("Val, sugiere nombre para el documento 1"), 1, "naming doc 1")
    assert_equals(_extract_document_number_ref("Val, clasifica el documento 3"), 3, "classify doc 3")
    assert_equals(_extract_specific_doc_name("Val, resume el documento 1"), "1", "summary extraction doc 1")
    assert_equals(_extract_specific_doc_name("Val, dame el resumen del documento 2"), "2", "summary extraction doc 2")
    assert_equals(_extract_document_naming_target("Val, sugiere nombre para el documento 1"), "el documento 1", "naming target doc 1")


def test_multiple_recent_uploads_clarify_safely() -> None:
    recent = [
        {**_items()[0], "filename": "scan_final.pdf", "created_at": "2026-05-28 15:05:30"},
        {**_items()[1], "filename": "scan_final.pdf", "created_at": "2026-05-28 15:05:10"},
    ]
    assert_true(_recent_documents_need_clarification(recent), "same-minute uploads need clarification")
    rendered = _render_recent_documents_clarification(recent)
    assert_contains(rendered, "Subiste varios documentos recientes", "clarification copy")
    assert_contains(rendered, "¿Quieres que trabaje con el último o con uno específico?", "clarification question")
    assert_contains(rendered, "20260528_000003", "first VFMS id")
    assert_contains(rendered, "20260528_000002", "second VFMS id")
    assert_contains(rendered, "usaré la más reciente si dices 'último documento'", "duplicate-ish copy")
    assert_not_contains(rendered, "/opt/val0", "no internal path")


def test_accentless_matching_preserves_accented_display() -> None:
    item = _items()[0]
    assert_true(_doc_match_score(_doc_match_keys("Junca"), item) > 0, "accentless query matches accented alias")
    assert_true(_doc_match_score(_doc_match_keys("Juncá"), item) > 0, "accented query matches accented alias")
    summary = _build_specific_doc_summary_reply({
        **item,
        "saved_summary": "📋 Resumen claro\n- Se menciona a Ricardo Juncá.",
    })
    assert_contains(summary, "Auto_secuestro_Embargo_o_Medidas_Cautelares_Juncá", "summary title preserves accent")
    naming = render_document_naming_metadata_suggestion(item, case_id="KAREN-LAND-001")
    assert_not_contains(naming, "/opt/val0", "naming no internal path")


def test_routes_still_prioritize_document_followups() -> None:
    handle_text = _function_body(_bot_source(), "handle_text")
    summary_gate = handle_text.find("maybe_handle_document_summary_query")
    inventory_gate = handle_text.find("maybe_handle_document_query")
    assert_true(summary_gate >= 0, "summary gate wired")
    assert_true(inventory_gate < 0 or summary_gate < inventory_gate, "summary followups beat inventory")
    assert_contains(handle_text, "transcribe este documento", "no-caption transcribe priority marker")
    assert_contains(handle_text, "resume este documento", "current document priority marker")


def main() -> int:
    test_no_caption_followup_phrases_resolve_current_or_latest()
    test_inventory_is_newest_first_numbered_and_preserves_accents()
    test_numbered_references_are_parsed()
    test_multiple_recent_uploads_clarify_safely()
    test_accentless_matching_preserves_accented_display()
    test_routes_still_prioritize_document_followups()
    print("PASS: Karen no-caption numbered document smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
