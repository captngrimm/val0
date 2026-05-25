# MEMORY_FOUNDATION_IMPLEMENTATION_MAP_V0

Purpose:
Map the recent Memory Foundation product designs into a practical post-Tuesday build plan for Val0 / Valdia.

Inputs:

- `CARPETAS_TOPIC_CONTAINERS_V0`
- `DOCUMENT_LABELS_NAMING_CONVENTION_V0`
- `UNIFIED_AGENDA_SINGLE_DAY_VIEW_V0`
- `MEMORY_LIBRARY_V1_DESIGN`
- `CONVERSATIONAL_MEMORY_RETRIEVAL_V0`

This is a product/implementation planning document only. It is not runtime config, not a bot route, not a database migration, and not a promise that these phases are ready for Tuesday founder-beta delivery.

Tone:
Spanish-first examples, operator-ready, product-safe, practical, build-oriented.

---

## 1. Purpose

This map converts the Memory Foundation design work into a staged implementation path after Tuesday.

It should help decide:

- what to build first
- what to defer
- what files/modules are likely involved later
- what smoke tests prove each phase
- what risks require pause or redesign
- how to protect Karen Tuesday founder-beta stability

Operating rule:

```text
After Tuesday, build memory as read-only and source-aware first. Add mutation, smart suggestions, and conversational routing only after the basics are stable.
```

---

## 2. Simple Explanation

### What We Designed

Recent docs define five parts of the memory foundation:

- Carpetas / Topic Containers: broad human areas like Finca, Proyectos, Pendientes.
- Document Labels / Naming: human-readable names plus source/status/action labels.
- Unified Agenda: one read-only day view across calendar, reminders, tasks, documents, and follow-ups.
- Memory Library v1: typed, source-aware, client-isolated operational memory.
- Conversational Memory Retrieval: natural answers from scoped memory without hallucination or hidden actions.

### Why It Matters

Val0 Personal becomes useful when it can answer:

```text
Val, qué sabes de la finca?
Val, qué documentos tengo?
Val, qué falta revisar?
Val, qué tengo hoy?
Val, qué hago ahora?
```

without dumping raw technical data, mixing clients, inventing facts, or creating a folder for every idea.

### What Turns Into Code First

The first code should be read-only:

- memory/document inventory views
- document source/status labels
- review-needed lists
- clear source labels
- simple single-day agenda rendering

Do not start with full free-chat, auto-foldering, or mutation-heavy commands.

---

## 3. Implementation Phases

## Phase 0: Current Docs-Only Foundation

User value:

- clarifies the product direction before Tuesday
- protects founder-beta delivery from churn
- gives operator language for roadmap answers

Technical work:

- no runtime work
- keep docs sealed and coherent
- use docs as post-Tuesday build guide

Files/modules likely touched:

- `docs/product/*.md`

Risk level:
Low.

Suggested ETA in sessions:
Done as design commits.

Smoke tests:

- `git status --short`
- review docs for no private facts, runtime promises, raw paths, or cross-client assumptions

Exit criteria:

- docs are committed
- Tuesday runtime untouched

---

## Phase 1: Read-Only Memory Inventory Views

User value:

- Karen can ask what exists without needing to know where it lives
- document/review state becomes clearer
- first memory value arrives without mutation risk

Technical work:

- create read-only memory inventory helpers
- expose compact document/review/pending views
- require client scope for lookup
- hide technical IDs by default
- preserve existing Tuesday behavior until this is separately tested

Files/modules likely touched later:

- document registry or document inventory modules
- memory/read-model helpers
- tests or smoke scripts for document inventory
- Telegram response rendering only after helpers are stable

Risk level:
Medium.

Suggested ETA in sessions:
1-2 sessions.

Smoke tests:

- Karen-scoped document inventory returns only Karen-safe items
- review-needed list marks OCR/manual-review documents honestly
- no raw paths, chat IDs, internal IDs, or unrelated client data in default output
- existing Tuesday prompts still behave as before

Example prompts:

```text
Val, qué documentos tengo?
Val, qué falta revisar?
```

---

## Phase 2: Labels / Status / Source Fields

User value:

- documents become recognizable by human labels
- Val can say whether something is received, readable, summarized, or needs OCR/manual review
- labels reduce confusion without creating more folders

Technical work:

- add or normalize label/status/source fields in the read model
- distinguish source label, status label, domain label, and action label
- maintain original source metadata internally
- keep debug IDs hidden by default

Files/modules likely touched later:

- document metadata/read-model layer
- label formatter/helper module
- document inventory renderer
- focused tests for label display and status honesty

Risk level:
Medium.

Suggested ETA in sessions:
1-2 sessions.

Smoke tests:

- photo shows `requires OCR/manual review` and is not summarized as read
- PDF/readable doc shows readable/review status correctly
- label display is human-readable
- debug/internal IDs appear only in explicit debug path

Example labels:

```text
Finca 10082 - documento recibido
Foto de Finca - requiere OCR
Paquete legal Nora - revisión pendiente
```

---

## Phase 3: Unified Agenda Read View

User value:

- Karen can ask one question for today/tomorrow
- Google Calendar, Val reminders, tasks, document reviews, and follow-ups appear in one source-labeled view
- uncertain items are not mistaken for hard events

Technical work:

- merge read-only agenda sources into one ordered day view
- preserve source IDs internally
- deduplicate display without losing source identity
- separate hard events, reminders, pending actions, overdue/review-needed items
- no create/delete/edit behavior in read query

Files/modules likely touched later:

- calendar read helpers
- reminder/task read helpers
- document review read helpers
- unified agenda read model
- agenda renderer
- smoke tests for source distinction and no mutation

Risk level:
Medium-high, because calendar and reminder routing can be sensitive.

Suggested ETA in sessions:
2-3 sessions.

Smoke tests:

- `Val, qué tengo hoy?` shows source labels
- Google Calendar events are separate from Val reminders
- stale/overdue reminders are marked honestly
- document review item appears as review, not confirmed event
- no create/delete/edit path is triggered by read-only query

Example sections:

```text
Eventos confirmados
Recordatorios
Pendientes
Vencido / requiere revisión
Siguiente acción sugerida
```

---

## Phase 4: Topic Containers / Carpetas Basic Commands

User value:

- Karen gets stable broad areas: Finca, Proyectos, Pendientes
- notes/documents/pending items can be classified without over-fragmenting
- Val can explain where something was saved

Technical work:

- implement basic folder/topic read model
- support create/list/save-note commands after read-only foundation is stable
- keep initial Karen folders broad
- support candidate subtopics without automatic promotion
- require confirmation for sensitive cross-links or major reorganization

Files/modules likely touched later:

- topic/folder model or metadata store
- command parser/router for folder commands
- memory linkage helpers
- tests for create/list/save/move flows
- confirmation flow helpers if available

Risk level:
Medium-high, because this introduces mutation and routing surface.

Suggested ETA in sessions:
2-4 sessions.

Smoke tests:

- `Val, qué carpetas tengo?` lists Finca, Proyectos, Pendientes
- `Val, guarda esto en Finca` saves only after intended command path
- a one-off book idea stays under Proyectos > Libro as candidate, not a new folder
- sensitive Finca/book cross-link asks first
- no new folder is created for every random idea

---

## Phase 5: Timeline / Action Extraction

User value:

- Val can help answer when something happened
- document review can become timeline candidates
- pending actions become clearer after meetings/documents

Technical work:

- extract timeline entries only from readable/source-backed material
- extract action items separately from facts
- mark confidence/source status
- keep legal/admin actions separate from legal conclusions
- support review-needed and candidate timeline states

Files/modules likely touched later:

- timeline model/helpers
- document summary/extraction helpers
- action item model/helpers
- review queue helpers
- tests for no invented chronology and no legal conclusions

Risk level:
High.

Suggested ETA in sessions:
3-5 sessions.

Smoke tests:

- OCR-needed photo does not create a confirmed timeline entry
- readable document can produce candidate dates with source/status
- `Val, cuándo pasó X?` says unknown if source is missing
- `ask lawyer` remains an action label, not legal advice
- stale action remains stale until updated or completed

---

## Phase 6: Conversational Memory Retrieval

User value:

- Val starts to feel like a memory partner instead of separate commands
- users can ask naturally and get grounded answers
- next actions become easier without unsafe automation

Technical work:

- route natural memory questions to read-only retrieval modes
- use response templates with source/context/uncertainty/suggested action
- score or classify memory status internally
- ask one clarifying question only when needed
- keep action execution behind explicit confirmation

Files/modules likely touched later:

- conversational memory router
- memory retrieval orchestrator
- answer templates/renderers
- client identity resolver integration
- route-order tests
- no-action smoke tests

Risk level:
High.

Suggested ETA in sessions:
3-6 sessions.

Smoke tests:

- `Val, qué sabes de la finca?` answers from Karen-scoped memory only
- `Val, qué documentos tengo?` routes to document inventory
- `Val, qué falta revisar?` routes to review queue
- `Val, cuándo pasó X?` does not invent dates
- `Val, qué hago ahora?` suggests one action without creating/editing anything
- Frank/Karen/Sol/Roy memory cannot mix

---

## 4. Karen-First Implementation Path

### What Karen Gets First

Start with the least risky, highest clarity improvements:

1. cleaner document inventory labels
2. review-needed list
3. source/status honesty for OCR/manual review
4. read-only today/tomorrow view with source labels
5. broad static topic summary for Finca, Proyectos, Pendientes

User-facing first wins:

```text
Val, qué documentos tengo?
Val, qué falta revisar?
Val, qué tengo hoy?
Val, qué sabes de la finca?
```

### What Can Wait

Defer:

- automatic folder creation
- smart cross-linking
- timeline extraction from unread/OCR-needed documents
- full conversational router
- mark-done / move / create commands
- shared/family permissioning
- advanced roadmap-memory integration

### What Must Not Be Touched Before Tuesday

Do not touch before Tuesday:

- `bot.py`
- OAuth
- tokens
- systemd
- `/etc/val0`
- runtime routing
- real client data
- memory database schema
- production documents
- real document storage
- OCR/external services

Tuesday principle:

```text
Deliver the founder-beta safely. Build Memory Foundation after the baseline is protected.
```

---

## 5. Founder-Beta Product Path

### What Helps Sell Val0 Personal

Val0 Personal becomes easier to explain when it can show:

- "what you have"
- "what needs review"
- "what is next"
- "what changed"
- "where this belongs"

High-value founder-beta demos:

```text
Val, qué documentos tengo?
Val, qué falta revisar?
Val, qué tengo hoy?
Val, qué sabes de la finca?
Val, qué hago ahora?
```

Product language:

```text
Val organizes your personal operating context: documents, reminders, pending actions, and memory you can ask about.
```

### What Helps Val1 Business Later

The same foundation can later support:

- client/project memory
- deal/customer folders
- team follow-ups
- document status queues
- meeting action extraction
- source-aware operational Q&A
- role-based sensitive memory
- auditability and provenance

Business value depends on:

- client isolation
- permissions
- source/provenance
- reliable action status
- no hallucinated business facts

---

## 6. Conversationality Placement

### Why It Is Important

Conversationality is how the user experiences the memory system.

Without it, memory becomes a set of rigid commands. With safe conversationality, Val can answer naturally:

```text
De Finca tengo documentos, pendientes y cosas por revisar. Lo que requiere OCR todavía no lo trato como leído.
```

### Why It Should Not Be Full Free-Chat First

Full free-chat first is risky because:

- it can hide missing source data
- it may sound confident while guessing
- it can blur client scopes
- it can trigger action expectations
- it can confuse memory retrieval with tool execution

Conversational tone should come after read-only retrieval paths are reliable.

### Safe Conversationality Formula

Build conversationality from:

1. memory retrieval
2. source/status labels
3. route classification
4. response templates
5. confirmation before actions

Pattern:

```text
Direct answer.
Source/context note.
Uncertainty if needed.
Suggested next action.
One optional follow-up question.
```

This keeps Val warm and useful without turning memory into confident guessing.

---

## 7. Kill / Continue Criteria

### Continue When Healthy

Continue the architecture when:

- client-scoped lookups are mandatory and tested
- document status is honest
- source labels are visible in user-facing answers
- read-only views do not mutate data
- raw technical IDs are hidden by default
- existing Tuesday prompts remain stable
- smoke tests catch cross-client leakage and route confusion
- user answers are shorter and clearer than prior technical dumps

### Pause / Rebuild When Unhealthy

Pause or rebuild if:

- memory lookup can run without `client_id`
- a read-only query can mutate data
- OCR-needed documents are treated as understood
- labels/folders are used as proof of legal facts
- folder creation explodes for one-off ideas
- calendar events and internal reminders become indistinguishable
- route ordering steals existing Tuesday prompts
- source IDs or private filenames leak in normal answers
- confidence language is hidden from uncertain answers

Decision rule:

```text
If Val sounds smarter by becoming less grounded, pause. Grounding wins.
```

---

## 8. Open Questions

- Should the first read-only memory inventory be built from existing document registry helpers or a new read model?
- Should labels be persisted first, or computed at render time from current metadata?
- What is the smallest safe storage shape for topic containers?
- Should Unified Agenda merge happen before or after topic containers?
- What is the safest route boundary for `qué hago ahora`?
- How should source IDs be preserved internally while hidden from normal answers?
- What is the minimum client-isolation test fixture across Karen/Frank/Sol/Roy?
- How should user corrections update memory without creating false confidence?
- Should Roadmap Answer Mode read from Memory Library or remain a separate product registry?
- What is the first post-Tuesday smoke suite that proves the foundation is safe?

---

## 9. Operator Summary

Post-Tuesday build order:

1. Make memory visible without mutation.
2. Make documents readable by humans with honest labels.
3. Merge the day view read-only.
4. Add broad topic containers.
5. Extract timelines/actions from grounded sources.
6. Add conversational retrieval last, backed by the safe read paths.

Operator line:

```text
Primero memoria visible y honesta. Después etiquetas. Después agenda. Después carpetas. Después extracción. Y solo al final conversación natural encima de rutas seguras.
```
