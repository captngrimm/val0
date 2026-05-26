#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.document_inventory_queries import detect_intents, render_document_inventory_compact  # noqa: E402


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def _items() -> list[dict]:
    return [
        {
            "id": 1,
            "created_at": "2026-05-26 10:00:00",
            "filename": "20260526_101010__Escritura_finca_10082.pdf",
            "caption": "",
            "state": "texto leído; resumen disponible",
            "raw": "texto leído resumen disponible",
            "has_caption": False,
        },
        {
            "id": 2,
            "created_at": "2026-05-25 11:00:00",
            "filename": "Documento4.docx",
            "caption": "",
            "state": "guardado; requiere revisión",
            "raw": "",
            "has_caption": False,
        },
        {
            "id": 3,
            "created_at": "2026-05-24 12:00:00",
            "filename": "IMG_9999.jpg",
            "caption": "",
            "state": "guardado",
            "raw": "",
            "has_caption": False,
        },
        {
            "id": 4,
            "created_at": "2026-05-23 12:00:00",
            "filename": "foto_prueba_test.jpg",
            "caption": "",
            "state": "guardado; requiere revisión",
            "raw": "test",
            "has_caption": False,
        },
        {
            "id": 5,
            "created_at": "2026-05-22 12:00:00",
            "filename": "a8f19c20.pdf",
            "caption": "",
            "state": "guardado",
            "raw": "",
            "has_caption": False,
        },
    ]


def test_routes_and_clean_inventory() -> None:
    for prompt in (
        "Val, qué documentos tengo?",
        "qué documentos tengo",
        "qué documentos tengo registrados",
        "inventario de documentos",
        "documentos de finca",
        "documentos del caso",
    ):
        assert_true("list_all" in detect_intents(prompt), f"document route recognized: {prompt}")

    rendered = render_document_inventory_compact(_items(), visible_limit=5)
    assert_contains(rendered, "📎 Documentos registrados", "clean inventory header")
    assert_contains(rendered, "Resumen:", "summary block")
    assert_contains(rendered, "con texto leído", "readable count")
    assert_contains(rendered, "con resumen disponible", "summary count")
    assert_contains(rendered, "necesitan OCR/revisión manual", "review count")
    assert_contains(rendered, "PDF", "PDF type shown")
    assert_contains(rendered, "Word", "Word type shown")
    assert_contains(rendered, "foto", "photo type shown")
    assert_contains(rendered, "resumen disponible", "summary status shown")
    assert_contains(rendered, "guardado sin extracción", "saved without extraction shown")
    assert_contains(rendered, "histórico/test", "legacy/test item labelled if included")
    assert_contains(rendered, "nombre genérico", "weird filename hint")
    assert_contains(rendered, "pídeme el resumen", "suggested summary action")
    assert_contains(rendered, "renombra o clasifica", "suggested rename/classify action")
    assert_contains(rendered, "extrae fechas importantes", "suggested extraction action")
    assert_contains(rendered, "prepara paquete para Nora", "suggested Nora package action")
    assert_not_contains(rendered, "OCR listo", "does not overpromise OCR")
    assert_not_contains(rendered, "DOCX extraído", "does not overpromise DOCX extraction")
    assert_not_contains(rendered, "conclusión legal", "does not give legal conclusion")


def main() -> int:
    test_routes_and_clean_inventory()
    print("PASS: Karen clean document inventory smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
