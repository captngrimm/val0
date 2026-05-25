# ROADMAP_ANSWER_MODE_V0

Purpose:
Design Roadmap Answer Mode for Karen / client-zero and future founder-beta users.

Roadmap Answer Mode lets a user ask what is ready, what is next, what changed, what is paused, and what belongs later. The goal is expectation management: useful answers without vague promises, hidden deadlines, private fact leakage, or fake certainty.

Tone:
Spanish-first examples, operator-ready, product-safe, honest, concise.

---

## 1. Purpose

Roadmap Answer Mode should help founder-beta users ask:

- what is ready now
- what they can test this week
- what is next
- what is planned but not ready
- what changed since the last delivery
- what is later/future
- what is parked or blocked

It exists to support trust:

- distinguish ready from planned
- avoid vague promises
- explain changes plainly
- keep roadmap separate from legal/case memory
- keep private client facts out of reusable product docs

---

## 2. User Prompts To Support Eventually

Spanish-first prompts:

- `Val, qué viene`
- `Val, qué está listo`
- `Val, qué falta`
- `Val, qué cambió del roadmap`
- `Val, cuándo tendré carpetas`
- `Val, cuándo podrás leer fotos`
- `Val, qué puedo probar esta semana`
- `Val, qué está pausado`
- `Val, qué es futuro`

Possible variants:

- `Val, qué puedo usar hoy`
- `Val, qué sigue después de esta entrega`
- `Val, eso ya está listo?`
- `Val, qué no debo probar todavía`
- `Val, qué cambió desde ayer`

---

## 3. Roadmap Status Buckets

Use explicit buckets. Do not answer with "soon" as a status.

### `ready_now`

Verified in runtime/demo for this user or workflow.

User language:

```text
Esto ya está listo para probar en founder-beta.
```

### `next`

Near-term priority, but not yet promised as ready.

User language:

```text
Esto va en "next": es de las mejoras naturales después de esta entrega, pero no lo vendo como listo todavía.
```

### `planned`

Accepted roadmap item with clear direction, but not immediate.

User language:

```text
Está planificado, pero todavía no está en la versión que puedes probar hoy.
```

### `later`

Real possibility, but after higher-priority work.

User language:

```text
Eso va para más adelante. Quiero hacerlo bien antes de prometerlo.
```

### `parked`

Known idea intentionally paused.

User language:

```text
Eso está pausado por ahora. No lo estamos empujando en esta fase.
```

### `blocked`

Cannot move until a dependency, safety issue, consent, or scope decision is resolved.

User language:

```text
Eso está bloqueado hasta resolver [motivo simple].
```

### `unknown`

Not enough information to classify.

User language:

```text
No tengo suficiente información para darte una respuesta honesta todavía.
```

### `not_promised`

Not part of the current roadmap or requires separate scope.

User language:

```text
Eso no está prometido en este alcance. Si lo quieres, lo separamos para evaluar.
```

---

## 4. Answer Rules

Roadmap answers must:

- distinguish ready vs planned vs future
- use ranges/categories instead of hard dates unless explicitly confirmed
- never say a feature is ready unless runtime/demo is verified
- say why if a timeline changes, using plain language
- say uncertain when uncertain
- avoid professional advice promises
- avoid implying autonomous actions unless explicitly built and tested
- keep client-specific roadmap answers separate from reusable product roadmap answers
- avoid private legal facts, document IDs, local paths, chat IDs, or case IDs

Never say:

- "pronto" without defining what that means
- "ya casi" if there is no verified scope
- "eso ya está" unless it has been tested
- "Val va a hacer todo solo"
- "Val puede darte conclusión legal"
- "Val leerá todas las fotos perfecto"

Preferred wording:

```text
Lo pongo en "next", no como promesa cerrada. Primero confirmamos que lo actual funcione bien esta semana.
```

```text
Eso todavía no está listo para usar. Está en roadmap, pero no quiero vendértelo como hecho.
```

---

## 5. Karen-Specific Roadmap Examples

These are examples for Karen/client-zero delivery language. They should not include private legal facts.

### `ready_now`

- document inventory
- chronology
- 2024 recall
- Daily Operator compact
- tomorrow agenda
- lawyer/Nora/advisor prep checklist

Example:

```text
Listo para probar hoy: documentos, cronología, pregunta por 2024, Daily Operator compacto, agenda de mañana y prep para hablar con la abogada/Nora/advisor.
```

### `next`

- better document labels
- Roadmap Answer Mode
- timeline polish

Example:

```text
Lo próximo es que las respuestas sean más fáciles de reconocer: mejores nombres de documentos, menos ruido técnico en cronología y una forma clara de preguntarme qué viene.
```

### `planned`

- carpetas: Finca, Proyectos, Pendientes
- detail drilldown
- unified agenda

Example:

```text
Carpetas, detalle por número y agenda unificada están planificados, pero no están listos en la entrega de hoy.
```

### `later`

- OCR/photo-to-text
- async voice/car mode

Example:

```text
Leer fotos mejor y voz asíncrona van más adelante. No quiero prometer eso como listo hasta probarlo bien.
```

### `parked`

- advanced wearable/context button flows

Example:

```text
Los flujos avanzados tipo botón/contexto wearable están parqueados. Son interesantes, pero no son prioridad para esta semana.
```

---

## 6. Example Responses

### Prompt: `Val, qué viene`

```text
Lo próximo para ti va en tres niveles:

Listo hoy:
- documentos
- cronología
- Daily Operator compacto
- agenda de mañana
- prep para hablar con la abogada/Nora/advisor

Next:
- mejores nombres de documentos
- menos ruido técnico en cronología
- modo roadmap para preguntarme qué viene y qué falta

Planificado, pero no listo todavía:
- carpetas
- detail drilldown
- agenda unificada

No te doy fecha exacta todavía. Prefiero confirmar primero qué te sirve esta semana.
```

### Prompt: `Val, cuándo tendré carpetas`

```text
Carpetas está en "planned", no en "ready_now".

La idea es organizar cosas como Finca, Proyectos y Pendientes, pero todavía no lo vendo como listo. Primero validamos esta semana documentos, cronología, Daily Operator y prep de reuniones.

Si sigue siendo prioridad después del piloto, lo subimos como candidato fuerte para "next".
```

### Prompt: `Val, qué cambió desde ayer`

```text
Cambios desde la última revisión:

- Documentos: ahora el inventario por defecto debe ser más compacto y menos técnico.
- Daily Operator: el modo normal debe ser corto; el resumen largo solo si lo pides.
- Prep con abogada/Nora/advisor: debe salir como checklist, no como dump de documentos.

No cambió:
- OCR/fotos todavía no son perfectos.
- Carpetas y detail drilldown siguen en roadmap.
```

### Prompt: `Val, qué está listo para mí hoy`

```text
Listo para probar hoy:

1. Qué eres / qué puedes hacer.
2. Inventario compacto de documentos.
3. Cronología del caso desde lo registrado.
4. Pregunta por 2024.
5. Daily Operator compacto.
6. Agenda de mañana si está configurada.
7. Prep para hablar con la abogada/Nora/advisor.

Límite: esto organiza información y próximos pasos; no reemplaza criterio legal ni toma acciones sola.
```

### Prompt: `Val, qué no está listo todavía`

```text
Todavía no está listo:

- OCR/fotos como lectura perfecta.
- DOCX/fotos con extracción garantizada.
- Carpetas.
- Agenda unificada.
- Detail drilldown tipo "dame detalles del 2".
- Acciones autónomas.
- Consejos o conclusiones legales.

Si algo de eso te importa más, lo marcamos como prioridad de roadmap, pero no lo vendo como listo hoy.
```

---

## 7. Roadmap Update Log Concept

Roadmap updates should be stored as dated notes.

Each update includes:

- date
- feature
- status before
- status after
- reason
- user-facing summary
- internal/operator note

Example shape:

```yaml
- date: 2026-05-25
  feature: document_inventory
  status_before: planned
  status_after: ready_now
  reason: compact client-facing output verified in smoke
  user_facing_summary: "El inventario de documentos ahora debe salir más compacto y menos técnico por defecto."
  internal_operator_note: "Technical IDs remain available only via explicit technical request."
```

Rules:

- User-facing summaries must not expose private implementation details.
- Internal notes must not include private legal facts unless stored in an approved client-specific location.
- Product update logs should describe reusable capabilities, not private case history.

---

## 8. Client-Specific Vs Reusable

Keep these layers separate.

### Client Roadmap Files

May contain:

- client alias
- workflow priority
- client-specific feedback
- selected pilot workflow
- sanitized success criteria
- client-facing roadmap priorities

Must avoid:

- detailed legal facts
- document IDs
- chat IDs
- private filenames
- raw case chronology
- local/server paths

### Product Roadmap Docs

May contain:

- reusable capabilities
- generic workflow patterns
- roadmap statuses
- renderer/architecture ideas
- privacy and boundary rules

Must avoid:

- private client facts
- one client's legal story
- implementation secrets
- exact commitments not approved as product roadmap

Principle:

```text
Client-specific priorities can inform product R&D, but private facts do not belong in reusable docs.
```

---

## 9. Future Runtime Architecture

### Simple Version

Static roadmap file plus deterministic renderer.

Pros:

- quick
- readable
- low risk
- good for Karen/client-zero

Cons:

- harder to validate
- easy for prose to become stale

### Better Version

Structured YAML/JSON roadmap plus renderer.

Pros:

- status buckets can be validated
- easier to test
- easier to keep client-specific and product roadmap separate

Cons:

- needs schema and migration discipline

### Later Version

LLM-assisted summary constrained by structured roadmap.

Rules:

- LLM can summarize, not invent status
- source of truth remains structured roadmap
- uncertain status must remain uncertain
- no private legal facts in reusable roadmap context

Do not let freeform Markdown alone become truth without validation.

---

## 10. Guardrails

- No magic timeline.
- No "soon" without definition.
- No hidden promises.
- No private fact leakage.
- No confusing product roadmap with legal/case memory.
- No claiming runtime availability without verification.
- No professional advice promises.
- No autonomous action claims unless explicitly implemented and tested.
- No cross-client roadmap contamination.

Safe fallback:

```text
No tengo suficiente información para prometer eso. Lo marco como pregunta de roadmap y lo revisamos.
```

---

## 11. Suggested Implementation Phases

### Phase 0: Docs / Design Only

Document answer rules, buckets, examples, and guardrails.

Status:
This document.

### Phase 1: Karen Roadmap Q&A Static Command

Create deterministic answers from a static Karen-safe roadmap source.

Requirements:

- no private legal facts
- no LLM required
- no route stealing from documents/timeline/agenda
- status bucket tests

### Phase 2: Structured Roadmap Data

Move roadmap items into YAML/JSON with fields:

- feature
- status
- user-facing label
- user-facing summary
- client scope
- last updated
- owner/operator note

### Phase 3: Update Log

Add dated update log with status transitions and plain-language summaries.

### Phase 4: Proactive Roadmap Update Notifications With Consent

Only after consent and routing are safe.

Example:

```text
Te aviso cuando algo de tu roadmap cambie de "planned" a "ready_now"?
```

Do not add proactive messages without user consent.

