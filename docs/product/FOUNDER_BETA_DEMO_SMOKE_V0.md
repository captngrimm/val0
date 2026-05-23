# FOUNDER_BETA_DEMO_SMOKE_V0 — Val0

Purpose:
Run a short pre-demo sanity check before showing Val0 to a founder-beta client or prospect.

This is a founder-beta readiness check. It is not a production certification, security audit, or guarantee that every workflow is ready for public use.

---

## When To Use This

Use this checklist before:

- a $150 assessment call with a live Val0 walkthrough
- a founder-beta demo
- a Karen-style legal/admin workflow demo
- a prospect conversation where Val0 might be shown live

Do not use this to justify improvising with real sensitive documents or untested workflows.

---

## Preconditions

Before demo:

- Correct repo: `/opt/val0`
- Correct branch: `karen-client-zero-mvp-2026-05-25`
- Latest intended commits are pushed or otherwise accounted for.
- Bot is active after any runtime code change.
- Client isolation audit passes.
- Relevant smoke scripts pass.
- Demo data is safe to show.
- Sensitive client documents are not used unless explicit consent exists.
- Demo scope is selected: one narrow workflow, not a stress test.

If any precondition is unclear, stop and verify before demo.

---

## Server Verification Block

Run from `/opt/val0`:

```bash
git status --short
./scripts/val0py -m py_compile bot.py core/pending_actions.py core/document_registry.py core/document_extraction_readiness.py core/case_timeline.py core/daily_operator.py core/response_envelope.py core/client_profiles.py
python3 scripts/quality/client_isolation_audit.py
./scripts/val0py scripts/quality/pending_actions_smoke.py
./scripts/val0py scripts/quality/document_registry_smoke.py
./scripts/val0py scripts/quality/document_extraction_readiness_smoke.py
./scripts/val0py scripts/quality/case_timeline_smoke.py
./scripts/val0py scripts/quality/daily_operator_smoke.py
./scripts/val0py scripts/quality/response_envelope_smoke.py
./scripts/val0py scripts/quality/client_profiles_smoke.py
```

Expected:

- Working tree is clean or only expected doc/demo changes are present.
- Compile passes.
- Client isolation audit passes.
- Smoke scripts pass.

If `bot.py` changed since the last deployment/restart, do not demo until the live service is confirmed on the intended version.

---

## Karen Telegram Live Smoke

Run only in the intended Karen/client-zero test chat.

### 1. Document Inventory

Send:

```text
Val, qué documentos tengo
```

Expected:

- Routes to document inventory/listing.
- Does not route to timeline.
- Does not route to Daily Operator.
- Does not expose raw local paths.

### 2. Case Timeline

Send:

```text
Val, ordéname la cronología del caso
```

Expected:

- Routes to case timeline.
- Shows chronological bullets or a clear no-events message.
- Includes source/provenance when events exist.
- Includes legal boundary language.

### 3. Year Query

Send:

```text
Val, qué pasó en 2024
```

Expected:

- Routes to Karen case timeline for 2024.
- Does not answer as generic world history.
- Does not route to document inventory.

### 4. Daily Operator

Send:

```text
Val, qué hago hoy
```

Expected:

- Routes to Daily Operator.
- Clearly says read-only/no changes.
- Keeps agenda, reminders/tasks, case/legal, documents, and suggested next action separated.
- Does not claim Google Calendar was consulted inside Daily Operator v0.

### 5. Agenda

Send:

```text
Val, qué tengo mañana
```

Expected:

- Routes to agenda/calendar/reminder dashboard.
- Does not route to Daily Operator.
- Does not route to document/timeline/legal routes.

### 6. Optional Safe Upload

Only if a safe demo file is available.

Upload a small demo `.txt` file or a harmless image/photo.

Expected for text:

- File is received.
- VFMS ID is shown if registration succeeds.
- Status says text extracted/indexed or otherwise clearly reports failure.
- Case link status is clear.

Expected for photo/image:

- File is received/stored.
- Status says OCR or manual review is needed.
- Val0 does not pretend it read the photo.

Do not upload real sensitive documents in a prospect demo.

---

## Controlled Demo Script

Use 8-10 minutes.

1. Show the premise:
   - “Val0 is founder-beta, Telegram-first, and workflow-specific.”
2. Show a normal capability:
   - `Val, qué puedes hacer hoy`
3. Show document organization:
   - `Val, qué documentos tengo`
4. Show timeline:
   - `Val, ordéname la cronología del caso`
5. Show Daily Operator:
   - `Val, qué hago hoy`
6. Show confirmation safety only if needed:
   - mention calendar create/delete requires explicit confirmation
7. Close with boundaries:
   - beta
   - not legal advice
   - OCR/DOCX limitations
   - actions require confirmation

Demo the shape of value, not every feature.

---

## What To Show

Show:

- focused workflow setup
- client-specific organization
- document status honesty
- read-only timeline and Daily Operator
- confirmation-based actions
- unknown-client safety if relevant
- roadmap language for not-ready requests

---

## What Not To Show

Do not show:

- real sensitive documents without consent
- raw `/ops` or `/health` output to prospects
- raw VFMS paths or server internals
- OCR/photo reading as guaranteed
- DOCX extraction as ready
- autonomous legal/calendar/document action
- open-ended “try to break it” tests
- public dashboard or multi-client setup as if self-serve

---

## Red Flags

Stop the demo if:

- `bot.py` changed and the live bot was not restarted/verified.
- Client isolation audit fails.
- Any smoke script fails.
- Document inventory routes to timeline/operator.
- Timeline query routes to generic world-history response.
- Daily Operator steals agenda/calendar/document/timeline routes.
- Unknown client can enter Karen document/timeline/legal/operator workflow.
- Photo/image is presented as read when OCR is not ready.
- Calendar create/delete happens without explicit confirmation.
- Val0 exposes raw local paths, tokens, server internals, or unrelated client data.
- The demo starts turning into a broad stress test.

If a red flag appears, stop, name it as beta behavior, and move to follow-up. Do not improvise live fixes.

---

## Client-Facing Boundaries

Use simple language:

“Val0 is in founder-beta. It can already help organize notes, reminders, documents, timelines, and next actions, but it is not finished public software.”

“It does not replace a lawyer, accountant, doctor, or professional reviewer.”

“Sensitive documents should only be uploaded with consent and with beta-storage limits understood.”

“Calendar creates/deletes and other sensitive actions require explicit confirmation.”

“OCR/photo reading and DOCX extraction are limited. If Val0 cannot read a file, it should say so.”

---

## Pass / Fail Checklist

Mark each item:

- [ ] Repo/branch verified.
- [ ] Working tree clean or expected doc-only changes.
- [ ] Bot active on expected version.
- [ ] Compile PASS.
- [ ] Client isolation audit PASS.
- [ ] Pending actions smoke PASS.
- [ ] Document registry smoke PASS.
- [ ] Document extraction readiness smoke PASS.
- [ ] Case timeline smoke PASS.
- [ ] Daily Operator smoke PASS.
- [ ] Response envelope smoke PASS.
- [ ] Client profiles smoke PASS.
- [ ] `qué documentos tengo` routes correctly.
- [ ] `ordéname la cronología del caso` routes correctly.
- [ ] `qué pasó en 2024` routes correctly.
- [ ] `qué hago hoy` routes correctly.
- [ ] `qué tengo mañana` routes correctly.
- [ ] Optional upload status is honest.
- [ ] No raw private paths or unrelated client data shown.
- [ ] Boundaries are ready to say out loud.

Result:

- PASS: proceed with assessment call or founder demo.
- PARTIAL: demo only the passing flows and disclose skipped areas.
- FAIL: stop demo, inspect logs, patch safely, rerun smoke.

---

## Next Action After Pass

Proceed with one of:

- $150 workflow assessment call
- controlled founder-beta demo
- Karen-style legal/admin workflow walkthrough
- candidate onboarding conversation

Keep the demo narrow and end by asking what would be useful this week.

---

## Next Action After Fail

Do not demo.

Do:

- inspect logs
- identify the failing route or smoke
- decide whether this is a quick fix or a Codex task
- patch only within scope
- rerun compile, audit, and smoke
- update this checklist if the failure reveals a recurring demo risk

Do not:

- improvise live
- promise the failing feature is ready
- upload real client data to reproduce the issue
- bypass confirmation or client-isolation guardrails
