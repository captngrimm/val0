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

def find_extracted_txt(ingest_id: str) -> Path:
    txt = EXTRACTED_DIR / f"{ingest_id}.txt"
    if not txt.exists():
        raise SystemExit(f"ERROR: extracted text not found for ingest_id {ingest_id}. Run: vfms extract {ingest_id}")
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
        "notes": ""
    }
    append_manifest(rec)

    print(f"Ingested: {src_path.name}")
    print(f"ingest_id: {ingest_id}")
    print(f"stored_as: {dest_path}")
    return ingest_id

def run_pdftotext(pdf_path: Path, out_txt: Path) -> bool:
    try:
        subprocess.run(["pdftotext", "-layout", str(pdf_path), str(out_txt)], check=True)
        return True
    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError:
        return False

def extract_text_only(src_path: Path, out_txt: Path) -> None:
    data = src_path.read_bytes()
    try:
        txt = data.decode("utf-8")
    except UnicodeDecodeError:
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

    if suffix == ".pdf":
        engine = "pdftotext"
        ok = run_pdftotext(raw_path, out_txt)
        if not ok:
            raise SystemExit("ERROR: pdftotext not available or failed. Install poppler-utils or use a different extraction method.")
        ocr_used = False
    elif suffix in [".txt", ".md", ".csv", ".log"]:
        engine = "direct"
        extract_text_only(raw_path, out_txt)
        ocr_used = False
    elif suffix in [".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"]:
        if ocr_mode == "off":
            raise SystemExit("ERROR: OCR is off but the input is an image. Re-run with --ocr auto or --ocr force.")
        engine = "tesseract"
        try:
            subprocess.run(
                ["tesseract", str(raw_path), str(out_txt.with_suffix(''))],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except FileNotFoundError:
            raise SystemExit("ERROR: tesseract not installed. Install tesseract-ocr to extract from images.")
        except subprocess.CalledProcessError:
            raise SystemExit("ERROR: tesseract failed on this image.")
        if not out_txt.exists():
            raise SystemExit("ERROR: tesseract did not produce output text.")
        ocr_used = True
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

def ensure_db():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SQLITE_DB))
    conn.execute("""
    CREATE TABLE IF NOT EXISTS docs (
      ingest_id TEXT PRIMARY KEY,
      source_filename TEXT,
      raw_path TEXT,
      text_path TEXT,
      created_at_utc TEXT
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
      chunk_id TEXT PRIMARY KEY,
      ingest_id TEXT,
      chunk_index INTEGER,
      page INTEGER,
      chunk_text TEXT,
      created_at_utc TEXT,
      FOREIGN KEY (ingest_id) REFERENCES docs (ingest_id)
    )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_ingest ON chunks(ingest_id)")
    conn.commit()
    return conn

def chunk_text(txt: str):
    txt = txt.strip()
    if not txt:
        return []
    chunks = []
    i = 0
    n = len(txt)
    step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
    while i < n:
        chunks.append(txt[i:i+CHUNK_SIZE])
        i += step
    return chunks

def index_one(ingest_id: str) -> None:
    raw_path = find_raw_by_ingest_id(ingest_id)
    txt_path = find_extracted_txt(ingest_id)

    source_filename = raw_path.name.split("__", 1)[-1] if "__" in raw_path.name else raw_path.name
    text = txt_path.read_text(encoding="utf-8", errors="replace")
    pieces = chunk_text(text)

    conn = ensure_db()
    try:
        conn.execute("""
        INSERT INTO docs (ingest_id, source_filename, raw_path, text_path, created_at_utc)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(ingest_id) DO UPDATE SET
          source_filename=excluded.source_filename,
          raw_path=excluded.raw_path,
          text_path=excluded.text_path
        """, (ingest_id, source_filename, str(raw_path), str(txt_path), utc_now()))

        conn.execute("DELETE FROM chunks WHERE ingest_id = ?", (ingest_id,))

        created = utc_now()
        for idx, chunk in enumerate(pieces, start=1):
            chunk_id = f"{ingest_id}_c{idx:04d}"
            conn.execute("""
            INSERT INTO chunks (chunk_id, ingest_id, chunk_index, page, chunk_text, created_at_utc)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (chunk_id, ingest_id, idx, None, chunk, created))

        conn.commit()
    finally:
        conn.close()

    append_manifest({
        "type": "index_update",
        "ingest_id": ingest_id,
        "indexed": True,
        "indexed_at_utc": utc_now(),
        "db_path": str(SQLITE_DB),
        "chunk_count": len(pieces)
    })

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

def summarize(prompt: str, top: int = 5, ingest_id: str | None = None, out_path: str | None = None) -> None:
    # v0: summarization is "grounded compilation" (no model). It writes chunks with citations.
    rows = query_db(prompt, top=top, ingest_id=ingest_id)
    if not rows:
        raise SystemExit("ERROR: no matches to summarize from. Try a different query.")

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    if out_path:
        out = Path(out_path)
    else:
        slug = prompt.lower().replace(" ", "_")[:40]
        out = OUTPUTS_DIR / f"summary__{slug}.md"

    with out.open("w", encoding="utf-8") as f:
        f.write("# VFMS v0 Grounded Output\n\n")
        f.write(f"**Query:** {prompt}\n\n")
        if ingest_id:
            f.write(f"**Doc filter:** {ingest_id}\n\n")
        f.write("## Sources (extracted chunks)\n\n")
        for (iid, fname, cid, text) in rows:
            f.write(f"### {fname} — {cid}\n\n")
            f.write(text.strip() + "\n\n")
        f.write("---\n")
        f.write("_Generated manually from indexed chunks. No background processing._\n")

    append_manifest({
        "type": "summarize_update",
        "prompt": prompt,
        "ingest_id": ingest_id,
        "top": top,
        "out_path": str(out),
        "created_at_utc": utc_now()
    })

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
    p_s.add_argument("prompt", help="Query text to retrieve chunks for the output")
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
