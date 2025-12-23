#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

DATA_ROOT = Path("vfms_data")
RAW_DIR = DATA_ROOT / "raw"
EXTRACTED_DIR = DATA_ROOT / "extracted"
INDEX_DIR = DATA_ROOT / "index"
MANIFEST = INDEX_DIR / "manifest.jsonl"

def utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def make_ingest_id() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

def append_manifest(rec: dict) -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def find_raw_by_ingest_id(ingest_id: str) -> Path:
    if not RAW_DIR.exists():
        raise SystemExit("ERROR: vfms_data/raw does not exist")
    matches = sorted(RAW_DIR.glob(f"{ingest_id}__*"))
    if not matches:
        raise SystemExit(f"ERROR: no raw file found for ingest_id {ingest_id}")
    if len(matches) > 1:
        raise SystemExit(f"ERROR: multiple raw files found for ingest_id {ingest_id}: {[m.name for m in matches]}")
    return matches[0]

def ingest_file(src_path: Path) -> str:
    if not src_path.exists() or not src_path.is_file():
        raise SystemExit(f"ERROR: file not found: {src_path}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    ingest_id = make_ingest_id()
    dest_name = f"{ingest_id}__{src_path.name}"
    dest_path = RAW_DIR / dest_name

    shutil.copy2(src_path, dest_path)
    digest = sha256_of(dest_path)

    rec = {
        "type": "ingest",
        "ingest_id": ingest_id,
        "source_filename": src_path.name,
        "stored_path": str(dest_path),
        "mime": None,  # v0: optional
        "sha256": digest,
        "ingested_at_utc": utc_now(),
        "extracted": False,
        "extracted_at_utc": None,
        "ocr_used": None,
        "text_path": None,
        "meta_path": None,
        "notes": ""
    }
    append_manifest(rec)

    print(f"Ingested: {src_path.name}")
    print(f"ingest_id: {ingest_id}")
    print(f"stored_as: {dest_path}")
    return ingest_id

def run_pdftotext(pdf_path: Path, out_txt: Path) -> tuple[bool, int]:
    """
    Uses poppler's pdftotext if available. Returns (success, pages_guess).
    pages_guess is best-effort; 0 if unknown.
    """
    try:
        # -layout preserves tables better
        subprocess.run(["pdftotext", "-layout", str(pdf_path), str(out_txt)], check=True)
        return True, 0
    except FileNotFoundError:
        return False, 0
    except subprocess.CalledProcessError:
        return False, 0

def extract_text_only(src_path: Path, out_txt: Path) -> None:
    # Plain text / md / etc: copy as extracted text (normalized to UTF-8)
    data = src_path.read_bytes()
    try:
        txt = data.decode("utf-8")
    except UnicodeDecodeError:
        # fallback: latin-1 to avoid crashes; still v0-safe
        txt = data.decode("latin-1", errors="replace")
    out_txt.write_text(txt, encoding="utf-8")

def extract(ingest_id: str, ocr_mode: str) -> None:
    raw_path = find_raw_by_ingest_id(ingest_id)
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    out_txt = EXTRACTED_DIR / f"{ingest_id}.txt"
    out_meta = EXTRACTED_DIR / f"{ingest_id}.json"

    suffix = raw_path.suffix.lower()
    ocr_used = None
    engine = None
    pages = None

    # Minimal branching: PDF -> pdftotext; text-like -> direct; images -> require OCR tool (future slice if needed)
    if suffix == ".pdf":
        engine = "pdftotext"
        ok, pages_guess = run_pdftotext(raw_path, out_txt)
        if not ok:
            raise SystemExit("ERROR: pdftotext not available or failed. Install poppler-utils or use a different extraction method.")
        pages = pages_guess or None
        ocr_used = False
    elif suffix in [".txt", ".md", ".csv", ".log"]:
        engine = "direct"
        extract_text_only(raw_path, out_txt)
        pages = None
        ocr_used = False
    elif suffix in [".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"]:
        # v0-safe: OCR is allowed when applicable, but only when explicitly invoked (this command).
        # Requires tesseract installed.
        if ocr_mode == "off":
            raise SystemExit("ERROR: OCR is off but the input is an image. Re-run with --ocr auto or --ocr force.")
        engine = "tesseract"
        try:
            subprocess.run(["tesseract", str(raw_path), str(out_txt.with_suffix(''))], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            raise SystemExit("ERROR: tesseract not installed. Install tesseract-ocr to extract from images.")
        except subprocess.CalledProcessError:
            raise SystemExit("ERROR: tesseract failed on this image.")
        # tesseract writes .txt automatically
        if not out_txt.exists():
            raise SystemExit("ERROR: tesseract did not produce output text.")
        ocr_used = True
        pages = None
    else:
        raise SystemExit(f"ERROR: unsupported file type for extraction in v0: {suffix}")

    meta = {
        "type": "extract",
        "ingest_id": ingest_id,
        "raw_path": str(raw_path),
        "text_path": str(out_txt),
        "ocr_used": ocr_used,
        "engine": engine,
        "created_at_utc": utc_now(),
        "pages": pages,
    }
    out_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Append an update record to manifest (append-only audit trail)
    append_manifest({
        "type": "extract_update",
        "ingest_id": ingest_id,
        "extracted": True,
        "extracted_at_utc": utc_now(),
        "ocr_used": ocr_used,
        "text_path": str(out_txt),
        "meta_path": str(out_meta),
        "engine": engine
    })

    print(f"Extracted ingest_id: {ingest_id}")
    print(f"text: {out_txt}")
    print(f"meta: {out_meta}")
    print(f"ocr_used: {ocr_used}, engine: {engine}")

def main():
    ap = argparse.ArgumentParser(prog="vfms", description="VFMS v0 (manual triggers only)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_ingest = sub.add_parser("ingest", help="Manually ingest a file into vfms_data/raw and manifest.jsonl")
    p_ingest.add_argument("path", help="Path to a file to ingest")

    p_ext = sub.add_parser("extract", help="Extract text for an ingest_id (manual; no background)")
    p_ext.add_argument("ingest_id", help="Ingest ID to extract")
    p_ext.add_argument("--ocr", choices=["auto", "force", "off"], default="auto", help="OCR mode (only applies to images)")

    args = ap.parse_args()

    if args.cmd == "ingest":
        ingest_file(Path(args.path))
    elif args.cmd == "extract":
        extract(args.ingest_id, args.ocr)

if __name__ == "__main__":
    main()
