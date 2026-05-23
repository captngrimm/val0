# Conversational Router v1 Design

## Goal

Conversational Router v1 should make Val feel less brittle while preserving the deterministic tools that already work. The router classifies intent and chooses a safe route; deterministic handlers still own all actions, writes, confirmations, calendar operations, reminders, grocery updates, legal/finca flows, and memory storage.

## Current Routing Map Summary

Telegram registration currently routes commands before text, voice, and attachments. Text messages enter `handle_text`.

High-level `handle_text` order:

1. Technical paste guard.
2. Spam and idempotency guards.
3. Priority update and reminder action intercept.
4. Audit log.
5. Frank operator mode.
6. Karen Google Calendar delete priority gate.
7. Grocery/list priority gate.
8. Karen reminder/agenda/multi-intent shield, including pending Google Calendar appointment confirmation, agenda summary, anchored reminder, appointment save, and agenda windows.
9. Nora/attorney prep priority gate.
10. VFMS/document summary priority gate.
11. Completion loop.
12. Reminder creation gate.
13. Transcript guard.
14. Karen appointment, recent activity, document inventory, document query, summary, and semantic gates.
15. Karen case facts/status/lawyer package/next action/plan/questions/passive facts capture.
16. Pending bug/feedback/idea report.
17. Unified memory insertion/task capture.
18. Mode/group logic.
19. Final capability/document guard.
20. `_process_text_pipeline()` fallback.

High-level `_process_text_pipeline` order:

1. Slash and technical paste guard.
2. Client resolution and preference loading.
3. Early Karen agenda/capability gates.
4. Active Karen interrogator session gate.
5. Greeting/help/identity/capability deterministic replies.
6. Upper Karen agenda/reminder/calendar shields.
7. Grocery/capability/agenda anti-hijack shield.
8. Client context reader.
9. Karen intent router and legal/document onboarding gates.
10. Broader deterministic case/reminder/calendar/report/control handlers.
11. LLM/model path last.

Voice has a separate partial routing path, so v1 should first stabilize text routing and later bring voice into parity.

## Top 10 Routing Risks / Trust-Killers

1. Order dependence: small gate moves can silently hijack agenda/legal/grocery behavior.
2. Duplicate intent logic in `handle_text` and `_process_text_pipeline`.
3. Pending confirmations are scattered; short replies like `sí` can be stolen.
4. Memory insertion can happen before some late routing, risking accidental storage.
5. Group logic sits late in `handle_text`, after several DM-oriented guards.
6. Karen-specific legal copy and reusable agenda behavior coexist in `bot.py`.
7. Multiple normalizers exist with slightly different punctuation/accent behavior.
8. LLM fallback can answer operational/tool requests conversationally instead of routing safely.
9. Voice path can diverge from text path.
10. Calendar create/delete flows are high-trust and should not be touched by broad routing changes.

## Where Conversationality Should Sit

Conversationality should sit after hard safety guards and pending confirmations, but before generic memory insertion and LLM fallback.

Recommended placement:

1. Safety gates: slash bypass, technical paste guard, transcript/log guard, attachment boundaries.
2. Client resolution: `resolve_client_id(chat_id)` with no Karen fallback for unknown clients.
3. Pending confirmations: Google Calendar create/delete, reminder confirmation, transcript choice, report flows, next-action continuation.
4. Deterministic high-confidence routes: exact agenda, grocery, reminders, legal/finca, document, help, and identity flows.
5. Conversational Router v1 classification for ambiguous safe input.
6. Deterministic execution of the selected route.
7. Fallback response layer.
8. Generic memory insertion only when the route says storage is appropriate.

The router should not sit before technical paste, pending confirmations, or destructive/create/delete confirmations.

## Proposed Architecture

### Normalized Input

Create a shared normalized message object:

- raw text
- stripped text
- lowercase/accentless text
- Val-prefix removed text
- line count
- chat type
- client id
- technical-paste flags
- explicit command flags
- possible confirmation token

All router and deterministic gates should use this shared normalization over time.

### Safety And Technical Paste Guard

Safety runs first and can return immediately. Technical shell/code/log blocks should not be stored as case facts, agenda, grocery, legal memory, or generic memory unless the user explicitly asks for analysis.

### Client Resolution

Resolve client id once near entry:

- Known Karen chat resolves to `karen`.
- Unknown clients get an empty or neutral client id.
- User-facing vocatives come from `client_vocative`.
- No unknown client inherits Karen personality, calendar config, paths, or copy.

### Pending Action Confirmation

Introduce a pending-action registry conceptually, even if implementation starts by wrapping current dictionaries/functions:

- pending Google Calendar appointment confirmation
- pending Google Calendar delete confirmation
- pending reminder confirmation
- pending transcript choice
- pending next action
- pending bug/feedback/idea report

Short replies should be consumed by pending states before new intent classification.

### Deterministic High-Confidence Intents

Keep deterministic ownership for:

- Google Calendar create/delete confirmation and execution
- reminder creation/cancel/action
- agenda today/tomorrow/week/date lookup
- grocery add/list/delete
- legal/finca package, status, facts, missing review
- document inventory/query/summary/semantic lookup
- technical paste refusal
- help/identity/capability basics

### LLM-Assisted Intent Classification

LLM classification is allowed only when deterministic routes return unknown or ambiguous and the input is safe.

The classifier may return:

- intent
- confidence
- entities
- whether confirmation is needed
- suggested deterministic route
- brief rationale for logs/debug

The classifier must not execute tools, write memory, create events, delete events, create reminders, or mutate client files.

### Fallback Response Layer

Fallback should be conversational but bounded:

- If action-like and ambiguous, ask one short clarifying question.
- If it is smalltalk, answer naturally without claiming tool execution.
- If client-specific but client id is unknown, avoid Karen-specific language.
- If it may be technical output, ask the user to send it as output or say `Val, analiza este log`.

## Activation Policy

- Router starts in shadow mode.
- No writes or tools are executed by the LLM.
- Deterministic handlers keep ownership of actions.
- Destructive/create/delete flows stay behind explicit confirmation.
- Router predictions are compared against actual consumed handlers before enabling live routing.
- Live routing starts only for low-risk fallback/clarification intents.

## Minimum Viable Implementation Plan

Commit 1: add `core/conversation_router.py`

- Add normalized input model and deterministic intent enum.
- Add pure classification functions with no side effects.
- Add tests/smokes for normalization and safe classification.
- No runtime behavior change.

Commit 2: shadow mode in `bot.py`

- Call router after safety/client resolution and pending confirmations.
- Log predicted intent versus actual consumed handler.
- Do not route based on the prediction yet.
- Compile, audit, and smoke current deterministic flows.

Commit 3: enable low-risk fallback routing

- Use router only for safe fallback outcomes: smalltalk, help, clarify, unknown.
- Do not route Google Calendar create/delete, reminders, legal writes, grocery writes, document mutation, or memory writes through LLM classification.
- Keep deterministic handlers as the only action executors.

## Required Smoke Tests

- Technical paste: `cd /opt/val0 && git status`, `git status`, `systemctl status val0-bot.service`, multiline heredoc.
- Pending confirmations: Google Calendar create yes/no, Google Calendar delete yes/no, reminder confirmation yes/no.
- Agenda: today, tomorrow, week, specific date, `mi agenda`.
- Grocery: add, list, delete, delete shortcut.
- Legal/finca: package for Nora, missing review, finca facts, document inventory.
- Memory safety: command paste is not stored; ambiguous text is not forced into a task.
- Unknown client: no Karen vocative, no Karen calendar/config/path leakage.
- Voice parity audit: verify voice path still reaches Karen appointment/legal basics before any voice router work.
- Regression: `py_compile`, client isolation audit, and deterministic handler smoke tests.

## Do Not Do

- Do not rewrite the whole bot.
- Do not replace working Google Calendar create/delete flows.
- Do not let the LLM directly execute tools or writes.
- Do not move memory insertion earlier.
- Do not make unknown clients inherit Karen profile/copy.
- Do not broaden audit allowlists to hide reusable violations.
- Do not use conversational routing for destructive actions without deterministic confirmation.
- Do not merge voice/text routing until text v1 is stable.
- Do not touch OAuth, tokens, systemd, `/etc/val0`, or real client data as part of router work.
