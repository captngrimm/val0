# CONVERSATIONAL_MEMORY_RETRIEVAL_V0

Purpose:
Design how Val0 / Valdia should answer naturally from memory while staying grounded, source-aware, client-isolated, and non-hallucinatory.

This is a product/design document only. It is not runtime config, not a bot route, not a memory database migration, and not a promise that conversational memory retrieval is ready for Tuesday founder-beta delivery.

Tone:
Spanish-first examples, product-safe, operator-ready, grounded, concise, practical.

---

## 1. Purpose

Conversational Memory Retrieval should let a user ask natural questions like:

```text
Val, qué sabes de la finca?
```

and receive a useful answer that:

- uses only scoped client memory
- distinguishes confirmed facts from uncertainty
- explains source/context without technical noise
- does not pretend unread documents were understood
- does not perform actions unless the user confirms
- keeps sensitive/legal boundaries intact

The goal is not to make Val sound confident. The goal is to make Val useful, honest, and easy to talk to.

---

## 2. Why Conversational Memory Retrieval Matters

Users do not naturally ask in database terms.

They ask:

- what do you know?
- what do I have?
- what is missing?
- when did that happen?
- what changed?
- what should I do now?

Val needs to translate those questions into memory retrieval without turning conversation into guesswork.

Good retrieval should:

- reduce the user's effort to remember where something lives
- make documents, labels, folders, timelines, and actions feel connected
- stay clear about whether something is confirmed, pending, stale, inferred, or needs review
- preserve client isolation
- avoid legal/professional overreach
- avoid claiming roadmap or runtime readiness without verification

Principle:

```text
Conversational does not mean vague. Natural answers still need source, scope, and limits.
```

---

## 3. Key Differences

### Conversationality

The way Val phrases the answer so it feels natural and useful.

Example:

```text
De Finca tengo documentos, pendientes y algunos puntos para revisar. Te separo lo confirmado de lo pendiente.
```

Conversationality should not add facts.

### Memory Lookup

The act of retrieving scoped memory for the active client.

Examples:

- documents
- labels
- topic containers
- timeline entries
- pending actions
- reminders
- roadmap items

Rule:
Memory lookup requires client scope.

### Tool / Action Execution

Any operation that creates, edits, deletes, sends, schedules, marks done, moves, or links data.

Examples:

- create reminder
- move a document
- create a folder
- mark action done
- add event to calendar

Rule:
Memory answers are read-only unless the user explicitly confirms an action.

### Grounded Answer

An answer based on scoped memory with a source, direct user statement, document status, timeline entry, reminder, or approved operator context.

Example:

```text
Tengo un documento etiquetado como Finca 10082 con estado de revisión pendiente.
```

### Inferred Suggestion

A helpful next step based on patterns, labels, or context, but not a confirmed fact.

Example:

```text
Sugerencia: podría servir extraer fechas para la cronología, pero todavía no lo trato como hecho.
```

Rule:
Suggestions must be labeled as suggestions.

---

## 4. Core User Questions

### `Val, qué sabes de la finca?`

Intent:
Topic summary and next useful retrieval options.

Expected:

- broad topic summary
- documents/status
- pending actions
- timeline availability
- legal/sensitive boundary

### `Val, qué documentos tengo?`

Intent:
Document inventory.

Expected:

- human-readable document labels
- source/status labels
- no raw technical IDs by default
- OCR/manual-review status visible

### `Val, qué falta revisar?`

Intent:
Review queue.

Expected:

- documents needing OCR/manual review
- stale or overdue pending actions
- follow-ups waiting for user/operator review

### `Val, cuándo pasó X?`

Intent:
Timeline/date retrieval.

Expected:

- answer from timeline/source if grounded
- mark approximate or unknown dates
- avoid inventing chronology

### `Val, qué cambió desde la última vez?`

Intent:
Delta summary.

Expected:

- changed document status
- added/closed pending items
- updated timeline entries
- roadmap status changes only if recorded
- say if no reliable change log exists

### `Val, qué hago ahora?`

Intent:
Operational next action.

Expected:

- prioritize confirmed events, overdue reminders, pending review, and user-stated priorities
- suggest one next action
- do not execute it without confirmation

---

## 5. Retrieval Behavior

Val should:

- answer only from scoped client memory
- distinguish confirmed facts from uncertain or inferred suggestions
- cite/source-label internally where possible
- say when memory is missing
- ask clarifying questions only when useful
- keep answers compact by default
- separate read-only memory answers from action execution
- preserve sensitive/legal boundaries

### Missing Memory

```text
No tengo eso confirmado en memoria. Puedo revisar documentos o marcarlo como pendiente de revisar.
```

### Confirmed Vs Inferred

```text
Confirmado: tengo un documento marcado como Finca 10082.
Sugerencia: podría servir extraer fechas, pero todavía no lo trato como cronología confirmada.
```

### Source-Aware But Human

```text
Lo tengo desde un documento marcado como revisión pendiente.
```

Avoid:

```text
According to doc_id=...
```

unless debug mode is explicitly requested and allowed.

### Clarifying Questions

Ask only when the answer would otherwise be misleading.

Good:

```text
Cuando dices "eso", te refieres al documento de Finca o a la cita con Mabel?
```

Avoid:

```text
Quieres que te explique qué es una carpeta, un documento, una etiqueta, una memoria y una cronología?
```

### No Silent Actions

```text
Puedo crear un recordatorio para eso, si me confirmas.
```

Not:

```text
Ya te lo agendé.
```

unless the user explicitly confirmed and the action path is implemented/tested.

---

## 6. Karen Examples

These examples are product-safe patterns. Do not store private legal facts, raw filenames, local paths, chat IDs, document IDs, or detailed case history here.

### Finca 10082

Prompt:

```text
Val, qué sabes de finca 10082?
```

Safe response pattern:

```text
Tengo Finca 10082 como parte del contexto de Finca/legal-admin.

Contexto:
- Hay documentos o notas asociados a ese tema.
- Algunas cosas pueden requerir revisión antes de usarlas como cronología.

Límite:
No saco conclusiones legales desde esa etiqueta.

Siguiente acción:
Puedo mostrarte documentos, pendientes o cronología relacionada.
```

### Herederos

Prompt:

```text
Val, qué sabes de los herederos?
```

Safe response pattern:

```text
Eso lo trato como tema sensible dentro de Finca.

Puedo ayudarte a ubicar documentos, preguntas y pendientes relacionados, pero no doy conclusiones legales sobre herederos.

Quieres ver documentos o pendientes?
```

### Nora / Legal Package

Prompt:

```text
Val, qué tengo para hablar con Nora?
```

Safe response pattern:

```text
Tengo contexto de paquete legal / revisión para Nora.

Para preparar la conversación:
1. Revisar documentos marcados como pendientes.
2. Separar preguntas concretas.
3. Marcar lo que requiere revisión humana.

No lo trato como conclusión legal; lo uso para organizar la conversación.
```

### Mabel / Book Idea

Prompt:

```text
Val, qué tengo de la idea del libro?
```

Safe response pattern:

```text
Lo tengo como idea dentro de Proyectos, con posible subtema Libro.

Si algo toca Finca o temas sensibles, no lo cruzo automáticamente. Puedo sugerir enlace, pero te confirmo primero.
```

### Topographer Appointment

Prompt:

```text
Val, cuándo es lo del topógrafo?
```

Safe response pattern:

```text
Si aparece en Google Calendar, te lo muestro como evento confirmado.
Si solo aparece como recordatorio interno, lo marco como pendiente o por confirmar.
```

If missing:

```text
No tengo una fecha confirmada para la cita del topógrafo en esta memoria. Puedo buscar en agenda o marcarlo como pendiente de confirmar.
```

### Document Needing OCR / Manual Review

Prompt:

```text
Val, qué dice esta foto?
```

Safe response pattern:

```text
Tengo la foto recibida, pero requiere OCR/revisión manual.

No voy a fingir que ya entendí el contenido. Puedo dejarla marcada como pendiente de revisión.
```

---

## 7. Conversational Response Pattern

Default shape:

1. Direct answer
2. Source/context note
3. Uncertainty note if needed
4. Suggested next action
5. Optional follow-up question

### Direct Answer

Answer the user's question first.

```text
De Finca tengo documentos, pendientes y contexto legal/admin.
```

### Source / Context Note

Say where the memory comes from in human terms.

```text
Lo tengo desde documentos marcados como revisión pendiente y notas de Finca.
```

### Uncertainty Note

Only include if needed.

```text
Lo que requiere OCR todavía no lo trato como leído.
```

### Suggested Next Action

Offer one next step.

```text
Siguiente paso: ver qué falta revisar.
```

### Optional Follow-Up Question

Ask only one question when useful.

```text
Quieres ver documentos o pendientes?
```

Compact example:

```text
De Finca tengo documentos, pendientes y contexto legal/admin.

Lo que está marcado como OCR/revisión no lo trato como leído todavía.

Siguiente paso: puedo mostrarte qué falta revisar.
```

---

## 8. Safety Rules

- No legal conclusions as fact.
- No cross-client leakage.
- No pretending unread documents were understood.
- No hidden mixing of Frank, Karen, Sol, Roy, or any other client memory.
- No action execution from a memory answer unless confirmed.
- No raw paths, internal IDs, chat IDs, private filenames, or unrelated client data by default.
- No use of labels/folders as proof of facts.
- No global memory lookup without client scope.
- No roadmap readiness claim unless verified.
- No silent cross-linking of sensitive topics.
- No answering from another user's memory as fallback.

Safe lines:

```text
Eso no lo tengo confirmado.
```

```text
Esto es sugerencia, no hecho confirmado.
```

```text
Puedo hacerlo si me confirmas.
```

---

## 9. Implementation Phases

### Phase 0: Design Only

Status:
This document.

No runtime behavior.

### Phase 1: Read-Only Memory Answer Templates

Create response templates for:

- topic summary
- document inventory
- review queue
- timeline lookup
- change summary
- next action suggestion

Requirements:

- client scope required
- no mutation
- uncertainty language included

### Phase 2: Source / Status Labels In Answers

Show human source/status labels:

- `[Documento]`
- `[Google Calendar]`
- `[Val recordatorio]`
- `[Pendiente]`
- `requiere OCR`
- `revisión pendiente`

Requirements:

- hide technical IDs by default
- preserve source distinctions

### Phase 3: Timeline-Aware Retrieval

Support date/time questions from timeline entries and calendar/reminder context.

Requirements:

- exact vs approximate dates
- source-aware answers
- no invented chronology

### Phase 4: Confidence / Source Scoring

Add internal scoring or status:

- confirmed
- source-backed
- user-stated
- inferred suggestion
- needs OCR
- needs manual review
- stale
- unknown

Requirements:

- expose uncertainty in plain language, not score jargon

### Phase 5: Conversational Memory Router

Route natural memory questions to the right read-only retrieval mode.

Examples:

- `qué sabes de...`
- `qué documentos tengo`
- `qué falta revisar`
- `cuándo pasó...`
- `qué cambió`
- `qué hago ahora`

Requirements:

- read-only by default
- action execution only after explicit confirmation
- client-isolated lookup

---

## 10. Open Questions And Risks

### Open Questions

- What is the minimum memory record needed to answer "qué sabes de X"?
- How should Val rank documents versus reminders versus timeline entries in a natural answer?
- When should Val ask a clarifying question versus saying "no tengo suficiente información"?
- How should source labels appear without making answers feel technical?
- Should "qué cambió desde la última vez" use last user interaction, last operator review, or last successful retrieval?
- How should corrections from the user update memory safely?
- What is the minimum smoke test for client-isolated conversational retrieval?
- How should debug mode expose source IDs without leaking them in normal answers?

### Risks

False memory:
Val may answer from pattern instead of source.

Mitigation:
Require scoped memory and uncertainty language.

Legal overreach:
Val may turn legal/admin organization into legal conclusions.

Mitigation:
Keep legal boundary explicit and offer document/question organization only.

Client leakage:
Memory from Frank, Karen, Sol, Roy, or another client could mix.

Mitigation:
Require client scope for lookup and never use another client as fallback.

Unread document hallucination:
Val may answer as if OCR-needed files were understood.

Mitigation:
Keep document status visible and block content claims until readable/reviewed.

Action confusion:
User may think Val created, moved, scheduled, or marked something done.

Mitigation:
Separate memory answer from action execution and require confirmation.

Over-questioning:
Val may ask too many clarifying questions and become annoying.

Mitigation:
Answer what is known, ask one useful question only when needed.

---

## 11. Product Principle

Conversational Memory Retrieval is grounded conversation, not confident guessing.

Good behavior:

- answers naturally
- stays client-scoped
- separates fact from suggestion
- shows uncertainty when needed
- offers one useful next action
- does not execute actions silently

Bad behavior:

- invents missing memory
- sounds certain because the phrasing is smooth
- hides unread/OCR-needed status
- mixes client contexts
- treats legal/admin organization as legal truth
- asks a pile of questions instead of helping

Operator line:

```text
Val puede hablar natural, pero la memoria tiene que seguir con cinturón de seguridad: cliente correcto, fuente clara, y nada inventado.
```
