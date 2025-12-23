# docs/VFMS_EXEC_PLAN.md

VFMS v0 Execution Plan (Build Plan Only — No Code)

Source of truth: docs/VMFS_v0.md (frozen)

VFMS v0 goal:
Manual ingestion → extraction (OCR if needed) → basic indexing → directed retrieval → on-demand summaries/MD outputs.
No background agents. No auto prioritization. Manual triggers only.
“VFMS does not think. It remembers.”


## 1) Storage Layout (Confirmed)

Create a single data root at repo root:

vfms_data/
  raw/          # originals as ingested (pdf/txt/png/jpg)
  extracted/    # extracted text + extraction metadata artifacts
  index/        # sqlite index + manifest
  outputs/      # generated markdown summaries (on-demand only)
  tmp/          # scratch space; safe to delete

Naming convention:
- ingest_id: YYYYMMDD_NNNNNN (monotonic per host)
- raw file: <ingest_id>__<original_filename>
- extracted text: <ingest_id>.txt
- extraction metadata: <ingest_id>.json
- output md: <run_id>__<short_label>.md

Notes:
- No processing implied by file presence. Everything is manual-triggered.
- outputs/ is written only when user explicitly requests a summary/MD output.


## 2) Dependencies / Packages

Runtime:
- Python 3.10+ (existing project baseline)
- sqlite3 (stdlib; use SQLite FTS5 if available)

Extraction:
- pypdf (PDF text extraction)
- Pillow (image handling for OCR)
- pytesseract (OCR wrapper)
- System package: tesseract-ocr (engine) + language pack(s) as needed

Optional (only if needed for robust chunking/token counts; keep minimal):
- regex (stdlib re is fine; optional not required)

Explicit non-requirements (v0):
- No background schedulers/agents
- No vector DB required unless VMFS_v0 explicitly allows it
- No proactive analysis jobs


## 3) Minimal Data Model / Schema

A) Manifest (append-only) — vfms_data/index/manifest.jsonl
One JSON object per ingest:
- ingest_id (string)
- source_filename (string)
- stored_path (string)
- sha256 (string)
- mime (string)
- ingested_at_utc (string ISO)
- extracted (bool)
- extracted_at_utc (string ISO or null)
- ocr_used (bool or null)
- text_path (string or null)
- meta_path (string or null)
- notes (string)

B) SQLite index — vfms_data/index/vfms.sqlite

Table: docs
- ingest_id TEXT PRIMARY KEY
- source_filename TEXT
- stored_path TEXT
- sha256 TEXT
- mime TEXT
- ingested_at_utc TEXT
- extracted_at_utc TEXT NULL
- ocr_used INTEGER NULL
- pages INTEGER NULL

Table: chunks
- chunk_id TEXT PRIMARY KEY
- ingest_id TEXT NOT NULL
- page INTEGER NULL
- chunk_text TEXT NOT NULL
- created_at_utc TEXT NOT NULL

Indexing option (preferred minimal):
- SQLite FTS5 virtual table for chunks (if enabled):
  - chunks_fts(chunk_id, ingest_id, chunk_text)

If FTS5 not available:
- fallback to LIKE queries over chunks.chunk_text (slower but acceptable for v0).


## 4) Minimal CLI Entry Points (Manual Triggers Only)

Single CLI module (name TBD during implementation, e.g., vfms.py). Commands:

1) Ingest
- vfms ingest <path_to_file>
Behavior:
- validate exists
- compute sha256
- copy into vfms_data/raw/<ingest_id>__<filename>
- append manifest record
Output:
- prints ingest_id

2) Extract (OCR if needed)
- vfms extract <ingest_id> [--ocr auto|force|off]
Behavior:
- if PDF: attempt text extraction via pypdf
- if empty/low-yield and ocr=auto: OCR page images (implementation chooses method)
- if image: OCR via pytesseract
- write extracted/<ingest_id>.txt + extracted/<ingest_id>.json
- update manifest record (extracted=true, ocr_used=bool, paths)
Output:
- prints extracted text path + whether OCR used

3) Index
- vfms index <ingest_id>
- vfms index --all
Behavior:
- split extracted text into chunks (page-aware when possible)
- write docs row (if missing) + chunks rows
- update FTS5 if available
Output:
- prints chunk count indexed

4) Query (Directed Retrieval)
- vfms query "<query>" [--top N] [--doc <ingest_id>]
Behavior:
- returns top matching chunks with citations:
  - source_filename, ingest_id, page (if known), chunk_id
Output:
- prints ranked list with short excerpts

5) Summarize (On-demand MD output)
- vfms summarize "<instruction>" --query "<query>" [--top N] [--out <path>]
Behavior:
- runs query to get top chunks
- produces a markdown summary grounded ONLY in retrieved chunks
- includes citations per paragraph or bullet:
  - Source: <filename> (ingest_id …), page X, chunk_id …
Output:
- writes vfms_data/outputs/<run_id>__*.md and prints path

Guardrails (must be enforced in prompts/logic during implementation):
- Must not invent facts beyond retrieved text.
- Must not run any step unless user explicitly triggers the command.
- Must not suggest actions outside the documents (summary must stay grounded).


## 5) Step-by-Step Implementation Sequence (No Code Yet)

Step 0 — Confirm repo and branch
- Ensure working directory: /opt/val0
- Ensure branch: docs/vfms-v0-freeze (docs frozen and pushed)

Step 1 — Create storage directories
- Create vfms_data/{raw,extracted,index,outputs,tmp}

Step 2 — Add manifest + sqlite skeleton
- Add manifest.jsonl creation on first run
- Create sqlite file vfms.sqlite and docs/chunks tables (+ FTS5 if available)

Step 3 — Implement ingest command
- Copy file into raw/
- Write manifest entry
- Print ingest_id

Step 4 — Implement extract command (PDF/text/image)
- PDF: pypdf extract
- Determine if OCR required (auto/force/off)
- Image: OCR
- Write extracted text + extraction metadata JSON
- Update manifest + docs.pages/ocr_used where possible

Step 5 — Implement index command
- Chunk extracted text
- Insert docs + chunks rows
- If FTS5: insert into FTS table
- Print chunk count

Step 6 — Implement query command
- Use FTS5 MATCH or fallback LIKE
- Return top N chunks with citations

Step 7 — Implement summarize command
- Pull top chunks from query
- Generate markdown summary grounded in those chunks
- Write outputs/<run_id>.md

Step 8 — Add acceptance-test harness notes
- Provide exact CLI invocations and expected outputs
- No automation; tests are manual runs


## 6) Acceptance Test Run Sheet (Manual)

Pre-req:
- vfms_data/ exists
- CLI available
- At least two docs ingested/extracted/indexed

Test Set A — Ingest/Extract/Index happy path
1) Ingest a PDF:
   - vfms ingest ./sample.pdf
   - Expect: ingest_id printed; file appears in vfms_data/raw/

2) Extract text:
   - vfms extract <ingest_id> --ocr auto
   - Expect: extracted/<id>.txt exists, extracted/<id>.json exists
   - extracted.json indicates ocr_used true/false

3) Index:
   - vfms index <ingest_id>
   - Expect: chunks created; query finds terms from doc

Test Set B — Directed retrieval behaviors (Acceptance prompts)

Using ingested docs, verify:

1) “Check the docs and tell me what they say about X.”
   - vfms query "X" --top 5
   - Expect: matching chunks with citations; no invented info

2) “Write a Markdown summary about Z based only on the docs.”
   - vfms summarize "Write a Markdown summary about Z based only on the docs." --query "Z" --top 8
   - Expect: outputs/*.md created; every claim traceable to citations

3) “Do we have anything that mentions Y? Quote the relevant lines.”
   - vfms query "Y" --top 5
   - Expect: direct excerpts returned (quoted) with citations

4) “Compare doc A vs doc B on topic T. Cite where each claim comes from.”
   - vfms query "T" --doc <ingest_id_A> --top 5
   - vfms query "T" --doc <ingest_id_B> --top 5
   - Summarize comparison manually via summarize:
     - vfms summarize "Compare doc A vs doc B on topic T. Cite where each claim comes from." --query "T"
   - Expect: clearly separated claims + citations per doc; no external suggestions

Test Set C — Non-goals / guardrails validation
- Verify there is no background processing:
  - After ingest, nothing is extracted or indexed unless explicitly commanded.
- Verify no recommendations / decision-making:
  - summaries must stay descriptive and grounded.


## 7) Definition of Done Checklist (Mapped to VMFS_v0.md Requirements)

DONE when all are true:
- Manual ingestion exists and stores raw files (receive files)
- Extraction exists and produces text; OCR used when applicable (extract text)
- Basic index exists over extracted content (index content)
- Query returns directed retrieval results with citations (directed retrieval)
- Summaries/MD outputs generated only on-demand and grounded in retrieved text (on-demand summaries/MD)
- No agents, no background runs, no prioritization, no recommendations (v0 does NOT do)
- Entire system explainable in 30 seconds (golden rule)
- Phase 0 only; no hooks for Phase 1/2

Stop Condition:
If any step implies proactive execution or analysis without a manual trigger → NOT VFMS v0.


END OF PLAN — Await explicit “start implementation” to begin coding.
