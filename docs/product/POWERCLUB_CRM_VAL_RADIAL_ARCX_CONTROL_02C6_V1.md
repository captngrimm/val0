# PowerClub CRM Battle 02C.6 - Val Radial Command + ArcX Control Layer

## Purpose

This lane makes Val Discovery Mode cleaner and easier to operate in a live meeting without adding real AI, backend services, recording, persistence, or external APIs.

The goal is presentation control:

- Val feels more like a room-facing presence.
- Frank can drive the flow without clicking visible operator panels.
- The ArcX Ring can trigger Val through ordinary keyboard hotkeys.

## Presentation Mode Minimalism

Presentation Mode now emphasizes:

- Val orb / core presence.
- Current Val state.
- Current Val message.
- Current guided question.
- Compact whiteboard highlights.
- A compact radial-inspired command hub.
- Back navigation to the CRM demo.

Presentation Mode hides or softens:

- Long technical copy.
- Presence/internal panel headings.
- Raw operator button row.
- STT implementation language.
- Browser voice controls.
- Category chips.
- Advanced capture controls.
- Full notes and summary tooling.

Operator Mode still exposes the full cockpit for Frank.

## Radial Command Menu

The new command hub is a radial-inspired control surface around a central "Comando" button.

Actions:

- `V` - Val pregunta.
- `C` - Confirmar respuesta.
- `O` - Organizar whiteboard.
- `R` - Generar resumen.
- `N` - Siguiente pregunta.
- `M` - Cambiar Presentación / Operador.
- `<` - Volver al CRM demo.

The command menu can open through:

- clicking the central command button
- pressing `H`

It closes with:

- clicking a command
- pressing `Esc`

## Keyboard Hotkeys

The page listens for normal keyboard events. It does not connect directly to ArcX hardware.

Hotkeys:

| Key | Action |
| --- | --- |
| `V` | Val pregunta |
| `C` | Confirmar respuesta |
| `O` | Organizar en whiteboard |
| `R` | Generar resumen |
| `N` | Siguiente pregunta |
| `M` | Toggle Presentation / Operator Mode |
| `H` | Show/hide radial command menu |
| `Esc` | Close radial command menu |

Safety behavior:

- Hotkeys do not trigger while Frank is typing in input fields, textareas, or selects.
- `Esc` remains available to close the command menu.
- On-screen controls remain available as fallback.

## Suggested ArcX Ring Profile

Recommended first mapping:

| ArcX Ring input | Browser key | Val action |
| --- | --- | --- |
| Button press | `V` | Val pregunta |
| Up | `C` | Confirmar respuesta |
| Right | `O` | Organizar whiteboard |
| Down | `R` | Generar resumen |
| Left | `N` | Siguiente pregunta |
| Long press / glowpress | `H` | Radial command menu |
| Mode switch | `M` | Presentation vs Operator |

This mapping can change later. The integration boundary is keyboard input only.

## Whiteboard Motion

When Frank organizes a captured response:

- Val enters organizing state.
- The message briefly shows "Val organizando..."
- A floating captured-idea card appears near the Val conversation area.
- The card moves quickly and fades toward the whiteboard.
- The target lane pulses.
- The settled card appears in the correct whiteboard lane with category and recommended-demo badges.

The motion is intentionally fast and restrained. It should feel like Val is putting information into structure, not like a game animation.

## Operator Mode Preservation

Operator Mode continues to support:

- meeting setup
- manual response capture
- category chips
- advanced capture buttons
- full whiteboard lanes
- notes / decisions / risks / next steps
- local summary generation
- copy fallback
- browser voice fallback
- browser STT fallback
- skin selector

STT remains secondary and experimental. Manual capture remains the safe default.

## Guardrails

- No real AI claims.
- No OpenAI, ChatGPT, LLM, ElevenLabs, or external API call.
- No backend.
- No persistence.
- No recording.
- No audio storage.
- No real PowerClub data.
- No production promise.
- No human or AGI framing.
- Frank remains the operator.
- Val Discovery Stage remains separate from the PowerClub CRM Demo.

## Meeting Guidance

Frank can say:

> "I can drive Val with a small ring or keyboard shortcuts, but Val is still an internal meeting cockpit. It helps structure the conversation; it is not autonomously listening or making decisions."

Frank should not say:

- "Val understands everything in the room."
- "Val is connected to PowerClub data."
- "The ring controls an AI agent."
- "This is production automation."

## Remaining Limitations

- ArcX Ring behavior depends on external ring configuration.
- Browser focus can affect hotkey delivery if another app/window is active.
- Floating-card motion still needs Frank-machine browser QA.
- No real LLM or backend reasoning is present in this lane.
