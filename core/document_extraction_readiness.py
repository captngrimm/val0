from __future__ import annotations

from pathlib import PurePath
from typing import Any

from core.document_registry import DocumentRecord, normalize_document_status


SAFE_STATUSES = {
    "stored",
    "extracted",
    "indexed",
    "ocr_needed",
    "ocr_failed",
    "unsupported",
    "ready",
    "needs_human_review",
}

TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".tsv", ".log"}
PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}
DOCX_EXTENSIONS = {".docx"}

TEXT_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "text/csv",
    "text/tab-separated-values",
}
PDF_MIME_TYPES = {"application/pdf"}
IMAGE_MIME_PREFIX = "image/"
DOCX_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _as_metadata(record_or_metadata: DocumentRecord | dict[str, Any]) -> dict[str, Any]:
    if isinstance(record_or_metadata, DocumentRecord):
        metadata = dict(record_or_metadata.metadata or {})
        metadata.update(
            {
                "document_id": record_or_metadata.document_id,
                "ingest_id": record_or_metadata.ingest_id,
                "filename": record_or_metadata.filename,
                "caption": record_or_metadata.caption,
                "status": record_or_metadata.status,
                "mime_type": record_or_metadata.mime_type,
                "source": record_or_metadata.source,
                "source_message_id": record_or_metadata.source_message_id,
                "created_at": record_or_metadata.created_at,
            }
        )
        return metadata
    return dict(record_or_metadata or {})


def _filename_from_metadata(metadata: dict[str, Any]) -> str:
    return str(
        metadata.get("filename")
        or metadata.get("source_filename")
        or metadata.get("stored_filename")
        or metadata.get("raw_path")
        or metadata.get("stored_path")
        or ""
    ).strip()


def _mime_from_metadata(metadata: dict[str, Any]) -> str:
    return str(metadata.get("mime_type") or metadata.get("mime") or "").strip().lower()


def _status_from_metadata(metadata: dict[str, Any]) -> str:
    return normalize_document_status(metadata.get("status") or metadata.get("state") or "")


def detect_supported_file_type(filename: str | None = None, mime_type: str | None = None) -> dict[str, Any]:
    raw_filename = (filename or "").strip()
    raw_mime = (mime_type or "").strip().lower()
    extension = PurePath(raw_filename).suffix.lower()

    file_type = "unsupported"
    can_extract_text = False
    can_ocr = False
    auto_extract_currently_wired = False
    requires_human_review = True
    reason = "unsupported_file_type"

    if extension in TEXT_EXTENSIONS or raw_mime in TEXT_MIME_TYPES or raw_mime.startswith("text/"):
        file_type = "text"
        can_extract_text = True
        auto_extract_currently_wired = True
        requires_human_review = False
        reason = "text_extractable"
    elif extension in PDF_EXTENSIONS or raw_mime in PDF_MIME_TYPES:
        file_type = "pdf"
        can_extract_text = True
        can_ocr = True
        auto_extract_currently_wired = True
        requires_human_review = False
        reason = "pdf_extractable_with_optional_ocr"
    elif extension in IMAGE_EXTENSIONS or raw_mime.startswith(IMAGE_MIME_PREFIX):
        file_type = "image"
        can_ocr = True
        requires_human_review = True
        reason = "image_requires_ocr_or_manual_review"
    elif extension in DOCX_EXTENSIONS or raw_mime in DOCX_MIME_TYPES:
        file_type = "docx"
        reason = "docx_unsupported_for_now"

    return {
        "file_type": file_type,
        "extension": extension,
        "mime_type": raw_mime,
        "can_extract_text": can_extract_text,
        "can_ocr": can_ocr,
        "auto_extract_currently_wired": auto_extract_currently_wired,
        "requires_human_review": requires_human_review,
        "reason": reason,
    }


def infer_extraction_status(
    record_or_metadata: DocumentRecord | dict[str, Any],
    *,
    extracted_exists: bool | None = None,
    indexed_chunk_count: int | None = None,
) -> str:
    metadata = _as_metadata(record_or_metadata)
    capability = detect_supported_file_type(
        filename=_filename_from_metadata(metadata),
        mime_type=_mime_from_metadata(metadata),
    )
    normalized_status = _status_from_metadata(metadata)

    if normalized_status not in SAFE_STATUSES:
        normalized_status = "stored"

    if capability["file_type"] in {"unsupported", "docx"}:
        return "unsupported"

    if normalized_status in {"ocr_failed", "unsupported", "needs_human_review"}:
        return normalized_status

    if indexed_chunk_count is not None and int(indexed_chunk_count) > 0:
        return "ready"

    if normalized_status in {"ready", "indexed"}:
        return "ready"

    if extracted_exists is True or normalized_status == "extracted":
        return "extracted"

    if capability["file_type"] == "image":
        if normalized_status == "ocr_needed":
            return "ocr_needed"
        return "ocr_needed"

    if normalized_status == "ocr_needed":
        return "ocr_needed"

    return "stored"


def needs_human_review(record_or_metadata: DocumentRecord | dict[str, Any]) -> bool:
    status = infer_extraction_status(record_or_metadata)
    if status in {"ocr_needed", "ocr_failed", "unsupported", "needs_human_review"}:
        return True

    metadata = _as_metadata(record_or_metadata)
    capability = detect_supported_file_type(
        filename=_filename_from_metadata(metadata),
        mime_type=_mime_from_metadata(metadata),
    )
    return bool(capability["requires_human_review"] and status != "ready")


def document_capability_summary(record_or_metadata: DocumentRecord | dict[str, Any]) -> dict[str, Any]:
    metadata = _as_metadata(record_or_metadata)
    filename = _filename_from_metadata(metadata)
    capability = detect_supported_file_type(filename=filename, mime_type=_mime_from_metadata(metadata))
    status = infer_extraction_status(metadata)

    return {
        "document_id": str(metadata.get("document_id") or ""),
        "ingest_id": str(metadata.get("ingest_id") or ""),
        "filename": filename,
        "status": status,
        "file_type": capability["file_type"],
        "extension": capability["extension"],
        "mime_type": capability["mime_type"],
        "ready_for_summary": status == "ready",
        "needs_human_review": needs_human_review(metadata),
        "can_extract_text": capability["can_extract_text"],
        "can_ocr": capability["can_ocr"],
        "auto_extract_currently_wired": capability["auto_extract_currently_wired"],
        "reason": capability["reason"],
    }
