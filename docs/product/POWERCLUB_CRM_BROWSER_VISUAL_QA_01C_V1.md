# PowerClub CRM Browser Visual QA 01C V1

## Purpose

Record the executive visual QA and polish pass for the current PowerClub CRM Demo and Val Discovery Stage before moving to the seven-day GM readiness plan.

Source-of-truth head reviewed:

`4b3e64e Add Val Discovery meeting cockpit for PowerClub demo`

## Pages Inspected

- Main PowerClub CRM demo:
  `docs/demo/powerclub_crm/index.html`
- Val Discovery Stage:
  `docs/demo/powerclub_crm/val_discovery.html`
- Shared CRM styling:
  `docs/demo/powerclub_crm/styles.css`
- Val Discovery Stage product spec:
  `docs/product/POWERCLUB_CRM_VAL_DISCOVERY_STAGE_V1.md`
- Demo narrative order:
  `docs/product/POWERCLUB_CRM_DEMO_NARRATIVE_ORDER_V1.md`
- Sales packet index:
  `docs/product/POWERCLUB_CRM_BATTLE_SALES_PACKET_INDEX_V1.md`

## Browser / Visual QA Method

Browser binary check:

- `chromium`: not available.
- `chromium-browser`: not available.
- `google-chrome`: not available.
- `firefox`: not available.
- `playwright`: not available.

JavaScript parser check:

- `node`: not available, so inline Val Discovery JavaScript could not be syntax-parsed locally.

Actual browser screenshot QA was not possible in this Codex environment. This pass used source-level visual QA, copy review, interaction-path inspection, guardrail scanning, and repository smoke tests.

## Visual QA Checklist Results

| Check | Result | Notes |
| --- | --- | --- |
| Main demo loads by static path | Pass by smoke/source | Existing static smoke verifies required demo files and labels. |
| Val Discovery link is visible and clear | Pass | Main demo now links to `Val Discovery Mode · herramienta interna de reunión`. |
| Val Discovery page loads by static path | Pass by source | Standalone static HTML with inline CSS/JS and relative asset path. |
| Navigation back to CRM demo is clear | Fixed | Added `Volver al CRM demo` link in the Val header badge. |
| Orb/pulse is controlled | Pass by source | Orb is CSS-only, no human avatar, no autoplay audio. |
| Speaking wave is optional/supportive | Pass by source | Wave only toggles through scripted speaking state. |
| TTS does not block UX | Pass by source | If `speechSynthesis` is unavailable or fails, text mode remains. |
| `Val dice` remains useful in text mode | Pass | Scripted messages and question prompts always render as text. |
| Question flow works conceptually | Pass by source | Next-question logic cycles through structured local question bank. |
| Capture fields are usable | Pass by source | Textareas for answer, notes, decisions, risks, next steps. |
| Summary/copy fallback exists | Pass by source | Clipboard failure shows manual-copy fallback. |
| Responsive/mobile-ish layout | Pass by source | Grid collapses at `1080px` and controls stack at `640px`. |
| Separation between CRM demo and Val Stage | Pass | Link and copy label Val as internal Isthmus meeting tool. |
| No real AI claim | Pass | Val is framed as internal/static/deterministic; no API claims. |
| No production promise | Pass | Both pages keep pilot/demo framing. |

## Issues Found

1. Val Discovery Stage did not have an obvious return path to the CRM demo.
2. A few usage-flow lines could be read as Val doing too much instead of Frank operating the meeting.
3. Browser and JS parser tooling were unavailable, so this could not be a true screenshot/console QA pass.

## Fixes Made

- Added `Volver al CRM demo` link to `docs/demo/powerclub_crm/val_discovery.html`.
- Added small `stage-actions` / `stage-link` styling inside the Val page.
- Changed Val usage-flow copy from:
  - `Val da el marco de la sesión`
  - `Val genera un resumen local`
- To safer operator-led wording:
  - `Frank usa Val para mostrar el marco de la sesión`
  - `Frank genera un resumen local`

## Known Limitations

- No browser screenshot was captured.
- No live console was inspected.
- No actual TTS playback was verified.
- No clipboard behavior was tested in a browser context.
- No mobile device or responsive viewport screenshot was captured.
- Val Discovery Stage remains static/deterministic and does not persist captured meeting notes.

## Safe To Show Karen

Safe with these framing points:

- The PowerClub CRM demo uses fictitious data.
- The CRM demo is pilot/discovery material, not production.
- Val Discovery Mode is an internal Isthmus Dynamics meeting tool.
- Val is not operating PowerClub.
- Val is not listening, recording, transcribing, or calling external AI services.
- WhatsApp/email/payment behavior remains manual/conceptual unless separately scoped.

Recommended Karen use:

1. Open the CRM demo first.
2. Explain the executive dashboard narrative.
3. Mention Val Discovery Mode only as Frank's internal meeting cockpit if useful.
4. Ask Karen what to adjust before showing leadership.

## Safe To Show GM

Safe if Frank keeps the sequence controlled:

1. Start with the PowerClub CRM executive dashboard.
2. Explain fake-data/pilot framing.
3. Show advisor workflow only after leadership understands management visibility.
4. Use Val Discovery Mode as an internal meeting aid, not as part of the CRM product promise.
5. Close toward discovery, scope freeze, and a paid pilot proposal.

Val Discovery Mode can be shown to GM if introduced as:

```text
Esta es una herramienta interna de Isthmus Dynamics para ordenar discovery y próximos pasos. No es parte del CRM de PowerClub ni una IA productiva conectada a sus datos.
```

## What Frank Should Not Say

- "Esto ya está listo para producción."
- "Esto usa datos reales de PowerClub."
- "Val ya opera PowerClub."
- "Val escucha o graba la reunión."
- "Val analiza automáticamente la conversación."
- "WhatsApp automático está incluido."
- "Email automático está incluido."
- "Pagos están incluidos."
- "La IA decide por gerencia."
- "Cualquier cambio entra sin costo."
- "Esto reemplaza un CRM completo desde hoy."

## Validation Run

- `python3 scripts/quality/powerclub_crm_static_demo_smoke.py`
- `python3 scripts/quality/markdown_docs_inventory_smoke.py`
- `git diff --check`

## 01C QA Conclusion

The current package is visually and commercially safer after this polish pass, with the important limitation that actual browser-render screenshot QA was not available in this environment.

Status:

- Ready for Karen review: yes, with fake-data/internal-tool framing.
- Ready for GM review: conditionally yes, if Frank uses the rehearsal/narrative order and avoids production/automation claims.

## Recommended Next Step

Proceed to:

`POWERCLUB-CRM-BATTLE-02A — Seven-Day GM Readiness Plan`

The next lane should define the week-long preparation sequence: Karen alignment, demo rehearsal, data/sample request strategy, scope-freeze agenda, proposal readiness, and meeting logistics.
