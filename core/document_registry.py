from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


READY_STATUSES = {"ready", "indexed", "extracted"}
PENDING_STATUSES = {"stored", "registered", "ocr_needed", "needs_human_review"}
FAILED_STATUSES = {"failed", "ocr_failed", "unsupported"}


@dataclass(frozen=True)
class DocumentRecord:
    document_id: str
    client_id: str
    case_id: str
    chat_id: int
    ingest_id: str
    filename: str
    caption: str
    status: str
    hash: str
    mime_type: str
    source: str
    source_message_id: int | None = None
    stored_path: str | None = None
    extracted_path: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


def normalize_document_status(status: str | None) -> str:
    raw = (status or "").strip().lower()
    if not raw:
        return "stored"

    normalized = raw.replace("_", " ").replace("-", " ")
    normalized = " ".join(normalized.split())

    if normalized in {"ready", "listo", "lista"}:
        return "ready"
    if normalized in {"indexed", "indexado", "indexada"}:
        return "indexed"
    if normalized in {"extracted", "extraido", "extraído", "extraida", "extraída"}:
        return "extracted"
    if "texto extra" in normalized and "index" in normalized:
        return "indexed"
    if "texto extra" in normalized:
        return "extracted"
    if "ocr" in normalized and ("fail" in normalized or "fall" in normalized):
        return "ocr_failed"
    if "unsupported" in normalized or "no soport" in normalized:
        return "unsupported"
    if "ocr" in normalized or "revision manual" in normalized or "revisión manual" in normalized:
        return "ocr_needed"
    if "registr" in normalized:
        return "registered"
    if "guard" in normalized or "stored" in normalized:
        return "stored"
    if "fail" in normalized or "fall" in normalized or "error" in normalized:
        return "failed"

    return normalized.replace(" ", "_")


def document_record_from_vfms_metadata(
    *,
    client_id: str,
    case_id: str,
    chat_id: int,
    metadata: dict[str, Any],
    caption: str = "",
    status: str | None = None,
    source: str = "vfms",
    source_message_id: int | None = None,
) -> DocumentRecord:
    ingest_id = str(metadata.get("ingest_id") or "").strip()
    filename = str(
        metadata.get("filename")
        or metadata.get("source_filename")
        or metadata.get("stored_filename")
        or "documento"
    ).strip()
    sha = str(metadata.get("sha256") or metadata.get("hash") or "").strip()
    mime_type = str(metadata.get("mime") or metadata.get("mime_type") or "").strip()
    stored_path = metadata.get("stored_path") or metadata.get("raw_path")
    extracted_path = metadata.get("extracted_path") or metadata.get("text_path")
    created_at = str(
        metadata.get("created_at")
        or metadata.get("ingested_at_utc")
        or metadata.get("created_at_utc")
        or datetime.now(timezone.utc).isoformat()
    )
    document_id = str(
        metadata.get("document_id")
        or (f"vfms:{ingest_id}" if ingest_id else f"document:{client_id}:{case_id}:{chat_id}:{filename}")
    )

    return DocumentRecord(
        document_id=document_id,
        client_id=str(client_id),
        case_id=str(case_id),
        chat_id=int(chat_id),
        ingest_id=ingest_id,
        filename=filename or "documento",
        caption=(caption or str(metadata.get("caption") or "")).strip(),
        status=normalize_document_status(status or metadata.get("status") or metadata.get("state")),
        hash=sha,
        mime_type=mime_type,
        source=source,
        source_message_id=source_message_id,
        stored_path=str(stored_path) if stored_path else None,
        extracted_path=str(extracted_path) if extracted_path else None,
        created_at=created_at,
        metadata=dict(metadata or {}),
    )


def is_document_ready_for_summary(record: DocumentRecord) -> bool:
    return bool(record.ingest_id and normalize_document_status(record.status) in READY_STATUSES)


def safe_document_summary(record: DocumentRecord) -> dict[str, Any]:
    return {
        "document_id": record.document_id,
        "client_id": record.client_id,
        "case_id": record.case_id,
        "chat_id": int(record.chat_id),
        "ingest_id": record.ingest_id,
        "filename": record.filename,
        "caption": record.caption,
        "status": normalize_document_status(record.status),
        "mime_type": record.mime_type,
        "source": record.source,
        "source_message_id": record.source_message_id,
        "created_at": record.created_at,
        "ready_for_summary": is_document_ready_for_summary(record),
    }
