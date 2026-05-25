# DOCUMENT_LABELS_NAMING_CONVENTION_V0

Purpose:
Design document labels and naming conventions for Val0 / Valdia, with Karen/client-zero founder-beta as the first practical reference.

This is a product/design document only. It is not runtime config, not a document registry, not a legal record, and not a promise that label automation is ready for Tuesday founder-beta delivery.

Tone:
Spanish-first examples, product-safe, operator-ready, concise, practical.

---

## 1. Purpose

Document labels should help Val answer:

- what a document is
- where it belongs
- whether it is readable
- what action may be needed next
- how it relates to a folder/topic without creating too many folders
- what can be retrieved later without exposing technical IDs

The goal is simple human recognition:

```text
Val should name and label documents in a way Karen can recognize, without pretending unreadable files were understood.
```

Labels support Karen's legal/finca/document/photo workflow, but the design must remain reusable and privacy-safe.

---

## 2. Naming Principles

Use names that are:

- human-readable
- short enough for Telegram-style answers
- stable enough to recognize later
- honest about read/review status
- broad enough to avoid premature folder sprawl
- free of raw paths, chat IDs, VFMS IDs, internal IDs, or private filenames by default

Prefer:

```text
Finca 10082 - documento recibido
Foto de Finca - requiere OCR
Paquete legal Nora - revisión pendiente
Idea de libro - relacionada con Finca
```

Avoid:

```text
[raw local path]/client/path/raw_file_name.pdf
doc_8f13_case_private_final_FINAL2.jpg
Prueba legal concluyente
Carpeta nueva para cada idea suelta
```

Naming rule:

```text
Use the least private name that still lets the user recognize the item.
```

---

## 3. Folder Vs Topic Container Vs Labels

### Folder

A broad persistent area the user expects to revisit.

Examples:

- Finca
- Proyectos
- Pendientes
- Supermercado, later if recurring

Folders should be few and stable.

### Topic Container

A memory container that can hold notes, documents, pending items, recurring themes, and candidate subtopics.

Example:

```text
Proyectos > Libro
```

In early phases, folder and topic container may feel similar to the user. Product design should treat a topic container as the broader memory concept and a folder as the user-facing simple name.

### Document Label

A human-readable label attached to a document or attachment.

Example:

```text
Foto de Finca - requiere OCR
```

It helps users recognize the item without exposing raw technical details.

### Source Label

Where the item came from or what format it appears to be.

Examples:

- user-uploaded
- photo
- PDF
- Word/doc
- manual note
- audio transcript

### Status Label

What Val can honestly say about the item right now.

Examples:

- received
- readable
- needs OCR
- needs manual review
- summarized
- linked to case
- archived

### Action Label

What the next useful human or product action might be.

Examples:

- ask lawyer
- review with Karen
- extract dates
- add to timeline
- create reminder

Action labels are suggestions or next-step markers. They are not legal conclusions.

---

## 4. Suggested Label Categories

### Source

Use source labels to say what kind of input Val received.

- `user-uploaded`
- `photo`
- `PDF`
- `Word/doc`
- `manual note`
- `audio transcript`

User-facing examples:

```text
Recibido como foto.
Recibido como PDF.
Guardado como nota manual.
```

### Domain

Use domain labels to connect the item to a broad area without necessarily creating a folder.

- `finca`
- `legal`
- `agenda`
- `grocery`
- `health/life`
- `project`
- `book idea`

User-facing examples:

```text
Lo marco como Finca y Legal.
Lo guardo en Proyectos como idea de libro.
Esto suena a agenda, no a documento legal.
```

### Status

Use status labels to preserve honesty about what Val has actually read.

- `received`
- `readable`
- `needs OCR`
- `needs manual review`
- `summarized`
- `linked to case`
- `archived`

User-facing examples:

```text
Recibido, pero requiere OCR antes de resumirlo.
Leíble y listo para resumen.
Resumido, con revisión humana pendiente.
```

### Action

Use action labels to mark likely next steps.

- `ask lawyer`
- `review with Karen`
- `extract dates`
- `add to timeline`
- `create reminder`

User-facing examples:

```text
Siguiente acción sugerida: revisar con Karen.
Puedo extraer fechas y proponerlas para la cronología.
Puedo crear un recordatorio, si me confirmas.
```

---

## 5. Karen Examples

These examples are product-safe naming patterns. They should not store private legal facts, raw document names, local paths, IDs, or detailed case history.

### Finca 10082 Document

Suggested display label:

```text
Finca 10082 - documento recibido
```

Suggested labels:

- source: `PDF` or `photo`, depending on actual input
- domain: `finca`, `legal`
- status: `received`, then `readable` or `needs OCR`
- action: `review with Karen`, `extract dates`, `add to timeline`

Safe response:

```text
Lo guardé como "Finca 10082 - documento recibido". Estado: recibido. Si no está leíble, lo marco como requiere OCR/revisión.
```

### Photo Needing OCR

Suggested display label:

```text
Foto de Finca - requiere OCR
```

Suggested labels:

- source: `photo`
- domain: `finca`
- status: `received`, `needs OCR`
- action: `manual review`, `extract dates` only after readable text exists

Safe response:

```text
Recibí la foto y la marqué como Finca. Todavía requiere OCR/revisión; no voy a fingir que ya entendí el contenido.
```

### Nora / Legal Package

Suggested display label:

```text
Paquete legal Nora - revisión pendiente
```

Suggested labels:

- source: `PDF`, `manual note`, or mixed package
- domain: `legal`, `finca` if confirmed
- status: `received`, `needs manual review`
- action: `ask lawyer`, `review with Karen`, `extract dates`

Safe response:

```text
Lo marco como paquete legal para revisar con Nora. No saco conclusiones legales; puedo ayudarte a ordenar preguntas y pendientes.
```

### Book Idea Related To Finca

Suggested display label:

```text
Idea de libro - relacionada con Finca
```

Suggested labels:

- source: `manual note`
- domain: `project`, `book idea`
- status: `received`
- action: `review with Karen`

Default placement:

```text
Proyectos > Libro
```

Safe response:

```text
Lo guardo en Proyectos como idea de libro. Como toca Finca, puedo sugerir un enlace cruzado, pero te confirmo antes por ser sensible.
```

---

## 6. Rules

- Do not create a new folder for every idea.
- Start broad, then promote repeated topics into folders.
- Never pretend unreadable or OCR-needed files were understood.
- Keep labels human-readable.
- Keep document names shorter than the explanation around them.
- Separate label from fact: a label helps organize; it does not prove legal meaning.
- Do not infer legal conclusions from folder membership or labels.
- Do not expose raw paths, chat IDs, document IDs, private filenames, or cross-client data by default.
- Do not silently cross-link sensitive legal/admin material into creative projects.
- Preserve client isolation across all label generation, retrieval, and display.

Safe line:

```text
Puedo etiquetarlo para encontrarlo mejor, pero si el archivo requiere OCR/revisión, todavía no lo trato como leído.
```

---

## 7. Runtime Notes For Later Implementation

No runtime behavior is implemented by this document.

Later implementation should consider:

- label schema separate from folder schema
- many-to-many labels per document
- one primary display label plus structured labels underneath
- status labels generated from extraction/readability state, not from guesswork
- source labels generated from intake metadata where available
- domain labels suggested by routing/classification but confirmed when sensitive
- action labels as pending suggestions, not automatic actions
- debug mode for internal IDs only
- audit trail for label changes
- client-aware label vocabulary with reusable defaults

Possible structured shape:

```yaml
document_label:
  item_id: "doc_or_attachment_id"
  client_id: "client_alias_or_id"
  display_label: "Foto de Finca - requiere OCR"
  source_labels:
    - "photo"
  domain_labels:
    - "finca"
  status_labels:
    - "received"
    - "needs OCR"
  action_labels:
    - "review with Karen"
  linked_folders:
    - "Finca"
  candidate_topics: []
  provenance:
    created_by: "operator_or_system"
    reason: "user upload plus classification suggestion"
  privacy_notes:
    - "Hide technical IDs by default."
    - "Do not expose private filenames in reusable docs."
```

Implementation phases should happen after Tuesday stability is protected:

1. Design-only naming vocabulary.
2. Manual/operator label examples in docs.
3. Read-only display labels for document inventory.
4. Structured labels from source/status metadata.
5. User-confirmed domain/action labels.
6. Smart suggestions across folders, topics, documents, and roadmap answers.

---

## 8. Open Questions

- Should display labels be stored separately from original filenames?
- Should labels live in DB, Markdown, structured JSON, or document registry metadata first?
- Which labels are user-editable in founder-beta?
- How should Val show multiple labels without making answers noisy?
- When should `legal` be a domain label versus a sensitive scope flag?
- Should `book idea` remain a domain label or become a candidate subtopic under Proyectos?
- What is the minimum smoke test for document labels without touching runtime routes?
- How should label changes be audited?
- Should labels inherit from folders, or should folders inherit from labels?
- How should shared/family folders handle document labels and permissions?

---

## 9. Product Principle

Labels are not folders.

Good label behavior:

- helps the user recognize a document
- makes unread/readable/review-needed status obvious
- supports search and follow-up
- stays broad until repeated use proves a stronger structure is useful
- asks before sensitive cross-linking

Bad label behavior:

- creates a folder for every random idea
- claims OCR/photo content was understood when it was not
- exposes private technical details
- turns labels into legal conclusions
- hides where a document was saved or why it was marked

Operator line:

```text
Primero ponemos nombres y etiquetas claras. Si un tema se repite y sirve, después Val puede sugerir carpeta o subtema.
```
