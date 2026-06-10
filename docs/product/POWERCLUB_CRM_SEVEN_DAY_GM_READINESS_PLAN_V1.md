# PowerClub CRM - Seven-Day GM Readiness Plan V1

## Purpose

Prepare Frank/Isthmus Dynamics for a PowerClub GM/general manager meeting where two assets work together:

- PowerClub CRM Demo: what PowerClub might use in a paid pilot.
- Val Discovery Stage: Isthmus Dynamics internal meeting cockpit for guided discovery, decision capture, risk capture, and next steps.

This plan starts after the 01C browser visual QA/polish pass. It is not permission to add production behavior, real PowerClub data, backend persistence, microphone/STT, recording, direct browser LLM calls, or payment/WhatsApp/email integrations.

## Operating Principle

Do not measure progress only by number of days. Measure by effective build hours, risk reduction, and meeting readiness.

The seven days are a calendar structure. The real control metric is whether the work reduces GM-meeting risk and produces a clear path to discovery, scope freeze, and paid pilot.

## Product Stance

Val should not pretend to be human.

Val should have:

- Presence.
- Guided perception.
- Operator-assisted intelligence.
- Consultative behavior.
- Clear boundaries.

Val is an internal tool in development, not a complete autonomous AI.

Avoid:

- Human/AGI framing.
- Fake LLM claims.
- "Val already operates PowerClub."
- "Val understands everything automatically."
- "Val is production-ready."

## Seven-Day Outcome

By the end of Day 7, Frank should be able to:

- Show the PowerClub CRM Demo cleanly.
- Explain the difference between the CRM demo and Val Discovery Stage.
- Use Val Discovery Stage to guide questions and capture meeting outputs.
- Answer GM questions about CRM, Val, AI, price, scope, WhatsApp, data, and production readiness.
- Close toward discovery, scope freeze, and a three-month pilot proposal.
- Fall back gracefully if Val/TTS/browser behavior fails.

## Day 1 - Visual QA And Polish

Goal:
Verify that the CRM demo and Val Discovery Stage feel executive/premium on Frank's actual machine.

Tasks:

- Open `docs/demo/powerclub_crm/index.html` in Frank's browser.
- Open `docs/demo/powerclub_crm/val_discovery.html` in Frank's browser.
- Check desktop viewport and mobile-ish/narrow viewport.
- Confirm fake-data/demo framing is visible.
- Confirm Val Discovery Stage is clearly labeled as internal Isthmus meeting tool.
- Confirm CRM demo and Val Stage are not confused as the same product.
- Check first impression: executive, not stitched together.
- Check Spanish-executive copy.
- Fix only obvious polish issues: spacing, labels, guardrail copy, confusing link text, tiny responsive issues.

Estimated hours:
3-4 hours.

Dependencies:

- Frank's actual laptop/browser.
- Current static files.
- Browser visual QA doc from 01C.

Risk level:
Medium, because visual issues can appear only on real browser/viewport.

Can cut if time slips:

- Minor aesthetic refinements that do not affect comprehension.
- Alternate dark/light polish.

Must not cut:

- Fake-data visibility.
- Internal-tool label for Val.
- CRM vs Val separation.
- Back/forth navigation between CRM demo and Val Stage.

Definition of done:

- Frank can open both pages without confusion.
- No visible claim of production readiness.
- No obvious first-screen clutter.
- Any critical visual issue is fixed or documented.

## Day 2 - Operator-Assisted Intelligence

Goal:
Make Val Discovery Stage feel like a consultative meeting cockpit without real AI or backend.

Tasks:

- Add or polish client name/context inputs.
- Improve response capture for the current question.
- Add/confirm category buttons:
  - leads
  - follow-up
  - close
  - manager visibility
  - advisor workflow
  - data sources
  - pilot scope
  - risks/exclusions
- Improve deterministic `Val observa`.
- Show recommended next question.
- Show recommended CRM section to open next.
- Improve local summary structure.
- Keep all behavior local/static.

Estimated hours:
5-6 hours.

Dependencies:

- Day 1 polish decisions.
- Current Val Discovery Stage.
- GM meeting narrative.

Risk level:
Medium.

Can cut if time slips:

- Extra capture categories beyond the core seven.
- Advanced summary formatting.
- Visual micro-animations.

Must not cut:

- Deterministic behavior.
- No AI claims.
- No persistence.
- No real data.
- Summary of pains, decisions, risks, data needs, pilot candidates, and next step.

Definition of done:

- Frank can type a response, classify it, see Val's deterministic observation, choose a next question, and generate a usable summary.

## Day 3 - LLM-Ready Architecture

Goal:
Design the safe path to future real LLM support without putting API keys or calls in the browser demo.

Tasks:

- Draft secure backend/proxy plan.
- Define no API key in browser rule.
- Define Val Discovery prompt capsule/shard.
- Define allowed topics:
  - discovery guidance
  - CRM demo explanation
  - follow-up questions
  - risk/exclusion detection
  - summary drafting
- Define refusal/guardrail behavior:
  - no production claims
  - no legal/financial promises
  - no real-data assumptions
  - no hidden integrations
- Define fallback to deterministic local mode.
- Define privacy/logging boundaries.
- Define when not to use LLM live.

Estimated hours:
4-5 hours.

Dependencies:

- Day 2 operator-assisted flow.
- Security/hosting decision.
- Decision about whether LLM will be shown live or held for later.

Risk level:
High, because a real LLM path adds security, privacy, cost, latency, and expectation risk.

Can cut if time slips:

- Detailed prompt examples.
- Multi-client prompt registry.
- Advanced analytics/logging design.

Must not cut:

- No direct browser LLM calls.
- No browser API keys.
- Fallback local deterministic mode.
- Privacy/logging boundaries.
- "Do not use LLM live" criteria.

Definition of done:

- Frank has a clear architecture story if asked "Can Val become real AI later?" without promising it is already implemented.

## Day 4 - Voice / Presence

Goal:
Make Val presence polished while keeping audio optional, safe, and non-invasive.

Tasks:

- Confirm browser TTS fallback.
- Test audio-off flow.
- Consider optional premium pre-recorded clips for intro/wrap only.
- Keep no microphone/STT/recording unless separately approved.
- Confirm speaking-state orb animation is subtle.
- Add voice safety and consent notes if audio is used.
- Prepare "text-only mode" fallback.

Estimated hours:
3-5 hours.

Dependencies:

- Frank's browser audio behavior.
- Decision on whether to use voice in GM meeting.
- Any approved audio assets if premium clips are pursued.

Risk level:
Medium-high, because voice can impress but also distract or feel gimmicky.

Can cut if time slips:

- Premium pre-recorded clips.
- Any voice in live GM meeting.
- Extra speaking animation polish.

Must not cut:

- Text-only mode.
- No microphone/STT/recording.
- No claim that Val listens.
- Ability to run meeting without audio.

Definition of done:

- Frank can choose either silent cockpit mode or browser-native TTS without breaking the meeting.

## Day 5 - PowerClub Demo Integration

Goal:
Make the CRM demo and Val Discovery Stage work as a coherent meeting pair without blurring their boundaries.

Tasks:

- Val recommends which CRM section to show next:
  - executive dashboard
  - risk/recovery
  - advisor scorecard
  - advisor queue
  - templates/dictation
  - scope/pricing docs
- Confirm link flow between Val Discovery Stage and CRM demo.
- Practice GM-friendly story:
  - pain
  - visibility
  - action
  - scope
  - pilot
- Reinforce fake-data guardrails.
- Reinforce internal-tool guardrails.
- Define discovery-to-scope transition language.

Estimated hours:
4-5 hours.

Dependencies:

- Day 2 recommended-section logic.
- Day 1 visual QA.
- Narrative order doc.

Risk level:
Medium.

Can cut if time slips:

- Deep-link anchors into every CRM section.
- Extra recommended-section detail.

Must not cut:

- CRM vs Val separation.
- Fake-data framing.
- Discovery-to-scope close.
- Simple navigation between pages.

Definition of done:

- Frank knows when to show Val and when to show CRM, without making Val look like the CRM product.

## Day 6 - Commercial Readiness

Goal:
Prepare Frank to discuss a paid pilot without improvising or overpromising.

Tasks:

- Review three-month pilot shape.
- Review pricing boundaries.
- Review scope freeze checklist.
- Review exclusions:
  - WhatsApp automation
  - payments
  - production SLA
  - unlimited reports
  - full SaaS configurability
  - Val Copilot production assistant
- Prepare proposal follow-up path.
- Prepare post-meeting summary template.
- Prepare stakeholder questions.
- Define what Karen must help validate before GM meeting:
  - pain accuracy
  - boss/GM appetite
  - strongest demo section
  - forbidden language
  - who approves scope/budget

Estimated hours:
4-5 hours.

Dependencies:

- Pricing model.
- Scope freeze checklist.
- Objection handling.
- Karen feedback.

Risk level:
Medium.

Can cut if time slips:

- Extra proposal formatting.
- Detailed maintenance tier edits.

Must not cut:

- Scope freeze.
- Exclusions.
- Pricing boundaries.
- Next-step close.
- Karen validation questions.

Definition of done:

- Frank can discuss pilot structure without promising infinite changes or production behavior.

## Day 7 - QA / Rehearsal / Fallback

Goal:
Run a complete dry run and prepare fallback paths.

Tasks:

- Test on Frank laptop.
- Test with audio.
- Test without audio.
- Test with weak internet or offline static files.
- Full demo dry run:
  - open Val
  - introduce internal tool
  - open CRM demo
  - show executive dashboard
  - show advisor workflow
  - return to Val
  - capture responses
  - generate summary
  - close to discovery/scope/pilot
- Prepare fallback script if Val fails.
- Prepare answer if asked "Is this ChatGPT?"
- Final pre-meeting checklist.

Estimated hours:
5-6 hours.

Dependencies:

- Day 1-6 completion.
- Frank availability.
- Karen feedback if available.

Risk level:
High, because rehearsal reveals timing, confidence, and equipment risks.

Can cut if time slips:

- Multiple full dry runs.
- Voice demo.
- Optional Val screen-share.

Must not cut:

- One end-to-end dry run.
- Fallback script.
- "Is this ChatGPT?" answer.
- Fake-data/internal-tool guardrails.
- Final checklist.

Definition of done:

- Frank can run the meeting calmly even if Val voice, browser, or internet fails.

## Projected vs Actual ETA Tracker

Initial planning assumption:

- 7 calendar days.
- 28-35 effective working hours as the base plan.
- 40-50 effective working hours as the stretch/wow plan if voice/LLM/backend polish is pursued.

Tracker rule:

After each completed lane, Codex must report:

1. Planned hours for that lane.
2. Actual elapsed time.
3. Variance.
4. Whether the seven-day plan is still on track.
5. Updated total projected hours.
6. What should be cut or deferred if the ETA expands.

| Lane / Day | Planned hours | Actual hours | Variance | Status | Updated total ETA | Notes |
| --- | ---: | ---: | ---: | --- | --- | --- |
| Day 1 - Visual QA and polish | 3-4 | TBD | TBD | on track | 28-35 base | Cut minor aesthetic polish first; never cut guardrail copy. |
| Day 2 - Operator-assisted intelligence | 5-6 | TBD | TBD | on track | 28-35 base | Cut extra categories if needed; keep deterministic capture/summary. |
| Day 3 - LLM-ready architecture | 4-5 | TBD | TBD | on track | 28-35 base | Cut deep prompt examples; keep secure-backend/no-browser-key plan. |
| Day 4 - Voice/presence | 3-5 | TBD | TBD | on track | 28-35 base / 40-50 stretch | Cut premium voice first; keep text-only fallback. |
| Day 5 - CRM demo integration | 4-5 | TBD | TBD | on track | 28-35 base | Cut deep-link polish; keep CRM/Val separation. |
| Day 6 - Commercial readiness | 4-5 | TBD | TBD | on track | 28-35 base | Cut formatting; keep scope/pricing/exclusions. |
| Day 7 - QA/rehearsal/fallback | 5-6 | TBD | TBD | on track | 28-35 base | Cut extra dry runs; keep one full dry run and fallback script. |

## Cut / Defer Strategy

If ETA expands beyond 35 hours:

- Defer premium pre-recorded voice.
- Defer real LLM/backend build.
- Defer deep-linking every CRM section.
- Defer advanced summary formatting.
- Defer visual micro-animation polish.

Do not defer:

- Frank laptop browser QA.
- Fake-data and internal-tool guardrails.
- CRM vs Val separation.
- Scope freeze and exclusions.
- "Is this ChatGPT?" answer.
- One full rehearsal.

## Recommended Next Build Lane

`POWERCLUB-CRM-BATTLE-02B — Day 1 Frank Machine Visual QA + Critical Polish`

Purpose:

- Run the actual browser check on Frank's machine.
- Capture visual issues.
- Fix only critical meeting polish.
- Update ETA tracker with actual Day 1 elapsed time and variance.
