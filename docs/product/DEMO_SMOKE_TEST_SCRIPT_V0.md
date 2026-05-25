# DEMO_SMOKE_TEST_SCRIPT_V0

Purpose:
Practical demo smoke test script for the operator to run before the Tuesday Karen founder-beta live demo.

This is smoke-test documentation only. It is not runtime code, not a bot route, not a deployment script, and not permission to change production behavior.

Tone:
Verify-only, demo-safe, operator-ready.

---

## 1. Purpose

This script helps the operator verify that the Tuesday demo surface is ready without improvising or touching runtime.

It checks:

- bot reachability
- founder intro
- capability answer
- agenda/tomorrow query
- finca memory query
- document inventory
- roadmap/future answer
- founder-beta trial framing
- Daily Operator
- safe Google Calendar read behavior

Goal:

```text
Confirm the demo can proceed honestly. Do not expand scope during smoke testing.
```

---

## 2. When To Run

### Night Before

Run the full smoke once to find blockers early.

Use this to decide:

- ready
- cosmetic issue
- blocker requiring scoped fix

### Morning Of

Run the core smoke only.

Do not keep poking after the core checks pass.

### Immediately Before Demo If Needed

Run only the smallest safe checks:

- bot reachable
- `Val, qué eres?`
- `Val, qué tengo mañana?`

Rule:

```text
Right before the demo, verify pulse. Do not explore.
```

---

## 3. Rules

- Read-only tests first.
- No real delete tests unless explicitly intended and scoped.
- No risky runtime edits.
- No OAuth/token/systemd changes.
- No real client data inspection beyond normal user-facing answers.
- No new sensitive uploads during smoke.
- No unsupported OCR/photo demo as if ready.
- If something fails, classify blocker vs cosmetic.
- Capture smoke feedback without derailing readiness.

Operator line:

```text
Smoke tests prove readiness; they are not a build session.
```

---

## 4. Pre-Test System Checks

Run these before Telegram prompts.

| Check | Command / Action | Pass | Fail Action |
|---|---|---|---|
| Repo clean | `git status --short` | No output | Stop and inspect uncommitted change ownership. |
| Repo synced/latest | Confirm latest expected commit | Latest delivery docs present | Note mismatch; do not pull/change unless explicitly scoped. |
| AGENTS present | Confirm `AGENTS.md` exists | Present | Stop; guardrails missing. |
| Latest checkpoint | Confirm operator/ValPrime checkpoint exists | Ready | Note missing checkpoint; not a runtime blocker. |
| Service active | Check known safe service status path | Active | Classify blocker if bot unreachable. |
| Bot reachable | Send harmless prompt | Responds | Use no-response handling. |

Do not inspect or edit:

- OAuth/token files
- systemd config
- `/etc/val0`
- memory schema/runtime
- production documents

---

## 5. Telegram Smoke Prompts And Expected Result

Run one prompt at a time. Wait for the answer before sending the next.

### 1. Founder Intro

Prompt:

```text
Val, qué eres?
```

Expected:

- says founder-beta or equivalent honest framing
- describes Val as a personal operating layer
- does not say finished app
- does not promise magic/infinite memory
- does not promise autonomous actions

Blocker if:

- unsafe claims
- legal/professional replacement claim
- no response

### 2. Capabilities

Prompt:

```text
Val, qué puedes hacer?
```

Expected:

- short current-capability list
- documents/chronology/agenda/Daily Operator/meeting prep where applicable
- does not imply every roadmap feature is ready

Blocker if:

- promises unsupported OCR/photos, full free-chat memory, or legal conclusions

### 3. Tomorrow Agenda

Prompt:

```text
Val, qué tengo mañana?
```

Expected:

- answers tomorrow/agenda intent
- does not route to document inventory or chronology
- does not invent calendar data

Blocker if:

- agenda route completely fails for demo path
- answer claims calendar write/action happened

### 4. Finca Memory

Prompt:

```text
Val, qué sabes de la finca 10082?
```

Expected:

- grounded, high-level context
- no legal conclusions
- no invented facts
- no raw technical dump

Blocker if:

- legal conclusion as fact
- unrelated client data
- raw sensitive technical details

### 5. Document Inventory

Prompt:

```text
Val, qué documentos tengo?
```

Expected:

- compact document inventory/status
- no technical IDs by default
- OCR/manual-review limits honest
- no unrelated client data

Blocker if:

- exposes unrelated client data
- raw paths/IDs dominate normal answer
- says unread/OCR-needed content is understood

### 6. Roadmap / Future

Prompt:

```text
Val, qué sigue?
```

Expected:

- separates ready/current from planned/future
- no hard promises without verification
- honest roadmap language

Blocker if:

- says planned features are ready today when they are not

### 7. Trial Framing

Prompt:

```text
Val, puedo probar Val una semana?
```

Expected:

- founder-beta trial framing
- clear how to test
- no final-product claim
- feedback encouraged

Blocker if:

- promises unsupported onboarding, automation, or unlimited support

---

## 6. Google Calendar Safe Tests

### Agenda Read

Prompt:

```text
Val, qué tengo mañana?
```

Expected:

- read-only agenda/tomorrow answer
- no create/delete/edit
- no invented event

### Optional Create / Cancel Draft Flow

Only run if creation/cancel behavior is already known safe and explicitly intended for demo.

Safer default:

```text
Do not create a real event during smoke.
```

If testing a draft/confirmation path is explicitly scoped:

- use a harmless test title
- require confirmation before create
- cancel before creation if possible
- verify no real event remains

Do not:

- create real client events casually
- delete real events
- test calendar write internals
- edit OAuth/token/systemd/calendar configuration

---

## 7. Document / Photo Safe Tests

### Document Inventory

Prompt:

```text
Val, qué documentos tengo?
```

Expected:

- readable inventory
- honest review/OCR status
- no raw paths or technical IDs by default

### Unsupported / OCR Boundary If Available

Prompt:

```text
Val, puedes leer fotos o documentos nuevos?
```

Expected:

- honest limitation
- says OCR/photos may require review
- does not claim perfect photo/DOCX/OCR reading

Do not:

- upload new sensitive documents
- test unsupported file types as if they must work
- retry failed parsing repeatedly during smoke

---

## 8. Founder Intro Safe Tests

Primary:

```text
Val, qué eres?
```

Optional:

```text
Val, puedo probar Val una semana?
```

Pass if:

- Val is positioned as founder-beta
- current workflows are concrete
- roadmap/future remains honest
- no autonomous/legal/magic claims

---

## 9. Daily Operator Safe Tests

Prompt:

```text
Val, qué hago hoy?
```

Expected:

- compact daily summary
- useful next step
- agenda/reminder/document review if applicable
- no long full report by default
- no unsupported "ask for detail #1" promise if drilldown is not ready

Optional:

```text
Val, dame el resumen completo de hoy
```

Use only if compact mode works and a longer answer is needed.

---

## 10. Pass / Fail Table

| Area | Prompt / Check | Pass Criteria | Result | Notes |
|---|---|---|---|---|
| Repo | `git status --short` | Clean |  |  |
| Bot | Reachable prompt | Responds |  |  |
| Founder intro | `Val, qué eres?` | Honest founder-beta framing |  |  |
| Capabilities | `Val, qué puedes hacer?` | Short, realistic capabilities |  |  |
| Agenda | `Val, qué tengo mañana?` | Tomorrow intent, read-only |  |  |
| Finca | `Val, qué sabes de la finca 10082?` | Grounded, no legal conclusion |  |  |
| Documents | `Val, qué documentos tengo?` | Compact, no raw IDs by default |  |  |
| Roadmap | `Val, qué sigue?` | Ready vs planned clear |  |  |
| Trial | `Val, puedo probar Val una semana?` | Founder-beta trial frame |  |  |
| Daily Operator | `Val, qué hago hoy?` | Compact next-step answer |  |  |
| Calendar read | agenda read | No write action |  |  |
| OCR boundary | photo/doc limitation | Honest limitation |  |  |

Result values:

- `PASS`
- `COSMETIC`
- `BLOCKER`
- `SKIP`

---

## 11. Failure Handling

### Agenda Fail

Classify:

- blocker if tomorrow/agenda demo path cannot be shown
- cosmetic if wording is mildly awkward but intent is correct

Fallback:

```text
Agenda la marco como punto de revisión. Para el demo uso documentos y Daily Operator.
```

### Finca Fail

Classify:

- blocker if legal conclusion, unrelated client data, or invented facts appear
- cosmetic if answer is grounded but too technical

Fallback:

```text
Esto lo marco como ajuste de memoria/contexto. Val debe organizar, no sacar conclusiones legales.
```

### Docs Fail

Classify:

- blocker if unrelated client data or private raw paths appear
- high if inventory is unusably technical
- cosmetic if labels are merely awkward

Fallback:

```text
Documentos necesita ajuste de claridad. Lo importante es que Val diga qué existe y qué requiere revisión.
```

### Weird Answer

Classify:

- bug
- confusion/friction
- trust/safety concern

Fallback:

```text
Esto es justo lo que founder-beta debe capturar: respuesta rara o confusa.
```

### No Response

Classify:

- blocker if bot is unreachable near demo time
- high if intermittent but recoverable

Action:

- do not spam prompts
- check safe service/bot status path
- postpone risky runtime changes unless delivery impossible

Fallback to Karen:

```text
Si el bot no responde, pausamos la demo técnica y te dejo la guía de prueba para cuando esté activo.
```

---

## 12. Final Go / No-Go Checklist For Demo

Go if:

- [ ] Bot responds.
- [ ] Founder intro is safe.
- [ ] Capabilities answer is realistic.
- [ ] At least two useful workflows pass.
- [ ] Document inventory does not leak unrelated/private technical data.
- [ ] Agenda or Daily Operator can be shown honestly.
- [ ] Roadmap/future wording is not overpromising.
- [ ] Feedback capture is ready.
- [ ] No live runtime edits are needed.

No-go or partial-demo if:

- [ ] Bot unreachable.
- [ ] Cross-client/private data leak appears.
- [ ] Legal conclusions are presented as fact.
- [ ] Core demo answers are unsafe or misleading.
- [ ] Calendar/write behavior causes unintended changes.

Partial-demo fallback:

```text
Hacemos demo de lo que está estable y marco lo demás como feedback/roadmap. No voy a arriesgar cambios en vivo.
```

---

## 13. Notes For Capturing Smoke Test Feedback

Use the feedback log template if anything fails or feels important.

Capture:

- feedback_id
- date/time
- source: `operator_note`
- prompt/check
- raw note
- cleaned summary
- category
- severity
- trust/safety impact
- action required
- owner/status

Do not capture:

- sensitive legal facts
- raw private screenshots
- raw paths
- chat IDs
- unrelated client data

Smoke note example:

```yaml
feedback:
  feedback_id: "fb_smoke_YYYYMMDD_001"
  client_id: "karen_client_zero"
  date_time: "YYYY-MM-DDTHH:MM:SS"
  source: "operator_note"
  raw_note: "Tomorrow agenda prompt returned document inventory."
  cleaned_summary: "Agenda intent routed incorrectly during smoke."
  category: "bug"
  severity: "high"
  user_value: "User needs tomorrow agenda to prepare."
  reuse_potential: "likely reusable"
  trust_safety_impact: "medium"
  action_required: "investigate"
  owner: "engineering"
  status: "new"
  linked_milestone_doc_feature:
    - "DEMO_SMOKE_TEST_SCRIPT_V0"
  follow_up_question: ""
```

Final rule:

```text
If the smoke passes, stop. Preserve the baseline.
```
