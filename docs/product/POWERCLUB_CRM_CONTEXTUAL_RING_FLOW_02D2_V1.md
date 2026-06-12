# PowerClub CRM Battle 02D.2 - Contextual Ring Flow + Audio Mode Clarity

## Purpose

This lane simplifies Val Discovery Mode so Frank does not need to memorize a long list of hotkeys during a GM meeting.

The new model is contextual:

- Val shows the current meeting step.
- Val shows the next recommended action.
- The ring center/button performs the current action.
- Directional controls move the conversation forward, backward, or toward summary.

No real LLM, backend, external API, persistence, recording, or real PowerClub data was added.

## Contextual Meeting Steps

Presentation Mode now tracks a local meeting step:

- `intro`
- `ask`
- `capture`
- `confirm`
- `organize`
- `recommend`
- `summary`

The screen shows:

- current step
- next action
- what the center/ring button does now

Examples:

- `Ahora: captura la respuesta.`
- `Centro: confirmar respuesta`
- `Ahora: organiza en whiteboard.`
- `Ahora: muestra el demo recomendado.`

## Contextual Ring Model

Recommended ArcX mental model:

| Ring action | Browser fallback | Meaning |
| --- | --- | --- |
| Center / button | `Space` or `Enter` | Perform current recommended action |
| Up | `ArrowUp` | Previous/alternate question |
| Right | `ArrowRight` | Next question / next step |
| Down | `ArrowDown` | Generate or show summary |
| Left | `ArrowLeft` | Back / correct response |
| Long press / glowpress | `H` | Open command menu |
| Mode switch | `M` | Toggle Presentation / Operator |

Legacy hotkeys still exist quietly:

- `P` intro
- `Q` quick Q&A
- `V` Val pregunta
- `C` confirm
- `O` organize
- `R` summary
- `N` next question

They are fallback controls, not the primary mental model.

## Presentation Mode Simplification

The old visible hotkey list was replaced with a compact ring hint:

- center action
- right/left/down direction behavior
- hold/menu behavior

The radial command center now changes label based on the current step:

- Iniciar
- Pregunta
- Confirmar
- Ordenar
- Siguiente
- Resumen

## Capture Flow

The meeting flow is now:

1. Center action asks a question.
2. Frank writes a short client response.
3. Center action confirms the response.
4. Center action organizes it into the whiteboard.
5. Val recommends what to ask or show next.

If Frank presses organize before typing a response, Val directs him back to capture:

> Primero captura una respuesta del cliente. Puedes escribir una frase corta y luego organizarla.

## Audio Modes

Presentation Mode now shows a compact audio mode control:

- `Audio: Texto`
- `Audio: Voz navegador`
- `Audio: Premium futuro`

Default:

- `Texto`

Behavior:

- Text mode uses the typewriter display only.
- Browser voice mode uses `speechSynthesis` only if a browser voice is available.
- Premium future is a label for later; it does not play audio in this static demo.

Small presentation copy explains why audio may not be heard:

> Audio en modo texto. Cambia a Voz navegador si quieres probar TTS.

Operator Mode still keeps:

- voice selector
- rate/pitch controls
- browser voice fallback details

## Why This Reduces Cognitive Load

Frank no longer has to remember many shortcuts during a live meeting. The screen tells him:

- where the conversation is
- what to do next
- what the ring center action will do now

The ring becomes a presentation remote, not a keyboard cheat sheet.

## Operator Mode Preservation

Operator Mode still includes:

- meeting setup
- legacy hotkeys
- radial command menu
- voice selector / rate / pitch
- STT language selector
- Q&A drawer
- capture tools
- notes / decisions / risks / next steps
- summary
- guardrails

## Future Items

Not included in this lane:

- premium local audio package
- real LLM/backend
- reliable STT/transcription
- persistent meeting notes
- direct ArcX/browser hardware integration

The integration boundary remains normal keyboard input.

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
