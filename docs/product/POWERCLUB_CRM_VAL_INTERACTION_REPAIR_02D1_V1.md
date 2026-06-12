# PowerClub CRM Battle 02D.1 - Val Interaction Repair

## Purpose

This lane repairs the live-meeting interaction in Val Discovery Mode. Presentation Mode now follows a clear guided loop:

1. Val asks.
2. Frank captures what the client said.
3. Val organizes the response into the whiteboard.
4. Val recommends what to ask or show next.

No real LLM, backend, external API, persistence, recording, or real PowerClub data was added.

## Presentation Capture Flow

Presentation Mode now includes a visible capture area:

- Label: `Respuesta del cliente`
- Placeholder: `Escribe aquí una frase corta de lo que dijo el cliente...`
- Button: `Capturar respuesta`
- Button: `Organizar en whiteboard`

Manual capture is the normal safe mode. It is not treated as a fallback failure.

## Guided Next Action

Presentation Mode now shows a `Siguiente acción` style indicator:

- `Ahora: haz la pregunta.`
- `Ahora: captura la respuesta.`
- `Ahora: organiza en whiteboard.`
- `Ahora: muestra el demo recomendado.`

This gives Frank a simple live-meeting rhythm instead of forcing him to infer the next step from hidden controls.

## Hotkey Repair

Hotkeys remain available but now follow the guided flow:

- `P` - Val preséntate
- `Q` - open/toggle quick Q&A panel
- `V` - Val pregunta / next discovery question
- `C` - capture/confirm visible response
- `O` - organize captured response
- `R` - generate summary
- `N` - next discovery question
- `M` - toggle Presentation / Operator Mode
- `H` - radial command menu
- `Esc` - close radial / Q&A panel

If `C` is pressed with no response, Val focuses/highlights the response field.

If `O` is pressed with no response, Val says:

> Primero captura una respuesta del cliente. Puedes escribir una frase corta y luego organizarla.

Hotkeys still do not trigger while Frank is typing in inputs, textareas, or selects, except `Esc`.

## Quick Q&A Repair

`Q` no longer repeats the same line. In Presentation Mode it opens a compact quick Q&A panel with safe choices:

- Preséntate
- ¿Qué eres?
- ¿Eres parte del CRM?
- ¿Esto es ChatGPT?
- ¿Qué puedes hacer hoy?
- Empecemos discovery

Typed unknown Q&A remains Operator Mode only.

## Voice Control Repair

Presentation Mode now includes a compact voice toggle:

- default: `Voz: texto`
- optional: `Voz: on`

This prevents browser voice surprises, especially if the available Spanish voice sounds male or inappropriate for Val. Detailed voice selector/rate/pitch controls remain in Operator Mode.

## Radial Command Repair

The radial command still supports the meeting controls, but the live flow is now clearer:

- Pregunta
- Captura / confirma
- Organiza
- Q&A
- Resumen
- Modo
- CRM

The radial menu is now a convenience layer, not the only way to understand the flow.

## Operator Mode Preservation

Operator Mode still includes:

- meeting setup
- voice selector/rate/pitch
- STT language selector
- category chips
- notes/decisions/risks/next steps
- full summary tools
- guardrails
- typed Q&A input
- full hotkey mapping

## Guardrails

- No fake LLM claims.
- No OpenAI/ChatGPT API.
- No external services.
- No backend.
- No persistence.
- No real PowerClub data.
- No production promise.
- No human/AGI framing.
- No claim that Val autonomously understands/listens.
- No recording or audio storage.
- Deterministic/operator-assisted only.
- Frank remains operator.
- CRM demo and Val Discovery Stage remain separate.

## Remaining Risks

- Frank should test the capture/highlight/hotkey loop on his machine before a GM meeting.
- Browser voice remains dependent on the machine/browser and should stay optional.
- The Q&A capsule is scripted and intentionally bounded.
