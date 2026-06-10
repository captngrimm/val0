# PowerClub CRM - Day 1 Frank Machine QA 02B V1

## Purpose

Give Frank a concrete browser QA loop to run on his actual laptop/browser before the PowerClub Karen/GM review.

This is Day 1 of the seven-day GM readiness plan:

- Planned Day 1 budget: 3-5 effective working hours.
- Overall base plan: 28-35 effective working hours.
- Stretch/wow plan: 40-50 effective working hours if voice/LLM/backend polish is pursued later.

This lane is not for new features. It is for visual safety, executive polish, browser access, and Frank-machine readiness.

## Exact Paths / URLs To Open

If opening directly from the file system:

- Main CRM demo:
  `file:///opt/val0-powerclub/docs/demo/powerclub_crm/index.html`
- Val Discovery Stage:
  `file:///opt/val0-powerclub/docs/demo/powerclub_crm/val_discovery.html`

If using a local static server from repo root:

```bash
cd /opt/val0-powerclub
python3 -m http.server 8765
```

Then open:

- Main CRM demo:
  `http://127.0.0.1:8765/docs/demo/powerclub_crm/index.html`
- Val Discovery Stage:
  `http://127.0.0.1:8765/docs/demo/powerclub_crm/val_discovery.html`

Use the file path first if it works. Use the local server if the browser blocks clipboard/TTS behavior or relative assets behave differently.

## Browser QA Checklist For Frank

### Main CRM Demo

- First impression feels executive, not like a random feature list.
- Hero says `PowerClub CRM Battle Stage`.
- Opening message explains the demo objective.
- Fake-data framing is visible near the top.
- It is clear this is pilot/discovery material, not production.
- Isthmus Dynamics / Honest AI Ops branding appears clean.
- Val Discovery link is visible and clearly labeled:
  `Val Discovery Mode · herramienta interna de reunión`
- The link does not make Val look like part of the PowerClub CRM product.
- `Vista gerencial` is the default/obvious first view.
- Dashboard sections feel scan-friendly.
- Collapsible headers do not clip text.
- Advisor workflow is reachable but does not dominate the first screen.
- No wording implies:
  - real PowerClub data
  - production readiness
  - WhatsApp automation
  - payment integration
  - Val already operates PowerClub

### Val Discovery Stage

- Page loads cleanly.
- First impression feels premium/internal, not stitched together.
- Header says `Isthmus Dynamics · Honest AI Ops`.
- Header says `Val Discovery Mode`.
- It is clear this is an internal meeting tool.
- Badge says internal/static/no external services.
- `Volver al CRM demo` link is visible and works.
- Orb/pulse visual quality feels controlled, not distracting.
- Speaking wave feels subtle and does not overwhelm the text.
- Text remains readable over the dark background.
- Buttons are clear:
  - Iniciar sesión
  - Hablar como Val
  - Siguiente pregunta
  - Siguiente pregunta inteligente
  - Generar resumen
  - Copiar resumen
- TTS button behavior:
  - If voice works, it should not hijack the meeting.
  - If voice fails or is unsupported, text mode should still be usable.
- `Val dice` panel remains useful without audio.
- Next question behavior works.
- Quick capture buttons work:
  - Capturar dolor
  - Capturar decisión
  - Marcar riesgo
  - Dato pendiente
  - Candidato para piloto
- `Val observa` updates after a capture.
- Summary generation works from captured fields.
- Copy summary works or shows manual-copy fallback.
- No wording implies Val listens, records, transcribes, or autonomously understands the meeting.

### Mobile-ish / Narrow Viewport

Shrink the browser to a narrow width and check:

- Main CRM hero does not overlap.
- First-screen cards stack cleanly.
- Toolbar controls are usable.
- Val Discovery cockpit columns stack cleanly.
- Val buttons do not overflow.
- Capture textareas are usable.
- Back navigation remains visible.

## What Frank Should Report Back

Send one of these:

- Screenshot of anything ugly, clipped, too small, or confusing.
- Short description if screenshot is not available.
- Browser name/version if something breaks.
- Whether Val feels premium or stitched together.
- Whether CRM and Val feel clearly separated.
- Whether the CRM first screen tells the story.
- Whether any wording feels like fake AI, production claim, or overpromise.
- Whether TTS worked, failed, or felt distracting.
- Whether copy-summary worked.

## Do Not Fix Blindly Rule

If a visual issue requires seeing the problem, do not guess from memory.

Ask Frank for:

- Screenshot.
- Browser.
- Approximate viewport size.
- Which page.
- What clicked or changed right before the issue.

Do not make broad redesign changes without visual evidence.

## Critical Polish Allowed

Allowed in Day 1:

- Clearer labels.
- Safer wording.
- Spacing/readability fixes.
- Navigation fixes.
- Tiny responsive CSS fixes.
- Reducing clutter.
- Clarifying internal/static/fake-data labels.

Not allowed in Day 1:

- New CRM features.
- LLM/API/backend.
- Microphone/STT/recording.
- Persistence.
- Real PowerClub data.
- Production promises.
- Human/AGI framing.
- Blurring CRM Demo and Val Discovery Stage.
- Claims that Val listens, understands, or acts autonomously.

## Critical Polish From Source Review

Source review on this lane found no mandatory code polish required before Frank-machine QA.

Current safe points already present:

- CRM demo first-screen framing is clear.
- Fake-data notice remains near the top.
- Val link is clearly labeled as internal meeting tool.
- Val Discovery Stage has a back link to the CRM demo.
- Val copy says Frank operates the meeting.
- Val page says it does not listen, record, or use real data.

## Planned vs Actual ETA Tracker For 02B

| Lane | Planned hours | Actual hours | Variance | Seven-day status | Updated total ETA | Notes |
| --- | ---: | ---: | ---: | --- | --- | --- |
| 02B Day 1 Frank Machine QA prep | 3-5 | TBD after lane | TBD | On track pending Frank browser run | 28-35 base | This doc prepares the actual Frank-machine QA loop; real visual findings still depend on Frank's laptop/browser. |

## Reporting Rule After Day 1 Completes

After Frank completes the browser run, report:

1. Planned hours for Day 1.
2. Actual elapsed time.
3. Variance.
4. Whether the seven-day plan is still on track.
5. Updated total projected hours.
6. What should be cut or deferred if ETA expands.

## What To Cut If Day 1 Slips

Cut/defer:

- Premium voice clips.
- Extra animation polish.
- Deep-linking every CRM section.
- Advanced summary formatting.
- Non-critical copy tweaks.

Do not cut:

- Fake-data guardrails.
- CRM vs Val separation.
- Navigation between CRM and Val.
- One full Frank-machine browser pass.
- Final fallback script before GM.

## Day 1 Exit Criteria

Day 1 is complete only when:

- Frank opens both pages on his laptop.
- Any ugly/confusing issue is screenshotted or described.
- Critical polish issues are fixed or explicitly deferred.
- The seven-day ETA tracker is updated with actual time.
- The demo is safe enough for Karen review, or blockers are documented.

## Recommended Next Lane

If Frank-machine QA passes:

`POWERCLUB-CRM-BATTLE-02C — Day 2 Operator-Assisted Intelligence Polish`

If Frank-machine QA finds visual blockers:

Run a focused 02B hotfix lane using screenshots and exact browser details.
