# CARPETAS_TOPIC_CONTAINERS_V0

Purpose:
Design Carpetas / Topic Containers for Val0 / Valdia as the next memory foundation.

Carpetas organize a user's life/work into broad human areas without creating a separate folder for every random thought too early. They should support memory, retrieval, follow-up, documents, pending items, and future Roadmap Answer Mode.

Tone:
Spanish-first examples, product-safe, operator-ready, concise, practical.

---

## 1. Purpose

Carpetas should help Val answer:

- where something belongs
- what a user has in a topic
- what is pending in a topic
- what documents are linked to a topic
- which ideas are recurring enough to become their own folder
- what roadmap items relate to a user's real workflow

The goal is not to build a file cabinet with hundreds of tiny folders. The goal is a human memory map:

```text
Fewer broad containers first. More structure only when repeated use proves it is useful.
```

---

## 2. Core Concept

Use broad folders first.

Inside each folder, allow:

- notes
- documents
- pending items
- candidate subtopics
- recurring themes
- links to related folders

Promotion rule:

```text
A subtopic becomes a dedicated folder only after repeated use, clear value, or explicit user request.
```

Val may suggest classification:

```text
Esto suena a Proyectos. Lo guardo ahí?
```

Val should ask before major reorganization:

```text
Veo que "Libro" aparece varias veces dentro de Proyectos. Quieres que lo convierta en carpeta propia?
```

Val must not silently reorganize important or sensitive content.

---

## 3. Karen Initial Folders

Initial broad folders for Karen/client-zero:

- Finca
- Proyectos
- Pendientes

Optional later:

- Supermercado

Optional candidate subtopic:

- Libro, under Proyectos

Important:
These are product-safe labels. Do not put private legal facts, document IDs, case IDs, local paths, or private filenames into reusable product docs.

---

## 4. Folder Vs Subtopic Vs Note

### Folder

A broad persistent area.

Examples:

- Finca
- Proyectos
- Pendientes
- Supermercado

Use when:

- the area will recur
- the user expects to ask about it later
- documents/pending items may link to it
- it helps organize retrieval

### Subtopic

A recurring theme inside a folder.

Example:

- Proyectos > Libro

Use when:

- the idea appears more than once
- it is not yet big enough to become its own folder
- it helps cluster related notes

### Note

A one-off capture.

Example:

```text
Val, esto es una idea para un libro: una historia sobre memoria familiar.
```

Default:
Save as a note under Proyectos, candidate subtopic Libro.

### Pending

An actionable item.

Example:

```text
Val, agrega a Pendientes revisar documentos antes de la cita.
```

Default:
Create/link a pending item under Pendientes, and optionally cross-link to Finca if user confirms.

### Document

An attachment/file item linked to a folder/topic.

Example:

```text
Val, guarda este documento en Finca.
```

Default:
Link document to Finca; preserve document status separately.

---

## 5. Example Flows

### Save To Finca

User:

```text
Val, guarda esto en Finca: revisar documentos antes de hablar con la abogada.
```

Val:

```text
Listo. Lo guardo en Finca como nota/pending de revisión.
```

If action is unclear:

```text
Lo guardo en Finca como nota o como pendiente?
```

### Add To Pendientes

User:

```text
Val, agrega esto a Pendientes: preparar preguntas para Nora.
```

Val:

```text
Listo. Lo agrego a Pendientes.
```

### Book Idea

User:

```text
Val, esto es una idea para un libro: organizar la historia por capítulos.
```

Val:

```text
Lo guardo en Proyectos como idea. También lo marco como candidato de subtema: Libro.
```

### Ask Pending

User:

```text
Val, qué tengo pendiente?
```

Val:

```text
Tienes pendientes en:
1. Finca
2. Proyectos
3. General

Quieres ver todos o solo uno?
```

### Ask Projects

User:

```text
Val, qué tengo en Proyectos?
```

Val:

```text
En Proyectos tengo:
1. Ideas recientes
2. Candidato de subtema: Libro
3. Pendientes relacionados
```

### Search Finca Documents

User:

```text
Val, busca fotos/documentos en Finca.
```

Val:

```text
Busco documentos vinculados a Finca. Si una foto requiere OCR/revisión, te lo marco sin fingir que ya está leída.
```

---

## 6. Smart Suggestion Behavior

### Single Mention

If user mentions book once:

- save under Proyectos
- mark `Libro` as candidate subtopic
- do not create a standalone folder yet

Example:

```text
Lo guardo en Proyectos como idea de Libro. Si esto se repite, puedo sugerirte convertir Libro en carpeta.
```

### Repeated Use

If user mentions book repeatedly:

```text
Veo que Libro ya aparece varias veces dentro de Proyectos. Quieres que lo convierta en carpeta propia?
```

### Cross-Link Sensitive Content

If a legal/admin case becomes a possible book idea:

```text
Esto podría vincularse a Finca y también a Proyectos > Libro. Por ser sensible, no lo cruzo automáticamente. Quieres que lo enlace en ambos lugares?
```

Rule:
Do not silently cross-link sensitive content.

### Major Reorganization

Before moving many items:

```text
Puedo reorganizar esto, pero antes confirmo: quieres mover estas notas de Proyectos a una carpeta Libro?
```

---

## 7. Data Model Design

Future structured shape:

```yaml
folder:
  folder_id: "folder_finca"
  client_id: "client_alias_or_id"
  display_name: "Finca"
  description: "Legal/admin continuity and related documents/pending items."
  status: "active"
  created_at: "2026-05-25T00:00:00"
  updated_at: "2026-05-25T00:00:00"
  visibility: "client_private"
  scope: "personal_founder"
  items_linked:
    notes: []
    documents: []
    pending_items: []
    reminders: []
  candidate_subtopics:
    - name: "Libro"
      evidence_count: 1
      status: "candidate"
  source:
    created_by: "operator_or_user"
    provenance: "explicit_user_request"
  privacy_notes:
    - "Do not expose technical IDs by default."
    - "Do not copy private legal facts into product docs."
```

Fields:

- `folder_id`
- `user/client_id`
- `display_name`
- `description`
- `status`
- `created_at`
- `updated_at`
- `visibility/scope`
- `items_linked`
- `candidate_subtopics`
- `source/provenance`
- `privacy_notes`

Possible status values:

- `active`
- `candidate`
- `archived`
- `parked`
- `needs_confirmation`
- `blocked`

---

## 8. Commands / Phrases To Support Eventually

Folder creation:

- `Val, crea carpeta Finca`
- `Val, crea carpeta Proyectos`
- `Val, crea carpeta Pendientes`

Save/link:

- `Val, guarda esto en Finca`
- `Val, guarda esto en Proyectos`
- `Val, agrega pendiente`
- `Val, agrega esto a Pendientes`

List/query:

- `Val, qué tengo en Pendientes`
- `Val, qué tengo en Proyectos`
- `Val, qué carpetas tengo`
- `Val, busca documentos en Finca`

Move/reclassify:

- `Val, mueve esto a Proyectos`
- `Val, crea subtema Libro dentro de Proyectos`
- `Val, esto no va en Finca, va en Proyectos`

Search:

- `Val, busca fotos/documentos en Finca`
- `Val, qué documentos tengo en Finca`
- `Val, qué pendientes tengo en Proyectos`

---

## 9. Guardrails

- No over-fragmentation.
- No silent creation of many folders.
- No private fact leakage into product docs.
- No legal conclusion based on folder membership.
- No automatic cross-linking without user confirmation when sensitive.
- Preserve client isolation.
- Do not expose technical IDs by default.
- Do not treat folder names as proof of facts.
- Do not infer legal status from a folder label.
- Do not move/delete content without explicit confirmation.

Safe line:

```text
Puedo sugerir dónde va, pero no voy a reorganizar contenido importante sin confirmarte primero.
```

---

## 10. UX Rules

Confirm concisely:

```text
Listo. Lo guardé en Finca.
```

Ask one clarifying question only when needed:

```text
Esto lo guardo como nota o como pendiente?
```

Allow lightweight confirmation:

- `sí`
- `dale`
- `ok`
- `sí, crea la carpeta`

Explain where something was saved:

```text
Lo guardé en Proyectos > Libro como idea.
```

Let user rename/move later:

```text
Después puedes decir: "Val, mueve esto a Finca" o "Val, renombra Libro".
```

Avoid long taxonomy explanations in normal use. Save that for help/debug.

---

## 11. Implementation Phases

### Phase 0: Design Doc Only

Status:
This document.

No runtime behavior.

### Phase 1: Static Folder List / Manual Roadmap

Create a static folder list for Karen:

- Finca
- Proyectos
- Pendientes

Use it in docs/manual roadmap only.

### Phase 2: Create/List/Add Note To Folder

Support deterministic commands:

- create folder
- list folders
- save note to folder
- show folder contents

No smart reorganization yet.

### Phase 3: Link Documents/Pending Items

Allow documents and pending items to link to folders.

Requirements:

- preserve document status
- hide technical IDs by default
- keep read-only views safe
- do not mutate document facts silently

### Phase 4: Smart Suggestions / Candidate Subtopics

Add suggestions:

- repeated themes
- candidate subtopics
- "create folder?" prompts

Must ask before major changes.

### Phase 5: Cross-Folder Search And Roadmap Integration

Enable:

- search by folder
- query pending by folder
- Roadmap Answer Mode referencing folder status
- cross-folder links with confirmation

---

## 12. Karen-Specific Examples

### Finca

Use for:

- legal/admin continuity
- related documents
- chronology references
- meeting prep items
- review/pending items

Do not use for:

- legal conclusions
- detailed private legal fact dumps in product docs
- raw document IDs in normal user answers

### Proyectos

Use for:

- personal projects
- ideas
- creative work
- future plans

### Pendientes

Use for:

- simple actionable list
- next steps
- reminders that need follow-up
- tasks waiting on review

### Libro As Candidate Subtopic

Start as:

```text
Proyectos > Libro
```

Promote only if repeated use/value appears.

### Supermercado Later

Start as optional later folder if grocery/list workflow becomes recurring enough.

Do not create by default unless it becomes useful.

---

## 13. Open Questions

- Should folders live in DB, Markdown, or structured JSON first?
- How should shared/family folders work?
- How should permissions work for sensitive folders?
- How should technical IDs be exposed only in debug mode?
- Should folder membership be many-to-many from day one?
- How should folder history/audit be shown to the user?
- Should folder suggestions be per-client or reusable model behavior?
- What is the minimum smoke test for folder routing without stealing document/timeline/agenda routes?

---

## 14. Product Principle

Carpetas are not decoration. They are a memory boundary.

Good Carpetas behavior:

- helps the user find things later
- keeps broad areas stable
- avoids premature structure
- asks before reorganizing sensitive content
- supports retrieval and follow-up
- stays honest about what is stored vs understood

Bad Carpetas behavior:

- creates a folder for every thought
- hides where things went
- silently cross-links sensitive information
- turns folder labels into legal conclusions
- exposes private facts in reusable product docs

Operator line:

```text
Primero organizamos en pocas carpetas humanas. Si un tema se repite y te sirve, Val puede sugerir convertirlo en carpeta propia.
```

