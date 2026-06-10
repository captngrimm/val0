# PowerClub CRM - Val Live Discovery Whiteboard 02C V1

## Purpose

Document the Day 2 live discovery/whiteboard prototype added to Val Discovery Stage.

This lane makes Val feel more participatory in a GM discovery meeting while staying safe:

- Frank remains the operator.
- Val does not pretend to be human.
- Val does not claim autonomous understanding.
- Speech capture is browser-native and experimental only.
- Manual capture remains first-class.
- All classification is local and deterministic.

## Files Updated

- `docs/demo/powerclub_crm/val_discovery.html`
- `docs/product/POWERCLUB_CRM_VAL_LIVE_DISCOVERY_WHITEBOARD_02C_V1.md`

## Meeting Setup

The Val Discovery Stage now includes meeting setup fields:

- Client/person name.
- Role/company/context.
- Meeting objective preset.

These fields are used in:

- Val scripted greeting.
- Local meeting summary.
- Context framing for the session.

## Speech Capture Prototype

Added:

- `Escuchar respuesta` button.
- Browser-native Web Speech Recognition when available.
- Clear unsupported fallback:

```text
STT no disponible en este navegador. Escribe la respuesta o usa dictado del sistema.
```

Guardrails:

- No external APIs.
- No backend.
- No recording.
- No audio storage.
- No transcript persistence.
- No production transcription claim.
- Frank must review and classify any transcript before capture.

## Manual Fallback

Manual capture remains first-class:

- Response textarea remains fully usable.
- Added `Usar respuesta escrita`.
- Frank can type the response, choose a category, and classify it manually.
- Manual path is not treated as failure.

## Live Discovery Whiteboard

Added a visual whiteboard section with lanes:

- Dolor detectado.
- Señales / patrones.
- Datos pendientes.
- Decisiones.
- Riesgos / exclusiones.
- Próximo paso recomendado.

Design intent:

- Meeting-friendly.
- Structured.
- Premium internal cockpit.
- More like a consultant whiteboard than a form.
- Not childish or crayon-like.

Captured notes appear as local cards in the whiteboard lanes. Captured text is escaped before rendering.

## Deterministic Classification

Val classifies locally using selected categories and simple keyword logic.

Supported categories:

- Leads.
- Seguimiento.
- Cierre.
- Visibilidad gerencial.
- Flujo asesor.
- Datos/fuentes.
- Alcance/piloto.
- Riesgo/exclusión.

Keyword/category logic supports:

- Leads/prospect/socio.
- Seguimiento/contacto/llamada/atraso.
- Venta/cierre/compra/conversión.
- Gerencia/dashboard/reportes/visibilidad.
- Asesor/operador/cola.
- Datos/Excel/fuente/export/campo.
- Piloto/alcance/sucursal/V1.
- Riesgo/exclusión/WhatsApp/pago.

This is not AI generation. It is deterministic routing.

## Val Acknowledgement Behavior

After capture, `Val observa` updates with deterministic acknowledgement.

Examples:

Follow-up pain:

```text
Entendido. Si el dolor principal es seguimiento, conviene revisar oportunidades en riesgo, atrasos y cola diaria del asesor.
```

Manager visibility:

```text
Entendido. Si el dolor es visibilidad gerencial, conviene empezar por KPIs, sucursales y asesores.
```

Data/source:

```text
Antes de cotizar, falta confirmar fuente de datos, campos obligatorios y una muestra aprobada.
```

Scope risk:

```text
Esto debe ir a alcance o exclusiones para proteger el piloto.
```

## Demo Bridge

Added `Val recomienda mostrar`:

- Vista gerencial.
- Riesgo y rescate.
- Ficha del asesor.
- Cola del asesor.
- Templates / dictado.
- Scope freeze / piloto.

The current implementation maps captured categories to recommended sections:

- Leads -> Vista gerencial.
- Seguimiento -> Riesgo y rescate.
- Cierre -> Riesgo y rescate.
- Visibilidad -> Vista gerencial.
- Asesor -> Cola del asesor.
- Datos -> Scope freeze / piloto.
- Alcance -> Scope freeze / piloto.
- Riesgo -> Scope freeze / piloto.

## Summary Behavior

The local summary now includes:

- Person/client.
- Role/context.
- Meeting objective.
- Last detected category.
- Recommended CRM section.
- Recommended next question.
- Captured responses.
- Pains.
- Signals/patterns.
- Decisions.
- Risks.
- Pending data.
- Pilot candidates.
- General notes.
- Next steps.

Copy behavior remains local and uses browser clipboard when available, with manual fallback.

## Meeting Flow

Recommended live use:

1. Frank opens Val Discovery Stage.
2. Frank enters client/person/context/objective.
3. Frank clicks `Iniciar sesión`.
4. Val asks a guided question.
5. Client answers verbally.
6. Frank clicks `Escuchar respuesta` if browser STT is appropriate.
7. If STT is unavailable or awkward, Frank types the response manually.
8. Frank selects category.
9. Frank clicks quick capture or `Usar respuesta escrita`.
10. Whiteboard updates.
11. Val acknowledges and recommends next question/CRM section.
12. Frank decides what to ask or show next.

## Copy Safety

Use:

- "captura asistida"
- "transcripción experimental del navegador"
- "Frank confirma y clasifica la respuesta"
- "Val sugiere próximos pasos con reglas locales"

Avoid:

- "Val escucha todo"
- "Val entiende automáticamente"
- "Val analiza la reunión"
- "IA autónoma"
- "producción lista"

## Guardrails

- No fake LLM claims.
- No OpenAI/ChatGPT API.
- No external services.
- No backend.
- No persistence.
- No real PowerClub data.
- No production promise.
- No human/AGI framing.
- No claim that Val autonomously understands the meeting.
- No recording.
- No audio storage.
- No STT if browser does not support it.
- Deterministic/operator-assisted only.
- Keep CRM demo and Val Discovery Stage separate.

## ETA Tracker Update

Planned 02C lane:

- 4-6 effective hours.

Actual implementation time should be reported in the final report for the lane.

If ETA expands:

- Cut premium voice polish.
- Cut advanced whiteboard visuals.
- Cut extra categorization complexity.
- Keep manual capture, guardrails, summary, and CRM/Val separation.

## Recommended Next Lane

If Frank-machine review accepts this whiteboard:

`POWERCLUB-CRM-BATTLE-02D — Val Discovery Whiteboard Browser QA + GM Rehearsal`

If browser STT fails or feels awkward:

Keep STT as optional and rehearse manual capture as the default.
