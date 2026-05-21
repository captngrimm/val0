# FOUNDER_BETA_INTAKE_V0 — Val0

Purpose:
Convert an interested person/client into a clear founder-beta setup without guessing, overpromising, or building random features.

This intake helps decide:
- what the client needs
- what Val can do now
- which reusable capabilities apply
- what belongs in Month 1
- what must be deferred
- what the client should expect

---

## Core positioning

Val is not sold as a generic ChatGPT clone.

Val is a personalized operator that starts with simple useful workflows and grows with the client.

Promise:
- We begin with practical memory, lists, reminders, documents, ideas, and follow-up.
- We configure Val around the client’s life/business.
- We capture ideas and prioritize them.
- If a capability already exists, we adapt it faster.
- If something is new, it enters the roadmap; it is not an automatic promise.

Do not promise:
- full human-level conversation
- perfect voice
- full OCR/photo/barcode automation
- legal/medical/financial advice
- autonomous execution without review

---

## Intake stages

### Stage 1 — Identify client type

Ask:
1. Is this for personal life, business, legal/admin process, family, school, sales, operations, or something else?
2. Who will use Val? One person, family, team, employees, clients?
3. What language should Val use first?
4. What name should Val call the user?

Output:
- client_type
- primary_user
- language
- display_name

---

### Stage 2 — Find the first pain point

Ask:
1. What are you currently forgetting, losing, delaying, or repeating?
2. What causes the most stress or wasted time?
3. What do you wish someone would remind you about?
4. What do you currently manage in WhatsApp, notes, paper, Excel, memory, or screenshots?
5. What is one thing Val could help with this week that would feel useful?

Output:
- main_pain_point
- current_workaround
- week_1_value_target

---

### Stage 3 — Map to existing capabilities

Compare the client’s needs against CAPABILITY_REGISTRY.

Available base capabilities:

1. client_context_reader_v0
Use when:
- client wants to ask what Val can do
- client wants status/roadmap/next steps

2. client_ideas_v0
Use when:
- client gives ideas
- client wants improvement backlog
- client wants Val to remember future requests

3. grocery_list_v0 / item_list_v0 candidate
Use when:
- client wants grocery lists
- inventory
- products
- materials
- purchase tracking

4. reminders_agenda_v0
Use when:
- client needs reminders
- appointments
- follow-ups
- basic schedule support

5. document_inventory_v0 / carpeta_clara pattern
Use when:
- client has scattered documents
- legal/admin paperwork
- forms
- receipts
- case files

6. meeting_prep_package_v0 / nora pattern
Use when:
- client needs prep for lawyer, consultant, supplier, sales meeting, school meeting

Output:
- candidate_capabilities
- reusable_from
- adaptation_needed

---

### Stage 4 — Define Month 1 scope

Month 1 should be small enough to prove value.

Pick 1-3 starter workflows max.

Good Month 1 examples:
- remember and list important items
- track appointments and reminders
- organize documents for one process
- capture ideas and next actions
- prep for meetings
- create simple status summaries

Bad Month 1 examples:
- automate entire company
- OCR all documents perfectly
- connect every platform
- replace human judgment
- build custom CRM/ERP immediately

Output:
- month_1_scope
- not_in_scope
- success_criteria

---

### Stage 5 — Capture privacy/safety boundaries

Ask:
1. What should Val avoid storing?
2. Are there sensitive documents or topics?
3. Who is allowed to see summaries?
4. Should Val be conservative with legal/medical/financial topics?
5. What decisions must always remain human-reviewed?

Default:
- sensitive data stays client-specific
- no private client data goes into platform registry
- reusable capability descriptions must be abstracted
- Val does not provide legal/medical/financial advice as a professional

Output:
- privacy_notes
- human_review_required
- sensitive_boundaries

---

### Stage 6 — Client communication

Explain clearly:

“Val starts with a focused setup. We pick the first few workflows that will help you immediately. As you use it, we capture ideas, compare them with existing capabilities, and update your roadmap. Some things can be adapted quickly if they already exist. Other things go into later phases.”

Use this language:
- “captured”
- “under review”
- “candidate for roadmap”
- “planned”
- “deferred”
- “not in this sprint”

Avoid:
- “yes, it will do everything”
- “automatic”
- “perfect”
- “done tomorrow”
- “AI handles it all”

---

## Intake output template

After intake, create/update:

clients/<client_id>/CLIENT_PROFILE.md
clients/<client_id>/CLIENT_STATUS.md
clients/<client_id>/CLIENT_ROADMAP.md
clients/<client_id>/CLIENT_IDEAS.md
clients/<client_id>/CLIENT_CAPABILITIES.md

Recommended summary:

Client:
Primary use case:
Main pain point:
Week 1 value target:
Candidate capabilities:
Month 1 scope:
Deferred:
Privacy/safety boundaries:
Next action:

---

## Example: personal/legal/admin client

Client:
Karen

Primary use case:
Family land/legal-administrative process + personal operator.

Main pain point:
Losing track of documents, dates, case facts, lawyer prep, and everyday reminders.

Week 1 value target:
Help organize case context, prepare lawyer meeting, and remember simple personal tasks/lists.

Candidate capabilities:
- karen_legal_case_v0
- carpeta_clara_v0
- nora_lawyer_package_v0
- client_ideas_v0
- grocery_list_v0
- reminders_agenda_v0

Month 1 scope:
- legal/finca support
- document organization
- grocery/list add/list/delete
- ideas and roadmap questions
- basic reminders/agenda QA

Deferred:
- full OCR/photo analysis
- barcode/nutrition facts
- full ChatGPT-like conversation
- automatic legal conclusions

---

## Example: business/client candidate

Client:
Ángel or Roy

Primary use case:
Business operations / sales / supplier tracking / product submissions.

Main pain point:
To be confirmed by intake.

Possible week 1 value target:
Track products, suppliers, follow-ups, documents, and pending actions.

Candidate reusable capabilities:
- client_context_reader_v0
- client_ideas_v0
- item_list_v0 candidate from grocery_list_v0
- meeting_prep_package_v0 pattern
- document_inventory_v0 pattern

Month 1 possible scope:
- product/vendor list
- follow-up reminders
- meeting prep
- document checklist
- simple status summary

Deferred:
- full CRM
- API integrations
- automatic platform submission
- advanced analytics

---

## Decision rules

If the need is already similar to a sealed capability:
- mark as reusable candidate
- adapt carefully
- update client roadmap

If the need is new but valuable across clients:
- add to platform roadmap
- mark as reusable candidate
- do not promise immediate delivery

If the need is client-specific:
- keep in client roadmap only

If the need is risky or too broad:
- defer
- explain why
- suggest smaller first step

---

## Minimum viable founder-beta promise

“Val will start by helping you remember, organize, and follow up on a few important things. It will not do everything on day one. The value is that we configure it around your real workflows, keep a roadmap, and improve it based on what you actually use.”

