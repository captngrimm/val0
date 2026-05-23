#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.document_registry import (
    DocumentRecord,
    document_record_from_vfms_metadata,
    is_document_ready_for_summary,
    normalize_document_status,
    safe_document_summary,
)


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def main() -> int:
    assert_equal(normalize_document_status("texto extraído e indexado"), "indexed", "indexed Spanish status")
    assert_equal(
        normalize_document_status("archivo guardado; OCR/análisis queda como paso manual"),
        "ocr_needed",
        "manual OCR status",
    )
    assert_equal(normalize_document_status("OCR failed"), "ocr_failed", "OCR failed status")
    assert_equal(normalize_document_status("unsupported"), "unsupported", "unsupported status")

    metadata = {
        "ingest_id": "20260523_000001",
        "source_filename": "registro_publico.pdf",
        "stored_path": "/opt/val0/vfms_data/raw/20260523_000001__registro_publico.pdf",
        "text_path": "/opt/val0/vfms_data/extracted/20260523_000001.txt",
        "sha256": "abc123",
        "mime": "application/pdf",
        "ingested_at_utc": "2026-05-23T12:00:00+00:00",
        "state": "texto extraído e indexado",
    }

    record = document_record_from_vfms_metadata(
        client_id="fixture-client",
        case_id="CASE-FIXTURE-001",
        chat_id=12345,
        metadata=metadata,
        caption="Registro publico de prueba",
        source="telegram_attachment_vfms",
        source_message_id=99,
    )

    assert isinstance(record, DocumentRecord)
    assert_equal(record.document_id, "vfms:20260523_000001", "document id")
    assert_equal(record.client_id, "fixture-client", "client id")
    assert_equal(record.case_id, "CASE-FIXTURE-001", "case id")
    assert_equal(record.chat_id, 12345, "chat id")
    assert_equal(record.ingest_id, "20260523_000001", "ingest id")
    assert_equal(record.filename, "registro_publico.pdf", "filename")
    assert_equal(record.caption, "Registro publico de prueba", "caption")
    assert_equal(record.status, "indexed", "status")
    assert_equal(record.hash, "abc123", "hash")
    assert_equal(record.mime_type, "application/pdf", "mime type")
    assert_equal(record.source, "telegram_attachment_vfms", "source")
    assert_equal(record.source_message_id, 99, "source message id")
    assert is_document_ready_for_summary(record)

    summary = safe_document_summary(record)
    assert_equal(summary["ready_for_summary"], True, "safe ready")
    assert_equal(summary["ingest_id"], "20260523_000001", "safe ingest")
    if "stored_path" in summary or "extracted_path" in summary or "hash" in summary:
        raise AssertionError("safe summary leaked internal path or hash")

    photo_record = document_record_from_vfms_metadata(
        client_id="fixture-client",
        case_id="CASE-FIXTURE-001",
        chat_id=12345,
        metadata={
            "ingest_id": "20260523_000002",
            "source_filename": "photo_12345_42.jpg",
            "mime": "image/jpeg",
            "state": "archivo guardado; OCR/análisis queda como paso manual",
        },
        source="telegram_attachment_vfms",
    )
    assert_equal(photo_record.status, "ocr_needed", "photo status")
    assert not is_document_ready_for_summary(photo_record)

    print("PASS: document registry smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
