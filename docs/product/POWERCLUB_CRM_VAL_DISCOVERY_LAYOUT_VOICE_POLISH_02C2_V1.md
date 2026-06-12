# PowerClub CRM - Val Discovery Layout + Voice Polish 02C.2 V1

## Purpose

Document the 02C.2 polish pass for Val Discovery Stage after Frank-machine QA.

Frank's findings:

- Visual impression is generally good.
- Val presence card had visible button overflow/clipping on the right.
- Browser voice selector found one usable female Spanish voice: Google español Estados Unidos.
- That voice is acceptable but too slow.
- Do not move to LLM/premium voice until current browser UI is clean.

## Files Updated

- `docs/demo/powerclub_crm/val_discovery.html`
- `docs/product/POWERCLUB_CRM_VAL_DISCOVERY_LAYOUT_VOICE_POLISH_02C2_V1.md`

## Layout Overflow Fix

Changed Val presence card controls from a rigid two-column grid to a wrapping flex layout.

Key fixes:

- `.control-grid` now uses `display: flex` and `flex-wrap: wrap`.
- Buttons use `flex: 1 1 132px`.
- Buttons have `max-width: 100%`.
- Button text can wrap with `overflow-wrap: anywhere`.
- Cockpit columns use slightly smaller minimum widths.
- Presence panels have `min-width: 0`.
- Orb area is slightly less height-demanding.

Expected result:

- Primary buttons wrap cleanly.
- No button should extend under or into the right column.
- The Val presence card should remain readable and premium.
- The orb/core should not force controls outside the card.

Frank still needs to confirm in browser because the original issue was visual/browser-specific.

## Voice Controls Added

Added:

- `Velocidad` slider.
- `Tono` slider.

Default behavior:

- Voice rate defaults to `1.05`, slightly faster than normal because Frank reported the available Spanish voice was too slow.
- Pitch defaults to `1`.

Safe ranges:

- Speed: `0.75` to `1.25`.
- Pitch: `0.9` to `1.15`.

The selected values are applied to each `SpeechSynthesisUtterance`.

## Voice Preference Polish

Voice selection still:

- Loads available browser voices.
- Prefers Spanish voices.
- Prefers female-sounding Spanish voices where detectable.

Additional preference:

- If no female-sounding Spanish voice is detected, prefer Google/Microsoft Spanish voices before generic Spanish voices.

This supports Frank's finding that `Google español Estados Unidos` is the only acceptable female Spanish option on his machine.

## Browser Voice Limitation Copy

Added clearer copy:

```text
Las voces dependen del navegador y del sistema operativo. Para demo ejecutiva, audio premium local puede reemplazar la voz del navegador.
```

This avoids implying browser voice availability or quality is guaranteed.

## Guardrails

- No LLM.
- No OpenAI/ChatGPT API.
- No ElevenLabs/API.
- No backend.
- No persistence.
- No microphone/STT changes in this lane.
- No recording.
- No real PowerClub data.
- No production promise.
- No human/AGI framing.
- Deterministic/operator-assisted only.
- Keep CRM demo and Val Discovery Stage separate.

## Validation Notes

Required validations:

- `python3 scripts/quality/powerclub_crm_static_demo_smoke.py`
- `python3 scripts/quality/markdown_docs_inventory_smoke.py`
- `git diff --check`

Browser confirmation still needed:

- Frank should confirm that presence-card buttons no longer clip.
- Frank should confirm the `Google español Estados Unidos` voice feels acceptable after increasing speed.
- Frank should confirm whether voice should be used live or kept text-only.

## ETA Tracker Update

Planned 02C.2 lane:

- 1-2 effective hours.

If ETA expands:

- Cut additional voice tuning.
- Cut animation polish.
- Cut premium audio discussion.

Do not cut:

- Layout fix.
- Text-only fallback.
- Browser voice limitation copy.
- CRM/Val separation.

## Recommended Next Lane

`POWERCLUB-CRM-BATTLE-02D — Simplified Val Discovery Browser QA + GM Dry Run`

Focus:

- Confirm layout fix on Frank laptop.
- Test speed/pitch controls with available Spanish voice.
- Decide whether live GM meeting uses voice or text-only mode.
