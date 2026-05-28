#!/usr/bin/env python3
"""
Smoke test for M3B: Specific Document Summary Route

Verifies that specific document summary requests:
1. Route to document summary handler, not inventory
2. Return appropriate summary or "not generated yet" message
3. Handle document name matching correctly (e.g., "six pdf" vs "six_pdf.pdf")
"""
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.document_summary_queries import (  # noqa: E402
    SUMMARY_MARKERS,
    _extract_specific_doc_name,
    _normalize_doc_name,
    _find_specific_doc_in_inventory,
    _build_specific_doc_summary_reply,
)


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_false(value, label: str) -> None:
    if value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def assert_equals(a, b, label: str) -> None:
    if a != b:
        raise AssertionError(f"{label}: {a!r} != {b!r}")


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


def test_summary_markers_include_specific_requests() -> None:
    """Verify SUMMARY_MARKERS include patterns for specific document requests."""
    markers_str = " ".join(SUMMARY_MARKERS).lower()
    
    # Should have specific document patterns
    assert_true("resumen de" in markers_str, "SUMMARY_MARKERS includes 'resumen de'")
    assert_true("dame resumen de" in markers_str, "SUMMARY_MARKERS includes 'dame resumen de'")
    assert_true("dame el resumen de" in markers_str, "SUMMARY_MARKERS includes 'dame el resumen de'")
    assert_true("hazme resumen de" in markers_str, "SUMMARY_MARKERS includes 'hazme resumen de'")
    assert_true("resume el documento" in markers_str, "SUMMARY_MARKERS includes 'resume el documento'")


def test_extract_specific_doc_name() -> None:
    """Test extraction of document names from various requests."""
    
    cases = [
        ("dame el resumen de six pdf", "six pdf"),
        ("Dame el resumen de six_pdf.pdf", "six_pdf.pdf"),
        ("resumen de document_1", "document_1"),
        ("resume el documento test.pdf", "test.pdf"),
        ("resume el pdf important", "important"),
        ("Hazme resumen de escritura", "escritura"),
        ("dame resumen de finca 10082", "finca 10082"),
    ]
    
    for prompt, expected in cases:
        result = _extract_specific_doc_name(prompt)
        assert_equals(result.lower(), expected.lower(), f"extract from: {prompt}")


def test_extract_no_match() -> None:
    """Test that non-specific prompts return empty string."""
    cases = [
        "resumen de documentos",  # plural - generic summary
        "qué documentos tengo",    # inventory query
        "dame un resumen general",  # generic summary
    ]
    
    for prompt in cases:
        result = _extract_specific_doc_name(prompt)
        assert_equals(result, "", f"should not extract from: {prompt}")


def test_normalize_doc_name() -> None:
    """Test normalization of document names for matching."""
    
    cases = [
        ("six pdf", "sixpdf"),
        ("six_pdf", "sixpdf"),
        ("six-pdf", "sixpdf"),
        ("six pdf.pdf", "sixpdf"),
        ("six_pdf.pdf", "sixpdf"),
        ("SIX PDF", "sixpdf"),
        ("document_1.docx", "document1"),
        ("DOCUMENT-1", "document1"),
    ]
    
    for name, expected in cases:
        result = _normalize_doc_name(name)
        assert_equals(result, expected, f"normalize: {name}")


def test_build_summary_reply_no_text() -> None:
    """Test that build_specific_doc_summary_reply handles documents without extracted text."""
    
    doc_meta = {
        "filename": "escritura_finca_10082.pdf",
        "ingest_id": "20260528_000001",
        "caption": "Documento de escritura",
        "state": "guardado",
        "text": "",
    }
    
    reply = _build_specific_doc_summary_reply(doc_meta)
    
    # Should NOT be an inventory response
    assert_not_contains(reply, "📎 Documentos registrados", "reply is not inventory")
    assert_not_contains(reply, "documentos con resumen", "reply is not inventory count")
    
    # Should be a summary-style response
    assert_contains(reply, "📄", "summary has document icon")
    assert_contains(reply, "escritura", "summary mentions filename")
    assert_contains(reply, "20260528_000001", "summary includes ID")


def test_build_summary_reply_with_text() -> None:
    """Test that build_specific_doc_summary_reply handles documents with extracted text."""
    
    doc_meta = {
        "filename": "test_document.pdf",
        "ingest_id": "20260528_000002",
        "caption": "",
        "state": "texto extraído e indexado",
        "text": "Line 1\nLine 2\nLine 3\n\nMore content here",
    }
    
    reply = _build_specific_doc_summary_reply(doc_meta)
    
    # Should NOT be an inventory response
    assert_not_contains(reply, "📎 Documentos registrados", "reply is not inventory")
    
    # Should be a summary-style response
    assert_contains(reply, "📄", "summary has document icon")
    assert_contains(reply, "test_document", "summary mentions filename")
    assert_contains(reply, "ya tengo el texto leído", "indicates text is available")
    assert_contains(reply, "todavía no tengo un resumen guardado", "honest no saved summary copy")
    assert_contains(reply, "puedo generar uno ahora", "offers generation")
    assert_not_contains(reply.splitlines()[0], "📎 Documentos registrados", "does not start with inventory")


def test_build_summary_reply_with_summary_state() -> None:
    """Test response when summary is already generated."""
    
    doc_meta = {
        "filename": "legal_doc.pdf",
        "ingest_id": "20260528_000003",
        "caption": "Resolución judicial",
        "state": "texto leído; resumen disponible",
        "text": "Resumen Point 1\nResumen Point 2\nResumen Point 3",
    }
    
    reply = _build_specific_doc_summary_reply(doc_meta)
    
    # Should indicate summary is available
    assert_contains(reply, "Resumen disponible", "indicates summary ready")
    assert_contains(reply, "legal_doc", "mentions filename")


def test_specific_requests_dont_match_inventory_intents() -> None:
    """Verify specific doc requests don't match inventory-only patterns."""
    from core.document_inventory_queries import detect_intents
    
    # These should NOT be detected as generic list_all inventory queries
    # They should be caught by SUMMARY_MARKERS instead
    
    # Note: detect_intents might still work, but these specific requests
    # should be routed to summary handler first due to routing order
    specific_requests = [
        "dame el resumen de six pdf",
        "resumen de documento_1",
        "hazme resumen de finca 10082",
    ]
    
    for prompt in specific_requests:
        intents = detect_intents(prompt)
        # These prompts should not have 'list_all' intent
        # because they don't match list_all patterns
        if intents:
            assert_false("list_all" in intents, f"specific request should not trigger list_all: {prompt}")


def test_specific_summary_routes_before_inventory_in_bot() -> None:
    source = _bot_source()
    handle_text = _function_body(source, "handle_text")
    summary_gate = handle_text.find("KAREN_VFMS_PRIORITY_SUMMARY_GATE")
    inventory_gate = handle_text.find("KAREN_DOCUMENT_INVENTORY_GATE")
    final_specific_gate = handle_text.find("KAREN_HANDLE_TEXT_SPECIFIC_DOC_SUMMARY")
    final_inventory_query = handle_text.rfind("maybe_handle_document_query")

    assert_true(summary_gate >= 0, "handle_text has priority summary gate")
    assert_true(inventory_gate >= 0, "handle_text has document inventory gate")
    assert_true(summary_gate < inventory_gate, "priority summary gate runs before inventory gate")
    assert_true(final_specific_gate >= 0, "handle_text has final specific summary guard")
    assert_true(final_specific_gate < final_inventory_query, "final specific summary guard runs before inventory query")
    assert_contains(handle_text, "dame el resumen de", "specific summary phrase wired")
    assert_contains(handle_text, "hazme resumen de", "hazme summary phrase wired")
    assert_contains(handle_text, "resume el documento", "resume document phrase wired")


def test_summary_markers_still_include_general_patterns() -> None:
    """Verify we didn't break general summary patterns."""
    
    general_requests = [
        "dame un resumen de documentos",
        "resume documentos",
        "qué dicen los documentos",
        "resumen general",
    ]
    
    for prompt in general_requests:
        has_marker = any(m in prompt.lower() for m in SUMMARY_MARKERS)
        assert_true(has_marker, f"general summary pattern still recognized: {prompt}")


if __name__ == "__main__":
    tests = [
        test_summary_markers_include_specific_requests,
        test_extract_specific_doc_name,
        test_extract_no_match,
        test_normalize_doc_name,
        test_build_summary_reply_no_text,
        test_build_summary_reply_with_text,
        test_build_summary_reply_with_summary_state,
        test_specific_requests_dont_match_inventory_intents,
        test_specific_summary_routes_before_inventory_in_bot,
        test_summary_markers_still_include_general_patterns,
    ]
    
    failed = []
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed.append((test.__name__, e))
    
    if failed:
        print(f"\n{len(failed)} test(s) failed:")
        for name, error in failed:
            print(f"  {name}: {error}")
        sys.exit(1)
    else:
        print(f"\nAll {len(tests)} tests passed!")
        sys.exit(0)
