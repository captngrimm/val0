#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.document_ocr_runtime import (  # noqa: E402
    DEFAULT_MAX_PAGES,
    DocumentOCRResult,
    run_pdf_ocr,
)
from core.document_summary_queries import (  # noqa: E402
    _build_specific_doc_summary_reply,
    _build_ocr_summary_reply,
    _with_cached_ocr_notice,
    _extract_document_ocr_target,
    _looks_like_document_ocr_request,
    _watermark_guard_reply,
    OCR_WORKING_MESSAGE,
    OCR_CACHED_MESSAGE,
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


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_runtime_helper_shape() -> None:
    source = _source("core/document_ocr_runtime.py")
    assert_contains(source, "DEFAULT_MAX_PAGES = 3", "default page limit")
    assert_contains(source, "tmp/ocr_runtime", "tmp output root")
    assert_contains(source, "pdftoppm", "rendering tool")
    assert_contains(source, "tesseract", "ocr tool")
    assert_contains(source, "legal_marker_counts", "legal marker metrics")
    assert_contains(source, "watermark_count", "watermark metrics")
    result = run_pdf_ocr(ROOT / "no_such_file.pdf")
    assert_true(isinstance(result, DocumentOCRResult), "returns structured result")
    assert_true(result.status == "file_missing", "missing file is graceful")
    assert_true(DEFAULT_MAX_PAGES == 3, "page limit constant is 3")


def test_route_phrase_detection() -> None:
    phrases = [
        "Val, haz OCR del último documento",
        "Val, haz OCR de este documento",
        "Val, lee visualmente el último documento",
        "Val, resume con OCR el último documento",
        "Val, resume con OCR este documento",
        "Val, haz OCR del documento 1",
        "Val, resume con OCR el documento 1",
    ]
    for phrase in phrases:
        assert_true(_looks_like_document_ocr_request(phrase), f"OCR phrase detected: {phrase}")
    assert_true(_extract_document_ocr_target("Val, resume con OCR el documento 1") == "1", "numbered doc target")
    assert_true(_extract_document_ocr_target("Val, haz OCR del último documento") == "__latest__", "latest target")
    assert_true(_extract_document_ocr_target("Val, lee visualmente este documento") == "__current__", "current target")


def test_normal_watermark_summary_does_not_auto_ocr() -> None:
    watermark_text = "Copia para propositos informativos solamente\n" * 8
    reply = _build_specific_doc_summary_reply({
        "filename": "Auto_secuestro.pdf",
        "ingest_id": "20260531_000001",
        "state": "texto extraído e indexado",
        "text": watermark_text,
    })
    assert_contains(reply, "necesita OCR o revisión visual", "watermark guard still wins")
    assert_contains(reply, "Val, resume con OCR el último documento", "guard suggests explicit OCR command")
    assert_not_contains(reply, "Resumen generado con OCR", "normal summary does not auto-run OCR")

    guard = _watermark_guard_reply("Auto_secuestro.pdf")
    assert_contains(guard, "resume con OCR", "watermark guard includes OCR next action")


def test_ocr_summary_copy_and_separate_storage_markers() -> None:
    doc_meta = {
        "filename": "Auto_secuestro_Embargo.pdf",
        "ingest_id": "20260531_000001",
        "text": "Copia para propositos informativos solamente",
    }
    ocr_text = (
        "JUZGADO PRIMERO DE CIRCUITO CIVIL. AUTO No. 629. "
        "OFICIO dirigido al REGISTRO Público. DEMANDA relacionada con FINCA 10082."
    )
    reply = _build_ocr_summary_reply(doc_meta, ocr_text, pages=3)
    assert_contains(reply, "Resumen generado con OCR/lectura visual del PDF. Es una primera pasada", "OCR first-pass disclosure")
    assert_contains(reply, "Nota: por ahora revisé hasta las primeras 3 páginas.", "OCR page-limit note")
    assert_contains(reply, "📋 Resumen claro", "summary style kept")
    assert_contains(reply, "Puede tener errores de OCR", "OCR error disclaimer")
    assert_contains(reply, "no sustituye la revisión de la abogada o del documento original", "lawyer/original review disclaimer")
    assert_contains(reply, "extraer fechas importantes", "OCR next action dates")
    assert_contains(reply, "sacar datos registrales", "OCR next action registry")
    assert_contains(reply, "preparar preguntas para Nora", "OCR next action Nora")
    assert_contains(reply, "hacer una versión más limpia del resumen", "OCR next action clean version")
    assert_not_contains(reply, "Límite: resumo información registrada", "OCR summary avoids robotic generic limit")


def test_ocr_working_copy_exists() -> None:
    assert_contains(OCR_WORKING_MESSAGE, "Estoy leyendo visualmente el PDF con OCR", "working copy")
    assert_contains(OCR_WORKING_MESSAGE, "puede tardar un momento", "working copy human timing")
    source = _source("core/document_summary_queries.py")
    assert_contains(source, "await update.message.reply_text(OCR_WORKING_MESSAGE)", "working copy sent before OCR")
    assert_true(source.find("OCR_WORKING_MESSAGE") < source.find("run_pdf_ocr(pdf_path"), "working copy appears before OCR run")
    saved_idx = source.find("if saved_ocr.get(\"text\"):")
    progress_idx = source.find("await update.message.reply_text(OCR_WORKING_MESSAGE)")
    assert_true(saved_idx >= 0 and progress_idx > saved_idx, "cached OCR branch is checked before progress message")


def test_cached_ocr_copy_exists_without_processing_claim() -> None:
    assert_contains(OCR_CACHED_MESSAGE, "Ya tenía una lectura OCR guardada", "cached OCR message")
    cached_reply = _with_cached_ocr_notice("📄 Documento\nResumen generado con OCR/lectura visual del PDF.")
    assert_contains(cached_reply, OCR_CACHED_MESSAGE, "cached reply preface")
    assert_contains(cached_reply, "Resumen generado con OCR/lectura visual del PDF", "cached keeps summary framing")
    assert_not_contains(cached_reply, "Estoy leyendo visualmente", "cached reply does not imply live processing")
    source = _source("core/document_summary_queries.py")
    assert_contains(source, "_with_cached_ocr_notice(", "cached path wrapper")

    summary_source = _source("core/document_summary_queries.py")
    assert_contains(summary_source, "source=\"generated_ocr\"", "OCR stored separately")
    assert_contains(summary_source, "OCR_TEXT_DIR", "separate OCR text path")
    assert_contains(summary_source, "no reemplaza la extracción original", "embedded text preserved")


def test_bot_route_ordering() -> None:
    bot = _source("bot.py")
    assert_contains(bot, "maybe_handle_document_ocr_query", "bot imports OCR route")
    ocr_idx = bot.find("maybe_handle_document_ocr_query")
    summary_idx = bot.find("maybe_handle_document_summary_query", ocr_idx)
    assert_true(ocr_idx >= 0 and summary_idx > ocr_idx, "OCR route appears before normal document summary after import")
    assert_contains(bot, "KAREN_DOCUMENT_OCR_EARLY_PIPELINE", "early OCR route log")


def main() -> int:
    test_runtime_helper_shape()
    test_route_phrase_detection()
    test_normal_watermark_summary_does_not_auto_ocr()
    test_ocr_summary_copy_and_separate_storage_markers()
    test_ocr_working_copy_exists()
    test_cached_ocr_copy_exists_without_processing_claim()
    test_bot_route_ordering()
    print("PASS: Karen OCR runtime smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
