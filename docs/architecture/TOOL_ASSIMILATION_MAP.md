# Val0 Tool Assimilation Map

## Purpose

Val0 should not reinvent every layer. The product should keep the parts that create durable differentiation and assimilate commodity tools where they improve speed, reliability, or leverage without weakening client privacy, source-of-truth rules, or deterministic confirmation layers.

## Current Core Stack

| Layer | Current Tooling | Role |
| --- | --- | --- |
| Val0 backend | Python Telegram bot, local memory, deterministic handlers | Product core, client routing, reminders, agenda, legal/finca flows, operator behavior |
| Telegram | Telegram bot interface | Primary user interface for current MVP |
| Memory | Local encrypted memory/db and client files | Source of truth for client context and operational state |
| Custom operator logic | `bot.py`, `core/*`, quality scripts | Deterministic execution, guardrails, routing, audits |
| Codex | API/CLI coding collaborator | Code changes, refactors, repo analysis, tests, documentation |
| Launchpad | Server verification/recovery workflow | Runtime checks, logs, service state, recovery plans |
| ValPrime | Checkpoints/operator continuity | Continuity across sessions, priorities, operating memory |

## Candidate Tools To Evaluate

| Candidate | Use Case | Status |
| --- | --- | --- |
| Codex IDE/CLI/Cloud | Engineering tasks, repo refactors, PR-style changes, background work | Evaluate deeper workflow fit |
| Lovable / Bolt / v0 / Replit | Dashboard and client portal prototypes | Evaluate before hand-building dashboards |
| n8n / Make / Zapier | Workflow automation, intake, notifications, integrations | Evaluate with non-sensitive test payloads first |
| GitHub Actions | Compile, audit, smoke tests, quality gates | Good near-term candidate |
| Codex review | PR review and regression-risk checks | Evaluate after CI gates exist |
| Future vector DB/document tools | Retrieval, document search, embeddings, OCR workflows | Placeholder only; needs privacy and source-of-truth review |

## Build-vs-Buy Rule

Build only where Val0 has product differentiation:

- client-aware routing and memory boundaries
- deterministic confirmation layers for calendar/legal/reminder actions
- operator personality and continuity
- privacy-preserving client context
- source-of-truth orchestration

Assimilate or integrate where the capability is commodity:

- dashboard scaffolding
- CI/check automation
- simple workflow automation
- generic admin/internal tools
- prototype UI surfaces
- non-sensitive integration plumbing

## Tool Decision Matrix

| Area | Val0 Keeps | External Tools Handle | Needs Experiment | Risk/Cost | First Test |
| --- | --- | --- | --- | --- | --- |
| Telegram assistant core | Intent ownership, deterministic execution, memory boundaries | None for runtime core | Conversation router shadow mode | High trust risk if outsourced | Keep in Val0 |
| Calendar/legal/reminders | Confirmation layer, client identity, audit trail | Optional notification plumbing later | Whether workflow tools can trigger safe intake only | High privacy/action risk | Read-only or test-only webhook |
| Client dashboard | Data ownership, API contract, auth rules | UI prototype generation | Lovable/v0/Bolt/Replit output quality | Medium; risk of duplicated state | Prototype Karen dashboard against fake data |
| Workflow automation | Final approval and source-of-truth updates | n8n/Make/Zapier intake, routing, notifications | Webhook reliability and privacy posture | Medium; SaaS data exposure | Test webhook with dummy payload |
| Quality gates | Test definitions, audit policy | GitHub Actions runs checks | CI speed and secrets handling | Low/medium | Compile + audit + router smoke |
| Engineering work | Architecture decisions and review | Codex IDE/CLI/Cloud task execution | Cloud task workflow and PR quality | Medium; repo access/approval | Small doc/test PR |
| Document retrieval | Client boundaries and final answers | Possible vector DB/OCR tooling | Privacy, cost, accuracy, local vs SaaS | High until reviewed | Placeholder only |

## First Experiments

### E1: n8n Webhook Intake

Goal: prove an external workflow can send a safe, non-sensitive event into Val0 or a test endpoint.

First test:

- create a dummy webhook payload
- route it to a test endpoint or Telegram test chat
- do not mutate memory, calendar, legal data, or client files
- log only safe metadata

Success criteria:

- predictable delivery
- clear failure behavior
- no client data exposure
- no automatic action execution

### E2: Lovable/v0 Karen Dashboard Prototype

Goal: test whether an AI app builder can quickly prototype a Karen client dashboard without hand-building UI first.

First test:

- use fake/sample data only
- prototype agenda, grocery, documents, and case summary views
- identify API/data contract Val0 would need
- do not connect to real memory or client files

Success criteria:

- useful layout within one short iteration
- no one-off UI debt forced into Val0 backend
- clear path to replace fake data with controlled API later

### E3: GitHub Action Quality Gate

Goal: run the core checks automatically.

First test:

- `./scripts/val0py -m py_compile bot.py core/conversation_router.py scripts/quality/client_isolation_audit.py`
- `python3 scripts/quality/client_isolation_audit.py`
- `./scripts/val0py scripts/quality/conversation_router_smoke.py`

Success criteria:

- no secrets required
- clear pass/fail output
- can run on PRs or protected branches

### E4: Codex Cloud Task / PR Workflow

Goal: evaluate Codex Cloud for bounded repo tasks.

First test:

- assign a small doc or smoke-test change
- require a branch/PR
- review diff, tests, and audit output

Success criteria:

- small, reviewable changes
- no broad refactors
- respects client isolation and AGENTS.md guardrails

## Source-of-Truth Rules

- Val0 memory/client files remain authoritative unless a future architecture explicitly changes that.
- External tools may hold temporary prototype data or non-sensitive test payloads.
- Any persistent external copy of client state requires privacy review, source-of-truth ownership, and deletion rules.
- External automation may suggest or enqueue actions, but Val0 confirmation layers decide execution.

## Do Not Do

- Do not move core client memory into random SaaS without privacy review.
- Do not let external automation mutate calendar/legal data without the Val0 confirmation layer.
- Do not duplicate Val0 client state across tools without source-of-truth rules.
- Do not build dashboards manually until AI app builders are evaluated.
- Do not connect real OAuth tokens, calendar data, legal data, or client files to prototype tools.
- Do not use external tools to bypass client identity, client isolation, compile checks, audit checks, or smoke tests.
