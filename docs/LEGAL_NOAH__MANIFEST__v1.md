# Legal/Noah — Manifest v1 (Repo-visible pointers)

This repo does NOT store the raw datastore (`vfms_data/`) in git.
All outputs referenced below exist on the server filesystem.

## Key outputs (filesystem paths)
- Timeline (dates → evidence lines):
  - vfms_data/outputs/LEGAL_NOAH__TIMELINE__v1.md
- Timeline merge (doc-by-doc grounded chunks):
  - vfms_data/outputs/LEGAL_NOAH__TIMELINE_MERGE__v1.md
- Case binder:
  - vfms_data/outputs/LEGAL_NOAH__CASE_BINDER__v1.md
  - vfms_data/outputs/LEGAL_NOAH__CASE_BINDER__v1.tsv
- OCR audit:
  - vfms_data/outputs/LEGAL_NOAH__OCR_ONLY_AUDIT__v1.tsv

## Document facts directory (52 files)
- vfms_data/outputs/legal_noah_docs/
  - DOC__*__FACTS_DATES.md (date-bearing evidence lines)
  - DOC__*__JUZGADO.md / other grounded extracts
