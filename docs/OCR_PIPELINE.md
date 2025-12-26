# OCR Pipeline (VFMS v0) — Notes

## Problem
Some PDFs are "dirty scans": they look readable to humans but extract into junk (vertical letters, broken spacing).
This causes VFMS `query`/`summarize` to return "No matches" even when the page visibly contains text.

## Solution
Run OCR normalization using `ocrmypdf` (Spanish language) and ingest the OCR’d PDFs.

### Command used
- Input: /opt/vfms_inbox/frank_legal_noah/staged_pdfs/*.pdf
- Output: /opt/vfms_inbox/frank_legal_noah/ocr_fixed/*__OCR.pdf

Example:
ocrmypdf --force-ocr --deskew --clean --rotate-pages --language spa "IN.pdf" "OUT__OCR.pdf"

### Notes
- OCR can increase file size significantly (expected with --force-ocr, --deskew).
- Runtime can be slow; this is normal.

## Verification layer (minimum viable)
After ingest, run an OCR-only audit for the ingest IDs list:
- Ensures extracted text exists (non-zero)
- Checks density (chars/page)
- Flags garbage-heavy outputs

Artifact:
vfms_data/outputs/LEGAL_NOAH__OCR_ONLY_AUDIT__v1.tsv

## Outputs (legal/noah case pack)
- Per-doc facts/dates: vfms_data/outputs/legal_noah_docs/
- Timeline merge: vfms_data/outputs/LEGAL_NOAH__TIMELINE_MERGE__v1.md
- Case binder: vfms_data/outputs/LEGAL_NOAH__CASE_BINDER__v1.md + .tsv

## Rule
All outputs must remain grounded: no inference, only what appears in extracted chunks.
