# PowerClub CRM Battle 02C.4 - Val Presentation Mode + Skin Foundation

## Purpose

This lane separates Val Discovery Mode into two meeting-safe experiences:

- **Presentation Mode** for Karen/GM-facing use.
- **Operator Mode** for Frank's advanced controls and capture workflow.

The goal is to make Val feel more like a calm meeting presence and less like a crowded operator dashboard, while keeping every current workflow available when Frank needs it.

## Presentation Mode

Presentation Mode is now the default. It shows only the meeting-facing essentials:

- Val presence / orb.
- Current Val state.
- "Val dice" message.
- Current guided question.
- Compact whiteboard highlights.
- Primary actions:
  - Val pregunta.
  - Organizar en whiteboard / siguiente paso.
- Compact internal-tool framing.

Presentation Mode hides technical and operational controls:

- Voice selector.
- Voice speed/pitch sliders.
- STT language selector.
- Long agenda and usage notes.
- Category chips.
- Advanced capture buttons.
- Notes/decisions/risks textareas.
- Summary/copy tools.

## Operator Mode

Operator Mode keeps the full cockpit available for Frank:

- Meeting setup.
- Voice selector and browser voice tuning.
- STT language selector.
- Response capture.
- Category chips.
- Advanced capture buttons.
- Full whiteboard.
- Notes, decisions, risks, and next steps.
- Summary generation and copy fallback.
- Guardrail details.

Secondary areas are now organized into collapsible drawers where useful:

- Voz de Val / fallback navegador.
- Agenda.
- Uso en reunión.
- Guardrails / límites.
- Categorías.
- Captura avanzada.
- Banco de categorías.
- Resumen local.

## Clipping / Overflow Fixes

The Val presence area was tightened to reduce clipping risk:

- Smaller responsive orb dimensions.
- Bounded ring sizes.
- Slightly narrower cockpit columns.
- Buttons continue to wrap.
- Presentation Mode hides nonessential controls from the presence card.

Frank should still confirm on his laptop/browser because visual clipping depends on viewport, font rendering, and browser UI scale.

## Typewriter Pacing

The Val message reveal was slowed slightly with a small local typing configuration:

- Shorter text reveals in smaller increments.
- Longer text still reveals quickly enough for meeting flow.
- No external library or AI generation was added.

## Skin Foundation

A lightweight session-only skin selector now supports three visual directions:

- **Executive Clean** - safest GM default; premium corporate, less glow, stronger readability.
- **Isthmus Signature** - black/red/cyan Val identity closer to the current core look.
- **Retro Tactical** - industrial console direction inspired by the moodboard, but kept business-safe and not game-like.

Skins are CSS variable/layout variations only. They do not persist and do not represent a final brand decision.

## STT / Voice Positioning

- STT remains experimental browser functionality.
- Manual typing/correction remains the safe default.
- Browser voice remains optional fallback.
- Copy continues to clarify that executive demos can use premium local audio later if desired.
- No ElevenLabs, Forge, OpenAI, ChatGPT, or external voice service was added.

## Guardrails

- No real AI claims.
- No backend.
- No external services.
- No persistence.
- No recording or audio storage.
- No real PowerClub data.
- No production promise.
- No human/AGI framing.
- Val remains deterministic and operator-assisted.
- PowerClub CRM Demo and Val Discovery Stage remain separate.

## Recommended Frank Use

Start the meeting in Presentation Mode with Executive Clean skin.

Use Operator Mode only when Frank needs to:

- Type or correct a response.
- Classify a category.
- Capture a pain, decision, risk, data requirement, or pilot candidate.
- Generate the local follow-up summary.

Keep STT optional and do not make it the centerpiece unless it works reliably on the meeting machine.

## Remaining Limitations

- Browser STT remains unreliable and should not be promised.
- Browser voice quality remains machine/browser dependent.
- Skins are a foundation for visual exploration, not final brand identity.
- Frank-machine visual QA is still required before a GM meeting.
