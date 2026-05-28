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
    _generate_specific_doc_summary_text,
    _with_summary_available_state,
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


def _doc_meta() -> dict:
    return {
        "filename": "six_pdf.pdf",
        "ingest_id": "20260528_000001",
        "caption": "Val, transcribe este documento y hazme un resumen",
        "state": "texto extraído e indexado",
        "text": (
            "Juzgado Primero de Circuito Civil. Finca No. 10082. "
            "Se menciona el Oficio No. 792 dirigido al Registro Público. "
            "Auto No. 629 fechado 29 de abril de 2024."
        ),
    }


def test_generated_summary_output_is_polished() -> None:
    generated = _generate_specific_doc_summary_text(_doc_meta())
    reply = _build_specific_doc_summary_reply({**_doc_meta(), "saved_summary": generated})

    assert_contains(reply, "📄 six_pdf.pdf", "document title shown")
    assert_contains(reply, "ID: 20260528_000001", "document id shown")
    assert_contains(reply, "Estado: resumen disponible", "summary status shown")
    assert_contains(reply, "📋 Resumen claro", "polished summary header shown")
    assert_contains(reply, "Siguientes acciones útiles", "next actions kept")
    assert_contains(reply, "renombrar o clasificar este documento", "rename/classify action kept")
    assert_not_contains(reply, "Resumen grounded", "internal grounded wording removed")
    assert_true(reply.count("six_pdf.pdf") == 1, "title not repeated")
    assert_true(reply.count("20260528_000001") == 1, "id not repeated")
    assert_true(reply.count("no sustituye revisión legal o profesional") == 1, "legal limit not duplicated")
    assert_not_contains(reply, "/opt/val0", "no internal path exposed")


def test_legacy_saved_summary_is_cleaned_for_reply() -> None:
    legacy_saved = (
        "Resumen generado de documento VFMS\n"
        "- VFMS ingest_id: 20260528_000001\n"
        "- Archivo: six_pdf.pdf\n\n"
        "📄 six_pdf.pdf\n"
        "VFMS: 20260528_000001\n"
        "Estado: texto extraído e indexado\n"
        "Resumen grounded:\n"
        "- Finca No. 10082.\n\n"
        "Límite: resumo información registrada; no sustituye revisión legal o profesional.\n"
        "Límite: resumo información registrada; no sustituye revisión legal o profesional."
    )
    reply = _build_specific_doc_summary_reply({**_doc_meta(), "saved_summary": legacy_saved})

    assert_contains(reply, "📋 Resumen claro", "legacy header is polished")
    assert_contains(reply, "- Finca No. 10082.", "legacy bullet preserved")
    assert_not_contains(reply, "Resumen grounded", "legacy internal wording removed")
    assert_true(reply.count("six_pdf.pdf") == 1, "legacy title not repeated")
    assert_true(reply.count("20260528_000001") == 1, "legacy id not repeated")
    assert_true(reply.count("no sustituye revisión legal o profesional") == 1, "legacy limit deduped")


def test_inventory_still_counts_summary_available() -> None:
    updated_note = _with_summary_available_state(
        "Documento recibido vía Telegram y registrado en VFMS.\n"
        "- Archivo: six_pdf.pdf\n"
        "- VFMS ingest_id: 20260528_000001\n"
        "- Estado: texto extraído e indexado; listo para resumen"
    )
    inventory = render_document_inventory_compact([
        {
            "filename": "six_pdf.pdf",
            "created_at": "2026-05-28 10:00:00",
            "state": "texto extraído e indexado; listo para resumen; resumen disponible",
            "raw": updated_note,
        }
    ])
    assert_contains(inventory, "1 con resumen disponible", "inventory still counts saved summary")


def main() -> int:
    test_generated_summary_output_is_polished()
    test_legacy_saved_summary_is_cleaned_for_reply()
    test_inventory_still_counts_summary_available()
    print("PASS: Karen document summary output polish smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
