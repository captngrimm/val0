#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.document_extraction_readiness import (
    detect_supported_file_type,
    document_capability_summary,
    infer_extraction_status,
    needs_human_review,
)


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(f"{label}: expected truthy value")


def assert_false(value, label: str) -> None:
    if value:
        raise AssertionError(f"{label}: expected falsey value")


def assert_no_path_or_hash(summary: dict) -> None:
    forbidden = {
        "hash",
        "sha",
        "sha256",
        "raw_path",
        "stored_path",
        "text_path",
        "extracted_path",
        "meta_path",
    }
    leaked = forbidden.intersection(summary.keys())
    if leaked:
        raise AssertionError(f"safe summary leaked keys: {sorted(leaked)}")


def main() -> int:
    text_doc = {
        "document_id": "vfms:20260523_000010",
        "ingest_id": "20260523_000010",
        "source_filename": "notes.txt",
        "mime": "text/plain",
        "status": "indexed",
        "sha256": "not-safe-to-expose",
        "stored_path": "/opt/val0/vfms_data/raw/20260523_000010__notes.txt",
    }
    assert_equal(infer_extraction_status(text_doc), "ready", ".txt indexed status")
    assert_true(document_capability_summary(text_doc)["ready_for_summary"], ".txt ready")

    pdf_extracted = {
        "ingest_id": "20260523_000011",
        "source_filename": "registro.pdf",
        "mime": "application/pdf",
        "status": "extracted",
        "text_path": "/opt/val0/vfms_data/extracted/20260523_000011.txt",
    }
    assert_equal(
        infer_extraction_status(pdf_extracted, indexed_chunk_count=0),
        "extracted",
        ".pdf extracted no chunks",
    )
    assert_false(
        document_capability_summary(pdf_extracted)["ready_for_summary"],
        ".pdf extracted not ready without chunks",
    )

    pdf_ready = {
        "ingest_id": "20260523_000012",
        "source_filename": "registro_publico.pdf",
        "mime": "application/pdf",
        "status": "indexed",
    }
    assert_equal(
        infer_extraction_status(pdf_ready, indexed_chunk_count=4),
        "ready",
        ".pdf indexed chunks ready",
    )

    jpg_stored = {
        "ingest_id": "20260523_000013",
        "source_filename": "photo_12345_42.jpg",
        "mime": "image/jpeg",
        "status": "stored",
    }
    assert_equal(infer_extraction_status(jpg_stored), "ocr_needed", ".jpg stored needs OCR")
    assert_true(needs_human_review(jpg_stored), ".jpg stored human review")

    jpg_failed = {
        "ingest_id": "20260523_000014",
        "source_filename": "photo_12345_43.jpg",
        "mime": "image/jpeg",
        "status": "ocr_failed",
    }
    assert_equal(infer_extraction_status(jpg_failed), "ocr_failed", ".jpg OCR failed")

    docx = {
        "ingest_id": "20260523_000015",
        "source_filename": "contrato.docx",
        "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "status": "stored",
    }
    assert_equal(infer_extraction_status(docx), "unsupported", ".docx unsupported")
    assert_true(needs_human_review(docx), ".docx human review")

    unknown = {"source_filename": "archive.bin", "mime": "application/octet-stream"}
    assert_equal(infer_extraction_status(unknown), "unsupported", "unknown unsupported")

    root_shape = {
        "ingest_id": "20260523_000016",
        "source_filename": "root_shape.pdf",
        "mime": "application/pdf",
        "sha256": "root-sha",
        "extracted_at_utc": "2026-05-23T12:00:00+00:00",
        "status": "extracted",
    }
    assert_equal(detect_supported_file_type(root_shape["source_filename"], root_shape["mime"])["file_type"], "pdf", "root file type")
    assert_equal(infer_extraction_status(root_shape, extracted_exists=True), "extracted", "root extracted shape")

    package_shape = {
        "ingest_id": "20260523_000017",
        "source_filename": "package_shape.pdf",
        "raw_path": "vfms_data/raw/20260523_000017__package_shape.pdf",
        "text_path": "vfms_data/extracted/20260523_000017.txt",
        "status": "indexed",
    }
    assert_equal(infer_extraction_status(package_shape), "ready", "package indexed shape")

    summary = document_capability_summary(package_shape)
    assert_equal(summary["ready_for_summary"], True, "summary ready")
    assert_no_path_or_hash(summary)

    print("PASS: document extraction readiness smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
