#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

DATA_ROOT = Path("vfms_data")
RAW_DIR = DATA_ROOT / "raw"
EXTRACTED_DIR = DATA_ROOT / "extracted"
INDEX_DIR = DATA_ROOT / "index"
OUTPUTS_DIR = DATA_ROOT / "outputs"

MANIFEST = INDEX_DIR / "manifest.jsonl"
SQLITE_DB = INDEX_DIR / "vfms.sqlite"

# v0: deterministic chunking
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 150


def utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def make_ingest_id() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")


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
        raise SystemExit(
            f"ERROR: multiple raw files found for ingest_id {ingest_id}: {[m.name for m in matches]}"
        )
    return matches[0]


def find_extracted_txt(ingest_id: str) -> Path:
    txt = EXTRACTED_DIR / f"{ingest_id}.txt"
    if not txt.exists():
        raise SystemExit(
            f"ERROR: extracted text not found for ingest_id {ingest_id}. Run: vfms extract {ingest_id}"
        )
    return txt


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
        "notes": "",
    }
    append_manifest(rec)

    print(f"Ingested: {src_path.name}")
    print(f"ingest_id: {ingest_id}")
    print(f"stored_as: {dest_path}")
    return ingest_id


def run_pdftotext(pdf_path: Path, out_txt: Path) -> None:
    # Requires poppler-utils: pdftotext
    cmd = ["pdftotext", "-layout", str(pdf_path), str(out_txt)]
    subprocess.run(cmd, check=True)


def run_ocrmypdf(pdf_path: Path, out_pdf: Path, lang: str = "eng") -> None:
    # Requires ocrmypdf + tesseract
    # Force OCR to ensure a text layer is created
    cmd = [
        "ocrmypdf",
        "--force-ocr",
        "--deskew",
        "--clean",
        "--rotate-pages",
        "--language",
        lang,
        str(pdf_path),
        str(out_pdf),
    ]
    subprocess.run(cmd, check=True)


def extract(ingest_id: str, ocr: str = "auto") -> None:
    raw_path = find_raw_by_ingest_id(ingest_id)
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    txt_path = EXTRACTED_DIR / f"{ingest_id}.txt"
    meta_path = EXTRACTED_DIR / f"{ingest_id}.json"

    ocr_used = False

    # v0 logic:
    # - Try pdftotext. If it yields almost nothing (or user forces OCR), run OCR and then pdftotext again.
    # - This is deterministic and auditable.
    if raw_path.suffix.lower() == ".pdf":
        tmp_txt = EXTRACTED_DIR / f"{ingest_id}__tmp_pdftotext.txt"
        try:
            run_pdftotext(raw_path, tmp_txt)
        except Exception as e:
            tmp_txt.write_text("", encoding="utf-8")
        text = tmp_txt.read_text(encoding="utf-8", errors="replace")

        needs_ocr = False
        if ocr == "force":
            needs_ocr = True
        elif ocr == "off":
            needs_ocr = False
        else:
            # auto: if text layer is basically empty, OCR it
            stripped = "".join(ch for ch in text if not ch.isspace())
            if len(stripped) < 200:
                needs_ocr = True

        if needs_ocr:
            ocr_used = True
            ocr_pdf = EXTRACTED_DIR / f"{ingest_id}__ocr.pdf"
            # default Spanish for your current legal corpus; adjust if needed
            run_ocrmypdf(raw_path, ocr_pdf, lang="spa")
            run_pdftotext(ocr_pdf, txt_path)
        else:
            shutil.move(str(tmp_txt), str(txt_path))
    else:
        # For now, v0 only supports PDFs in extraction
        raise SystemExit("ERROR: v0 extract supports only PDFs")

    # Metadata record
    meta = {
        "ingest_id": ingest_id,
        "raw_path": str(raw_path),
        "text_path": str(txt_path),
        "ocr_used": ocr_used,
        "extracted_at_utc": utc_now(),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    append_manifest(
        {
            "type": "extract_update",
            "ingest_id": ingest_id,
            "extracted": True,
            "extracted_at_utc": utc_now(),
            "ocr_used": ocr_used,
            "text_path": str(txt_path),
            "meta_path": str(meta_path),
        }
    )

    print(f"Extracted ingest_id: {ingest_id}")
    print(f"text: {txt_path}")
    print(f"meta: {meta_path}")
    print(f"ocr_used: {ocr_used}")


def chunk_text(text: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    pieces = []
    i = 0
    n = len(text)
    while i < n:
        j = min(i + CHUNK_SIZE, n)
        chunk = text[i:j]
        pieces.append(chunk)
        if j >= n:
            break
        i = max(0, j - CHUNK_OVERLAP)
    return pieces


def ensure_db() -> sqlite3.Connection:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SQLITE_DB))
    conn.execute(
        """
    CREATE TABLE IF NOT EXISTS docs (
        ingest_id TEXT PRIMARY KEY,
        source_filename TEXT,
        raw_path TEXT,
        text_path TEXT,
        created_at_utc TEXT
    )
    """
    )
    conn.execute(
        """
    CREATE TABLE IF NOT EXISTS chunks (
        chunk_id TEXT PRIMARY KEY,
        ingest_id TEXT,
        chunk_index INTEGER,
        page INTEGER,
        chunk_text TEXT,
        created_at_utc TEXT,
        FOREIGN KEY (ingest_id) REFERENCES docs(ingest_id)
    )
    """
    )
    return conn


def index_one(ingest_id: str) -> None:
    raw_path = find_raw_by_ingest_id(ingest_id)
    txt_path = find_extracted_txt(ingest_id)

    source_filename = raw_path.name.split("__", 1)[-1] if "__" in raw_path.name else raw_path.name
    text = txt_path.read_text(encoding="utf-8", errors="replace")
    pieces = chunk_text(text)

    conn = ensure_db()
    try:
        conn.execute(
            """
        INSERT INTO docs (ingest_id, source_filename, raw_path, text_path, created_at_utc)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(ingest_id) DO UPDATE SET
          source_filename=excluded.source_filename,
          raw_path=excluded.raw_path,
          text_path=excluded.text_path
        """,
            (ingest_id, source_filename, str(raw_path), str(txt_path), utc_now()),
        )

        conn.execute("DELETE FROM chunks WHERE ingest_id = ?", (ingest_id,))

        created = utc_now()
        for idx, chunk in enumerate(pieces, start=1):
            chunk_id = f"{ingest_id}_c{idx:04d}"
            conn.execute(
                """
            INSERT INTO chunks (chunk_id, ingest_id, chunk_index, page, chunk_text, created_at_utc)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
                (chunk_id, ingest_id, idx, None, chunk, created),
            )

        conn.commit()
    finally:
        conn.close()

    append_manifest(
        {
            "type": "index_update",
            "ingest_id": ingest_id,
            "indexed": True,
            "indexed_at_utc": utc_now(),
            "db_path": str(SQLITE_DB),
            "chunk_count": len(pieces),
        }
    )

    print(f"Indexed ingest_id: {ingest_id}")
    print(f"chunks: {len(pieces)}")
    print(f"db: {SQLITE_DB}")


def index_all():
    if not EXTRACTED_DIR.exists():
        raise SystemExit("ERROR: vfms_data/extracted does not exist. Nothing to index.")
    ids = sorted([p.stem for p in EXTRACTED_DIR.glob("*.txt")])
    if not ids:
        raise SystemExit("ERROR: no extracted .txt files found to index.")
    for ingest_id in ids:
        index_one(ingest_id)


def query_db(q: str, top: int = 5, ingest_id: str | None = None) -> list[tuple[str, str, str, str]]:
    if not SQLITE_DB.exists():
        raise SystemExit("ERROR: index DB not found. Run: vfms index <ingest_id>")

    q = q.strip()
    if not q:
        raise SystemExit("ERROR: empty query")

    conn = sqlite3.connect(str(SQLITE_DB))
    try:
        params = []
        where = "chunk_text LIKE ?"
        params.append(f"%{q}%")
        if ingest_id:
            where += " AND chunks.ingest_id = ?"
            params.append(ingest_id)

        sql = f"""
        SELECT chunks.ingest_id, docs.source_filename, chunks.chunk_id, chunks.chunk_text
        FROM chunks
        JOIN docs ON docs.ingest_id = chunks.ingest_id
        WHERE {where}
        ORDER BY chunks.ingest_id ASC, chunks.chunk_index ASC
        LIMIT ?
        """
        params.append(int(top))
        rows = conn.execute(sql, params).fetchall()
        return rows
    finally:
        conn.close()


def print_query(rows):
    if not rows:
        print("No matches.")
        return
    for (iid, fname, cid, ctext) in rows:
        snippet = ctext.replace("\n", " ").strip()
        if len(snippet) > 240:
            snippet = snippet[:240] + "…"
        print(f"- ingest_id: {iid} | file: {fname} | chunk: {cid}")
        print(f"  {snippet}")


def parse_prompt(prompt: str) -> tuple[str, str | None]:
    """
    Supports: "QUERY :: INSTRUCTIONS"
    - QUERY is used for retrieval (literal substring match).
    - INSTRUCTIONS are written into the output but NOT used for retrieval.
    Backwards compatible: if no '::', prompt is treated as QUERY only.
    """
    if prompt is None:
        return "", None
    raw = prompt.strip()
    if "::" not in raw:
        return raw, None

    left, right = raw.split("::", 1)
    query_text = left.strip()
    instructions = right.strip() if right.strip() else None
    return query_text, instructions


def summarize(prompt: str, top: int = 5, ingest_id: str | None = None, out_path: str | None = None) -> None:
    # v0: summarization is "grounded compilation" (no model). It writes chunks with citations.
    query_text, instructions = parse_prompt(prompt)

    if not query_text:
        raise SystemExit("ERROR: empty query (left side of '::' is blank)")

    rows = query_db(query_text, top=top, ingest_id=ingest_id)
    if not rows:
        raise SystemExit("ERROR: no matches to summarize from. Try a different query.")

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    if out_path:
        out = Path(out_path)
    else:
        slug = query_text.lower().replace(" ", "_")[:40]
        out = OUTPUTS_DIR / f"summary__{slug}.md"

    with out.open("w", encoding="utf-8") as f:
        f.write("# VFMS v0 Grounded Output\n\n")
        f.write(f"**Query:** {query_text}\n\n")
        if instructions:
            f.write("**Instructions:** " + instructions + "\n\n")
        if ingest_id:
            f.write(f"**Doc filter:** {ingest_id}\n\n")
        f.write("## Sources (extracted chunks)\n\n")
        for (iid, fname, cid, text) in rows:
            f.write(f"### {fname} — {cid}\n\n")
            f.write(text.strip() + "\n\n")
        f.write("---\n")
        f.write("_Generated manually from indexed chunks. No background processing._\n")

    append_manifest(
        {
            "type": "summarize_update",
            "prompt": prompt,
            "query_text": query_text,
            "instructions": instructions,
            "ingest_id": ingest_id,
            "top": top,
            "out_path": str(out),
            "created_at_utc": utc_now(),
        }
    )

    print(f"Summary written to: {out}")


def main():
    ap = argparse.ArgumentParser(prog="vfms", description="VFMS v0 (manual triggers only)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_ingest = sub.add_parser("ingest", help="Manually ingest a file into vfms_data/raw and manifest.jsonl")
    p_ingest.add_argument("path", help="Path to a file to ingest")

    p_ext = sub.add_parser("extract", help="Extract text for an ingest_id (manual; no background)")
    p_ext.add_argument("ingest_id", help="Ingest ID to extract")
    p_ext.add_argument("--ocr", choices=["auto", "force", "off"], default="auto", help="OCR mode (only applies to images)")

    p_idx = sub.add_parser("index", help="Index an extracted ingest_id into SQLite (manual; no background)")
    p_idx.add_argument("ingest_id", nargs="?", help="Ingest ID to index")
    p_idx.add_argument("--all", action="store_true", help="Index all extracted .txt files")

    p_q = sub.add_parser("query", help="Directed retrieval from SQLite (manual; no background)")
    p_q.add_argument("text", help="Query text (substring match in v0)")
    p_q.add_argument("--top", type=int, default=5, help="Max results")
    p_q.add_argument("--doc", dest="doc", default=None, help="Filter to a specific ingest_id")

    p_s = sub.add_parser("summarize", help="Generate grounded Markdown output (manual; no background)")
    p_s.add_argument("prompt", help="Query text to retrieve chunks for the output. You may use: QUERY :: INSTRUCTIONS")
    p_s.add_argument("--top", type=int, default=5, help="Max chunks")
    p_s.add_argument("--doc", dest="doc", default=None, help="Filter to a specific ingest_id")
    p_s.add_argument("--out", dest="out", default=None, help="Output .md path")

    args = ap.parse_args()

    if args.cmd == "ingest":
        ingest_file(Path(args.path))

    elif args.cmd == "extract":
        extract(args.ingest_id, args.ocr)

    elif args.cmd == "index":
        if args.all:
            index_all()
        elif args.ingest_id:
            index_one(args.ingest_id)
        else:
            raise SystemExit("ERROR: provide an ingest_id or use --all")

    elif args.cmd == "query":
        rows = query_db(args.text, top=args.top, ingest_id=args.doc)
        print_query(rows)

    elif args.cmd == "summarize":
        summarize(args.prompt, top=args.top, ingest_id=args.doc, out_path=args.out)


if __name__ == "__main__":
    main()
