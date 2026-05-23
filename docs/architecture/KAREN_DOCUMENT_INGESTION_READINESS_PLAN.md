# Karen Document / Photo Ingestion Readiness Plan

## Purpose

Karen's highest-value workflow is legal/finca document support: storing documents, preserving provenance, extracting readable text, summarizing contents, building a timeline, preparing lawyer/Nora packages, and answering later questions from grounded sources.

This plan defines what is already working, what is limited, and what must be built before document/photo ingestion can be considered Karen-ready.

## Current Working Pieces

- Telegram attachment handler exists.
- Uploaded files are downloaded locally under `/opt/val0/vfms_data/telegram_uploads/<chat_id>/...`.
- Files can be registered through VFMS.
- VFMS supports ingest, extract, index, query, and summarize.
- Text-like documents can be extracted/indexed.
- PDFs have an OCR-related path, but full scanned-PDF readiness is not yet proven.
- Uploaded attachments can be linked to active case notes with VFMS metadata.
- Karen has a manual document inventory flow.
- Karen can list registered documents.
- Karen can request grounded summaries from extracted VFMS text.
- Specific VFMS summary routes include chat/case privacy guards.
- Semantic-ish lookup is scoped to active case ingest IDs before querying VFMS chunks.

## Current Limits

- Photos are accepted, but image OCR is not truly automated/end-to-end ready.
- Word/docx ingestion is not currently supported in the auto path.
- Legal summaries are partly deterministic and Karen-case-specific.
- Grounding is based on extracted text/VFMS IDs/snippets, not robust page/region citations.
- If no active case exists, uploads may be stored but not easily queryable through Karen case routes.
- Prior validation was mostly text/PDF-light; scanned PDF/photo/docx readiness remains incomplete.

## Missing For Karen-Ready MVP

1. First-class document registry.
2. Client/case-scoped document records.
3. Explicit statuses:
   - stored
   - extracted
   - indexed
   - ocr_needed
   - ocr_failed
   - ready
   - needs_human_review
4. Reliable image OCR path or honest manual-review fallback.
5. Scanned PDF OCR smoke test.
6. Word/docx extraction or honest unsupported response.
7. Duplicate detection by hash.
8. Source/provenance metadata:
   - client_id
   - case_id
   - chat_id
   - message_id if available
   - filename
   - hash
   - MIME/type
   - caption
   - source path
   - VFMS ingest id
   - extraction status
9. Karen-facing document list:
   - “qué documentos tengo”
   - only scoped to her case/client
10. Grounded summary flow:
   - “qué dice este documento”
   - cites document/VFMS ID and extracted snippets
   - labels weak OCR or missing extraction clearly

## Trust Killers

- Saying a photo/document was received when Val cannot actually read it.
- Treating OCR/LLM summaries as ground truth.
- Mixing global VFMS results into Karen answers.
- Letting uploads become invisible because there is no active case.
- Exposing raw local paths as the user-facing provenance model.
- Legal summaries sounding too confident when extraction quality is weak.
- Two VFMS implementations drifting apart.

## Minimum Karen-Ready Definition

Karen-ready means:

1. Karen can upload PDF/photo/text/docx.
2. Val stores the file safely and records metadata.
3. Val tells Karen the real status:
   - stored only
   - extracted
   - OCR/manual review needed
   - ready to summarize
4. Karen can ask:
   - “qué documentos tengo”
   - “qué dice este documento”
   - “dónde sale Finca 10082”
   - “qué pasó en 2024”
5. Answers are scoped to Karen/client/case.
6. Answers cite document/VFMS IDs or snippets.
7. Low-confidence extraction is labeled.
8. Nora/lawyer packages can reference documents, not just manual notes.

## Three-Commit Implementation Plan

### Commit 1: Document Registry Abstraction

No behavior change.

Create a helper over existing VFMS/case-note metadata.

Normalize:
- client_id
- case_id
- chat_id
- ingest_id
- filename
- caption
- status
- hash
- MIME/type
- source/provenance

### Commit 2: Extraction Readiness Layer

Add safe status reporting and fixture-based smoke tests.

Support/check:
- text extraction
- PDF extraction
- scanned PDF OCR readiness
- photo OCR status
- docx unsupported/extracted status

No real client files in tests.

### Commit 3: Karen-Ready Telegram Intake

Update attachment reply behavior so Karen gets clear status.

Examples:
- “Guardé el documento, pero todavía no pude leerlo.”
- “Texto extraído y listo para resumen.”
- “La foto quedó guardada, pero necesita OCR/revisión manual.”

Wire document listing/summaries through registry-scoped docs.

## Required Smoke Tests

- .txt upload saved, ingested, extracted, indexed, case-linked.
- Text PDF upload extracted/indexed and summary works.
- Scanned PDF fixture records OCR status.
- Photo upload records OCR status or needs_human_review.
- .docx fixture extracted or clearly unsupported.
- Wrong chat cannot summarize another chat’s VFMS ID.
- No active case response explains stored but not linked.
- “Qué documentos tengo” lists only current client/case docs.
- “Qué dice VFMS <id>” answers only from extracted text.
- Client isolation audit passes.

## Tool Assimilation Notes

n8n/Nate may help with intake reminders, webhook intake of non-sensitive test payloads, queueing metadata, or notifications.

Val0 must remain source of truth for:
- client isolation
- legal/finca memory
- document registry
- confirmation/safety policy
- grounded retrieval
- final answers

## Do Not Do

- Do not send real Karen documents to external SaaS without privacy review.
- Do not let external automation mutate memory or legal data directly.
- Do not treat OCR/LLM summaries as legal truth.
- Do not mix client memories.
- Do not rewrite all document routes at once.
- Do not expose raw local paths as the long-term user-facing provenance model.
