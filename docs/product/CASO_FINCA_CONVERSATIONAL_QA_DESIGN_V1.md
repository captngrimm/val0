# Caso Finca Conversational Q&A Design v1

Status: DESIGN FIRST ONLY.

Purpose:
Define the first bounded conversational Q&A layer for Karen's Caso Finca. This is not open-domain ChatGPT. It is a scoped case/workspace intelligence layer that answers natural questions using known Caso Finca context, source-labeled document metadata, saved OCR-backed summaries, pending items, questions for Nora, and legal safety boundaries.

No runtime behavior is implemented by this document.

## 1. Current State / Source-of-Truth Summary

Current Val0 state:

- A-023 is live-green: founder-demo natural aliases route correctly.
- `docs/product/CASO_FINCA_CARPETA_CLARA_DESIGN_V1.md` defines the workspace/case model.
- `docs/product/FOUNDER_DEMO_READINESS_V1.md` defines the canonical founder-demo path.
- `core/case_workspace.py` renders the Caso Finca compact dashboard, document list, technical document details, pending items, questions for Nora, full workspace view, and numbered document summaries.
- `tests/fixtures/karen/caso_finca_workspace.json` contains safe source-labeled Caso Finca fixture data.
- Document #1 in Caso Finca can use saved OCR/text-backed summary when available.
- Existing document/OCR guards prevent fake summaries from watermark-only text.
- Karen RC and client fixtures protect agenda, tasks, reminders, GCal, documents, OCR, and folder behavior.

Live data constraints:

- Do not reset, discard, stage, or casually commit `clients/karen/CLIENT_GROCERY.md`.
- Do not reset, discard, stage, or casually commit `clients/karen/CLIENT_FOLDERS.json`.
- This design must not require live data mutation.

## 2. User-Facing Goals

Karen should be able to ask natural Caso Finca questions without remembering exact commands:

- "Val, que sabes del caso?"
- "Que falta revisar?"
- "Que significa este documento?"
- "Que le pregunto a Nora?"
- "Cual documento deberia revisar primero?"
- "Que sabemos seguro y que falta confirmar?"
- "Explicame lo de la finca en palabras simples."
- "Ese primer documento, por que importa?"
- "Hay algo raro o contradictorio?"
- "Que hago antes de hablar con la abogada?"

The answer should feel like:

- Val knows this is about Caso Finca.
- Val separates known facts from things to confirm.
- Val can explain why a document might matter, without pretending to decide legal effect.
- Val gives Karen practical next steps and Nora questions.
- Val remains warm and Tany-facing, but grounded.

## 3. Non-Goals

This lane does not:

- Make Val open-domain ChatGPT.
- Let an LLM execute writes, deletes, reminders, tasks, calendar actions, or document changes.
- Replace Nora/la abogada.
- Produce legal conclusions as certainty.
- Automatically OCR new documents.
- Mutate live client files.
- Refactor the broad router.
- Create a generic multi-client workspace engine in one jump.
- Promise perfect contradiction detection.

## 4. Data Sources Available Today

Available sources for a bounded Q&A packet:

- `WorkspaceCase` from `core/case_workspace.py`.
- Source-labeled fixture/workspace data from `tests/fixtures/karen/caso_finca_workspace.json`.
- Trusted document attachment metadata:
  - document title
  - document_id
  - OCR status
  - summary status
  - relevance
  - confidence/status/source labels
  - safe next action
- Saved OCR/extracted text for specific trusted documents when already available.
- Existing document summary helpers in `core/document_summary_queries.py`.
- Karen case status helpers in `core/karen_case_status.py`.
- Nora/legal packet logic in `core/karen_lawyer_package.py`.
- General client context reader surfaces in `core/client_context_reader.py`.
- Intent shadow/interpreter diagnostics in `core/intent_interpreter.py`.

Not source-of-truth for Q&A:

- Random recent chat memory unless it has been stored with source/context.
- Open-ended LLM speculation.
- Unreviewed OCR as legal truth.
- Generic case/finca legacy summary if it conflicts with source-labeled workspace data.

## 5. Retrieval / Source Grounding Plan

Use a small deterministic retrieval layer before any LLM wording:

1. Resolve the user question to Caso Finca.
   - Explicit aliases: `caso finca`, `finca`, `terreno`, `papeles de la finca`, `Nora`.
   - Demo-safe context: if user just viewed Caso Finca documents and asks "el primer documento", use the workspace document list.

2. Classify the question type.
   - `case_overview`
   - `needs_review`
   - `document_explanation`
   - `document_priority`
   - `known_vs_uncertain`
   - `nora_questions`
   - `next_action`
   - `possible_contradictions`
   - `plain_language_explanation`

3. Build a bounded evidence packet.
   - Workspace title and aliases.
   - What we know.
   - Needs confirmation.
   - Documents list with short metadata.
   - Selected document summary/OCR-backed bullets if a document is referenced.
   - Questions for Nora.
   - Pending items.
   - Legal boundary.
   - Source labels, confidence, status, and OCR caveat.

4. Answer only from that packet.
   - If evidence is missing, say so.
   - If a document has no OCR/text, say it is registered but not readable enough yet.
   - If there may be contradictions, frame them as "cosas que revisaria con Nora", not conclusions.

5. Include source grounding in friendly language.
   - "Lo saco del tablero Caso Finca y de documentos registrados."
   - "Esto viene de una lectura OCR guardada, asi que puede tener errores."
   - "Esto esta pendiente de confirmar."

## 6. Legal / Safety Boundary

Core rule:
Val organizes, explains, and prepares questions. Nora/la abogada confirms legal effect.

Allowed wording:

- "Esto parece importante porque..."
- "Esto conviene revisarlo con Nora."
- "Dato a confirmar."
- "Posible punto de atencion."
- "La lectura OCR sugiere..."
- "No lo tomaria como conclusion legal todavia."

Disallowed wording:

- "Legalmente significa que..."
- "El caso esta ganado/perdido."
- "Esto prueba definitivamente..."
- "No necesitas abogada."
- "Nora debe hacer..."

Every legal/document Q&A answer should include a compact boundary:

```text
Limite legal: Val organiza y resume; Nora/la abogada confirma efecto legal.
```

For OCR-backed answers, add:

```text
Nota OCR: esta lectura puede tener errores; conviene contrastarla con el PDF original.
```

## 7. Conversation State Needs

Minimum state needed for v1:

- `active_workspace`: `Caso Finca`
- `last_workspace_view`: compact, documents, technical details, full, pending, questions
- `last_document_list`: visible document numbers and document_ids
- `last_document_number`: if the user asked about "ese documento" or "el primer documento"
- `last_question_type`: overview, document explanation, Nora prep, etc.
- `last_answer_sources`: IDs/labels used in previous answer

Rules:

- State must be chat/client-scoped.
- State must expire or be invalidated when the visible list changes.
- Short replies like "ese", "el primero", "por que importa" can only use prior context if a valid workspace/document context exists.
- No state can authorize a write/delete action.

## 8. Proposed Deterministic vs LLM Responsibilities

Deterministic code responsibilities:

- Detect Caso Finca Q&A phrases.
- Resolve workspace/case identity.
- Resolve document numbers to current workspace attachments.
- Build the evidence packet.
- Validate source availability.
- Enforce legal boundary.
- Enforce no-write behavior.
- Decide if answer should be fallback, metadata-only, OCR-backed, or "needs manual review".
- Prevent cross-client contamination.

LLM-assisted wording responsibilities, if enabled later:

- Rewrite the bounded evidence packet into warmer Spanish.
- Convert facts into plain-language explanation.
- Group points into "Lo importante", "Que falta confirmar", "Preguntas para Nora", and "Siguiente paso".
- Avoid adding unsupported facts.

The LLM must not:

- Execute actions.
- Fetch new data.
- Invent facts.
- Decide legal meaning.
- Change tasks, reminders, calendar events, documents, or client files.

## 9. Prompt / Context Packet Shape

Future helper shape:

```text
CasoFincaQAPacket
- client_id
- chat_id
- workspace_id
- workspace_title
- user_question
- question_type
- visible_context
- known_facts[]
  - text
  - source_label
  - confidence
  - status
- needs_confirmation[]
- documents[]
  - visible_number
  - document_id
  - title
  - ocr_status
  - summary_status
  - relevance
  - confidence
  - status
  - short_safe_summary
- selected_document
  - visible_number
  - document_id
  - title
  - ocr_backed_bullets[]
  - caveats[]
- questions_for_nora[]
- pending_items[]
- next_actions[]
- legal_boundary
- forbidden_claims[]
```

LLM system instruction, if later used:

```text
You are Val answering Karen about Caso Finca.
Use only the supplied packet.
Do not add legal conclusions.
Separate known facts from things to confirm.
Write in Spanish, warmly, using Tany when natural.
If evidence is missing, say what is missing.
End with a Nora/legal boundary.
```

## 10. Answer Format Examples In Spanish

### Overview

User:
"Val, que sabes del caso?"

Answer:

```text
Tany, lo que tengo del Caso Finca en limpio es esto:

Lo que sabemos
1. Es un caso familiar relacionado con una finca/terreno.
2. Hay documentos registrados en Val0, y al menos uno tiene lectura OCR disponible.
3. Hay puntos que Nora/la abogada debe confirmar antes de tratarlos como efecto legal.

Que falta confirmar
1. Estado registral actual.
2. Que documento prueba mejor el estado del caso.
3. Si los autos/oficios mencionados siguen vigentes.

Siguiente paso
Yo revisaria primero el documento con OCR disponible y sacaria preguntas para Nora.

Limite legal: Val organiza y resume; Nora/la abogada confirma efecto legal.
```

### Known vs uncertain

User:
"Que sabemos seguro y que falta confirmar?"

Answer:

```text
Tany, te lo separo sin mezclar peras con escrituras publicas:

Mas firme por ahora
- Tengo documentos relacionados con Registro Publico/juzgado registrados en el tablero.
- El documento 1 tiene una lectura OCR guardada.

Todavia por confirmar
- Si esos documentos reflejan el estado registral actual.
- Que autos/oficios tienen efecto vigente.
- Cual documento debe llevar mas peso para explicarle el caso a Nora.

Pregunta clave para Nora
- "Con estos documentos, cual prueba mejor el estado actual de la finca?"

Limite legal: Val organiza y resume; Nora/la abogada confirma efecto legal.
```

### Document explanation

User:
"Ese primer documento, por que importa?"

Answer:

```text
Tany, el documento 1 importa como punto de partida porque tiene lectura OCR disponible y parece tocar temas de juzgado/Registro Publico/finca.

Lo importante
- Puede ayudar a ubicar una actuacion judicial o registral.
- Puede contener datos para identificar la finca o el expediente.

Que no doy por hecho
- Que la medida o actuacion siga vigente.
- Que el Registro Publico ya refleje ese estado.

Pregunta para Nora
- "Este documento sigue teniendo efecto legal o solo es antecedente?"

Nota OCR: esta lectura puede tener errores; conviene contrastarla con el PDF original.
Limite legal: Val organiza y resume; Nora/la abogada confirma efecto legal.
```

### Contradiction check

User:
"Hay algo raro o contradictorio?"

Answer:

```text
Tany, no voy a declarar contradiccion legal todavia, pero si marcaria estos focos para revisar:

Posibles puntos raros
1. Si un documento menciona una actuacion y otro no la refleja, hay que confirmar cual es mas reciente.
2. Si OCR lee mal nombres, numeros de finca o fechas, eso puede cambiar la interpretacion.
3. Si hay medidas cautelares, hay que confirmar si estan vigentes o canceladas.

Que haria antes de decidir
- Pedir certificacion o estado registral actualizado.
- Llevarle a Nora el documento 1 y la lista de documentos candidatos.

Limite legal: Val organiza y resume; Nora/la abogada confirma efecto legal.
```

## 11. Test Plan

Design/runtime smoke coverage for first implementation lane:

- Phrase detection:
  - "Val, que sabes del caso?"
  - "Que falta revisar?"
  - "Que le pregunto a Nora?"
  - "Cual documento deberia revisar primero?"
  - "Que sabemos seguro y que falta confirmar?"
  - "Explicame lo de la finca en palabras simples."
  - "Ese primer documento, por que importa?"
  - "Hay algo raro o contradictorio?"
  - "Que hago antes de hablar con la abogada?"

- Grounding:
  - Answer includes `Caso Finca`.
  - Answer includes a source/caveat phrase.
  - Document-specific answer maps "primer documento" to document 1.
  - OCR-backed answer includes OCR caveat when OCR text is used.

- Safety:
  - No legal conclusions.
  - No "definitivamente", "ganado", "perdido", or "no necesitas abogada".
  - Legal boundary appears.
  - No raw OCR body dump.
  - No internal IDs in normal Q&A unless user asks technical details.

- No mutation:
  - `CLIENT_GROCERY.md` unchanged.
  - `CLIENT_FOLDERS.json` unchanged.
  - No tasks/reminders/calendar/docs writes.

- Regression:
  - `python3 scripts/quality/caso_finca_workspace_smoke.py`
  - `python3 scripts/quality/client_fixture_smoke.py --client karen`
  - `python3 scripts/quality/karen_rc_full_smoke.py --keep-going`
  - `python3 scripts/quality/client_isolation_audit.py`

## 12. Acceptance Criteria

A-024 implementation should not start until design review approves:

- The Q&A layer is bounded to Caso Finca.
- Deterministic code builds the evidence packet.
- Any LLM use is wording-only and cannot execute.
- Answers are grounded in workspace/document/OCR/pending/Nora data.
- Legal boundary is always present for legal/document/case Q&A.
- Missing evidence produces honest fallback.
- No runtime writes occur.
- Client isolation audit passes.
- Existing demo/canonical routes still pass.

## 13. Risks And Guardrails

Risk: Open-domain drift.
Guardrail: Only answer if Caso Finca context is explicit or valid recent workspace context exists.

Risk: Legal overreach.
Guardrail: Required legal boundary plus banned legal-certainty phrases.

Risk: OCR hallucination or OCR errors.
Guardrail: OCR-backed answers must identify OCR as first-pass and avoid raw text dumps.

Risk: Stale facts.
Guardrail: Source labels, confidence/status, and "falta confirmar" sections.

Risk: Cross-client contamination.
Guardrail: Workspace packets must include client_id and workspace_id; no global case facts.

Risk: Route hijack.
Guardrail: Q&A route must not beat direct utilities like agenda, reminders, tasks, GCal, or document commands unless the phrase is clearly Caso Finca.

Risk: Too much answer density.
Guardrail: Default answer should be compact. Offer follow-ups:
- "Val, dame mas detalle del documento 1"
- "Val, sacame preguntas para Nora"
- "Val, muestrame documentos del Caso Finca"

## 14. Recommended Smallest Implementation Lane After Design

Recommended next lane:

`A-024B — Caso Finca Deterministic Q&A Packet + Read-Only Renderer v1`

Smallest safe scope:

1. Add a new helper module, likely `core/case_workspace_qa.py`.
2. Implement deterministic question classification for 6-8 approved phrases.
3. Build a `CasoFincaQAPacket` from `load_caso_finca_workspace_source_labeled()`.
4. Render deterministic Spanish answers without LLM for v1.
5. Support:
   - overview
   - needs review
   - Nora questions
   - known vs uncertain
   - document 1 why-it-matters
   - next action before talking to Nora
6. Route only after direct agenda/tasks/reminders/GCal/folder commands and only for explicit Caso Finca/finca/Nora/document context.
7. Add `scripts/quality/caso_finca_conversational_qa_smoke.py`.
8. Keep runtime read-only and mutation-free.

Defer to later:

- LLM wording.
- Conversation memory beyond simple last workspace/document context.
- Automatic contradiction analysis.
- New OCR runs.
- Writes/actions from Q&A.
- Generic multi-client domain expert architecture.
