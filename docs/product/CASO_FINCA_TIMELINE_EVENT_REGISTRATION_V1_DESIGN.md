# Caso Finca Timeline Event Registration v1 Design

## Purpose

Design the safe write path for Caso Finca timeline events before implementation.

Karen already has read-only timeline views:

- "Val, muéstrame la línea de tiempo del Caso Finca"
- "Val, qué eventos tengo registrados del Caso Finca?"
- "Val, qué falta ordenar por fecha?"

The next product step is letting Karen register important timeline events in natural Spanish, while Val keeps strict boundaries: no invented dates, no silent legal conclusions, no destructive writes without confirmation, and no mutation of live client data during design.

This document is design-only. It does not change runtime behavior.

## User-Facing Examples

Create / register:

- "Val, registra en Caso Finca que en 2021 pasó X"
- "Val, anota que el documento 1 parece ser de 2019"
- "Val, registra que el 12 de mayo de 2024 recibimos una respuesta del juzgado"
- "Val, agrega a la línea de tiempo que falta confirmar la fecha del oficio"

Status / confirmation:

- "Val, marca este evento como pendiente de confirmar"
- "Val, marca el evento 2 como confirmado por mí"
- "Val, este evento lo tengo que confirmar con Nora"

Correction / deletion:

- "Val, corrige la fecha del evento 2"
- "Val, cambia el evento 2 a 2021"
- "Val, borra el evento 3"
- "Val, elimina el evento 3 de la línea de tiempo"

Read / view:

- "Val, qué pasó primero?"
- "Val, qué eventos faltan confirmar?"
- "Val, muéstrame la línea de tiempo del Caso Finca"
- "Val, qué falta ordenar por fecha?"

Example draft interaction:

```text
Karen: Val, registra en Caso Finca que en 2021 se presentó una solicitud al Registro Público.

Val: Tany, tengo este borrador de evento para Caso Finca:

Título: Solicitud presentada al Registro Público
Fecha: 2021 (solo año)
Estado: pendiente de confirmar
Fuente: nota tuya

¿Lo guardo en la línea de tiempo?
```

## Event Schema Proposal

Internal naming should stay English and reusable.

```text
CaseTimelineEvent
- event_id
- case_id / workspace_id
- title
- description
- event_date
- event_date_precision
- recorded_at
- source_type
- source_ref
- confirmation_status
- confidence
- legal_effect_status
- created_by
- created_at
- updated_at
- deleted_at
- deletion_reason
- supersedes_event_id
- audit_trail
```

Field notes:

- `event_id`: durable event ID, for example `event:case-karen-land-001:20260604-0001`.
- `case_id / workspace_id`: for Caso Finca, `CASE:KAREN-LAND-001`.
- `title`: short event label, user-facing.
- `description`: longer natural-language event note.
- `event_date`: normalized date when known. Empty/null if unknown.
- `event_date_precision`: `exact`, `year_only`, `month_only`, or `unknown`.
- `recorded_at`: when Val recorded the event.
- `source_type`: `user_note`, `document_metadata`, `ocr_summary`, `manual_review`, or `inferred_candidate`.
- `source_ref`: safe source pointer. Internal IDs can exist internally, but should not be shown in normal user-facing output.
- `confirmation_status`: `confirmed_by_user`, `pending_confirmation`, `candidate`, `contradicted`, or `rejected`.
- `confidence`: `high`, `medium`, `low`, or `unknown`.
- `legal_effect_status`: `unknown`, `asks_nora`, `confirmed_by_lawyer`, or `not_legal_effect`.
- `created_by`: `user`, `val_draft`, `operator`, or `system_import`.
- `updated_at`: last edit timestamp.
- `audit_trail`: append-only list of create/update/delete/restore decisions.

## Safety Model

Rules:

- Do not invent dates.
- Separate user-said events from document-derived events.
- Separate confirmed facts from candidate/inferred events.
- No legal conclusions.
- Nora/la abogada confirms legal effect.
- Add OCR caveat when an event came from OCR or OCR-backed summary.
- Never overwrite old event values silently.
- Event edits preserve audit trail.
- Deletes are soft-deletes first.
- Destructive or corrective actions require confirmation.
- User-facing output must avoid raw OCR body dumps and internal IDs unless Karen asks for technical details.

Date handling:

- "en 2021" -> `event_date_precision: year_only`.
- "en mayo de 2021" -> `month_only`.
- "el 12 de mayo de 2021" -> `exact`.
- "pasó hace años" or no date -> `unknown`, label as `fecha pendiente`.
- If the phrase contains uncertainty like "parece", "creo", "puede ser", default to `candidate` or `pending_confirmation`.

Legal effect handling:

- Default `legal_effect_status` is `unknown`.
- If the user says "Nora confirmó..." then still store a source note and mark as `confirmed_by_lawyer` only after a confirmation prompt.
- If the event is from OCR, do not mark legal effect as confirmed.

## Storage Options

### Option A: Client JSON File

Example future path:

```text
clients/karen/CLIENT_CASE_TIMELINE_EVENTS.json
```

Pros:

- Simple and easy to inspect.
- Matches the current lightweight client-folder pattern.
- Good for a small first v1.
- Easy to guard in smokes.

Cons:

- Becomes live client data immediately.
- Higher risk of accidental staging/commit if not guarded.
- Manual merge conflicts are awkward.
- Needs explicit audit-trail discipline.

### Option B: SQLite Table

Example future table:

```text
case_timeline_events
case_timeline_event_audit
```

Pros:

- Better auditability and update safety.
- Cleaner soft-delete/correction model.
- Easier to query/sort.
- Less likely to leak into git if stored in existing encrypted/local DB.

Cons:

- More implementation work.
- Needs migration and backup thinking.
- Smokes need dry/mock patterns.

### Option C: Markdown Append Log

Example future path:

```text
clients/karen/CASE_TIMELINE_APPEND_LOG.md
```

Pros:

- Human-readable.
- Natural audit trail.
- Easy operator review.

Cons:

- Harder to parse reliably.
- Risk of drift between log and rendered state.
- Edits/corrections need careful conventions.

### Recommendation For v1

Use a two-phase approach:

1. A-028B storage spike/fixture-only or draft parser skeleton using tests/fixtures first.
2. For runtime v1, prefer SQLite/event table if existing Val0 memory storage can support it safely. If that is too heavy, use a Karen-scoped JSON file only with:
   - explicit live-data guard,
   - soft-delete only,
   - append-only audit trail inside each event,
   - smoke tests that use temp storage, not the live file.

Do not use `clients/karen/CLIENT_GROCERY.md` or `clients/karen/CLIENT_FOLDERS.json`.

## Runtime Flow

Create flow:

1. Parse registration phrase.
2. Resolve workspace/case to `Caso Finca`.
3. Detect date and precision.
4. Build a draft event.
5. Render confirmation preview.
6. Ask confirmation before any write.
7. On "sí" / "dale" / "guardar", write event.
8. Render event-added summary.
9. Show timeline updated or suggest viewing it.

Draft preview should include:

- title
- date label
- date precision
- source type
- confirmation status
- legal effect status
- caveats

Example:

```text
Tany, antes de guardarlo te lo confirmo:

Evento: Solicitud presentada al Registro Público
Fecha: 2021 (solo año)
Estado: pendiente de confirmar
Efecto legal: desconocido; Nora/la abogada confirma

¿Lo guardo en Caso Finca?
```

Confirmation should be required before write. The parser never writes directly.

## Correction / Delete Flow

Correction:

1. User references a numbered event from the latest timeline view.
2. Check context freshness.
3. Build edit draft.
4. Show before/after.
5. Ask confirmation.
6. Write update with audit trail.
7. Keep previous values in audit trail.

Delete:

1. User says "borra/elimina el evento N".
2. Check latest numbered timeline context.
3. Show event title/date.
4. Ask confirmation.
5. Soft-delete only.
6. Preserve event and audit trail.

Stale context guard:

- Numbered corrections/deletes are valid only after a recent timeline view.
- If context is stale, Val should say:

```text
Tany, necesito que veamos la línea de tiempo actual primero para no borrar/corregir el evento equivocado.
Di: "Val, muéstrame la línea de tiempo del Caso Finca".
```

## Read / View Flow

Timeline sorting:

- Exact dates first by date.
- Month-only after exact dates for the same year/month when possible.
- Year-only grouped by year.
- Unknown dates in `fecha pendiente`.

Sections:

- `Línea de tiempo`
- `Eventos confirmados en Val`
- `Eventos por confirmar`
- `Huecos / falta fecha`
- `Preguntas para Nora`
- `Próximo paso sugerido`
- legal boundary

Candidate vs confirmed:

- `confirmed_by_user`: user confirmed the event happened.
- `pending_confirmation`: user/doc mentioned it, but it needs checking.
- `candidate`: plausible event extracted from document metadata/OCR.
- `contradicted`: conflict detected; needs Nora/manual review.
- `rejected`: excluded from active timeline but kept in audit trail.

Unknown dates:

- Do not hide unknown-date events.
- Put them in `Huecos / falta fecha`.
- Ask for the missing date instead of inventing it.

## Test Plan

Smokes for A-028B/A-028C should include:

- Create draft with exact date:
  - "Val, registra en Caso Finca que el 12 de mayo de 2021 pasó X"
  - draft has `event_date_precision: exact`
- Create draft with year-only date:
  - "Val, registra en Caso Finca que en 2021 pasó X"
  - draft has `event_date_precision: year_only`
- Create draft with unknown date:
  - "Val, registra en Caso Finca que pasó X"
  - draft has `event_date_precision: unknown`
- Confirmation required before write.
- Correction requires confirmation.
- Delete/soft-delete requires confirmation.
- No legal advice or fake legal certainty.
- OCR-derived event includes OCR caveat.
- No raw OCR dumps.
- No internal IDs in normal user-facing output.
- Client isolation audit passes.
- Live data file guard:
  - `CLIENT_GROCERY.md` untouched.
  - `CLIENT_FOLDERS.json` untouched.
  - future timeline live file not staged accidentally.
- Existing A-027B/A-027D timeline phrases still pass.
- Generic "Val, qué hago ahora?" remains generic operational summary.
- Founder limitations prompts still work:
  - "Val, qué no puedes hacer todavía?"
  - "Val, cuáles son tus límites?"

## Acceptance Criteria

- No write without explicit confirmation.
- No raw OCR dumps.
- No event silently marked legally valid.
- Timeline read remains stable.
- Existing read-only timeline phrases still pass:
  - "Val, muéstrame la línea de tiempo del Caso Finca"
  - "Val, qué eventos tengo registrados del Caso Finca?"
  - "Val, qué falta ordenar por fecha?"
- Generic what-now still remains generic.
- Corrections preserve previous values in audit trail.
- Deletes are soft-deletes first.
- All live-data files remain protected from accidental commits.

## Risks And Guardrails

Risks:

- Split-brain if events are stored separately from documents without source refs.
- User may phrase legal interpretations as facts.
- OCR may misread dates, names, or numbers.
- Numbered event corrections/deletes can target the wrong event if context is stale.
- JSON live files can be accidentally staged.

Guardrails:

- Confirmation before writes.
- Stale numbered context guard.
- Source labels on every event.
- Legal effect remains unknown unless explicitly confirmed and still source-labeled.
- Soft-delete only.
- Audit trail on every mutation.
- Temp-store smokes before live-store implementation.

## Recommended Next Implementation Lane

Recommended:

```text
A-028B — Timeline Event Draft Parser + Confirmation Skeleton
```

Scope:

- Parse natural registration phrases into draft events.
- No persistence yet, or temp/fixture-only persistence.
- Render confirmation preview.
- Confirm that parser never writes directly.
- Add smokes for exact/year-only/unknown date precision.

If storage risk looks high during implementation, switch A-028B to:

```text
A-028B — Timeline Event Storage Spike / Fixture-only
```

That variant should design/test storage with temp files or fixtures before any live client data file exists.
