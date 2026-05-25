# MEMORY_LIBRARY_V1_DESIGN

Purpose:
Design Memory Library v1 for Val0 / Valdia: how Val should store, retrieve, explain, and organize client memory without becoming a chaotic folder swamp.

This is a product/design document only. It is not runtime config, not a memory database schema migration, not a legal record, and not a promise that Memory Library v1 is ready for Tuesday founder-beta delivery.

Tone:
Spanish-first examples, product-safe, operator-ready, source-aware, concise, practical.

---

## 1. Purpose

Memory Library v1 should help Val answer:

- what Val knows
- where that knowledge came from
- what is confirmed versus uncertain
- what needs review
- what is pending
- what changed since the last useful interaction
- how documents, reminders, calendar items, timelines, labels, folders, and ideas connect

The goal is not:

```text
Val remembers everything forever.
```

The goal is:

```text
Val keeps useful operational context, explains what it is using, and stays honest about source and confidence.
```

---

## 2. Why Memory Library Matters

Val should not just "remember everything."

Memory needs structure because founder-beta users may ask about:

- documents they uploaded
- meetings they have
- legal/admin context
- pending actions
- ideas that may become projects
- roadmap changes
- feedback from prior testing

Without structure, memory becomes noisy:

- every note looks equally important
- stale reminders look current
- unread documents look understood
- folders multiply too early
- private client facts risk leaking into reusable docs or another client context

Memory Library should organize memory into useful operational context:

- source-aware
- explainable
- client-isolated
- searchable
- retrievable in human language
- honest about missing review, OCR, or uncertainty

Principle:

```text
Memory is useful only when Val can explain what it knows, why it thinks it knows it, and what remains uncertain.
```

---

## 3. Memory Types

Memory Library v1 should support these memory types:

- facts
- preferences
- reminders
- calendar events
- documents
- document summaries
- timelines
- pending actions
- ideas
- roadmap items
- client feedback

### Facts

Stable statements about a user, project, document, case, or topic.

Rule:
Facts must be grounded in a source, direct user statement, or approved operator note.

### Preferences

User-specific choices about tone, language, formatting, timing, and workflow.

Example:

```text
Karen prefiere ejemplos en español y respuestas prácticas.
```

### Reminders

Internal Val reminders or user-requested follow-ups.

Rule:
Stale reminders must be marked as stale/overdue, not presented as fresh.

### Calendar Events

External or internal agenda items with date/time context.

Rule:
Google Calendar events must be distinguished from Val internal reminders.

### Documents

Files, attachments, photos, PDFs, notes, transcripts, or other source items.

Rule:
Document presence does not mean document understanding.

### Document Summaries

Human-readable summaries of documents that are readable, reviewed, or explicitly summarized.

Rule:
If a document needs OCR/manual review, do not summarize it as if understood.

### Timelines

Chronological entries grounded in source context.

Rule:
Timeline entries should separate date, event, source, confidence, and review status.

### Pending Actions

Things the user or operator may need to do.

Examples:

- review a document
- ask a lawyer
- extract dates
- create a reminder after confirmation

### Ideas

One-off or recurring creative/product/life ideas.

Rule:
Ideas should begin as notes or candidate subtopics, not automatic folders.

### Roadmap Items

Product or workflow capabilities that are ready, planned, next, later, parked, blocked, unknown, or not promised.

Rule:
Roadmap memory must not imply runtime readiness unless verified.

### Client Feedback

Founder-beta feedback such as:

- helped
- confusing
- too long
- missing
- priority next

Rule:
Feedback is product-learning context, not private factual record unless explicitly scoped.

---

## 4. Raw Memory Vs Structured Memory

### Raw Memory

Unprocessed capture.

Examples:

- uploaded photo
- pasted note
- transcript
- raw document text
- user message

Rule:
Raw memory may be stored, but Val should not overstate what it means.

### Structured Memory

Organized, typed, source-aware memory.

Examples:

- fact with source
- task with due date
- document label with status
- timeline entry
- folder/topic link

Structured memory should include client scope and provenance.

### Source Document

The original item or attachment that grounds later memory.

Examples:

- PDF
- photo
- manual note
- audio transcript

Rule:
Source document status must remain visible: received, readable, needs OCR, needs manual review, summarized, archived.

### Summary

A compact explanation generated from readable/reviewed source material.

Rule:
Summary should not replace source; it should point back to source internally where possible.

### Label

A human-readable tag or display name that helps recognition and retrieval.

Examples:

- `Foto de Finca - requiere OCR`
- `Paquete legal Nora - revisión pendiente`

Rule:
A label is not proof of a legal fact.

### Folder / Topic Container

A broad memory area.

Examples:

- Finca
- Proyectos
- Pendientes
- Proyectos > Libro

Rule:
Use broad containers first. Promote repeated useful subtopics later.

### Timeline Entry

A dated or ordered event grounded in memory.

Fields may include:

- date or approximate date
- event label
- source
- confidence
- review status

### Action Item

A thing to do, review, ask, confirm, or follow up.

Rule:
Action items are not calendar events unless scheduled or explicitly confirmed.

---

## 5. Karen Examples

These examples are product-safe patterns. Do not store private legal facts, raw filenames, local paths, chat IDs, document IDs, or detailed case history here.

### Finca 10082 Facts

Possible memory shape:

```text
Topic: Finca
Label: Finca 10082
Type: fact/document context
Status: source-aware, legal/admin scope
```

Safe response:

```text
Sé que Finca 10082 pertenece al contexto de Finca/legal-admin. Para detalles específicos, necesito usar documentos o notas registradas; si algo requiere revisión, te lo digo.
```

### Heirs

Possible memory shape:

```text
Topic: Finca
Type: sensitive legal/family fact category
Status: scoped, source-required
```

Safe response:

```text
Tengo esto como tema sensible dentro de Finca. No saco conclusiones legales sobre herederos; puedo ayudarte a ubicar documentos, preguntas y pendientes relacionados.
```

### Nora / Legal Package

Possible memory shape:

```text
Label: Paquete legal Nora - revisión pendiente
Type: document group / meeting prep context
Status: received or needs manual review
Action: prepare questions, review with Karen
```

Safe response:

```text
Tengo el paquete de Nora como contexto legal para organizar preguntas y documentos. No lo trato como conclusión legal.
```

### Mabel / Book Idea

Possible memory shape:

```text
Topic: Proyectos
Candidate subtopic: Libro
Related label: idea de libro
Sensitivity: ask before cross-linking to Finca
```

Safe response:

```text
Lo guardo como idea de libro dentro de Proyectos. Si quieres vincularlo con Finca, te confirmo antes por ser sensible.
```

### Topographer Appointment

Possible memory shape:

```text
Type: calendar event or reminder
Source: Google Calendar or Val internal reminder
Status: confirmed or needs confirmation
```

Safe response:

```text
Veo la cita del topógrafo como evento si viene de Google Calendar. Si solo es recordatorio interno, la marco como pendiente/por confirmar.
```

### Photo Needing OCR

Possible memory shape:

```text
Type: source document
Source label: photo
Status: needs OCR/manual review
Topic: Finca, if confirmed
```

Safe response:

```text
Tengo la foto recibida y marcada como requiere OCR/revisión. No voy a responder sobre su contenido como si ya estuviera leído.
```

---

## 6. Retrieval Behavior

Val should answer from memory only when grounded.

Rules:

- use memory when it has source, direct user statement, or approved operator context
- say when unsure
- cite/source-label internally where possible
- separate confirmed facts from inferred suggestions
- do not turn labels or folders into proof
- do not treat unread documents as understood
- do not merge clients
- do not answer legal questions as legal conclusions

User-facing uncertainty:

```text
No tengo eso confirmado en memoria. Puedo buscar en documentos o marcarlo como pendiente de revisar.
```

Confirmed versus suggested:

```text
Confirmado: tengo un documento marcado como Finca 10082.
Sugerencia: podría servir revisar fechas para la cronología, pero no lo hago pasar como hecho todavía.
```

Source-aware language:

```text
Lo tengo desde un documento marcado como revisión pendiente.
```

When memory is stale:

```text
Esto aparece como pendiente viejo. Te lo muestro como vencido, no como tarea nueva de hoy.
```

---

## 7. User-Facing Behaviors

### `Val, qué sabes de la finca?`

Expected:

- high-level topic summary
- documents/status
- pending actions
- timeline availability
- sensitive/legal boundary

Example:

```text
De Finca tengo contexto legal/admin, documentos marcados para revisión y algunos pendientes. No doy conclusiones legales; puedo mostrar documentos, pendientes o cronología.
```

### `Val, qué documentos tengo?`

Expected:

- compact document inventory
- human-readable labels
- status labels
- no raw technical IDs by default

Example:

```text
Documentos:
1. Finca 10082 - recibido / revisión pendiente
2. Foto de Finca - requiere OCR
3. Paquete legal Nora - revisión pendiente
```

### `Val, qué falta revisar?`

Expected:

- documents needing OCR/manual review
- pending actions
- stale/overdue items marked honestly

Example:

```text
Falta revisar:
1. Foto de Finca - requiere OCR/manual review.
2. Paquete legal Nora - preparar preguntas antes de reunión.
```

### `Val, cuándo pasó X?`

Expected:

- answer only if timeline/source supports it
- distinguish exact, approximate, and unknown

Example:

```text
No tengo una fecha confirmada para eso todavía. Puedo buscarlo en cronología/documentos o marcarlo como pendiente de revisar.
```

### `Val, qué cambió desde la última vez?`

Expected:

- new/updated documents
- changed statuses
- completed or added pending items
- roadmap status changes only if source exists

Example:

```text
Desde la última revisión veo cambios en estado de documentos y pendientes, pero no marco nada como listo si no fue verificado.
```

---

## 8. Privacy / Client Isolation Rules

- No cross-client leakage.
- No hidden mixing between Frank, Karen, Sol, Roy, or any other client.
- `client_id` is required for memory lookup.
- Sensitive/legal information must remain scoped.
- Memory retrieval must use client identity resolver or equivalent client-aware scope.
- Do not search global memory without client scope.
- Do not expose raw paths, internal IDs, chat IDs, private filenames, or unrelated client data by default.
- Do not copy detailed private legal facts into reusable product docs.
- Do not use Karen/client-zero memory as default truth for other users.
- Do not treat operator memory and client memory as the same thing unless explicitly scoped.

Safe line:

```text
Esa memoria está en otro contexto, así que no la mezclo aquí.
```

---

## 9. Implementation Phases

### Phase 0: Design Only

Status:
This document.

No runtime behavior.

### Phase 1: Memory Inventory / Read-Only Views

Create read-only views for:

- documents
- reminders
- calendar references
- pending items
- topic summaries

Requirements:

- no mutation
- source labels visible
- client scope required
- no raw technical IDs by default

### Phase 2: Labels + Topic Containers

Connect Memory Library to:

- document labels
- status labels
- source labels
- folders/topic containers
- candidate subtopics

Requirement:
Avoid folder explosion; start broad.

### Phase 3: Timeline / Action Extraction

Extract:

- timeline entries
- action items
- review-needed items
- follow-ups after meetings

Requirement:
Separate confirmed facts from suggested actions.

### Phase 4: Memory Confidence / Source Status

Add memory status:

- confirmed
- user-stated
- source-backed
- needs OCR
- needs manual review
- inferred suggestion
- stale
- unknown

Requirement:
Surface uncertainty in user language.

### Phase 5: Conversational Memory Retrieval

Support natural prompts:

- `Val, qué sabes de la finca?`
- `Val, qué falta revisar?`
- `Val, cuándo pasó X?`
- `Val, qué cambió desde la última vez?`

Requirement:
Answers must be source-aware, client-scoped, and honest about uncertainty.

---

## 10. Open Questions

- Should Memory Library use one table/collection per memory type or a unified typed item model?
- How should source documents link to summaries, labels, folders, timelines, and action items?
- What is the minimum source status needed before a memory can answer user questions?
- How should users correct false memory?
- Should memory confidence be visible by default or only when uncertainty matters?
- How should Val explain memory provenance without becoming too technical?
- How long should stale reminders remain in normal answers?
- How should Google Calendar events and Val internal reminders share one day view without confusion?
- Should roadmap items live in Memory Library or a separate roadmap registry?
- How should shared/family memory be permissioned?
- What is the minimum smoke test for client-isolated memory retrieval?

---

## 11. Risks

### False Memory

Risk:
Val may remember or retrieve something that was never confirmed.

Guardrail:
Require source/provenance and say when unsure.

### Overconfident Legal Conclusions

Risk:
Legal/admin memory could be phrased as legal advice or legal fact beyond the source.

Guardrail:
Organize documents, questions, and pending items; do not provide legal conclusions.

### Folder Explosion

Risk:
Every idea becomes a folder, making memory harder to use.

Guardrail:
Use broad topic containers first. Promote repeated topics only after repeated use/value or explicit request.

### Stale Memory

Risk:
Old reminders, outdated statuses, or prior assumptions appear fresh.

Guardrail:
Track updated status, stale/overdue markers, and "last reviewed" where possible.

### Calendar Confusion

Risk:
The user may confuse Val memory with Google Calendar.

Guardrail:
Always distinguish source labels such as `[Google Calendar]`, `[Val recordatorio]`, `[Pendiente]`, and `[Documento]`.

### Client Boundary Confusion

Risk:
Operator memory, Karen memory, and other client memory could blur.

Guardrail:
Require `client_id` for lookup, preserve scope, and never use one client's memory as another client's default context.

---

## 12. Product Principle

Memory Library is not a pile of remembered text. It is an operating memory layer.

Good Memory Library behavior:

- answers only when grounded
- explains uncertainty plainly
- keeps client boundaries hard
- links documents, labels, folders, timelines, and actions without over-fragmenting
- makes stale/review-needed state visible
- supports retrieval without raw technical noise

Bad Memory Library behavior:

- claims to remember everything
- invents facts from labels
- treats unread documents as understood
- creates folders for every thought
- mixes clients or operator/client scopes
- hides source uncertainty

Operator line:

```text
Val no necesita recordar todo como una bolsa gigante. Necesita guardar contexto útil, saber de dónde viene y decirte qué está confirmado, pendiente o por revisar.
```
