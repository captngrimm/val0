# PowerClub CRM Battle 02D.7 - ArcX Contextual Back + Rephrase Semantics

## Purpose

Refine ArcX Ring behavior so Val Discovery feels like a live meeting control system, not slideshow navigation.

This lane changes semantics only. It does not add LLM, backend, external services, persistence, real PowerClub data, or production AI behavior.

## Updated Direction Model

| Ring action | ArcX key/code | Meaning |
| --- | --- | --- |
| Center | `NumpadEnter` | Do current recommended action |
| Right | `Numpad6` | Advance / next question / next step |
| Left | `Numpad4` | Correct / go one safe step back |
| Up | `Numpad8` | Rephrase current question / alternate angle |
| Down | `Numpad2` | Summary / close |

`Numpad5` remains a center fallback. Arrow keys keep the same fallback meanings.

## Why Left Is Correction

In a live discovery meeting, Frank usually does not need previous-question navigation.

He needs a safe way to recover:

- fix a captured response
- return to response correction
- review the whiteboard before advancing
- pause before moving on
- avoid skipping an important confirmation

So left now means:

`corregir / volver un paso seguro`

Contextual behavior:

- Capture / confirm / organize: return to response correction.
- Recommend: return to whiteboard/review before moving on.
- Ask: pause so Frank can adjust or reframe.
- Intro: show calm copy: `Estamos al inicio. Podemos avanzar o reformular.`

## Why Up Is Rephrase

Up now keeps the same question intent but changes the angle.

Examples:

Original:

`¿En qué parte del seguimiento sienten que se pierden más oportunidades hoy?`

Rephrase:

`Lo pregunto de otra forma: ¿en qué punto del proceso sienten que una oportunidad se enfría o pierde dueño?`

Original:

`¿Qué necesita ver gerencia cada mañana para saber dónde actuar?`

Rephrase:

`Si mañana solo pudieran ver tres señales para decidir dónde actuar, ¿cuáles serían?`

This remains fully deterministic/local. No LLM is used.

## Right Advance Behavior

Right means:

`avanzar`

It can:

- move from intro to the first question
- advance to the next useful question
- continue after a recommendation

It should not skip confirmation if a response is pending:

- If there is text in the response field, Val prompts Frank to confirm it first.
- If a response was confirmed but not organized, Val prompts Frank to organize it before moving on.

## Down Summary / Close Behavior

Down generates or shows the local summary, including:

- captured pain
- responses
- pending data
- recommended CRM section
- next step
- guardrail that the summary is local/demo-only

This is the close button, not a hidden analytics feature.

## UI Hint

Presentation Mode now uses compact guidance:

- `Centro: acción actual`
- `→ avanzar`
- `← corregir`
- `↑ reformular`
- `↓ resumen/cierre`
- `Mantener: menú`

The goal is for Frank to think in meeting moves, not keyboard commands.

## Val Copy

The interaction copy should stay calm and operational:

- `Lo reformulo.`
- `Perfecto, corrijamos antes de seguir.`
- `Volvemos un paso para revisar el whiteboard antes de avanzar.`
- `Avancemos con la siguiente pregunta.`
- `Puedo cerrar con un resumen de lo detectado.`

Avoid:

- fake autonomous understanding
- LLM claims
- human/AGI framing
- production promises

## Operator Preservation

Operator Mode still keeps:

- ArcX / keyboard debug
- Ring ON/OFF
- voice and audio controls
- STT controls
- category chips
- advanced capture
- Q&A
- summary tools
- guardrails

## Guardrails

- Deterministic/operator-assisted only.
- Frank remains operator.
- No LLM/backend/API.
- No external services.
- No persistence.
- No real PowerClub data.
- No production promise.
- Keep PowerClub CRM Demo and Val Discovery Stage separate.
