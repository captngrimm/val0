# PowerClub CRM Battle 02D.6 - Contextual Ring + STT Capture Finalization

## Purpose

Finalize the dirty Val Discovery work from the interrupted contextual ArcX capture lane.

This lane preserves the useful UI/control changes, verifies the intended behavior, and documents how Frank should operate the ring-centered meeting flow.

No LLM, backend, external API, persistence, recording, real PowerClub data, or production AI behavior was added.

## Dirty Work Preserved

The following unsealed changes were kept and finalized:

- simplified radial command surface with four directional actions
- compact ring-map hints in Presentation Mode
- contextual center action for the current meeting step
- `captureModeHint` text for the current step
- optional `sttCenterToggle` in Operator Mode
- `runCaptureCenterAction()`
- `toggleListening()`
- Ring ON/OFF behavior and ArcX keyboard debug from 02D.5
- text-first audio mode and female Spanish voice preference from 02D.5

## Contextual Center Behavior

The ArcX center button emits `NumpadEnter`. It now follows the active meeting step:

| Meeting step | Center action |
| --- | --- |
| Intro | Present Val and move toward the first question |
| Ask | Ask the current guided question |
| Capture | Capture response mode |
| Confirm | Confirm captured response |
| Organize | Organize into whiteboard |
| Recommend | Advance to next question / recommendation |
| Summary | Generate/show local summary |

`Numpad5` remains a fallback center alias.

## Capture Step Behavior

Capture remains manual-first and meeting-safe.

When Val is waiting for the client response:

- If the response field is empty, center focuses/highlights the response field.
- Val tells Frank to write or correct a short answer.
- If the response field has text, center confirms the response.
- If Frank explicitly enables experimental STT in Operator Mode, center can attempt browser-native speech recognition.
- STT never records or stores audio.
- Frank must review/correct any transcript before confirming.

Presentation Mode copy keeps STT secondary:

`Modo seguro: escribe la respuesta. STT solo se usa si Frank lo activa en Operador.`

## Directional Mapping

The directional model is simple:

| Direction | ArcX key/code | Behavior |
| --- | --- | --- |
| Up | `Numpad8` | Alternate question |
| Right | `Numpad6` | Next question / next step |
| Down | `Numpad2` | Summary |
| Left | `Numpad4` | Correct / back |
| Center | `NumpadEnter` | Current contextual action |
| Center fallback | `Numpad5` | Current contextual action |
| Long/glowpress | `H` if configured | Command menu |
| Mode switch | `M` if configured | Operator Mode |

Plain number aliases `8/6/2/4/5` remain available only when Ring Control is ON.

## Radial Visual Cleanup

The previous command wheel felt crowded because it exposed too many commands at once.

The finalized Presentation Mode radial surface now shows:

- one large center action button
- four smaller directional actions:
  - `Alterna`
  - `Siguiente`
  - `Resumen`
  - `Corregir`

The compact hint reads like a ring remote rather than a keyboard cheat sheet:

- `Centro: [current action]`
- `→ siguiente`
- `← corregir`
- `↑ alternativa`
- `↓ resumen`
- `Mantener: menú`

## CRM Navigation

Back-to-CRM navigation remains available through the header link:

`Volver al CRM demo`

The radial left/back action now means correction/back within the meeting flow, not leaving the CRM demo. This avoids accidental navigation during a live presentation.

## Operator Mode Preservation

Operator Mode still keeps:

- ArcX / keyboard debug
- Ring ON/OFF
- voice selector
- audio mode controls
- STT language selector
- optional center-STT toggle
- category chips
- advanced capture buttons
- Q&A capsule
- notes / decisions / risks / next steps
- summary/copy tools
- guardrail copy

## Audio And Voice Status

Audio remains text-first by default:

- `Audio: Texto`
- no automatic male voice selection
- browser voice only if Frank explicitly selects `Voz navegador`
- preferred browser voice must be Spanish female-sounding when auto-selected
- if none exists, Val stays in text mode and asks Frank to select a voice manually or use text

## Known Limitations

- Browser STT is inconsistent and should not be treated as the main interaction.
- Browser voices depend on Frank's operating system and browser.
- ArcX behavior depends on the external ring profile.
- The static demo still has no backend, no persistence, and no real LLM.
- Browser visual QA on Frank's machine remains the final authority for ring ergonomics.

## Guardrails

- Deterministic/operator-assisted only.
- Frank remains operator.
- No real LLM implementation.
- No OpenAI/ChatGPT API.
- No external services.
- No backend.
- No persistence.
- No real PowerClub data.
- No production promise.
- No human/AGI framing.
- No recording or audio storage.
- CRM demo and Val Discovery Stage remain separate.
