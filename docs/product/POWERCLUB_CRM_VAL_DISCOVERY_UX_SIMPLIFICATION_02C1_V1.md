# PowerClub CRM - Val Discovery UX Simplification 02C.1 V1

## Purpose

Document the 02C.1 simplification pass for Val Discovery Stage after Frank-machine QA.

Frank's findings:

- Visual impression is decent/good.
- Whiteboard updates after manual capture.
- UX felt too complicated for live meeting use.
- STT was inconsistent and language handling was confusing.
- Windows dictation recognized English better than Spanish.
- Browser voice sounded male; Frank does not like male voice for Val.

Goal:

- Make live operation simpler.
- Keep categories optional.
- Improve Spanish STT defaults.
- Add voice selector and prefer Spanish female-sounding voices when available.
- Keep manual fallback first-class.

## Files Updated

- `docs/demo/powerclub_crm/val_discovery.html`
- `docs/product/POWERCLUB_CRM_VAL_DISCOVERY_UX_SIMPLIFICATION_02C1_V1.md`

## UX Simplification

Added visible guided steps:

1. Paso 1: Val pregunta.
2. Paso 2: Capturar respuesta.
3. Paso 3: Confirmar y organizar.
4. Paso 4: Mostrar recomendación / resumen.

Primary controls are now reduced to:

- Val pregunta.
- Escuchar respuesta.
- Confirmar respuesta.
- Organizar en whiteboard.
- Generar resumen.

Older quick capture buttons remain, but are labeled as `Captura avanzada opcional` so Frank does not need to decide everything at once during a live meeting.

## Category Behavior

Categories remain available as optional assistive chips:

- Leads.
- Seguimiento.
- Cierre.
- Visibilidad gerencial.
- Flujo asesor.
- Datos/fuentes.
- Alcance/piloto.
- Riesgo/exclusión.

If Frank does not select a category, Val tries deterministic keyword classification.

If classification is unclear, Val says:

```text
Necesito que Frank confirme si esto pertenece a seguimiento, visibilidad, datos o alcance.
```

This protects the meeting from fake certainty.

## Manual Fallback

Manual typing is now explicitly normal:

```text
Modo seguro: Frank puede escribir o corregir la respuesta antes de organizarla.
```

The live flow separates:

- Capturing/typing the response.
- Confirming the response.
- Organizing it into the whiteboard.

This keeps Frank in control and avoids pretending Val understood the answer autonomously.

## Spanish STT Defaults

Added STT language selector:

- Español LatAm (`es-419`).
- Español España (`es-ES`).
- English (`en-US`).

Default:

- Español LatAm.

Behavior:

- `Escuchar respuesta` uses the selected STT language.
- The selected language is shown in the STT status message.
- If STT is unsupported, Val shows:

```text
STT no disponible en este navegador. Escribe la respuesta o usa dictado del sistema.
```

Guardrail:

- STT remains experimental browser behavior.
- No external API.
- No recording.
- No audio storage.
- No production transcription claim.

## Voice Selector Behavior

Added browser `speechSynthesis` voice selector:

- Loads available browser voices.
- Prefers Spanish female-sounding voices when available.
- If no female Spanish voice is available, shows:

```text
Voz femenina en español no disponible en este navegador.
```

Behavior:

- Frank can choose another voice from dropdown.
- Frank can select text-only mode.
- Voice availability is not guaranteed.
- Val does not speak if no voice is selected.

Female voice heuristic:

- Looks for Spanish voices with names commonly associated with female voices or labels such as `female`, `mujer`, `Mónica`, `Paulina`, `Sabina`, `Helena`, `Laura`, `Luciana`, `Sofía`, `Soledad`, `Maria`, or `Elena`.

This is a browser capability preference, not a guarantee.

## Val Observa Copy Improvements

The acknowledgement copy is more consultative and less mechanical.

Examples:

Seguimiento:

```text
Entendido. Esto apunta a un problema de seguimiento. Antes de mostrar el demo, conviene confirmar impacto: ¿cuántas oportunidades sienten que se enfrían por falta de contacto a tiempo?
```

Visibilidad:

```text
Entendido. Si el dolor es visibilidad gerencial, conviene empezar por KPIs, sucursales y asesores.
```

Datos:

```text
Entendido. Antes de cotizar, falta confirmar fuente de datos, campos obligatorios y una muestra aprobada.
```

Riesgo:

```text
Entendido. Esto debe ir a alcance o exclusiones para proteger el piloto.
```

## Safe Live Flow

Recommended operation:

1. Frank clicks `Val pregunta`.
2. Client answers.
3. Frank clicks `Escuchar respuesta` only if browser STT is useful.
4. If STT fails or language is poor, Frank types/corrects manually.
5. Frank optionally selects category.
6. Frank clicks `Confirmar respuesta`.
7. Frank clicks `Organizar en whiteboard`.
8. Frank shows recommendation or generates summary.

## Guardrails

- No fake LLM claims.
- No OpenAI/ChatGPT API.
- No external services.
- No backend.
- No persistence.
- No real PowerClub data.
- No production promise.
- No human/AGI framing.
- No recording.
- No audio storage.
- No claim that Val listens autonomously.
- Deterministic/operator-assisted only.
- Keep CRM demo and Val Discovery Stage separate.

## ETA Tracker Update

Planned 02C.1 lane:

- 2-4 effective hours.

Actual implementation time should be reported in the final report for the lane.

If ETA expands:

- Cut premium voice tuning.
- Cut additional category logic.
- Cut animation polish.
- Keep simplified flow, manual fallback, STT language selector, and guardrails.

## Recommended Next Lane

`POWERCLUB-CRM-BATTLE-02D — Browser QA For Simplified Val Discovery + GM Dry Run`

Focus:

- Frank-machine browser check of simplified controls.
- Validate STT language selector behavior.
- Validate voice dropdown and female-Spanish availability.
- Rehearse manual fallback as default.
