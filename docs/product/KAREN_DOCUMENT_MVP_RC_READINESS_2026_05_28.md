# KAREN_DOCUMENT_MVP_RC_READINESS_2026_05_28

Purpose:
Release-candidate readiness audit for the Karen Document MVP after the M3 document workflow stabilization labs.

This is an operator/product readiness note. It is not a legal record, not a deployment instruction, not a promise of full OCR, and not permission to change OAuth, tokens, systemd, Google Calendar, OCR runtime, memory schema, or real client data.

---

## 1. Current Branch / Head

- Branch: `val0-post-m41-conversationality-memory-lab-2026-05-25`
- Current audited head: `8b96566 Add Karen last uploaded document context`
- Date: `2026-05-28`
- Scope: Karen founder-beta Document MVP release candidate

---

## 2. Safe Fallback

- Safe fallback branch/tag: `karen-founder-beta-safe-2026-05-25`
- Safe fallback commit: `4712a05`

Use fallback only if the live founder-beta surface becomes unsafe or unusable. Do not mix fallback restoration with unrelated runtime experiments.

---

## 3. Feature Checklist

| Feature | RC status | Notes |
|---|---|---|
| Upload | Ready for single-document founder-beta test | PDF upload path is live-tested. Keep batch uploads parked. |
| Extraction / index | Ready with honest limits | Text extraction/indexing works when supported by current pipeline. Do not claim OCR succeeded unless status says so. |
| Inventory | Ready | `Val, qué documentos tengo?` returns clean inventory with counts, status, and next actions. |
| Summary | Ready | Specific summary requests route by filename, alias, fuzzy name, or latest-document reference. |
| Summary persistence | Ready | Generated summaries are saved so inventory can show `resumen disponible`. |
| Alias / tags | Ready | User can get a naming/tag suggestion and confirm save. Original file remains intact. |
| Latest-document context | Ready | Commands like `resume el último documento` and `sugiere nombre para este documento` resolve the latest VFMS document for the chat. |

---

## 4. Tested User Commands

Use these as the primary Karen live-test flow:

1. `Val, transcribe este documento y hazme un resumen`
2. `Val, qué documentos tengo?`
3. `Val, qué fue lo último que subí?`
4. `Val, resume el último documento`
5. `Val, sugiere nombre para este documento`
6. `Val, guarda ese nombre`

Expected user-facing behavior:

- Val confirms document receipt/registration after upload.
- Inventory shows document status without exposing internal paths.
- Last-upload status shows display name/original filename, VFMS ID, date, type, and status.
- Summary is concise, Spanish-first, and uses `📋 Resumen claro`.
- Naming/tag suggestion is content-aware and does not force non-finca docs into finca.
- Alias save confirms that the display name/tags were saved and that the original file remains intact.

---

## 5. Known Caveats

- OCR/manual review limitations: OCR is not a blanket guarantee. If a document needs OCR/manual validation, Val must say so plainly.
- Word/DOCX boundaries: Word files may be registered/saved, but Val should not overpromise text extraction unless current status confirms readable text.
- Batch upload is parked: use one document at a time for the RC test.
- `clients/karen/CLIENT_GROCERY.md` is dirty runtime/client-data noise and must not be committed as part of this RC.
- `client_isolation_audit.py` currently reports a known `literal_karen` warning in `bot.py`; this should be migrated before multi-client expansion.
- This MVP organizes and summarizes registered information. It must not present legal conclusions or replace professional/legal review.
- Alias/tag save is a metadata/display operation. It does not physically rename original uploaded files.

---

## 6. Karen Live-Test Protocol

1. Use one real legal PDF only.
2. Upload it with:

```text
Val, transcribe este documento y hazme un resumen
```

3. Run the tested command flow from section 4 in order.
4. Ask Karen usefulness feedback:

```text
¿Esto te ayuda a entender qué documentos tienes, cuál fue el último que subiste, y qué hacer después?
```

5. Ask one naming question:

```text
¿El nombre sugerido te sirve, o lo dirías de otra forma?
```

6. Stop after one document. Do not run batch upload, broad OCR experiments, or legal analysis in this RC pass.

---

## 7. RC Criteria

Karen Document MVP is RC-ready only if all criteria are true:

- Compile passes:

```text
./scripts/val0py -m py_compile bot.py
```

- Client isolation audit passes with the known `literal_karen` warning only:

```text
python3 scripts/quality/client_isolation_audit.py || true
```

- Relevant document smokes pass:

```text
python3 scripts/quality/karen_document_fuzzy_matching_ux_smoke.py
python3 scripts/quality/karen_document_naming_metadata_smoke.py
python3 scripts/quality/karen_document_alias_save_smoke.py
python3 scripts/quality/karen_specific_document_summary_smoke.py
python3 scripts/quality/karen_document_summary_output_polish_smoke.py
python3 scripts/quality/karen_clean_document_inventory_smoke.py
python3 scripts/quality/document_inventory_smoke.py
python3 scripts/quality/karen_last_uploaded_document_context_smoke.py
python3 scripts/quality/karen_document_mvp_rc_smoke.py
```

- Service restart is clean after deployment.
- Recent logs show no new document-route exceptions.
- One real Karen PDF passes the section 4 flow.
- `clients/karen/CLIENT_GROCERY.md` remains uncommitted.

---

## 8. Go / No-Go Recommendation

Recommendation: **Go for a narrow Karen Document MVP RC live test.**

Go scope:

- one real PDF
- document upload
- inventory
- latest-document status
- summary generation/save
- naming/tag suggestion
- alias/tag confirmation save

No-go scope:

- batch upload
- broad OCR claims
- legal conclusions
- Word/DOCX extraction claims without status proof
- physical file rename
- multi-client rollout

Operator stance:

```text
Esto ya está listo para probar utilidad con un documento real, no para prometer que todos los documentos y formatos quedan perfectos.
```
