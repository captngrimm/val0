#!/usr/bin/env python3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.document_inventory_queries import (
    _looks_like_technical_inventory_request,
    _render_document_inventory_technical,
    detect_intents,
    render_document_inventory_compact,
)


def _sample_items():
    return [
        {
            "id": idx,
            "created_at": f"2026-05-{idx:02d} 10:00:00",
            "filename": filename,
            "vfms_id": f"202605{idx:02d}_000000",
            "caption": caption,
            "state": state,
            "raw": raw,
            "has_caption": bool(caption),
        }
        for idx, filename, caption, state, raw in [
            (1, "20260524_010101__IMG_1001.jpg", "", "", "- Estado: guardado"),
            (2, "20260524_010102__nota.txt", "", "texto extraído disponible", ""),
            (3, "20260524_010103__Resumen_judicial_mayo.pdf", "", "texto leído", ""),
            (4, "20260524_010104__Auto_medidas_cautelares.pdf", "", "texto indexado", ""),
            (5, "20260524_010105__Documento4.docx", "", "guardado; requiere revisión", ""),
            (6, "20260524_010106__foto_lote.png", "", "", ""),
            (7, "20260524_010107__documento_extra.pdf", "", "", ""),
            (8, "20260524_010108__otro_documento.pdf", "", "", ""),
            (9, "20260524_010109__anexo.pdf", "", "", ""),
        ]
    ]


def test_compact_inventory_hides_internal_ids():
    rendered = render_document_inventory_compact(_sample_items(), visible_limit=8)

    forbidden = (
        "VFMS",
        "Registro: #",
        "CASE:",
        "20260524_010101",
        "20260501_000000",
    )
    for token in forbidden:
        assert token not in rendered, token


def test_compact_inventory_has_summary_boundary_and_cap():
    rendered = render_document_inventory_compact(_sample_items(), visible_limit=8)

    assert "Documentos registrados" in rendered
    assert "8 de 9 documento(s) mostrado(s)." in rendered
    assert "con texto leído" in rendered
    assert "necesitan OCR/revisión manual" in rendered
    assert "Límite:" in rendered
    assert "no sustituye revisión legal o profesional" in rendered
    assert "Hay 1 documento(s) más no mostrados." in rendered
    assert "Siguientes acciones útiles" in rendered

    visible_items = [
        line for line in rendered.splitlines()
        if line[:2] in {f"{idx}." for idx in range(1, 10)}
    ]
    assert len(visible_items) == 8, visible_items


def test_compact_inventory_keeps_honest_statuses():
    rendered = render_document_inventory_compact(_sample_items(), visible_limit=8)

    assert "Foto reciente —" in rendered and "necesita OCR/revisión" in rendered
    assert "Nota de texto —" in rendered and "texto leído" in rendered
    assert "documento extra —" in rendered and "guardado sin extracción" in rendered


def test_technical_inventory_requires_explicit_phrase():
    assert _looks_like_technical_inventory_request("Val, dame el inventario técnico de documentos")
    assert _looks_like_technical_inventory_request("Val, documentos con IDs")
    assert not _looks_like_technical_inventory_request("Val, qué documentos tengo")
    assert "list_all" in detect_intents("Val, dame el inventario técnico de documentos")

    rendered = _render_document_inventory_technical(_sample_items(), "KAREN-SMOKE")
    assert "CASE:KAREN-SMOKE" in rendered
    assert "VFMS:" in rendered
    assert "Registro: #" in rendered


def main():
    test_compact_inventory_hides_internal_ids()
    test_compact_inventory_has_summary_boundary_and_cap()
    test_compact_inventory_keeps_honest_statuses()
    test_technical_inventory_requires_explicit_phrase()
    print("PASS: document inventory smoke cases passed.")


if __name__ == "__main__":
    main()
