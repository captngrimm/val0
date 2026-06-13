# PowerClub CRM Battle 02D.5 - ArcX Input Debug + Voice Selection Repair

## Purpose

This lane repairs two meeting-readiness issues in Val Discovery Mode:

- ArcX Ring direction keys were not reliably acting as Val commands.
- Browser voice could fall back to a male voice, which is not acceptable for the current Val meeting presence.

No LLM, backend, external services, persistence, recording, STT expansion, or real PowerClub data was added.

## ArcX / Keyboard Debug Panel

Operator Mode now includes a drawer called:

`ArcX / teclado debug`

Use it when testing the ArcX Ring on Frank's laptop. Press each ring direction and check the last event values:

| Field | Meaning |
| --- | --- |
| `event.key` | Browser key value detected |
| `event.code` | Browser physical key/code value detected |
| `event.location` | Keyboard location, useful for numpad keys |
| `target editable` | Whether focus was inside an input, textarea, select, or editable element |
| `handled` | Whether Val treated the key as a command |
| `Val action` | The Val command mapped from the key |

This is intentionally visible only in Operator Mode so Presentation Mode stays clean for the client.

## Recommended ArcX Mapping

The current recommended ArcX Ring profile is:

| ArcX Ring action | Browser key/code | Val behavior |
| --- | --- | --- |
| Center / button press | `NumpadEnter` | Current recommended action |
| Up | `Numpad8` | Alternate / previous question |
| Right | `Numpad6` | Next question / next step |
| Down | `Numpad2` | Generate or show summary |
| Left | `Numpad4` | Back / correct |
| Center fallback | `Numpad5` | Current recommended action if configured |
| Long press / glowpress | `H` if configurable | Command menu |
| Mode switch | `M` if configurable | Presentation / Operator Mode |

If the ring emits plain numbers instead of numpad codes, Val can also map:

- `8` = up / alternate
- `6` = right / next
- `2` = down / summary
- `4` = left / back
- `5` = center fallback

Plain-number aliases only act as Val commands when Ring Control is ON.

## Ring Control Behavior

Presentation Mode now shows compact ring status:

- `Ring: ON`
- `Ring: OFF`

When Ring Control is ON:

- recognized ArcX numpad keys are treated as Val commands
- recognized plain-number aliases are treated as Val commands
- recognized ring keys are prevented from typing numbers into the response field

When Ring Control is OFF:

- ArcX numpad and number keys behave like normal browser keyboard input
- this is useful if Frank needs to type or troubleshoot without Val intercepting ring input

Normal keyboard fallback controls remain:

- `Space` / `Enter` = current recommended action
- arrow keys = directional flow
- `H` = command menu
- `M` = Operator Mode
- `Esc` = close overlays

Hotkeys still avoid hijacking typing in inputs, textareas, and selects. The exception is recognized ArcX ring keys when Ring Control is ON.

## How To Confirm Actual Key Values

1. Open Val Discovery Mode.
2. Switch to Operator Mode.
3. Open `ArcX / teclado debug`.
4. Make sure Ring Control is ON.
5. Press each ArcX Ring direction.
6. Confirm the panel shows the expected `event.key`, `event.code`, and `Val action`.
7. If a direction types a number into the response field, confirm whether Ring Control is ON and capture the debug values for adjustment.

Frank should report exact values from the debug panel if a key still fails.

## Voice Selection Behavior

Default audio mode remains:

`Texto`

This avoids accidental male browser voice playback during a meeting.

Operator Mode keeps:

- browser voice selector
- velocity/rate control
- pitch control
- selected voice status
- audio mode status

Visible status now includes:

- `Voz actual: [name]`
- `Modo audio: Texto / Voz navegador / Premium futuro`

## Female Spanish Voice Preference

When browser voices load, Val prefers Spanish female-sounding voices when available.

If no preferred female Spanish voice is found:

- Val does not silently choose a male voice.
- `selectedVoice` remains empty.
- Val shows: `No se encontró voz femenina en español. Selecciona otra voz o usa modo texto.`

Frank may explicitly choose any browser voice from Operator Mode, but the demo will not automatically default to a male voice.

## Probar Voz Behavior

`Probar voz` now behaves safely:

- If audio mode is `Texto`, it shows: `Audio está en modo texto. Cambia a Voz navegador para probar TTS.`
- If audio mode is `Voz navegador` and a voice is selected, it speaks: `Val lista. Voz del navegador activa.`
- If browser voice fails, it shows: `No se pudo reproducir voz del navegador. Usa modo texto o revisa permisos/voz del sistema.`

Audio never autoplays. Frank must explicitly choose browser voice mode and test it.

## Why Text Mode Is Default

Browser voices depend on:

- operating system voices
- browser support
- installed language packs
- user device settings

Text mode is more reliable for a GM meeting. Browser voice remains a useful optional demo layer, not a promise of final Val voice quality.

## Known Limitations

- ArcX behavior still depends on the external ring profile.
- Different browsers may report different `key`/`code` values.
- Plain-number aliases can interfere with typing if Ring Control is ON, so they are only enabled in that mode.
- Browser voice may not include a female Spanish option.
- Premium Val audio remains future scope.
- No audio is recorded or stored.
- No meeting data is persisted.

## Guardrails

- Deterministic/operator-assisted only.
- Frank remains operator.
- No fake LLM claims.
- No OpenAI/ChatGPT API.
- No external services.
- No backend.
- No persistence beyond in-page session variables.
- No real PowerClub data.
- No production promise.
- No human/AGI framing.
- No recording or audio storage.
- CRM demo and Val Discovery Stage remain separate.
