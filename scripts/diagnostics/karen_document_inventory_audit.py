#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.client_identity import KAREN_CHAT_ID  # noqa: E402
from core.document_summary_queries import (  # noqa: E402
    _find_ordered_document_inventory,
    _find_saved_specific_doc_summary,
    _looks_like_watermark_dominated_saved_summary,
    _looks_like_watermark_dominated_text,
)
from memory_store import get_active_case_id  # noqa: E402


VFMS_ROOT = ROOT / "vfms_data"
MANIFEST_PATH = VFMS_ROOT / "index" / "manifest.jsonl"
UPLOAD_ROOT = VFMS_ROOT / "telegram_uploads" / str(KAREN_CHAT_ID)
EXTRACTED_DIR = VFMS_ROOT / "extracted"
OCR_RUNTIME_DIR = VFMS_ROOT / "ocr_runtime"

LEGAL_MARKERS = (
    "JUZGADO",
    "AUTO",
    "OFICIO",
    "FINCA",
    "REGISTRO",
    "DEMANDA",
    "SECUESTRO",
    "EMBARGO",
    "MEDIDAS CAUTELARES",
)
RELEVANCE_TERMS = (
    "finca",
    "registro",
    "juzgado",
    "auto",
    "oficio",
    "demanda",
    "secuestro",
    "embargo",
    "medidas cautelares",
    "junc",
    "nora",
)
PRIVATE_BODY_GUARDS = (
    "copia para propósitos informativos solamente",
    "copia para propositos informativos solamente",
    "juzgado primero de circuito",
    "prescripción adquisitiva de dominio",
    "prescripcion adquisitiva de dominio",
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only Karen document inventory audit.")
    parser.add_argument("--limit", type=int, default=40, help="Maximum records to print. Default: 40.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args(argv)


def _clean_filename(filename: str) -> str:
    name = str(filename or "documento").strip()
    if "__" in name:
        name = name.split("__", 1)[1].strip()
    return name or "documento"


def _safe_category(path: str) -> str:
    raw = str(path or "")
    if "telegram_uploads" in raw:
        return "telegram_uploads"
    if "/raw/" in raw or raw.startswith("vfms_data/raw"):
        return "vfms_raw"
    if "/extracted/" in raw:
        return "vfms_extracted"
    if "/ocr_runtime/" in raw:
        return "vfms_ocr_runtime"
    if not raw:
        return "unknown"
    return "vfms"


def _read_text_limited(path: Path, limit: int = 250_000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception:
        return ""


def _marker_counts(text: str) -> dict[str, int]:
    upper = str(text or "").upper()
    return {marker: upper.count(marker) for marker in LEGAL_MARKERS if upper.count(marker)}


def _relevance(filename: str, caption: str = "", state: str = "", marker_counts: dict[str, int] | None = None) -> tuple[str, list[str]]:
    haystack = " ".join([filename or "", caption or "", state or ""]).lower()
    reasons = [term for term in RELEVANCE_TERMS if term in haystack]
    if marker_counts:
        reasons.extend([marker.lower() for marker, count in marker_counts.items() if count > 0])
    deduped = []
    for item in reasons:
        if item not in deduped:
            deduped.append(item)
    if len(deduped) >= 3:
        return "high", deduped[:8]
    if deduped:
        return "medium", deduped[:8]
    return "low", []


def _next_action(record: dict[str, Any]) -> str:
    relevance = record.get("possible_caso_finca_relevance")
    if record.get("ocr_status") == "available":
        return "Candidate: review OCR summary and link as source-labeled read-only case document."
    if record.get("extracted_text_status") == "watermark_dominated":
        return "Candidate: run/reuse OCR before linking; embedded text is watermark-dominated."
    if record.get("saved_summary_status") == "available" and relevance in {"high", "medium"}:
        return "Candidate: link saved summary metadata to Caso Finca after human review."
    if relevance in {"high", "medium"}:
        return "Candidate: review metadata and confirm relevance before case attachment."
    return "No immediate case link; keep in inventory."


def _manifest_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not MANIFEST_PATH.exists():
        return rows
    for line in MANIFEST_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except Exception:
            continue
        event_type = item.get("type") or item.get("event")
        if isinstance(item, dict) and event_type == "ingest":
            rows.append(item)
    return rows


def _upload_filenames() -> set[str]:
    if not UPLOAD_ROOT.exists():
        return set()
    return {path.name for path in UPLOAD_ROOT.iterdir() if path.is_file()}


def _manifest_by_upload() -> dict[str, dict[str, Any]]:
    uploads = _upload_filenames()
    out: dict[str, dict[str, Any]] = {}
    for row in _manifest_rows():
        source_filename = str(row.get("source_filename") or "").strip()
        stored_name = Path(str(row.get("stored_path") or "")).name
        for upload in uploads:
            if source_filename == upload or stored_name.endswith("__" + upload):
                out[upload] = row
                break
    return out


def _record_from_meta(meta: dict[str, Any], *, source: str, case_id: str = "", chat_id: int = 0) -> dict[str, Any]:
    ingest_id = str(meta.get("ingest_id") or "").strip()
    filename = _clean_filename(str(meta.get("filename") or meta.get("source_filename") or "documento"))
    caption = str(meta.get("caption") or "").strip()
    state = str(meta.get("state") or meta.get("status") or "").strip()
    created_at = str(meta.get("created_at") or meta.get("ingested_at_utc") or "").strip()
    path_category = _safe_category(str(meta.get("stored_path") or meta.get("raw_path") or ""))

    extracted_path = EXTRACTED_DIR / f"{ingest_id}.txt" if ingest_id else Path("")
    extracted_text = _read_text_limited(extracted_path) if ingest_id else ""
    marker_counts = _marker_counts(extracted_text)
    watermark = _looks_like_watermark_dominated_text(extracted_text) if extracted_text else False
    extracted_status = "missing"
    if extracted_text:
        extracted_status = "watermark_dominated" if watermark else "available"

    ocr_path = OCR_RUNTIME_DIR / f"{ingest_id}__ocr_runtime.txt" if ingest_id else Path("")
    ocr_status = "available" if ingest_id and ocr_path.exists() and ocr_path.stat().st_size > 0 else "missing"

    saved_summary_status = "unknown"
    if meta.get("saved_summary"):
        saved_summary_status = (
            "watermark_dominated"
            if _looks_like_watermark_dominated_saved_summary(str(meta.get("saved_summary") or ""))
            else "available"
        )
    elif case_id and chat_id and ingest_id:
        try:
            saved = _find_saved_specific_doc_summary(str(case_id), int(chat_id), ingest_id)
            saved_summary_status = (
                "watermark_dominated" if _looks_like_watermark_dominated_saved_summary(saved) else "available"
            ) if saved else "missing"
        except Exception:
            saved_summary_status = "unknown"

    relevance, reasons = _relevance(filename, caption, state, marker_counts)
    record = {
        "document_id": f"vfms:{ingest_id}" if ingest_id else f"upload:{filename}",
        "ingest_id": ingest_id,
        "filename": filename,
        "source_category": source,
        "path_category": path_category,
        "created_or_observed_at": created_at,
        "extracted_text_status": extracted_status,
        "extracted_char_count": len(extracted_text),
        "ocr_status": ocr_status,
        "saved_summary_status": saved_summary_status,
        "legal_marker_counts": marker_counts,
        "possible_caso_finca_relevance": relevance,
        "relevance_reasons": reasons,
    }
    record["safe_next_action"] = _next_action(record)
    return record


def _db_inventory(limit: int) -> tuple[list[dict[str, Any]], str, str]:
    try:
        case_id = get_active_case_id(int(KAREN_CHAT_ID))
        docs = _find_ordered_document_inventory(str(case_id), int(KAREN_CHAT_ID), limit=int(limit or 40))
        return [_record_from_meta(doc, source="case_notes:telegram_attachment_vfms", case_id=case_id, chat_id=int(KAREN_CHAT_ID)) for doc in docs], str(case_id), ""
    except Exception as exc:
        return [], "", f"DB inventory unavailable: {type(exc).__name__}: {exc}"


def _filesystem_inventory(limit: int) -> list[dict[str, Any]]:
    by_upload = _manifest_by_upload()
    used_uploads: set[str] = set()
    records: list[dict[str, Any]] = []

    def sort_key(item: tuple[str, dict[str, Any]]) -> str:
        return str(item[1].get("ingested_at_utc") or item[1].get("created_at") or item[0])

    for upload, meta in sorted(by_upload.items(), key=sort_key, reverse=True):
        used_uploads.add(upload)
        records.append(_record_from_meta(meta, source="telegram_uploads_metadata"))
        if len(records) >= int(limit or 40):
            return records

    for upload in sorted(_upload_filenames() - used_uploads, reverse=True):
        meta = {
            "source_filename": upload,
            "stored_path": str(UPLOAD_ROOT / upload),
            "ingested_at_utc": "",
        }
        records.append(_record_from_meta(meta, source="telegram_uploads_metadata"))
        if len(records) >= int(limit or 40):
            break
    return records


def build_inventory(limit: int = 40) -> dict[str, Any]:
    db_records, case_id, warning = _db_inventory(limit)
    fs_records = _filesystem_inventory(limit)

    records = db_records or fs_records
    source_mode = "case_notes_db" if db_records else "filesystem_fallback"
    totals = {
        "records": len(records),
        "ocr_available": sum(1 for item in records if item.get("ocr_status") == "available"),
        "saved_summary_available": sum(1 for item in records if item.get("saved_summary_status") == "available"),
        "high_or_medium_relevance": sum(1 for item in records if item.get("possible_caso_finca_relevance") in {"high", "medium"}),
    }
    return {
        "label": "Karen document inventory audit",
        "client_id": "karen",
        "chat_id": str(KAREN_CHAT_ID),
        "case_id": case_id or "unknown",
        "mode": source_mode,
        "warning": warning,
        "privacy": "Metadata-only. No raw OCR text, extracted text, full document body, hashes, or private payload dump.",
        "totals": totals,
        "records": records,
    }


def render_text(report: dict[str, Any]) -> str:
    lines = [
        "Karen document inventory audit",
        "================================",
        f"Mode: {report.get('mode')}",
        f"Case: {report.get('case_id')}",
        str(report.get("privacy")),
    ]
    if report.get("warning"):
        lines.append(f"Warning: {report.get('warning')}")
    totals = report.get("totals") or {}
    lines.extend([
        "",
        "Summary",
        f"- Records audited: {totals.get('records', 0)}",
        f"- OCR available: {totals.get('ocr_available', 0)}",
        f"- Saved summaries available: {totals.get('saved_summary_available', 0)}",
        f"- Possible Caso Finca relevance: {totals.get('high_or_medium_relevance', 0)}",
        "",
        "Metadata inventory",
    ])
    for idx, item in enumerate(report.get("records") or [], start=1):
        marker_summary = ", ".join(f"{key}:{value}" for key, value in (item.get("legal_marker_counts") or {}).items()) or "none"
        reasons = ", ".join(item.get("relevance_reasons") or []) or "none"
        lines.extend([
            f"{idx}. {item.get('filename') or 'documento'}",
            f"   document_id: {item.get('document_id')}",
            f"   source/path category: {item.get('source_category')} / {item.get('path_category')}",
            f"   OCR status: {item.get('ocr_status')}",
            f"   saved summary status: {item.get('saved_summary_status')}",
            f"   extracted text status: {item.get('extracted_text_status')} ({item.get('extracted_char_count')} chars)",
            f"   legal marker counts: {marker_summary}",
            f"   possible Caso Finca relevance: {item.get('possible_caso_finca_relevance')} ({reasons})",
            f"   safe next action: {item.get('safe_next_action')}",
        ])
    if not report.get("records"):
        lines.append("- No document metadata found. Check VFMS paths and DB access before asking Karen to re-upload.")
    lines.extend([
        "",
        "No mutation performed. No document deletion, migration, OCR execution, or case attachment was attempted.",
    ])
    text = "\n".join(lines)
    lowered = text.lower()
    for forbidden in PRIVATE_BODY_GUARDS:
        if forbidden in lowered:
            text = re.sub(re.escape(forbidden), "[body-redacted]", text, flags=re.I)
    return text


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    report = build_inventory(limit=max(1, int(args.limit or 40)))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
