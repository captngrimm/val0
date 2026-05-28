#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.document_summary_queries import (  # noqa: E402
    _extract_document_naming_target,
    _extract_specific_doc_name,
    _looks_like_latest_upload_status_request,
    _looks_like_latest_document_reference,
    render_latest_document_status,
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


def _summary_source() -> str:
    return (REPO_ROOT / "core" / "document_summary_queries.py").read_text(encoding="utf-8")


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


def _latest_doc() -> dict:
    return {
        "filename": "A0x259_scan_final.pdf",
        "alias": "AGI_Predicciones_y_Timeline_2028_2030",
        "ingest_id": "20260528_000002",
        "created_at": "2026-05-28 14:30:00",
        "state": "texto extraído e indexado; resumen disponible",
        "saved_summary": "📋 Resumen claro\n- Habla de AGI y predicciones.",
        "text": "AGI predictions, artificial general intelligence, 2028, 2030.",
    }


def test_latest_summary_phrases_resolve_to_latest_token() -> None:
    latest_phrases = (
        "Val, resume el último documento",
        "Val, dame el resumen del último documento",
    )
    for phrase in latest_phrases:
        assert_true(_looks_like_latest_document_reference(phrase), f"latest reference recognized: {phrase}")
        assert_equals(_extract_specific_doc_name(phrase), "__latest__", f"summary latest token: {phrase}")
    current_phrases = (
        "Val, resume este documento",
        "Val, transcribe/resume el documento que acabo de subir",
    )
    for phrase in current_phrases:
        assert_true(_looks_like_latest_document_reference(phrase), f"current reference recognized: {phrase}")
        assert_equals(_extract_specific_doc_name(phrase), "__current__", f"summary current token: {phrase}")


def test_latest_naming_phrases_have_no_filename_target() -> None:
    phrases = (
        "Val, sugiere nombre para el último documento",
        "Val, sugiere nombre para este documento",
        "Val, clasifica el último documento",
        "Val, ponle etiquetas al último documento",
    )
    for phrase in phrases:
        assert_equals(_extract_document_naming_target(phrase), "", f"naming latest uses latest doc: {phrase}")


def test_latest_upload_status_response_shape() -> None:
    for phrase in (
        "Val, qué fue lo último que subí?",
        "Val, cuál fue el último documento que subí?",
    ):
        assert_true(_looks_like_latest_upload_status_request(phrase), f"latest upload status recognized: {phrase}")

    rendered = render_latest_document_status(_latest_doc())
    assert_contains(rendered, "📎 Último documento registrado", "latest status header")
    assert_contains(rendered, "AGI_Predicciones_y_Timeline_2028_2030", "display alias shown")
    assert_contains(rendered, "Original: A0x259_scan_final.pdf", "original filename preserved")
    assert_contains(rendered, "20260528_000002", "VFMS id shown")
    assert_contains(rendered, "2026-05-28", "date shown")
    assert_contains(rendered, "PDF", "type shown")
    assert_contains(rendered, "resumen disponible", "status shown")
    assert_contains(rendered, "resume este documento", "summary next action")
    assert_contains(rendered, "sugiere nombre para este documento", "naming next action")
    assert_not_contains(rendered, "/opt/val0", "no internal path exposed")
    assert_not_contains(rendered, "renombré", "no destructive rename language")


def test_latest_uses_persistent_vfms_source() -> None:
    source = _summary_source()
    latest_body = _function_body(source, "_find_ordered_document_inventory")
    assert_contains(latest_body, "source='telegram_attachment_vfms'", "latest doc uses VFMS notes")
    assert_contains(latest_body, "ORDER BY id DESC", "latest doc uses persisted newest record")
    assert_contains(source, "Primero te sugiero un nombre para el último documento", "save-without-pending guidance")
    assert_contains(source, "Todavía no veo documentos registrados", "no-doc registered copy")


def test_routes_are_wired_before_inventory() -> None:
    handle_text = _function_body(_bot_source(), "handle_text")
    latest_status = handle_text.find("maybe_handle_latest_document_status_query")
    naming = handle_text.find("maybe_handle_document_naming_metadata_query")
    inventory = handle_text.find("maybe_handle_document_query")
    summary = handle_text.find("maybe_handle_document_summary_query")

    assert_true(latest_status >= 0, "latest status gate wired")
    assert_true(naming >= 0, "naming gate wired")
    assert_true(summary >= 0, "summary gate wired")
    assert_true(inventory < 0 or latest_status < inventory, "latest status beats inventory")


def main() -> int:
    test_latest_summary_phrases_resolve_to_latest_token()
    test_latest_naming_phrases_have_no_filename_target()
    test_latest_upload_status_response_shape()
    test_latest_uses_persistent_vfms_source()
    test_routes_are_wired_before_inventory()
    print("PASS: Karen last uploaded document context smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
