#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.document_summary_queries import (  # noqa: E402
    _extract_document_naming_target,
    _normalize_doc_name,
    looks_like_document_naming_metadata_request,
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


def _doc_meta() -> dict:
    return {
        "filename": "six_pdf.pdf",
        "ingest_id": "20260528_000001",
        "state": "texto extraído e indexado; resumen disponible",
        "saved_summary": "📋 Resumen claro\n- Se menciona Finca No. 10082.",
        "text": (
            "Juzgado Primero de Circuito Civil. Finca No. 10082. "
            "Se menciona el Oficio No. 792 dirigido al Registro Público. "
            "Auto No. 629 fechado 29 de abril de 2024."
        ),
    }


def test_naming_phrases_are_recognized() -> None:
    phrases = (
        "Val, sugiere nombre para six pdf",
        "Val, renombra six pdf",
        "Val, clasifica six pdf",
        "Val, qué es este documento?",
        "Val, organiza este documento",
        "Val, ponle etiquetas a six pdf",
        "Val, qué nombre le pondrías a six pdf",
    )
    for phrase in phrases:
        assert_true(looks_like_document_naming_metadata_request(phrase), f"phrase recognized: {phrase}")

    assert_true(_extract_document_naming_target("Val, sugiere nombre para six pdf") == "six pdf", "extract six pdf")
    assert_true(_extract_document_naming_target("Val, renombra six pdf") == "six pdf", "extract rename target")
    assert_true(_extract_document_naming_target("Val, organiza este documento") == "", "latest-doc request has no target")
    assert_true(_normalize_doc_name("six pdf") == _normalize_doc_name("six_pdf.pdf"), "six pdf matches filename")


def test_metadata_suggestion_response_shape() -> None:
    rendered = render_document_naming_metadata_suggestion(_doc_meta(), case_id="KAREN-LAND-001")

    assert_contains(rendered, "📎 Documento", "document section")
    assert_contains(rendered, "Actual: six_pdf.pdf", "current filename shown")
    assert_contains(rendered, "ID: 20260528_000001", "VFMS id shown")
    assert_contains(rendered, "Estado: resumen disponible", "status shown")
    assert_contains(rendered, "🏷️ Sugerencia de nombre", "suggested name section")
    assert_contains(rendered, "Finca 10082", "finca tag/name included")
    assert_contains(rendered, "🧩 Etiquetas sugeridas", "tags section")
    assert_contains(rendered, "PDF", "PDF tag included")
    assert_contains(rendered, "🗂️ Carpeta / caso sugerido", "case section")
    assert_contains(rendered, "CASE:KAREN-LAND-001", "case suggested")
    assert_contains(rendered, "🧭 Por qué importa", "importance section")
    assert_contains(rendered, "📅 Línea de tiempo", "timeline section")
    assert_contains(rendered, "29 de abril de 2024", "detected date shown")
    assert_contains(rendered, "Todavía no cambié el nombre", "read-only naming disclaimer")
    assert_contains(rendered, "guardar este nombre", "next action save name")
    assert_not_contains(rendered, "renombré", "does not claim destructive rename")
    assert_not_contains(rendered, "guardé etiquetas", "does not claim saved tags")
    assert_not_contains(rendered, "/opt/val0", "no internal path exposed")
    assert_not_contains(rendered, "conclusión legal", "no legal conclusion")


def test_route_is_wired_before_inventory_summary_handlers() -> None:
    handle_text = _function_body(_bot_source(), "handle_text")
    naming_gate = handle_text.find("maybe_handle_document_naming_metadata_query")
    inventory_query = handle_text.find("maybe_handle_document_query")
    summary_query = handle_text.find("maybe_handle_document_summary_query")

    assert_true(naming_gate >= 0, "handle_text has naming metadata gate")
    assert_true(inventory_query < 0 or naming_gate < inventory_query, "naming gate beats inventory query")
    assert_true(summary_query < 0 or naming_gate < summary_query, "naming gate beats generic summary query")


def main() -> int:
    test_naming_phrases_are_recognized()
    test_metadata_suggestion_response_shape()
    test_route_is_wired_before_inventory_summary_handlers()
    print("PASS: Karen document naming metadata smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
