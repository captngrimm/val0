# FOUNDER_BETA_POST_TUESDAY_DECISION_MATRIX_V0

Purpose:
Decide what Val0 should build immediately after Karen Tuesday founder-beta delivery, what should wait for Karen feedback, what should stay doc-only, and what should remain parked.

This is a product decision document only. It is not runtime config, not a bot route, not a deployment plan, and not a promise that any lane is ready before Tuesday.

Tone:
Operator-ready, product-safe, practical, founder-beta focused.

---

## 1. Purpose

After Tuesday founder-beta delivery, Val0 needs focus.

The goal is to avoid building everything at once. The right next work should:

- protect Karen's working founder-beta baseline
- use real week-1 feedback
- improve clarity before adding automation
- prioritize read-only, source-aware, client-isolated memory
- avoid premature multi-client or business complexity

Decision rule:

```text
Build the smallest post-Tuesday improvements that make Karen's real pilot clearer, safer, and more useful.
```

---

## 2. Current Protected Baseline

### Karen Tuesday Founder-Beta Runtime Protected

The Tuesday delivery is protected.

Current protected workflows:

- `Val, qué eres`
- `Val, qué puedes hacer`
- `Val, qué documentos tengo`
- `Val, ordéname la cronología del caso`
- `Val, qué pasó en 2024`
- `Val, qué hago hoy`
- `Val, qué tengo mañana`
- `Val, prepárame para hablar con la abogada`

Do not destabilize these before Tuesday.

### Founder Offer Foundation Exists

The founder-beta offer has enough shape to explain:

- useful now, not final app
- no legal advice
- no autonomous actions
- no magic/infinite memory
- roadmap continues after Tuesday
- week-1 feedback drives next priority

### Memory Foundation Docs Exist

Recent design docs now cover:

- Carpetas / Topic Containers
- Document Labels / Naming Convention
- Unified Agenda / Single Day View
- Memory Library v1
- Conversational Memory Retrieval
- Memory Foundation Implementation Map

These docs are direction, not runtime readiness.

---

## 3. Decision Categories

### Build Immediately

Build after Tuesday if:

- it improves the existing pilot directly
- it is low or medium risk
- it is read-only or narrowly scoped
- it can be smoke-tested without external ambiguity
- it does not require changing core runtime routing before feedback is understood

### Build Only After Karen Feedback

Build after observing real use if:

- priority depends on what confused/helped Karen
- workflow value is plausible but not proven
- implementation may touch sensitive routes or response length
- feedback can decide between alternatives

### Keep Doc-Only For Now

Keep as design if:

- it is strategically important but too broad
- it needs lower-level foundation first
- it risks overpromising before implementation exists

### Park Until Later

Park if:

- it is interesting but not week-1 critical
- it adds complexity before the core pilot is validated
- it needs stronger architecture, permissions, or test coverage

### Do Not Build Unless Paid / Client-Driven

Require paid or explicit prospect demand if:

- it is business-specific
- it requires custom workflow execution
- it needs integrations, dashboards, migrations, or operator-heavy delivery
- it distracts from Val0 Personal founder-beta learning

---

## 4. Candidate Lanes

| Lane | User Value | Risk | Dependency | Effort | Build Now? | Reason |
|---|---|---|---|---:|---|---|
| Karen week-1 pilot feedback capture | Converts real use into product direction; prevents building from guesses. | Low | Tuesday delivery completed; feedback format shared. | 0.5-1 session | Yes | This is the safest highest-value next step. |
| Daily Operator polish | Makes `qué hago hoy` shorter, clearer, and more useful if feedback says it is long/confusing. | Medium | Karen feedback on Test 6; existing output behavior. | 1-2 sessions | Only after feedback | Polish should target real confusion, not imagined issues. |
| Unified agenda runtime v0 | Lets `qué tengo hoy/mañana` combine calendar, reminders, document review, and follow-ups. | Medium-high | Stable read-only calendar/reminder/document views; source labels. | 2-3 sessions | Not immediately | Good product value, but routing/source merge risk should wait until baseline feedback. |
| Document/photo ingestion runtime | Lets new documents/photos enter the system more naturally. | High | Safe intake, file handling, review status, OCR/manual-review boundary. | 3-5 sessions | No | Too risky before feedback and before read-only status clarity is stronger. |
| OCR/manual review path | Makes photos/screenshots useful while preserving honesty about unread content. | High | Document ingestion, OCR tooling/process, review queue, status labels. | 3-6 sessions | No | Important, but should follow source/status labels and a safe review queue. |
| Memory Library read-only inventory | Gives source-aware answers for documents, pending items, review-needed items, and topic summaries. | Medium | Existing document/reminder/context sources; client-scoped read model. | 1-2 sessions | Yes | Best bridge from current pilot to memory foundation with limited mutation risk. |
| Topic containers/carpetas commands | Allows Finca/Proyectos/Pendientes create/list/save flows. | Medium-high | Read-only memory inventory, labels, confirmation rules. | 2-4 sessions | Keep doc-only for now | Valuable, but mutation and routing should wait until read-only memory is stable. |
| Conversational memory retrieval v0 | Makes Val answer naturally from scoped memory. | High | Memory inventory, labels, topic containers, timeline/action status, router tests. | 3-6 sessions | Keep doc-only for now | Conversationality should sit on safe retrieval paths, not precede them. |
| Val1 business assessment execution | Tests business/professional value beyond personal founder-beta. | Medium-high | Clear paid/prospect scope; separate client isolation; offer definition. | 2-4 sessions | Do not build unless paid/client-driven | Avoid business buildout without a real prospect or paid scope. |
| Outreach execution | Helps find founder users/prospects and validate positioning. | Medium | Founder offer language; decision on target segment; operator bandwidth. | 1-2 sessions | Yes, lightly | Low-code/product learning path; should not distract from Karen feedback. |
| Multi-client onboarding v0 | Enables more testers beyond Karen. | High | Client identity resolver, onboarding boundaries, support model, privacy tests. | 3-6 sessions | Park until later | Too much risk before one founder-beta pilot is stable and supportable. |

---

## 5. Recommended First 3 Post-Tuesday Builds

### 1. Karen Week-1 Pilot Feedback Capture

Why first:

- highest signal
- lowest risk
- directly informs what to build next

Output:

- structured notes from Karen's feedback
- pass/fail/confusion by prompt
- top 3 next priorities

Smoke:

- feedback captured without private factual detail in reusable product docs
- clear list of what helped, confused, was too long, missing, and priority next

### 2. Memory Library Read-Only Inventory

Why second:

- improves document/review clarity
- builds toward labels, agenda, and conversational retrieval
- read-only limits blast radius

Output:

- source-aware inventory/read model
- clearer review-needed output
- client-scoped lookup requirement

Smoke:

- no cross-client leakage
- no raw IDs/paths in normal answer
- OCR/manual-review state visible
- no mutation from read-only prompts

### 3. Document Labels / Status / Source Fields

Why third:

- makes `qué documentos tengo` more readable
- supports review queue and future unified agenda
- helps Karen recognize documents without new folder sprawl

Output:

- human labels
- source labels
- status labels
- action labels where safe

Smoke:

- unread photo remains `requires OCR/manual review`
- readable document is not mislabeled
- labels do not imply legal conclusions
- debug/internal IDs hidden by default

Alternative:
If Karen's strongest feedback is Daily Operator length/confusion, swap Daily Operator polish into slot 2 or 3.

---

## 6. What Not To Touch Before Tuesday

Do not touch:

- `bot.py`
- runtime routing
- OAuth
- tokens
- systemd
- `/etc/val0`
- real client data
- memory database schema
- production documents
- real document storage
- OCR/external services
- multi-client onboarding
- business execution workflows

Do not promise:

- folders are ready
- unified agenda is ready
- OCR/photo reading is final
- conversational memory retrieval is active
- Val takes autonomous actions
- Val gives legal conclusions

Tuesday rule:

```text
No new runtime surface before founder-beta delivery unless explicitly scoped as a hotfix.
```

---

## 7. What Requires Karen Feedback First

Wait for Karen feedback before building:

- Daily Operator polish beyond tiny copy fixes
- unified agenda runtime v0
- detail drilldown behavior
- document naming preferences
- whether timeline provenance is too technical
- whether `qué tengo mañana` is useful enough
- whether lawyer/Nora prep needs more structure
- which missing workflow matters most

Feedback signals:

- `Me ayudó` = strengthen/keep
- `Me confundió` = route/copy/UX issue
- `Muy largo` = compacting/polish issue
- `Faltó` = candidate roadmap item
- `Prioridad próxima` = build-order input

Decision rule:

```text
If Karen does not feel the current answer yet, do not add a larger feature on top of it.
```

---

## 8. What Requires A Paying / Business Prospect First

Do not build unless paid or clearly client-driven:

- Val1 business assessment execution
- custom CRM/project workflows
- external dashboard/status portal
- team/multi-user permissions
- custom migrations
- bulk document cleanup
- custom integrations
- business outreach automation
- high-support onboarding
- role-based business memory

Reason:

These may be valuable, but they change support, privacy, and delivery shape. They should be scoped as Val1 Business or paid implementation work, not hidden inside Karen founder-beta.

---

## 9. Kill / Continue Criteria For Val0 After Founder-Beta

### Continue If

- Karen can understand what Val is
- at least 2-3 current workflows are useful
- document inventory/status is understandable
- Daily Operator or agenda helps decide what to do next
- Val stays honest about OCR/review limits
- no legal advice or unsupported automation is implied
- feedback identifies a clear next improvement
- operator support remains manageable

### Pause / Rebuild If

- basic prompts confuse more than help
- answers are too long despite compacting
- document inventory exposes technical/private details
- chronology invents or overstates facts
- agenda/reminder answers route incorrectly
- legal boundaries are unclear
- week-1 feedback points to wrong product shape
- support burden exceeds founder-beta value

### Park A Lane If

- risk is high and user value is still hypothetical
- it needs external services before core memory is stable
- it requires paid scope but no buyer exists
- it threatens Tuesday baseline or client isolation

Decision line:

```text
Continue Val0 when real use gets clearer. Pause any lane that makes Val sound bigger while becoming less trustworthy.
```

---

## 10. Open Questions

- Which feedback item should become the first post-Tuesday implementation ticket?
- Should read-only memory inventory happen before or after Daily Operator polish?
- What is the minimum useful "feedback capture" artifact: doc, issue list, or benchmark row?
- How many founder users should Val0 support before multi-client onboarding v0?
- What prospect signal is strong enough to start Val1 Business execution?
- Should outreach focus on personal founder users or business assessment leads first?
- What is the smallest safe OCR/manual review path that does not overpromise?
- Should document labels be persisted or computed in the first implementation?
- What smoke suite should be mandatory before any post-Tuesday runtime change?
- How should roadmap answers reflect post-Tuesday feedback without exposing private facts?

---

## 11. Operator Summary

Recommended post-Tuesday order:

1. Capture Karen week-1 feedback.
2. Build read-only memory inventory.
3. Improve document labels/source/status.
4. Polish Daily Operator only if feedback demands it.
5. Consider unified agenda after read-only sources are stable.
6. Keep carpetas and conversational memory doc-only until the retrieval foundation is safe.

Operator line:

```text
Después del martes, no construimos la app completa. Escuchamos el piloto, hacemos memoria visible y honesta, y solo después subimos a agenda, carpetas y conversación.
```
