# FOUNDER_BETA_WEEK1_FEEDBACK_CAPTURE_V0

Purpose:
Design how Val0 should capture, classify, and use week-1 founder-beta feedback from Karen/client-zero and future founder users.

This is a product/design document only. It is not runtime config, not a bot route, not a feedback database schema, and not a promise that automated feedback capture is ready for Tuesday founder-beta delivery.

Tone:
Operator-ready, privacy-safe, practical, founder-beta focused.

---

## 1. Purpose

Founder-beta feedback capture should turn real use into product direction.

It should help Val0 answer:

- what worked
- what failed
- what confused the user
- what created trust
- what reduced forgetting
- what should be built next
- what should stay parked
- what is reusable across users
- what is Karen-only sensitive context

The goal is not to collect every comment forever.

The goal is:

```text
Capture the signal, classify it cleanly, protect private details, and turn the right parts into roadmap decisions.
```

---

## 2. Why Feedback Capture Matters

### Prevent Random Anecdote Chaos

Founder-beta feedback can arrive as:

- screenshots
- voice notes
- live comments
- operator memory
- Telegram replies
- "this felt weird"
- "I wish it did X"

Without structure, everything becomes equally urgent. A single emotional comment can distort the roadmap.

### Separate Bugs From Wishes From Paid-Value Signals

A bug is not the same as a wish.

A wish is not the same as a willingness-to-pay signal.

A Karen-only legal/admin detail is not the same as a reusable Val0 Personal pattern.

Feedback capture should classify these differences before they become work.

### Turn Karen Feedback Into Product Roadmap

Karen week-1 feedback should inform:

- Daily Operator polish
- document labels
- review-needed language
- agenda usefulness
- roadmap priorities
- what must stay out of scope

Rule:

```text
Feedback becomes roadmap only after classification, privacy review, and priority decision.
```

---

## 3. Feedback Categories

### Bug

Something expected to work did not work.

Examples:

- wrong route
- broken answer
- missing expected document list
- agenda answer confused with document answer

### Confusion / Friction

The feature may work, but the user does not understand it or it feels hard.

Examples:

- too technical
- too long
- unclear status
- user does not know whether something was saved

### Delight / Value Moment

The user felt relief, usefulness, or trust.

Examples:

- "this helped me know what to do"
- "this saved me from searching"
- "this made the case easier to remember"

### Missing Feature

The user expected a capability that is not built or not ready.

Examples:

- upload photos/documents
- folders/carpetas
- unified agenda
- reminders before meetings

### Roadmap Idea

An idea that may belong later, but is not necessarily urgent.

Examples:

- book/project memory
- family/shared folders
- richer dashboard

### Trust / Safety Concern

Anything that makes the user doubt correctness, privacy, memory, or boundaries.

Examples:

- "I don't trust whether this is saved"
- "Is this legal advice?"
- "Where did this information come from?"

### Willingness-To-Pay Signal

Evidence that a user would pay or continue for a workflow.

Examples:

- "I would pay if it kept my documents organized"
- "I need this every week"
- "Can you set this up for my business/team?"

### Reusable Pattern

A feedback item likely useful beyond one user.

Examples:

- readable document labels
- "needs OCR" honesty
- compact daily summary
- pre-meeting checklist

### Karen-Only Case Detail

Sensitive or case-specific detail that should not become reusable product content.

Examples:

- private legal facts
- raw document details
- case chronology details
- family/legal specifics

Rule:
Store these only in approved client-scoped systems if explicitly needed. Do not copy them into reusable product docs.

---

## 4. Capture Sources

### Telegram Conversation

Examples:

- direct prompt/response failures
- user comments after a response
- screenshots copied from chat

Guideline:
Capture the product signal, not private transcript dumps.

### Live In-Person Notes

Examples:

- observed confusion
- immediate reaction
- comments during demo

Guideline:
Separate direct user quote from operator interpretation.

### Voice Notes

Examples:

- spoken feedback
- after-use comments
- longer explanation of what was missing

Guideline:
Summarize privacy-safely; do not transcribe sensitive details into product docs unless explicitly scoped.

### Screenshots

Examples:

- too-long answer
- technical ID leakage
- confusing document status

Guideline:
Record what the screenshot proves; avoid storing private visual content in reusable docs.

### Operator Notes From Frank

Examples:

- observed demo issue
- support burden
- priority judgment
- product intuition

Guideline:
Mark clearly as operator note, not user quote.

### ValPrime Checkpoints

Examples:

- daily founder-beta checkpoint
- milestone decision summary
- pass/fail status

Guideline:
Use checkpoints to aggregate, not to hide raw unresolved feedback.

---

## 5. Suggested Feedback Record Fields

Minimum structured record:

```yaml
feedback:
  feedback_id: "fb_YYYYMMDD_001"
  client_id: "client_alias_or_id"
  date_time: "2026-05-25T00:00:00"
  source: "telegram | live_note | voice_note | screenshot | operator_note | valprime_checkpoint"
  raw_note: "Short privacy-safe note or quote."
  category: "bug | confusion | delight | missing_feature | roadmap_idea | trust_safety | willingness_to_pay | reusable_pattern | client_only_detail"
  severity: "low | medium | high | blocker"
  user_value: "What the user needed or gained."
  reuse_potential: "none | low | medium | high"
  action_required: "none | investigate | fix | clarify_copy | add_to_roadmap | park | scope_paid"
  owner: "operator | product | engineering | support"
  status: "new | triaged | accepted | parked | fixed | closed | needs_followup"
  linked_milestone_doc_feature:
    - "MXX"
    - "DOCUMENT_LABELS_NAMING_CONVENTION_V0"
```

Field notes:

- `feedback_id`: stable reference for follow-up.
- `client_id`: required for client isolation.
- `raw_note`: short and privacy-safe by default.
- `category`: one primary category; add secondary tags only if needed.
- `severity`: blocker only if it breaks a protected founder-beta workflow or trust boundary.
- `reuse_potential`: high only if likely useful beyond one user.
- `action_required`: must not imply a promised timeline.
- `linked_milestone_doc_feature`: points to product docs or implementation tickets, not private facts.

---

## 6. Karen Week-1 Examples

These are sanitized examples. They should not include private legal facts, raw paths, chat IDs, document IDs, or detailed case history.

### "I Expected Val To Remember The Finca Number"

Likely category:

- confusion/friction
- trust/safety concern
- reusable pattern

Interpretation:
The user expects memory retrieval to connect a known topic to recognizable labels.

Possible action:

- improve document labels
- improve topic summary
- clarify when memory is missing versus present

### "I Want Reminders Before Lawyer Meetings"

Likely category:

- missing feature
- roadmap idea
- reusable pattern

Interpretation:
Pre-meeting prep and reminder timing may be a valuable workflow.

Possible action:

- add to roadmap
- wait for calendar/reminder safety review
- do not promise automation before tested

### "This Answer Was Too Robotic"

Likely category:

- confusion/friction
- product tone issue

Interpretation:
The content may be correct but not emotionally usable.

Possible action:

- polish copy
- shorten answer
- make response more read-aloud friendly

### "I Need To Upload Photos/Documents"

Likely category:

- missing feature
- willingness-to-pay signal if repeated/strong
- roadmap idea

Interpretation:
Document/photo ingestion may be high value, but high risk.

Possible action:

- capture as post-Tuesday candidate
- connect to OCR/manual-review path
- do not imply photos are understood until OCR/review exists

### "I Don't Trust Whether This Is Saved"

Likely category:

- trust/safety concern
- confusion/friction
- reusable pattern

Interpretation:
Val needs clearer save/confirmation/status language.

Possible action:

- improve confirmation copy
- explain where something was saved
- add source/status labels

---

## 7. Daily Review Loop

Run this loop during founder-beta week 1.

### 1. Capture

Collect feedback in a short structured form.

Rules:

- capture the product signal quickly
- mark source
- keep raw note privacy-safe
- do not paste sensitive legal facts into product docs

### 2. Classify

Assign:

- category
- severity
- user value
- reuse potential
- action required

Ask:

```text
Is this a bug, confusion, missing feature, trust issue, paid signal, or private case detail?
```

### 3. Decide

Choose one:

- fix now
- clarify copy
- add to roadmap
- park
- follow up
- scope as paid/client-driven
- ignore if not enough signal

### 4. Add To Roadmap / Parking Lot

Only add roadmap items when:

- they are reusable
- they have clear user value
- they do not violate safety/client isolation
- they are not just a one-off sensitive case detail

### 5. Follow Up With User

Close the loop simply:

```text
Esto lo marqué como prioridad de claridad: Val debe decir mejor si algo está guardado y dónde.
```

Do not promise:

```text
Eso estará listo mañana.
```

unless explicitly verified and scoped.

---

## 8. What Not To Do

- Do not treat every suggestion as a feature.
- Do not store sensitive case detail in product docs.
- Do not promise timelines from casual feedback.
- Do not let one user distort the whole product without pattern evidence.
- Do not convert Karen-only legal/admin details into reusable Val0 product facts.
- Do not treat willingness to use as willingness to pay unless the signal is explicit.
- Do not hide blockers because the feedback is emotionally positive.
- Do not ignore trust/safety concerns because the feature "mostly worked."
- Do not paste raw screenshots/transcripts into reusable docs by default.
- Do not use feedback from one client as context for another client.

---

## 9. Founder-Beta Success Metrics

Track signals, not vanity.

### Repeated Use

Does the user come back without being pushed?

Signals:

- asks again later
- uses the same workflow in real life
- requests next detail naturally

### Reduced Forgetting

Does Val help the user recover context?

Signals:

- "I had forgotten that"
- faster prep
- fewer scattered searches

### Trust In Memory

Does the user believe Val is honest about what it knows?

Signals:

- understands saved/review-needed status
- trusts OCR/manual-review caveat
- notices clear source/status language

### Calendar / Reminder Usefulness

Does agenda/reminder support reduce day-to-day friction?

Signals:

- `qué hago hoy` helps decide next step
- `qué tengo mañana` helps prepare
- stale/overdue items are not confusing

### Document / Case Organization Usefulness

Does Val make documents and legal/admin context easier to handle?

Signals:

- document list is readable
- review queue is useful
- meeting prep is easier
- chronology helps memory without legal conclusions

### Readiness To Pay / Continue

Does the user want to keep using Val after week 1?

Signals:

- asks for ongoing use
- says which workflow is worth paying for
- refers another potential user
- asks for setup beyond trial

---

## 10. Implementation Phases

### Phase 0: Design Only

Status:
This document.

No runtime behavior.

### Phase 1: Manual Feedback Log

Create a simple manual feedback log after Tuesday.

Requirements:

- privacy-safe notes
- `client_id`
- category
- severity
- action required
- status

Suggested storage:

- docs or ops note first
- no private case facts in product docs

### Phase 2: ValPrime Feedback Checkpoint Command

Create an operator-facing checkpoint pattern or command.

Goal:
Summarize current feedback and decisions without touching user runtime.

Output:

- new feedback count
- blockers
- top confusion
- top delight/value moment
- roadmap candidates
- parked items

### Phase 3: Structured Feedback File Per Client

Create a client-scoped structured feedback file.

Requirements:

- one file per founder client
- client-isolated
- privacy-aware
- link to milestones/features without copying sensitive details

### Phase 4: Product Roadmap Aggregation

Aggregate reusable feedback into product roadmap input.

Requirements:

- remove private facts
- group repeated patterns
- separate Val0 Personal from Val1 Business signals
- keep paid/custom signals scoped separately

### Phase 5: Privacy-Safe Cross-Client Pattern Library

Build a reusable pattern library only after multiple clients show similar needs.

Requirements:

- no raw client facts
- no private examples without sanitization
- source categories, not source identities
- product patterns only

---

## 11. Open Questions And Risks

### Open Questions

- Should the first manual feedback log live under `clients/karen`, `docs/ops`, or `docs/product`?
- What is the minimum useful feedback record without creating operator overhead?
- Who owns triage: operator, product, engineering, or ValPrime?
- How often should feedback be reviewed during week 1?
- What severity makes feedback a hotfix versus roadmap item?
- How should screenshots be referenced without storing private content?
- What is enough evidence to mark a pattern reusable?
- How should willingness-to-pay signals be validated?
- Should future founder users have the same feedback format as Karen?
- How should feedback link to benchmark/ETA logs?

### Risks

Feedback overload:
Too many small notes create noise.

Mitigation:
Daily triage and action-required field.

Privacy leakage:
Sensitive case details could enter product docs.

Mitigation:
Sanitize notes and keep private facts in client-scoped systems only.

Roadmap whiplash:
One user's wish could distort the product.

Mitigation:
Require reuse potential or explicit paid scope before major builds.

False urgency:
Emotional feedback may feel like a blocker when it is polish.

Mitigation:
Use severity definitions and protected workflow criteria.

Unclosed loop:
User gives feedback and never hears what happened.

Mitigation:
Use follow-up status and short user-facing closure.

Paid-signal confusion:
A user liking a feature may be mistaken for willingness to pay.

Mitigation:
Track willingness-to-pay only when explicit or behaviorally strong.

---

## 12. Product Principle

Founder-beta feedback is not a pile of comments. It is product evidence.

Good feedback capture:

- protects private details
- classifies signal clearly
- separates bugs from wishes
- identifies trust issues fast
- turns repeated patterns into roadmap
- parks one-off ideas without guilt

Bad feedback capture:

- stores raw private detail in product docs
- treats every request as a promise
- chases one user's every thought
- misses willingness-to-pay signals
- ignores confusion because the feature technically works

Operator line:

```text
No todo feedback es feature. Primero capturamos, clasificamos y decidimos: arreglar, aclarar, roadmap, parqueado o scope pagado.
```
