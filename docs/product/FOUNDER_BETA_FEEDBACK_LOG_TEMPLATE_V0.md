# FOUNDER_BETA_FEEDBACK_LOG_TEMPLATE_V0

Purpose:
Reusable feedback log template for Karen week-1 founder-beta and future founder users.

This is a docs/template artifact only. It is not runtime config, not a bot route, not a feedback database schema, and not a promise that feedback automation is implemented.

Tone:
Operator-ready, privacy-safe, practical, reusable.

---

## 1. Purpose

Use this template to capture founder-beta feedback in a consistent way.

It should help separate:

- bugs
- confusion/friction
- delight/value moments
- missing features
- roadmap ideas
- trust/safety concerns
- willingness-to-pay signals
- reusable product patterns
- client-only case details

Goal:

```text
Capture feedback as product evidence without leaking private case details or turning every comment into a promised feature.
```

---

## 2. How To Use This Template

Use one feedback record per clear signal.

Good record:

- one prompt/workflow
- one main issue or value moment
- one primary category
- clear action required
- privacy-safe wording

Avoid:

- dumping a whole transcript
- storing sensitive legal/case facts
- combining five unrelated comments into one record
- promising a delivery date in the feedback record
- using Karen-specific facts as reusable product truth

Workflow:

1. Capture raw note quickly.
2. Clean/sanitize summary.
3. Classify category/severity/reuse potential.
4. Decide action required.
5. Assign owner/status.
6. Add follow-up question if needed.
7. Link to milestone/doc/feature if useful.

---

## 3. Feedback Record Format

Copy this block for each feedback item.

```yaml
feedback:
  feedback_id: "fb_YYYYMMDD_001"
  client_id: "client_alias_or_id"
  date_time: "YYYY-MM-DDTHH:MM:SS"
  source: "telegram | live_note | voice_note | screenshot | operator_note | valprime_checkpoint"
  raw_note: "Short privacy-safe quote or note."
  cleaned_summary: "Product-safe summary without sensitive case detail."
  category: "bug | confusion_friction | delight_value | missing_feature | roadmap_idea | trust_safety | willingness_to_pay | reusable_pattern | client_only_case_detail"
  severity: "blocker | high | medium | low | note"
  user_value: "What the user needed, gained, lost, or expected."
  reuse_potential: "Karen-only | likely reusable | product pattern | business/Val1 pattern"
  trust_safety_impact: "none | low | medium | high"
  action_required: "none | investigate | fix | clarify_copy | add_to_roadmap | park | scope_paid | follow_up"
  owner: "operator | product | engineering | support | TBD"
  status: "new | triaged | accepted | parked | fixed | closed | needs_followup"
  linked_milestone_doc_feature:
    - "MXX"
    - "DOC_OR_FEATURE_NAME"
  follow_up_question: "Optional one-question follow-up for the user."
```

Short markdown version:

```text
Feedback ID:
Client ID:
Date/time:
Source:
Raw note:
Cleaned summary:
Category:
Severity:
User value:
Reuse potential:
Trust/safety impact:
Action required:
Owner:
Status:
Linked milestone/doc/feature:
Follow-up question:
```

---

## 4. Category Definitions

### Bug

Something expected to work did not work.

Examples:

- wrong route
- broken answer
- agenda query answered as documents
- document inventory missing expected status

### Confusion / Friction

The system may work, but the user does not understand it or it feels hard.

Examples:

- too long
- too technical
- unclear save status
- unclear roadmap versus ready

### Delight / Value Moment

The user experiences relief, usefulness, or trust.

Examples:

- "This helps me know what to do."
- "This saved me from searching."
- "This made the meeting easier."

### Missing Feature

The user expected something that is not ready or not built.

Examples:

- upload photos/documents
- OCR
- unified agenda
- folders/carpetas

### Roadmap Idea

A useful idea that may belong later, but is not necessarily urgent.

Examples:

- family/shared folders
- richer project memory
- dashboard/status view

### Trust / Safety Concern

Anything that affects trust, privacy, correctness, legal boundary, or user confidence.

Examples:

- "I don't trust whether this was saved."
- "Is this legal advice?"
- "Where did this information come from?"

### Willingness-To-Pay Signal

Evidence that a user may pay, continue, refer, or request setup.

Examples:

- "I would pay for this if reminders worked."
- "Can you set this up for my business?"
- "I need this every week."

### Reusable Pattern

Feedback likely useful across founder users.

Examples:

- clearer document labels
- honest OCR/review status
- compact Daily Operator
- pre-meeting checklist

### Client-Only Case Detail

Sensitive, client-specific detail that should not become product documentation.

Examples:

- private legal facts
- family/legal details
- detailed chronology
- raw document contents

Rule:
Do not store sensitive case detail in this product feedback template. Keep it in approved client-scoped systems only when explicitly needed.

---

## 5. Severity Scale

### Blocker

Breaks delivery, trust, privacy, legal boundary, or a protected core workflow.

Examples:

- bot unavailable
- cross-client data leakage
- legal conclusion presented as fact
- raw technical/private data exposed

### High

Major workflow failure or serious confusion, but demo/pilot can continue with fallback.

Examples:

- agenda route repeatedly wrong
- document inventory too technical to use
- response undermines trust in memory

### Medium

Meaningful friction that should be addressed after triage.

Examples:

- answer too long
- status wording unclear
- user unsure what to ask next

### Low

Small polish issue or minor preference.

Examples:

- tone slightly stiff
- heading could be clearer
- example wording could be warmer

### Note

Observation, idea, or product signal without immediate action.

Examples:

- "She liked checklist format."
- "Potential future family folder idea."

---

## 6. Reuse Potential Scale

### Karen-Only

Specific to Karen/client-zero context, sensitive case details, or one-off workflow.

Action:
Keep scoped; do not generalize without pattern evidence.

### Likely Reusable

Could help other Val0 Personal founder users, but needs more evidence.

Action:
Track and look for repeats.

### Product Pattern

Clearly reusable across Val0 Personal.

Action:
Add to product roadmap or implementation candidates.

### Business / Val1 Pattern

Likely more relevant to teams, client workflows, paid implementation, or business operations.

Action:
Do not hide inside Val0 Personal; scope separately.

---

## 7. Example Feedback Entries For Karen

These are sanitized examples. Do not add private legal facts, raw paths, chat IDs, document IDs, or detailed case history.

### Calendar Usefulness

```yaml
feedback:
  feedback_id: "fb_20260526_001"
  client_id: "karen_client_zero"
  date_time: "2026-05-26T09:00:00"
  source: "live_note"
  raw_note: "She said tomorrow agenda helped her prepare."
  cleaned_summary: "Tomorrow agenda created clear preparation value."
  category: "delight_value"
  severity: "note"
  user_value: "Reduced uncertainty about next-day preparation."
  reuse_potential: "likely reusable"
  trust_safety_impact: "none"
  action_required: "add_to_roadmap"
  owner: "product"
  status: "new"
  linked_milestone_doc_feature:
    - "UNIFIED_AGENDA_SINGLE_DAY_VIEW_V0"
  follow_up_question: "What part of the agenda answer helped most?"
```

### Finca Memory Trust

```yaml
feedback:
  feedback_id: "fb_20260526_002"
  client_id: "karen_client_zero"
  date_time: "2026-05-26T09:10:00"
  source: "telegram"
  raw_note: "Expected Val to remember the finca number."
  cleaned_summary: "User expected topic memory to connect Finca to recognizable labels."
  category: "trust_safety"
  severity: "medium"
  user_value: "Trust that Val remembers important labels and can retrieve them."
  reuse_potential: "product pattern"
  trust_safety_impact: "medium"
  action_required: "add_to_roadmap"
  owner: "product"
  status: "new"
  linked_milestone_doc_feature:
    - "MEMORY_LIBRARY_V1_DESIGN"
    - "CONVERSATIONAL_MEMORY_RETRIEVAL_V0"
  follow_up_question: "What label would make this easiest to recognize?"
```

### Document Upload / OCR Expectation

```yaml
feedback:
  feedback_id: "fb_20260526_003"
  client_id: "karen_client_zero"
  date_time: "2026-05-26T09:20:00"
  source: "live_note"
  raw_note: "Wants to upload photos/documents."
  cleaned_summary: "User expects easier document/photo intake, with clear OCR/manual-review status."
  category: "missing_feature"
  severity: "medium"
  user_value: "Reduce manual effort to capture documents."
  reuse_potential: "product pattern"
  trust_safety_impact: "medium"
  action_required: "add_to_roadmap"
  owner: "product"
  status: "new"
  linked_milestone_doc_feature:
    - "DOCUMENT_LABELS_NAMING_CONVENTION_V0"
  follow_up_question: "Would upload be useful even if Val clearly marks OCR/review needed?"
```

### Answer Too Robotic

```yaml
feedback:
  feedback_id: "fb_20260526_004"
  client_id: "karen_client_zero"
  date_time: "2026-05-26T09:30:00"
  source: "operator_note"
  raw_note: "Answer felt robotic."
  cleaned_summary: "Response tone was technically correct but not warm/read-aloud friendly."
  category: "confusion_friction"
  severity: "low"
  user_value: "Clearer and warmer answers are easier to trust and use."
  reuse_potential: "likely reusable"
  trust_safety_impact: "low"
  action_required: "clarify_copy"
  owner: "product"
  status: "new"
  linked_milestone_doc_feature:
    - "KAREN_FINAL_DELIVERY_PACK_V0"
  follow_up_question: "Was it too long, too technical, or just cold?"
```

### Reminder Usefulness

```yaml
feedback:
  feedback_id: "fb_20260526_005"
  client_id: "karen_client_zero"
  date_time: "2026-05-26T09:40:00"
  source: "live_note"
  raw_note: "Wants reminders before lawyer meetings."
  cleaned_summary: "Pre-meeting reminder flow may be valuable if reliable and clearly scoped."
  category: "roadmap_idea"
  severity: "medium"
  user_value: "Helps prepare before important meetings."
  reuse_potential: "product pattern"
  trust_safety_impact: "medium"
  action_required: "add_to_roadmap"
  owner: "product"
  status: "new"
  linked_milestone_doc_feature:
    - "UNIFIED_AGENDA_SINGLE_DAY_VIEW_V0"
  follow_up_question: "How much advance notice would be useful?"
```

### Roadmap Expectation

```yaml
feedback:
  feedback_id: "fb_20260526_006"
  client_id: "karen_client_zero"
  date_time: "2026-05-26T09:50:00"
  source: "telegram"
  raw_note: "Asked when folders/photos will be ready."
  cleaned_summary: "User wants clear distinction between ready, next, planned, and later."
  category: "confusion_friction"
  severity: "medium"
  user_value: "Trust through realistic roadmap expectations."
  reuse_potential: "likely reusable"
  trust_safety_impact: "medium"
  action_required: "clarify_copy"
  owner: "product"
  status: "new"
  linked_milestone_doc_feature:
    - "ROADMAP_ANSWER_MODE_V0"
  follow_up_question: "Which roadmap item matters most for week 2?"
```

---

## 8. Daily Review Process

### 1. Collect

Gather feedback from:

- Telegram
- live notes
- screenshots
- voice notes
- operator notes
- ValPrime checkpoints

### 2. Classify

Assign:

- category
- severity
- reuse potential
- trust/safety impact

### 3. Decide

Choose action:

- fix
- investigate
- clarify copy
- add to roadmap
- park
- scope paid
- follow up
- no action

### 4. Assign

Set:

- owner
- status
- linked milestone/doc/feature

### 5. Checkpoint

At the end of each founder-beta day, summarize:

- blockers
- top confusion
- top value moment
- trust/safety concerns
- roadmap candidates
- parked items

### 6. Follow Up

Ask one useful follow-up when needed.

Example:

```text
Cuando dijiste que no sabías si estaba guardado, querías ver la carpeta, el documento, o una confirmación más clara?
```

---

## 9. Rules

- Do not store sensitive legal facts in product feedback docs.
- Separate product feedback from case memory.
- Do not promise delivery dates from raw feedback.
- Do not let one-user feedback become global without pattern evidence.
- Do not copy raw transcripts/screenshots into reusable product docs by default.
- Do not mix feedback across clients without privacy-safe aggregation.
- Do not treat "I like this" as willingness to pay unless the signal is explicit or behaviorally strong.
- Do not bury trust/safety concerns under polish.
- Do not turn Karen-only details into default product behavior.

Safe line:

```text
Lo capturo como feedback, no como promesa de entrega.
```

---

## 10. Open Questions

- Where should the first actual Karen feedback log live: `clients/karen`, `docs/ops`, or another client-scoped location?
- Should feedback IDs be manual or generated by a helper later?
- What is the minimum daily checkpoint format?
- Who owns triage after Tuesday: operator, product, engineering, or ValPrime?
- What severity threshold creates a hotfix?
- How should screenshots be referenced without storing private content?
- When does a likely reusable signal become a product pattern?
- How should feedback link to benchmark/ETA logs?
- Should future founder users receive the same feedback categories?
- How should business/Val1 patterns be separated from Val0 Personal feedback?
