# Infinite Memory / Library Architecture v0

## Purpose

Val0 memory should become durable, structured, queryable operating memory, not just chat history. The goal is not to stuff every past message into a prompt. The goal is to build a memory library that knows what exists, where it came from, who it belongs to, how reliable it is, and when it should be loaded for a task.

This architecture treats memory as an operating system for client context: structured enough for deterministic tools, traceable enough for legal/document work, and selective enough to keep answers focused.

## Core Analogy

Val0 memory is a library:

- Hot memory = books open on the table.
- Warm memory = books nearby / recently used.
- Cold storage = archived books, documents, transcripts, events, and long-tail history.
- Librarian/index = catalog/key that knows where every book is.
- Reading desk = current context window loaded before answering.
- Book tags = metadata: client, topic, source, date, confidence, privacy level.

The assistant should not carry the entire library in its hands. It should ask the librarian for the right books, open only the relevant pages on the reading desk, and cite or track where each claim came from.

## Memory Layers

### Hot / Session Memory

Short-lived context for the current conversation, active confirmations, pending actions, recent user turns, and immediate task state.

Examples:

- pending yes/no confirmation
- current appointment draft
- current grocery command
- current document inventory answer
- active guided flow

### Warm / Recent Client Context

Recently used client context that is likely relevant across nearby turns or sessions.

Examples:

- last few agenda interactions
- recent legal/finca questions
- recent document summaries
- active reminders or tasks
- current client objective

### Structured Client Profile Memory

Durable client-level facts and preferences.

Examples:

- client id
- display name and vocative
- preferred language
- communication preferences
- connected tools status
- client-specific safety or routing rules

### Case / Project Memory

Structured memory for long-running matters, cases, projects, and operational threads.

Examples:

- case id
- stakeholders
- open questions
- current status
- next actions
- known facts
- unresolved contradictions

### Document / Timeline Memory

Grounded document and chronology memory with source references.

Examples:

- document registry
- extracted text
- document summaries
- timeline events
- source document ids
- confidence and OCR quality
- date ranges

### OPEL / Event-Log Memory

Append-only operational event memory for actions, tool results, confirmations, failures, audits, and handoff traces.

Examples:

- reminder created
- calendar event created/deleted
- document ingested
- user confirmed action
- external webhook received
- Launchpad verification result

### Cold Archival Storage

Long-term storage for documents, transcripts, logs, old chats, old generated artifacts, and raw source material.

Cold storage is not loaded by default. It is retrieved only through the index and only when relevant.

### Retrieval / Index Layer

The librarian/catalog layer that maps user tasks to relevant memory.

The index should support:

- exact fact lookup
- source lookup
- timeline lookup
- semantic/document retrieval
- client and privacy filters
- confidence and provenance filtering

## Source-of-Truth Rules

- Val0 client memory remains authoritative unless explicitly changed by a future architecture.
- External tools like n8n may send intake/events but should not become the source of truth.
- Documents must preserve provenance/source.
- Generated summaries must be traceable to source documents or explicit user notes.
- If a summary and a source document disagree, the source document wins until reviewed.
- Structured facts should record who/what created them, when, and from which source.
- Tool outputs should be logged as events, not silently merged into memory.

## Privacy And Safety Rules

- Client isolation is required.
- No cross-client leakage.
- Sensitive/legal data must be scoped to the correct client, case, and permission boundary.
- External SaaS use requires privacy review before real client data is sent.
- Memory should support deletion/export later.
- Memory reads should be filtered by client id before any semantic or keyword retrieval.
- Unknown clients must not inherit another client profile, path, calendar config, or memory.
- Legal/document answers should distinguish grounded facts from interpretation.

## Retrieval Rules

- Do not load everything into the prompt.
- Retrieve selectively based on task.
- Prefer exact structured facts over vague summary.
- Prefer source documents over generated summaries when answering factual/legal questions.
- Show uncertainty when the source is weak.
- Track confidence and source.
- Keep the reading desk small: current task, relevant profile, relevant case/project, relevant documents/events.
- If retrieval returns conflicts, surface the conflict instead of smoothing it away.

## Karen MVP Mapping

Current Karen/client-zero needs map naturally into this library model:

| Need | Memory Layer | Notes |
| --- | --- | --- |
| Finca facts | Case/project memory + structured facts | Must be scoped to Karen and the land case |
| Heirs | Case/project memory + document/timeline memory | Needs provenance and confidence |
| Public registry documents | Document/timeline memory + cold archival storage | Preserve source ids, dates, extracted text |
| Lawyer meeting notes | Warm context + case/project memory + OPEL | Separate user notes from generated prep |
| Timeline from 1986-present | Document/timeline memory | Events should cite source documents or explicit notes |
| Reminders/calendar | Hot/session + OPEL + structured agenda memory | Confirmation and audit trail required |
| Document/photo summaries | Document/timeline memory | Summaries must trace to source docs/photos |

Karen MVP should keep answering from the current deterministic flows while gradually moving facts, timelines, and document provenance into structured library layers.

## Roadmap Placement

### Phase 0: Current SQLite / Current Memory

Current state:

- encrypted/local memory database
- client files
- deterministic handlers
- case/document modules
- ad hoc summaries and routing guards

Goal:

- stabilize current behavior
- preserve client isolation
- continue compile/audit/smoke discipline

### Phase 1: Structured Client Profile + Source Tags

Add consistent metadata to client memory:

- client id
- topic
- source
- date
- confidence
- privacy level
- created_by

Outcome:

- less hardcoded client behavior
- cleaner retrieval boundaries
- safer multi-client expansion

### Phase 2: Karen Case Timeline Memory

Create a structured timeline for Karen’s land/finca case.

Must support:

- date or date range
- event text
- source document/note
- confidence
- unresolved questions

Outcome:

- grounded “what happened when?” answers
- better lawyer package generation
- fewer repeated manual summaries

### Phase 3: Document Registry + Retrieval Index

Build a document registry and retrieval layer.

Must support:

- document id
- filename/source
- extracted text location
- summary
- OCR quality
- linked case/client
- timeline facts extracted from source

Outcome:

- document answers can retrieve exact sources
- summaries become traceable
- cold documents stay out of the prompt unless needed

### Phase 4: OPEL / Event Log Integration

Unify operational events into a queryable event log.

Must include:

- user confirmations
- tool writes/deletes
- reminders
- calendar events
- workflow intake
- Launchpad verification results
- failed actions

Outcome:

- better continuity
- clearer audits
- easier recovery after failures

### Phase 5: Multi-Client Memory Graph With Privacy Boundaries

Expand from single client-zero flows to multiple clients with strict boundaries.

Must support:

- client-level access filters
- case/project boundaries
- shared generic knowledge separated from private client memory
- export/delete workflows
- privacy review for external tools

Outcome:

- Val0 can scale without cross-client contamination
- retrieval remains useful without becoming unsafe

## Tool Assimilation

n8n/Nate-style commands may become an intake/workflow lane for structured events, reminders, or admin workflows. They should not become the source of truth. They may submit events into Val0 for validation, confirmation, and storage.

Codex should be used for implementation, refactors, tests, and architecture changes that touch multiple files or shared behavior.

Launchpad should verify runtime health, logs, service state, and recovery steps when memory or retrieval changes affect production behavior.

Future vector/document tools are candidates for retrieval, indexing, OCR, and semantic search only after privacy review. They must respect client boundaries and source-of-truth rules.

## Do Not Do

- Do not dump all memory into the prompt.
- Do not let external tools mutate memory without Val0 confirmation/rules.
- Do not mix client memories.
- Do not treat LLM summaries as ground truth.
- Do not build “infinite memory” before source/provenance rules exist.
- Do not send real legal/client data to external SaaS without privacy review.
- Do not let semantic retrieval bypass client id filters.
- Do not store generated conclusions without the source trail that supports them.
