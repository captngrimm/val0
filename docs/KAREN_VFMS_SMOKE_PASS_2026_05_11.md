# Karen VFMS Smoke Pass — 2026-05-11

## Result

PASS.

## What was validated

- VFMS exists in active Val0 tree.
- System OCR tools exist on Val0:
  - tesseract
  - pdftotext
  - pdfinfo
  - ocrmypdf
- VFMS DB schema had drifted from current vfms.py expectations.
- After safe schema migration, manual VFMS ingest/extract/index/query works.

## Smoke test

Input:

Karen VFMS smoke test. Finca 10082. Tomo Rollo 316. Folio 308.

Command flow:

- vfms.py ingest
- vfms.py extract --ocr off
- vfms.py index
- vfms.py query "finca 10082"

## Output

VFMS returned:

Karen VFMS smoke test. Finca 10082. Tomo Rollo 316. Folio 308.

## Interpretation

Val0 has a working manual VFMS pipeline.

The missing Karen MVP bridge is not full OCR from scratch. The next needed layer is:

Telegram/document upload -> save file -> VFMS ingest -> extract -> index -> link to Karen case.

## Remaining unknowns

- Telegram PHOTO/DOCUMENT handlers are not yet confirmed.
- OCR on real PDF/image not yet retested after schema fix.
- Python dependencies for newer image/PDF OCR path are missing in Val0 venv.
- System-tool OCR path exists and should be tested separately.

