# Caso Finca / Carpeta Clara Design v1

## Plain-English Product Goal

Carpeta Clara is the first clear workspace model for Val0 life/admin/legal topics.

For Karen, the first workspace is `Caso Finca`: a living case folder where Val organizes documents, notes, events, questions, pending items, and next steps around the land/family/legal topic without making Karen remember random Telegram commands.

The product feeling should be:

- "Val knows where this belongs."
- "Val can open the folder and tell me what we know."
- "Val can separate facts, questions, pending items, and next actions."
- "Val helps me prepare for Nora without pretending to be Nora."

This is design-only v1. No runtime behavior changes are included here.

## User-Facing Examples

Karen-facing phrases should feel natural:

- "Val, abre mi Caso Finca"
- "Que sabemos del caso?"
- "Que documentos tengo?"
- "Que falta confirmar?"
- "Que le pregunto a Nora?"
- "Que sigue?"
- "Val, agrega esta nota al Caso Finca"
- "Val, guarda este documento en Caso Finca"
- "Val, preparame el paquete para Nora"

The response should feel like a workspace, not a command menu:

```text
Tany, abro Caso Finca.

Lo importante
- Tengo documentos registrados, notas del caso y algunos eventos con fecha.

Que falta confirmar
- El efecto legal exacto de los autos/oficios.
- Si Registro Publico ya refleja el estado actual.

Preguntas para Nora
- Que documento prueba mejor el estado actual?
- Que falta pedir al juzgado o Registro Publico?

Que sigue
- Revisar documentos con OCR pendiente.
- Preparar paquete corto para Nora.
```

## Proposed Internal Model

Internal naming should stay English/language-neutral so this can become reusable for other clients and topics.

```text
WorkspaceCase
- case_id
- client_id
- title
- aliases
- status
- created_at
- updated_at
- source_refs

CaseNote
- note_id
- case_id
- text
- source
- created_at
- confidence
- source_label

CaseDocument
- document_id
- case_id
- vfms_ingest_id
- filename
- alias
- document_type
- status
- extracted_text_status
- ocr_status
- summary_status
- source_label

CaseTimelineEvent
- event_id
- case_id
- event_date
- date_precision
- title
- description
- source_refs
- confidence

CaseQuestion
- question_id
- case_id
- question_text
- audience
- status
- source_refs

CasePendingItem
- item_id
- case_id
- text
- owner
- status
- due_date
- source_refs

CaseNextAction
- action_id
- case_id
- text
- priority
- status
- source_refs
```

Core fields:

- `case/workspace id`: durable identifier, for example `CASE:KAREN-LAND-001`.
- `title`: user-facing display name, for example `Caso Finca`.
- `aliases`: alternate phrases such as `caso del terreno`, `finca`, `terreno familiar`.
- `notes`: user notes and Val-generated factual notes.
- `documents`: VFMS/OCR/document summary references.
- `timeline/events`: dated events, deadlines, filings, meetings, case milestones.
- `questions_for_lawyer`: questions for Nora/abogada, never legal conclusions.
- `pending_items`: open confirmations, documents to request, OCR to run, facts to verify.
- `next_actions`: practical actions Val can suggest or track.
- `confidence/source labels`: every important fact should say where it came from and how certain it is.

## Safety / Legal Boundaries

Val summarizes and organizes. Val does not give legal conclusions.

Spanish user-facing boundary:

```text
Val organiza lo que esta registrado y te ayuda a preparar preguntas.
No reemplaza la revision de Nora/la abogada ni confirma efectos legales.
```

Rules:

- Use "observacion", "dato a confirmar", "posible punto para revisar", and "pregunta para Nora".
- Do not say a legal outcome is certain unless the source explicitly says it and the copy still frames it as source-based.
- Nora/abogada confirms legal effect.
- OCR summaries are first-pass reading aids and can contain OCR errors.
- Keep provenance visible enough for review without exposing internal IDs unnecessarily.

## Relationship To Existing Features

Document summaries:
- Specific and OCR summaries become document cards inside a workspace.
- Warm document summary sections map naturally to workspace sections.

OCR:
- OCR status becomes part of each document.
- OCR should remain on-demand until a later implementation decision.

Tasks:
- Workspace pending items can create or link to Val tasks.
- Tasks remain Val-managed, not Google Calendar events.

Reminders:
- Workspace reminders can help Karen remember calls, document requests, or Nora prep.
- Reminders stay Val-managed unless the user explicitly asks for calendar events.

Calendar:
- Nora meetings and real appointments belong in Google Calendar.
- The workspace can reference calendar events, but should not mirror every event into Val reminders.

Daily/operator view:
- The daily view can surface workspace next actions and deadlines.
- It should not dump the whole case every morning.

## MVP Phases

Phase 0: Design only
- This document.
- No runtime behavior change.
- No data mutation.

Phase 1: Read-only case status
- "Val, abre mi Caso Finca"
- "Que sabemos del caso?"
- Render current case facts from existing notes/documents/timeline.
- Include confidence/source labels and legal boundaries.

Phase 2: Add note/document to case
- "Agrega esta nota al Caso Finca"
- "Guarda este documento en Caso Finca"
- Use deterministic case resolution.
- Do not cross-contaminate clients.

Phase 3: Timeline
- Render dated events from documents, notes, calendar references, and manually added events.
- Separate "confirmed date" from "mentioned date".

Phase 4: Nora prep packet
- Produce a short packet:
  - lo importante
  - documentos clave
  - que falta confirmar
  - preguntas para Nora
  - proximos pasos

Phase 5: Workspace actions
- Convert selected pending items into tasks, reminders, or calendar events only after explicit user request/confirmation.

## Test Strategy

Fixture phrases:

- "Val, abre mi Caso Finca"
- "Que sabemos del caso?"
- "Que documentos tengo?"
- "Que falta confirmar?"
- "Que le pregunto a Nora?"
- "Que sigue?"
- "Agrega esta nota al Caso Finca"
- "Guarda este documento en Caso Finca"

Smoke tests:

- Case/workspace route beats generic case/finca summary only when phrase is explicit.
- Read-only status does not mutate live data.
- Document/OCR summaries still pass.
- Task/reminder/calendar smokes still pass.
- Client isolation audit stays clean.

No live data mutation:

- Use fixture data or mock case records.
- Do not mutate `clients/karen/CLIENT_GROCERY.md`.
- Do not create Google Calendar events in case smokes.

Client isolation:

- Internal model is generic: `WorkspaceCase`, not `KarenCase`.
- Karen-specific aliases live in client/profile/config or fixture data.
- Do not hardcode chat IDs or private names in reusable code.

## Risks / Watch Items

- Client-specific hardcoding: Caso Finca is the first example, not the only possible workspace.
- Legal overreach: Val must not present legal advice or final legal effects.
- Stale facts: source labels and updated timestamps are required.
- Document OCR errors: OCR text must stay marked as first-pass/possibly noisy.
- Cross-client contamination: aliases, notes, documents, and questions must stay client-scoped.
- Workspace sprawl: avoid making every tiny topic a workspace too early.

## Now Val Will Be Able To

After implementation, Val will be able to:

- Open a clear Caso Finca workspace instead of scattering answers across commands.
- Tell Karen what is known, what is uncertain, and what needs confirmation.
- Show documents, notes, timeline events, questions, pending items, and next actions in one place.
- Prepare a Nora-facing packet from grounded facts and OCR/document summaries.
- Keep legal boundaries visible while still being useful and warm.
- Reuse the same workspace model later for other clients and topics.

## Suggested Next Implementation Milestone

Recommended next milestone:

`A-011 — Caso Finca Read-Only Workspace Status v1`

Goal:

- Implement a read-only `open case/workspace` response for Caso Finca using existing stored notes/documents/timeline helpers.
- No writes.
- No new broad router refactor.
- Add fixture phrases and smoke tests first.

Acceptance shape:

- "Val, abre mi Caso Finca" returns a read-only workspace dashboard.
- It includes "Lo importante", "Documentos", "Timeline / eventos", "Que falta confirmar", "Preguntas para Nora", and "Que sigue".
- It includes a legal boundary.
- It does not mutate client data.
