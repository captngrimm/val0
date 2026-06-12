# PowerClub CRM Battle 02D.3 - ArcX Numpad Mapping + Audio Test + Motion Tuning

## Purpose

This lane improves actual meeting operability for Frank's ArcX Ring and clarifies browser audio behavior.

No LLM, backend, external services, persistence, recording, STT expansion, or real PowerClub data was added.

## ArcX Numpad Mapping

Frank confirmed the ArcX Ring can emit numpad-style keys. Val Discovery now supports those aliases directly.

Recommended ArcX profile:

| ArcX Ring action | Browser key | Val behavior |
| --- | --- | --- |
| Center / button press | `Numpad5` | Current recommended action |
| Up | `Numpad8` | Previous / alternate question |
| Right | `Numpad6` | Next question / next step |
| Down | `Numpad2` | Generate or show summary |
| Left | `Numpad4` | Back / correct response |
| Long press / glowpress | `H` | Command menu |
| Mode switch, if available | `M` | Presentation / Operator Mode |

Existing keyboard fallbacks remain:

- `Space` / `Enter` - current recommended action
- Arrow keys - directional flow
- `H` - menu
- `M` - Operator Mode
- `Esc` - close overlays

Hotkeys still do not trigger while Frank is typing in inputs, textareas, or selects, except `Esc`.

## Presentation Ring Hint

Presentation Mode now shows compact conceptual and numpad mapping:

- center = current action / `Numpad5`
- up = alternate / `Numpad8`
- right = next / `Numpad6`
- down = summary / `Numpad2`
- left = correct / `Numpad4`
- hold = menu / `H`

The visible mental model is the ring, not a long hotkey list.

## Audio Test Behavior

Presentation Mode now includes a `Probar voz` button.

When clicked:

- If audio mode is not `Voz navegador`, Val switches to browser voice mode.
- If `speechSynthesis` and a selected voice are available, Val says:
  - `Val lista. Voz del navegador activa.`
- If browser voice is unavailable or no voice is selected, Val shows:
  - `No se pudo reproducir voz del navegador. Usa modo texto o revisa permisos/voz del sistema.`

Audio never autoplays. Frank must click the test button or explicitly set browser voice mode.

## Audio Modes

Presentation Mode keeps three compact modes:

- `Audio: Texto`
- `Audio: Voz navegador`
- `Audio: Premium futuro`

Default remains:

- `Texto`

Operator Mode continues to hold detailed browser voice controls:

- voice selector
- rate
- pitch

## Whiteboard Motion Tuning

The captured-idea animation was slowed slightly:

- floating idea card now moves over about one second
- settled whiteboard cards animate more visibly
- target lane still pulses/glows

The intent is to feel like:

1. captured idea appears
2. Val moves it
3. target lane receives it
4. card settles into the whiteboard

Reduced-motion users get simplified animation.

## Copy Tuning

Organizing copy now uses safer, more vivid phrasing:

- `Estoy moviendo esta señal al whiteboard...`
- `Estoy colocando esto como dolor operativo...`
- `La separo como dato pendiente...`

The copy avoids:

- autonomous analysis claims
- "Val escucha todo"
- human/AGI framing
- fake production intelligence

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

- ArcX behavior still depends on the external ring profile and browser focus.
- Browser voice depends on OS/browser voices and permissions.
- Premium audio remains future scope.
- Motion still needs Frank-machine visual QA.
