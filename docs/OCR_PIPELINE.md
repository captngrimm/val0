# VFMS — OCR Pipeline (Legal / Dirty PDFs)

This document describes the **OCR normalization + verification pipeline** used by VFMS
when ingesting scanned or “dirty” legal PDFs.

This pipeline exists to:
- Normalize scanned PDFs into searchable text
- Detect OCR failures or low-confidence extractions
- Produce **auditable artifacts** for human (lawyer / intern) review
- Avoid silent data loss or hallucinated summaries

---

## When OCR Is Required

Run OCR **before ingest** if **any** of the following occur:

- Queries like `JUZGADO`, `AUTO`, names, or dates return **no matches**
- Extracted text looks like:
  - vertical letters (J U Z G A D O stacked)
  - excessive spacing / broken words
- PDFs are scans, photos, or court-stamped images
- PDFs open fine visually but behave like images

**Rule:**  
If VFMS cannot find obvious legal tokens, assume OCR is required.

---

## OCR Command (Canonical)

OCR is performed with `ocrmypdf` using Spanish language and cleanup flags.

```bash
ocrmypdf \
  --force-ocr \
  --deskew \
  --clean \
  --rotate-pages \
  --language spa \
  input.pdf \
  output__OCR.pdf
Notes
File size increase is normal
--force-ocr rasterizes even PDFs that “already have text”
JBIG2 warnings are safe to ignore (optimization only)
Output is PDF/A by default (good for legal archives)
OCR Output Location
OCR-fixed PDFs are stored in:
Copy code

/opt/vfms_inbox/<case_name>/ocr_fixed/
These OCR PDFs are then ingested normally into VFMS.
OCR Ingest Verification (Critical Step)
After ingest + extract, OCR quality is verified automatically.
OCR-Only Audit Script
The system generates a TSV audit file:
Copy code

vfms_data/outputs/LEGAL_NOAH__OCR_ONLY_AUDIT__v1.tsv
Each row includes:
filename
ingest_id
page count
total extracted characters
characters per page
garbage ratio
single-character line ratio
flags (if any)
Interpretation Rules
Expected (PASS)
chars_per_page ≈ 1000–3000 (legal text)
garbage_ratio < 0.35
single_char_line_ratio < 0.25
no flags
Flagged (REVIEW REQUIRED)
Examples:
Very low chars per page
High garbage ratio
Excessive single-letter lines
Missing pages
⚠️ Flagged does NOT mean wrong It means: requires human verification
Human Review Policy
For flagged OCR documents:
Open original PDF and OCR PDF side-by-side
Confirm:
Dates
Party names
Case numbers
Orders / decisions
Clear or annotate manually
This preserves legal defensibility.
Why This Exists (Design Rationale)
OCR is probabilistic. Legal work is not.
VFMS therefore:
Never assumes OCR is perfect
Surfaces extraction quality explicitly
Produces audit artifacts
Keeps humans in the loop where it matters
This design is intentional and enterprise-safe.
Summary
Pipeline order:
OCR dirty PDFs
Ingest OCR PDFs
Extract + index
Run OCR audit
Generate grounded summaries
Human review only where flagged
No silent failures. No hidden guesses. No hallucinated certainty.
