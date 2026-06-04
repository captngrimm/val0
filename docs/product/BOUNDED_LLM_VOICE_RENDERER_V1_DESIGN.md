# Bounded LLM Voice Renderer v1 Design

Status: DESIGN FIRST ONLY.

Purpose:
Design a bounded LLM voice renderer that can take a deterministic safe facts packet and rewrite it into warmer, more natural Spanish without adding facts, changing legal meaning, or executing actions.

Initial scope: Caso Finca Q&A packets for Karen/Tany.

No runtime behavior is implemented by this document.

## 1. Current State

Val0 currently has:

- Deterministic Caso Finca Q&A packet and renderer in `core/case_workspace_qa.py`.
- A context-aware Caso Finca Q&A route that stays bounded to explicit or active case context.
- Read-only workspace/dashboard/document routes in `core/case_workspace.py`.
- OCR-backed summaries only when saved OCR/text is already available.
- Legal/OCR boundaries in deterministic copy.
- Founder-demo natural aliases live-green.
- Karen RC full smoke coverage across agenda, reminders, tasks, GCal, documents, OCR, folders, and Caso Finca.

Current constraints:

- No LLM renderer exists yet.
- The deterministic renderer is intentionally safe but can still feel structured/canned.
- Live client data files must not be reset, discarded, staged, or casually committed:
  - `clients/karen/CLIENT_GROCERY.md`
  - `clients/karen/CLIENT_FOLDERS.json`

## 2. User-Facing Problem

The deterministic Q&A layer gives safe answers, but its voice can feel like a template. Karen needs the same grounded facts in a more natural Val voice:

- clearer transitions
- warmer Tany-facing framing
- a little personality
- less checklist stiffness
- same boundaries and uncertainty

The risk is obvious: if an LLM is allowed to "answer the case", it may invent facts, overstate legal meaning, hide uncertainty, or turn Val into open-domain ChatGPT.

The renderer must therefore be a voice layer only.

## 3. Goals

The bounded LLM voice renderer should:

- Rewrite only a deterministic packet or deterministic draft answer.
- Keep the same facts and uncertainty.
- Keep the same legal/OCR boundaries.
- Preserve "Val organizes; Nora/la abogada confirms legal effect."
- Keep user-facing Spanish warm and natural.
- Use Karen/Tany tone when client profile allows.
- Avoid internal IDs unless the deterministic packet says they are user-visible.
- Never execute actions.
- Fail closed to the deterministic answer.

## 4. Non-Goals

This design does not:

- Implement runtime behavior.
- Make Val open-domain ChatGPT.
- Let the LLM choose facts.
- Let the LLM classify route intent.
- Let the LLM execute writes, deletes, reminders, calendar actions, document actions, or DB mutations.
- Replace Nora/la abogada.
- Loosen OCR, watermark, legal, or document safety.
- Add generic multi-client voice rendering beyond the first Caso Finca/Karen scope.

## 5. Packet Contract

Input to the renderer must be structured and deterministic.

Minimum v1 packet:

```text
VoiceRenderPacket
- client_id
- user_display_name
- tone_profile
- domain
- workspace_id
- workspace_title
- question_type
- user_question
- deterministic_answer
- facts[]
  - text
  - source_label
  - confidence
  - status
  - must_include: true/false
- uncertainty[]
- questions_for_nora[]
- pending_items[]
- next_actions[]
- selected_document
  - visible_number
  - title
  - ocr_status
  - summary_status
  - relevance
  - include_internal_id: false
- required_boundaries[]
- forbidden_claims[]
- forbidden_terms[]
- max_length
- emoji_density
```

The packet is not free text memory. It is a bounded answer contract.

Required fields for Caso Finca v1:

- `domain = "caso_finca"`
- `workspace_title = "Caso Finca"`
- `deterministic_answer`
- `required_boundaries` containing the legal boundary
- `forbidden_claims` containing legal-certainty claims
- `facts` and `uncertainty` separated

## 6. LLM Prompt Contract

The renderer prompt must say, plainly:

```text
You are Val rewriting a deterministic answer for Karen/Tany.
Use Spanish.
Use only the supplied packet.
Do not add facts.
Do not remove required boundaries.
Do not change uncertainty into certainty.
Do not give legal advice.
Do not say Nora/la abogada is unnecessary.
Do not execute or suggest that you executed any action.
Do not mention internal IDs unless include_internal_id is true.
If the packet is insufficient, keep the deterministic fallback.
```

System behavior:

- The LLM receives the packet, not raw client files.
- The LLM returns only rendered text, not tool calls.
- The LLM must not be connected to database/calendar/reminder/document tools.
- Temperature should be low.
- Max output should be bounded.

## 7. Safety Guardrails

Hard guardrails:

- LLM output is never trusted blindly.
- Deterministic executor remains the only actor for writes/deletes.
- Renderer can only run after deterministic route and packet construction.
- Renderer cannot run for destructive confirmations.
- Renderer cannot run for Google Calendar writes/deletes.
- Renderer cannot run for reminder/task creation or deletion.
- Renderer cannot run when packet lacks required boundaries.
- Renderer cannot hide OCR caveat if `ocr_status = available` and OCR-backed facts are used.

Forbidden claims:

- "Legalmente significa que..."
- "Esto prueba definitivamente..."
- "El caso está ganado/perdido."
- "No necesitas abogada."
- "Nora debe..."
- Any claim that a legal effect is confirmed unless the packet explicitly frames it as source text and still requires review.

Forbidden leakage:

- raw OCR body dumps
- VFMS IDs in normal answer
- source_type/source_name/debug metadata in user-facing copy
- stale contamination like `bajar de peso`, `task_high`, `memoria pura`

## 8. Validation / Post-Check Rules

After LLM output, deterministic post-checks must run before sending:

1. Required boundary check:
   - legal boundary present
   - OCR caveat present when required

2. Forbidden claim check:
   - reject output if forbidden legal certainty appears
   - reject output if it says no lawyer is needed

3. Fact containment check:
   - every sentence that states a concrete fact must overlap packet facts, deterministic answer, or allowed connective language
   - v1 can start conservative: require all `must_include` facts to appear and reject known forbidden additions

4. Internal leakage check:
   - reject `vfms:`
   - reject `ID técnico`
   - reject raw source metadata unless explicitly allowed

5. Action safety check:
   - reject "creé", "eliminé", "agendé", "moví", "guardé" unless packet action type explicitly permits a past action confirmation
   - for Caso Finca Q&A v1, no such action confirmation is allowed

6. Length check:
   - keep answer compact enough for Telegram
   - fallback to deterministic answer if too long

If any check fails:

- log diagnostic reason
- send deterministic answer
- do not retry repeatedly

## 9. Fallback Behavior If LLM Fails

Fallback must be boring and safe:

- If OpenAI/API call fails: send deterministic answer.
- If output fails validation: send deterministic answer.
- If output omits legal boundary: send deterministic answer.
- If output adds legal certainty: send deterministic answer.
- If latency is too high: send deterministic answer.

User should not see internal failure details.

Optional future copy:

```text
Tany, te lo pongo en limpio:
<deterministic answer>
```

## 10. Tone Profiles

Initial tone profile: `karen_tany_warm_clear`

Attributes:

- Spanish-first
- uses Tany naturally, not in every sentence
- warm and consultative
- lightly sassy when safe
- low-to-medium emoji density
- no corporate parser tone
- no fake legal authority
- concise sections

Tone boundaries:

- Do not make jokes inside legal uncertainty itself.
- Do not make sarcasm about Nora, court, legal risk, client pain, or sensitive facts.
- Personality can live in transitions, not in conclusions.

Example tone hints:

- "Tany, te lo separo en limpio..."
- "sin mezclar papeles con novela registral"
- "esto lo llevaría como pregunta, no como conclusión"
- "aquí Val organiza; Nora confirma"

Future tone profiles:

- `neutral_professional`
- `legal_careful`
- `operator_brief`
- `family_plain_language`

## 11. Examples: Deterministic Input vs Rendered Output

### Example 1: Needs review

Deterministic input:

```text
Question type: needs_review
Facts:
- Es un caso familiar relacionado con una finca/terreno.
- Hay documentos registrados en Val0/VFMS.
Uncertainty:
- Estado registral actual.
- Qué autos u oficios tienen efecto legal vigente.
Boundary:
- Val organiza y resume; Nora/la abogada confirma efecto legal.
```

Rendered output:

```text
Tany, te lo separo en limpio. Lo que falta revisar del Caso Finca no es "todo el universo", gracias a Dios, sino estos puntos:

Lo que falta confirmar
1. El estado registral actual de la finca.
2. Qué documentos prueban mejor el estado del caso.
3. Qué autos u oficios siguen teniendo efecto legal.

Próximo paso sugerido
Revisaría primero el documento que ya tiene lectura OCR disponible y de ahí sacaría preguntas para Nora.

Límite legal: Val organiza y resume; Nora/la abogada confirma efecto legal.
```

### Example 2: Known vs uncertain

Deterministic input:

```text
Question type: known_vs_uncertain
Known:
- Hay documentos registrados.
- Uno tiene OCR disponible.
Uncertain:
- Efecto legal vigente.
- Estado registral actualizado.
Boundary required.
```

Rendered output:

```text
Tany, esto es lo firme versus lo que todavía no conviene dar por hecho:

Lo que sé
1. Hay documentos relacionados con Caso Finca registrados en Val0.
2. Al menos uno ya tiene lectura OCR disponible.

Lo que falta confirmar
1. Si esos documentos reflejan el estado registral actual.
2. Si los autos/oficios mencionados siguen vigentes.
3. Cuál documento debe pesar más para explicarle el caso a Nora.

Límite legal: Val organiza y resume; Nora/la abogada confirma efecto legal.
```

### Example 3: Document explanation with OCR caveat

Deterministic input:

```text
Question type: document_explanation
Selected document:
- visible_number: 1
- title: Auto_secuestro_Embargo_o_Medidas_Cautelares_Junc_.pdf
- ocr_status: available
Facts:
- Parece relacionado con juzgado/Registro Público/finca.
Uncertainty:
- Vigencia y efecto legal.
OCR caveat required.
Boundary required.
```

Rendered output:

```text
Tany, el documento 1 importa porque parece ser una de las piezas que conecta el caso con juzgado, Registro Público o datos de la finca.

Lo útil
1. Puede servir como punto de partida para ubicar una actuación judicial o registral.
2. Tiene lectura OCR disponible, así que Val puede ayudarte a ordenarlo mejor que un PDF mudo.

Lo que no doy por hecho
1. Que siga vigente.
2. Que ya esté reflejado en el Registro Público.
3. Que por sí solo pruebe el estado legal actual.

Pregunta para Nora
"¿Este documento sigue teniendo efecto legal o solo sirve como antecedente?"

Nota OCR: esta lectura puede tener errores; conviene contrastarla con el PDF original.
Límite legal: Val organiza y resume; Nora/la abogada confirma efecto legal.
```

## 12. Test Plan

Design-phase tests later become implementation smokes:

- Prompt contract smoke:
  - prompt includes "use only supplied packet"
  - prompt forbids adding facts
  - prompt forbids legal conclusions
  - prompt forbids action execution

- Renderer validation smoke:
  - accepts a safe rendered answer
  - rejects missing legal boundary
  - rejects missing OCR caveat when required
  - rejects `vfms:`
  - rejects "definitivamente", "caso ganado", "no necesitas abogada"
  - rejects action claims like "agendé" for Q&A packet

- Fallback smoke:
  - API failure returns deterministic answer
  - validation failure returns deterministic answer

- Integration smoke:
  - Caso Finca Q&A deterministic answer remains source of truth
  - LLM renderer is optional/disabled by default
  - no writes occur
  - live client files unchanged
  - Karen RC full smoke still passes

## 13. Acceptance Criteria

A future implementation is acceptable only if:

- Default behavior can remain deterministic/off.
- LLM renderer never executes actions.
- LLM renderer receives only a bounded packet.
- Post-check validation exists before user output.
- Missing/invalid LLM output falls back to deterministic answer.
- Legal boundary survives.
- OCR caveat survives when required.
- No forbidden legal certainty survives.
- No internal IDs leak unless packet explicitly permits.
- No live client data is mutated.
- Karen RC full smoke and client isolation audit pass.

## 14. Smallest Implementation Lane After Design

Recommended next lane:

`A-025B — Bounded LLM Voice Renderer Skeleton + Validation Smokes`

Smallest safe scope:

1. Add a non-runtime helper module, likely `core/bounded_voice_renderer.py`.
2. Define `VoiceRenderPacket`.
3. Define prompt builder for Caso Finca Q&A packets.
4. Define post-check validator.
5. Add pure unit/smoke tests for prompt and validation.
6. Do not call the live LLM yet.
7. Do not wire into Telegram runtime yet.

Follow-up lane:

`A-025C — Shadow-only Voice Renderer Trial`

Scope:

- Generate candidate rendered output in logs only.
- Compare deterministic vs rendered output.
- Do not send LLM output to user.
- Use test packets first, then short controlled shadow windows.

Runtime enablement should come only after:

- validation rejects unsafe outputs reliably
- shadow outputs are reviewed
- fallback behavior is proven
- Karen RC smokes remain green
