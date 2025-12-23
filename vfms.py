#!/usr/bin/env python3
"""
VFMS v0 — Val File / Forge Memory System (Phase 0 only)

Manual triggers only:
- ingest file
- extract text (OCR if needed)
- index extracted text
- query index (directed retrieval)
- generate Markdown output (grounded; no invention)

Golden rule: if it can't be explained in 30 seconds, it doesn't belong in v0.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


# -----------------------------
# Paths / constants
# -----------------------------
REPO_ROOT = Path(__file__).resolve().parent
DATA_ROOT = REPO_ROOT / "vfms_data"

RAW_DIR = DATA_ROOT / "raw"
EXTRACTED_DIR = DATA_ROOT / "extracted"
INDEX_DIR = DATA_ROOT / "index"
OUTPUTS_DIR = DATA_ROOT / "outputs"
TMP_DIR = DATA_ROOT / "tmp"

DB_PATH = INDEX_DIR / "vfms.sqlite"
MANIFEST_PATH = INDEX_DIR / "manifest.jsonl"

DEFAULT_CHUNK_CHARS = 1200
DEFAULT_TOP_K = 5


# -----------------------------
# Utilities
# -----------------------------
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def ensure_dirs() -> None:
    for d in (RAW_DIR, EXTRACTED_DIR, INDEX_DIR, OUTPUTS_DIR, TMP_DIR):
        d.mkdir(parents=True, exist_ok=True)


def next_ingest_id() -> str:
    """
    Monotonic-ish ingest id: YYYYMMDD_NNNNNN
    Uses a counter file under index/ to avoid collisions.
    """
    ensure_dirs()
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    counter_path = INDEX_DIR / f"counter_{day}.txt"
    n = 0
    if counter_path.exists():
        try:
            n = int(counter_path.read_text().strip())
        except Exception:
            n = 0
    n += 1
    counter_path.write_text(str(n))
    return f"{day}_{n:06d}"


def guess_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"


def write_manifest(event: dict) -> None:
    ensure_dirs()
    with MANIFEST_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def open_db() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS docs (
            ingest_id TEXT PRIMARY KEY,
            source_filename TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            mime TEXT NOT NULL,
            ingested_at_utc TEXT NOT NULL,
            extracted_at_utc TEXT,
            ocr_used INTEGER,
            pages INTEGER
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            ingest_id TEXT NOT NULL,
            page INTEGER,
            chunk_text TEXT NOT NULL,
            created_at_utc TEXT NOT NULL,
            FOREIGN KEY (ingest_id) REFERENCES docs(ingest_id)
        )
        """
    )

    # Try to create an FTS5 table for chunk search. If unavailable, we fall back to LIKE.
    try:
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
            USING fts5(chunk_id, ingest_id, chunk_text, tokenize='porter');
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
                INSERT INTO chunks_fts(chunk_id, ingest_id, chunk_text)
                VALUES (new.chunk_id, new.ingest_id, new.chunk_text);
            END;
            """
        )
    except sqlite3.OperationalError:
        # FTS5 not available; OK for v0.
        pass

    conn.commit()


# -----------------------------
# Extraction
# -----------------------------
@dataclass
class ExtractionResult:
    text: str
    ocr_used: bool
    pages: Optional[int]
    engine: str


def _extract_pdf_text_pypdf(pdf_path: Path) -> Tuple[str, int]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as e:
        raise RuntimeError("Missing dependency: pypdf (pip install pypdf)") from e

    reader = PdfReader(str(pdf_path))
    pages = len(reader.pages)
    parts: List[str] = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        t = t.strip()
        if t:
            parts.append(f"\n\n--- Page {i} ---\n{t}")
    return ("\n".join(parts).strip(), pages)


def _ocr_image_pytesseract(img_path: Path) -> str:
    try:
        from PIL import Image  # type: ignore
    except Exception as e:
        raise RuntimeError("Missing dependency: Pillow (pip install pillow)") from e
    try:
        import pytesseract  # type: ignore
    except Exception as e:
        raise RuntimeError("Missing dependency: pytesseract (pip install pytesseract) and system tesseract-ocr") from e

    img = Image.open(str(img_path))
    return (pytesseract.image_to_string(img) or "").strip()


def _ocr_pdf_via_pdf2image(pdf_path: Path) -> Tuple[str, int]:
    """
    Optional OCR path for scanned PDFs. Requires pdf2image + poppler installed on system.
    This is best-effort and only used when --ocr force or auto with low-yield text.
    """
    try:
        from pdf2image import convert_from_path  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "OCR for scanned PDFs requires pdf2image (pip install pdf2image) and poppler on the system."
        ) from e

    try:
        import pytesseract  # type: ignore
    except Exception as e:
        raise RuntimeError("Missing dependency: pytesseract (pip install pytesseract) and system tesseract-ocr") from e

    images = convert_from_path(str(pdf_path))
    pages = len(images)
    parts: List[str] = []
    for i, img in enumerate(images, start=1):
        t = (pytesseract.image_to_string(img) or "").strip()
        if t:
            parts.append(f"\n\n--- Page {i} (OCR) ---\n{t}")
    return ("\n".join(parts).strip(), pages)


def extract_text(path: Path, ocr_mode: str) -> ExtractionResult:
    """
    ocr_mode: 'auto' | 'force' | 'off'
    """
    mime = guess_mime(path)
    suffix = path.suffix.lower()

    # Text files
    if mime.startswith("text/") or suffix in {".txt", ".md", ".log"}:
        try:
            return ExtractionResult(text=path.read_text(encoding="utf-8", errors="replace").strip(),
                                   ocr_used=False, pages=None, engine="text")
        except Exception:
            return ExtractionResult(text=path.read_text(errors="replace").strip(),
                                   ocr_used=False, pages=None, engine="text")

    # Images
    if mime.startswith("image/") or suffix in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}:
        if ocr_mode == "off":
            raise RuntimeError("OCR is required to extract text from images; run with --ocr auto or --ocr force.")
        txt = _ocr_image_pytesseract(path)
        return ExtractionResult(text=txt, ocr_used=True, pages=None, engine="pytesseract")

    # PDFs
    if mime == "application/pdf" or suffix == ".pdf":
        text, pages = _extract_pdf_text_pypdf(path)
        # Decide whether to OCR
        if ocr_mode == "off":
            return ExtractionResult(text=text, ocr_used=False, pages=pages, engine="pypdf")

        low_yield = len(text.strip()) < 200  # heuristic; safe for v0
        if ocr_mode == "force" or (ocr_mode == "auto" and low_yield):
            ocr_text, ocr_pages = _ocr_pdf_via_pdf2image(path)
            # If OCR produces nothing, keep original extraction too (still grounded)
            merged = "\n".join([t for t in [text.strip(), ocr_text.strip()] if t])
            return ExtractionResult(text=merged.strip(), ocr_used=True, pages=ocr_pages or pages, engine="pypdf+ocr")

        return ExtractionResult(text=text, ocr_used=False, pages=pages, engine="pypdf")

    raise RuntimeError(f"Unsupported file type for extraction: {mime} ({path.name})")


# -----------------------------
# Chunking / indexing
# -----------------------------
def chunk_text(full_text: str, max_chars: int = DEFAULT_CHUNK_CHARS) -> List[str]:
    """
    Minimal chunker: paragraph-based packing up to max_chars.
    No fancy tokenizers in v0.
    """
    text = (full_text or "").strip()
    if not text:
        return []

    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    buf: List[str] = []
    size = 0

    for p in paras:
        if size + len(p) + 2 > max_chars and buf:
            chunks.append("\n\n".join(buf).strip())
            buf = [p]
            size = len(p)
        else:
            buf.append(p)
            size += len(p) + 2

    if buf:
        chunks.append("\n\n".join(buf).strip())

    return [c for c in chunks if c]


def index_ingest(conn: sqlite3.Connection, ingest_id: str, extracted_txt: str, pages: Optional[int]) -> int:
    # Remove old chunks for re-index (manual, explicit)
    conn.execute("DELETE FROM chunks WHERE ingest_id = ?", (ingest_id,))
    try:
        conn.execute("DELETE FROM chunks_fts WHERE ingest_id = ?", (ingest_id,))
    except sqlite3.OperationalError:
        pass

    chunks = chunk_text(extracted_txt, DEFAULT_CHUNK_CHARS)
    created = utc_now_iso()
    for i, c in enumerate(chunks, start=1):
        chunk_id = f"{ingest_id}_c{i:04d}"
        conn.execute(
            "INSERT INTO chunks(chunk_id, ingest_id, page, chunk_text, created_at_utc) VALUES (?, ?, ?, ?, ?)",
            (chunk_id, ingest_id, None, c, created),
        )
    if pages is not None:
        conn.execute("UPDATE docs SET pages = COALESCE(pages, ?) WHERE ingest_id = ?", (pages, ingest_id))

    conn.commit()
    return len(chunks)


def query_chunks(conn: sqlite3.Connection, q: str, top_k: int, ingest_filter: Optional[str]) -> List[Tuple[str, str, Optional[int], str]]:
    """
    Returns list of (chunk_id, ingest_id, page, chunk_text).
    """
    q = (q or "").strip()
    if not q:
        return []

    # Prefer FTS if available
    try:
        if ingest_filter:
            rows = conn.execute(
                """
                SELECT c.chunk_id, c.ingest_id, c.page, c.chunk_text
                FROM chunks_fts f
                JOIN chunks c ON c.chunk_id = f.chunk_id
                WHERE chunks_fts MATCH ? AND c.ingest_id = ?
                LIMIT ?
                """,
                (q, ingest_filter, top_k),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT c.chunk_id, c.ingest_id, c.page, c.chunk_text
                FROM chunks_fts f
                JOIN chunks c ON c.chunk_id = f.chunk_id
                WHERE chunks_fts MATCH ?
                LIMIT ?
                """,
                (q, top_k),
            ).fetchall()
        return rows
    except sqlite3.OperationalError:
        # FTS not available; fallback to LIKE
        like = f"%{q}%"
        if ingest_filter:
            rows = conn.execute(
                """
                SELECT chunk_id, ingest_id, page, chunk_text
                FROM chunks
                WHERE ingest_id = ? AND chunk_text LIKE ?
                LIMIT ?
                """,
                (ingest_filter, like, top_k),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT chunk_id, ingest_id, page, chunk_text
                FROM chunks
                WHERE chunk_text LIKE ?
                LIMIT ?
                """,
                (like, top_k),
            ).fetchall()
        return rows


def get_doc_meta(conn: sqlite3.Connection, ingest_id: str) -> Optional[Tuple[str, str]]:
    row = conn.execute(
        "SELECT source_filename, stored_path FROM docs WHERE ingest_id = ?",
        (ingest_id,),
    ).fetchone()
    return row if row else None


# -----------------------------
# Commands
# -----------------------------
def cmd_ingest(args: argparse.Namespace) -> int:
    ensure_dirs()
    src = Path(args.path).expanduser().resolve()
    if not src.exists():
        print(f"ERROR: file not found: {src}", file=sys.stderr)
        return 2

    ingest_id = next_ingest_id()
    dest = RAW_DIR / f"{ingest_id}__{src.name}"
    shutil.copy2(str(src), str(dest))

    sha = sha256_file(dest)
    mime = guess_mime(dest)

    event = {
        "event": "ingest",
        "ingest_id": ingest_id,
        "source_filename": src.name,
        "stored_path": str(dest),
        "mime": mime,
        "sha256": sha,
        "ingested_at_utc": utc_now_iso(),
    }
    write_manifest(event)

    conn = open_db()
    init_db(conn)
    conn.execute(
        """
        INSERT OR REPLACE INTO docs(ingest_id, source_filename, stored_path, sha256, mime, ingested_at_utc)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (ingest_id, src.name, str(dest), sha, mime, event["ingested_at_utc"]),
    )
    conn.commit()
    conn.close()

    print(ingest_id)
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    ensure_dirs()
    ingest_id = args.ingest_id.strip()
    conn = open_db()
    init_db(conn)
    row = conn.execute("SELECT stored_path, source_filename FROM docs WHERE ingest_id = ?", (ingest_id,)).fetchone()
    conn.close()
    if not row:
        print(f"ERROR: unknown ingest_id: {ingest_id}", file=sys.stderr)
        return 2

    stored_path = Path(row[0])
    ocr_mode = args.ocr.lower()
    if ocr_mode not in {"auto", "force", "off"}:
        print("ERROR: --ocr must be one of: auto|force|off", file=sys.stderr)
        return 2

    result = extract_text(stored_path, ocr_mode)
    if not result.text.strip():
        print("WARN: extracted text is empty.", file=sys.stderr)

    text_path = EXTRACTED_DIR / f"{ingest_id}.txt"
    meta_path = EXTRACTED_DIR / f"{ingest_id}.json"

    text_path.write_text(result.text, encoding="utf-8", errors="replace")

    meta = {
        "ingest_id": ingest_id,
        "source_filename": row[1],
        "stored_path": str(stored_path),
        "created_at_utc": utc_now_iso(),
        "pages": result.pages,
        "ocr_used": result.ocr_used,
        "engine": result.engine,
        "note": "Extraction artifact (assistive, read-only).",
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    write_manifest({
        "event": "extract",
        "ingest_id": ingest_id,
        "extracted_at_utc": meta["created_at_utc"],
        "ocr_used": result.ocr_used,
        "engine": result.engine,
        "text_path": str(text_path),
        "meta_path": str(meta_path),
    })

    conn = open_db()
    init_db(conn)
    conn.execute(
        """
        UPDATE docs
        SET extracted_at_utc = ?, ocr_used = ?, pages = COALESCE(pages, ?)
        WHERE ingest_id = ?
        """,
        (meta["created_at_utc"], 1 if result.ocr_used else 0, result.pages, ingest_id),
    )
    conn.commit()
    conn.close()

    print(f"OK: extracted -> {text_path}")
    print(f"OK: meta -> {meta_path}")
    print(f"OCR_USED: {result.ocr_used}")
    return 0


def cmd_index(args: argparse.Namespace) -> int:
    ensure_dirs()
    conn = open_db()
    init_db(conn)

    ingest_ids: List[str] = []
    if args.all:
        ingest_ids = [r[0] for r in conn.execute("SELECT ingest_id FROM docs WHERE extracted_at_utc IS NOT NULL").fetchall()]
        if not ingest_ids:
            print("ERROR: no extracted docs to index. Run: vfms extract <ingest_id>", file=sys.stderr)
            conn.close()
            return 2
    else:
        ingest_ids = [args.ingest_id.strip()]

    total_chunks = 0
    for ingest_id in ingest_ids:
        text_path = EXTRACTED_DIR / f"{ingest_id}.txt"
        if not text_path.exists():
            print(f"ERROR: missing extracted text for {ingest_id}. Run: vfms extract {ingest_id}", file=sys.stderr)
            conn.close()
            return 2
        txt = text_path.read_text(encoding="utf-8", errors="replace")
        pages_row = conn.execute("SELECT pages FROM docs WHERE ingest_id = ?", (ingest_id,)).fetchone()
        pages = pages_row[0] if pages_row else None
        n = index_ingest(conn, ingest_id, txt, pages)
        total_chunks += n
        print(f"OK: indexed {ingest_id} -> {n} chunks")

    conn.close()
    print(f"TOTAL_CHUNKS_INDEXED: {total_chunks}")
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    conn = open_db()
    init_db(conn)
    q = args.query
    top_k = int(args.top or DEFAULT_TOP_K)
    ingest_filter = args.doc.strip() if args.doc else None

    rows = query_chunks(conn, q, top_k, ingest_filter)
    if not rows:
        print("NO_RESULTS")
        conn.close()
        return 0

    for rank, (chunk_id, ingest_id, page, chunk_text) in enumerate(rows, start=1):
        meta = get_doc_meta(conn, ingest_id)
        filename = meta[0] if meta else ingest_id
        page_str = f"page {page}" if page is not None else "page ?"
        excerpt = chunk_text.strip().replace("\n", " ")
        if len(excerpt) > 260:
            excerpt = excerpt[:257] + "..."
        print(f"{rank}) {filename} | ingest_id={ingest_id} | {page_str} | chunk_id={chunk_id}")
        print(f"   {excerpt}")
        print()

    conn.close()
    return 0


def cmd_summarize(args: argparse.Namespace) -> int:
    """
    Grounded markdown generator (no LLM). Uses retrieved chunks as the only source.
    """
    conn = open_db()
    init_db(conn)

    instruction = (args.instruction or "").strip()
    q = (args.query or "").strip()
    top_k = int(args.top or 8)
    ingest_filter = args.doc.strip() if args.doc else None

    if not q:
        print("ERROR: summarize requires --query", file=sys.stderr)
        conn.close()
        return 2

    rows = query_chunks(conn, q, top_k, ingest_filter)
    if not rows:
        print("NO_RESULTS")
        conn.close()
        return 0

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = Path(args.out).expanduser().resolve() if args.out else (OUTPUTS_DIR / f"{run_id}__summary.md")

    lines: List[str] = []
    lines.append("# VFMS v0 — Markdown Output")
    lines.append("")
    if instruction:
        lines.append(f"**Instruction:** {instruction}")
        lines.append("")
    lines.append(f"**Query:** {q}")
    lines.append("")
    lines.append("## Retrieved excerpts (grounded sources)")
    lines.append("")
    for chunk_id, ingest_id, page, chunk_text in rows:
        meta = get_doc_meta(conn, ingest_id)
        filename = meta[0] if meta else ingest_id
        page_str = str(page) if page is not None else "?"
        lines.append(f"### Source: {filename} (ingest_id {ingest_id}), page {page_str}, chunk {chunk_id}")
        lines.append("")
        lines.append("```text")
        lines.append(chunk_text.strip())
        lines.append("```")
        lines.append("")

    # Minimal "summary" section: extractive bullets only (no invention).
    lines.append("## Notes (extractive, no inference)")
    lines.append("")
    for chunk_id, ingest_id, page, chunk_text in rows[: min(5, len(rows))]:
        meta = get_doc_meta(conn, ingest_id)
        filename = meta[0] if meta else ingest_id
        snippet = chunk_text.strip().splitlines()[0].strip()
        if len(snippet) > 180:
            snippet = snippet[:177] + "..."
        lines.append(f"- {snippet} *(Source: {filename}, chunk {chunk_id})*")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8", errors="replace")

    conn.close()
    print(f"OK: wrote -> {out_path}")
    return 0


# -----------------------------
# CLI
# -----------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vfms", description="VFMS v0 (manual triggers only)")
    sp = p.add_subparsers(dest="cmd", required=True)

    p_ing = sp.add_parser("ingest", help="Ingest a file into vfms_data/raw")
    p_ing.add_argument("path", help="Path to file")
    p_ing.set_defaults(func=cmd_ingest)

    p_ext = sp.add_parser("extract", help="Extract text (OCR if needed) into vfms_data/extracted")
    p_ext.add_argument("ingest_id", help="Ingest id from vfms ingest")
    p_ext.add_argument("--ocr", default="auto", help="auto|force|off (default: auto)")
    p_ext.set_defaults(func=cmd_extract)

    p_idx = sp.add_parser("index", help="Index extracted text into sqlite")
    g = p_idx.add_mutually_exclusive_group(required=True)
    g.add_argument("ingest_id", nargs="?", help="Ingest id to index")
    g.add_argument("--all", action="store_true", help="Index all extracted docs")
    p_idx.set_defaults(func=cmd_index)

    p_q = sp.add_parser("query", help="Query the index (directed retrieval)")
    p_q.add_argument("query", help="Query text")
    p_q.add_argument("--top", default=str(DEFAULT_TOP_K), help="Top K results (default 5)")
    p_q.add_argument("--doc", default=None, help="Filter to a single ingest_id")
    p_q.set_defaults(func=cmd_query)

    p_s = sp.add_parser("summarize", help="Generate grounded Markdown output from retrieval")
    p_s.add_argument("instruction", help="Instruction text (used as header only; no LLM)")
    p_s.add_argument("--query", required=True, help="Query for retrieval used to build the output")
    p_s.add_argument("--top", default="8", help="Top K chunks to include (default 8)")
    p_s.add_argument("--doc", default=None, help="Filter to a single ingest_id")
    p_s.add_argument("--out", default=None, help="Output path (default: vfms_data/outputs/<run_id>__summary.md)")
    p_s.set_defaults(func=cmd_summarize)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    ensure_dirs()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
