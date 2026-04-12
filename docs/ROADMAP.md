=====================================================================
VALERIA — COGNITIVE OPERATIONS SYSTEM
=====================================================================

Operational Roadmap
Last Updated: 2026-03-29 (Final Consolidated + TRL Integrated)

=====================================================================
MISSION
=====================================================================

Valeria is a multi-layer cognitive operations system composed of:

- Val0 (VPS) → user-facing deterministic execution layer
- ValPrime (Forge) → state, PM, and processing layer
- Cockpit (ChatGPT) → design and code generation

The system enables deterministic execution, structured memory,
and advisory intelligence without compromising data integrity.

=====================================================================
PRINCIPLE
=====================================================================

Deterministic core first
State + processing second
Advisory reasoning third
Personality last

Revenue stability first
Operational reliability second
Expansion third

=====================================================================
SYSTEM PHILOSOPHY
=====================================================================

Valeria is NOT a chatbot-first system.

Valeria is:

1. deterministic storage
2. deterministic retrieval
3. deterministic execution
4. state awareness (Forge)
5. externalized processing
6. advisory reasoning (non-authoritative)
7. controlled rendering last

LLM rules:

MAY:
- summarize
- phrase
- suggest
- analyze

MAY NOT:
- create facts
- mutate canonical records
- alter deadlines/reminders
- override DB truth
- write to memory

LLM is:
- last-stage
- non-authoritative
- non-mutating

=====================================================================
TRUTH & RELIABILITY LAYER (TRL)
=====================================================================

Purpose:

Prevent assumption drift, enforce verification-first behavior,
and maintain strict adherence to user constraints.

---------------------------------------------------------------------
Core Rules
---------------------------------------------------------------------

Advisory layers (ValPrime + Cockpit) MUST:

- verify before concluding when verification is possible
- explicitly label:
  - FACT
  - UNKNOWN
  - INFERENCE
- avoid converting inference into fact
- prefer uncertainty over incorrect certainty
- avoid answering before sufficient evidence is available

---------------------------------------------------------------------
Prohibited Behaviors
---------------------------------------------------------------------

- assumption-based conclusions presented as facts
- momentum-driven reasoning without verification
- ignoring user-defined response constraints
- repeated apology without behavioral correction

---------------------------------------------------------------------
Instruction Lock (Constraint Enforcement)
---------------------------------------------------------------------

User-defined constraints must be treated as session-level rules.

Examples:

- response format
- language
- step-by-step mode
- verbosity limits

These MUST:

- persist throughout the session
- override default model tendencies
- not degrade over time

---------------------------------------------------------------------
Error Memory
---------------------------------------------------------------------

When a correction occurs:

- system must store:
  - type of error
  - context
  - corrected version

Goal:

Reduce recurrence of identical failure patterns.

---------------------------------------------------------------------
Answer Gating
---------------------------------------------------------------------

Before producing a response, Valeria must internally evaluate:

- Do I know this or am I inferring?
- Can this be verified?
- Is this high-risk or low-risk?
- Am I respecting user constraints?

If uncertainty is high:

- ask instead of conclude

=====================================================================
SYSTEM ARCHITECTURE (CURRENT REALITY)
=====================================================================

Val0 (VPS) — Execution Layer

Responsibilities:

- Telegram bot interface
- deterministic command execution
- case management
- email delivery
- routing to Forge

Constraints:

- must remain lightweight
- no heavy processing
- fast response priority
- canonical source of truth


ValPrime (Forge) — PM + State + Processing Layer

ValPrime is the execution brain of the system.

Responsibilities:

- roadmap + tasks + notes (operational truth)
- current state tracking
- next-action generation
- drift detection
- ingestion processing (audio, notes, events)
- transcription + summarization
- structured extraction (tasks, deadlines, entities)
- classification + routing
- advisory reasoning (non-authoritative)
- embeddings (future)

Constraints:

- does NOT mutate Val0 canonical records
- outputs advisory action packets only
- handles all heavy processing
- maintains persistent operational context


Cockpit (ChatGPT)

- architecture design
- code generation
- debugging
- system planning

=====================================================================
CURRENT STATE — VERIFIED
=====================================================================

Val0:

- Telegram interaction stable
- email sending working (Resend)
- document generation working
- onboarding basic (name/email capture)
- multi-user separation working
- deterministic flows intact

Forge:

- Ubuntu installed
- remote access (SSH + Tailscale)
- ops workspace initialized (valeria_ops)
- architecture + roadmap defined
- ready for ValPrime bring-up

System:

- separation of concerns established
- VPS vs Forge roles defined
- deployment pipeline manual but stable

=====================================================================
EXECUTION LOOP (CORE BEHAVIOR)
=====================================================================

The system operates as a continuous loop:

1. Capture:
   - user input (commands, notes, audio)

2. Process (ValPrime):
   - interpret input
   - classify
   - extract structured data

3. State Update:
   - update notes.md (if applicable)
   - update done_log.md (explicit only)
   - update current_state.md (deterministic only)
   - never update tasks.md without explicit confirmation

4. Evaluate:
   - compare state vs roadmap
   - detect drift
   - determine next action

5. Output:
   - generate advisory packet
   - return to Val0 or user

Rules:

- loop must be deterministic where possible
- advisory reasoning must remain non-authoritative
- state must remain consistent across iterations

=====================================================================
PHASE 1 — VALPRIME CORE (CURRENT)
=====================================================================

Goal:
Activate Forge as a functional PM + state layer

Structure:

~/valeria_ops/
- roadmap.md
- tasks.md
- notes.md
- architecture.md
- current_state.md
- done_log.md

/opt/valprime/ask.py

Capabilities:

- read roadmap + tasks + notes
- maintain current_state.md
- track completed actions (done_log.md)
- track active focus
- return:
  - current priorities
  - pending tasks
  - next concrete action
  - drift warning (if any)

Output MUST include:

- current focus
- what was just done
- what is pending
- next action (explicit, executable)
- optional drift signal

Definition of Done:

python3 /opt/valprime/ask.py "what should I be doing?"

Output is actionable and consistent.

=====================================================================
PHASE 1.5 — STATE CONSOLIDATION
=====================================================================

Goal:
Establish reliable operational continuity

Components:

- current_state.md
- done_log.md
- tasks.md (active tracking)

Capabilities:

- track last completed actions
- track current focus
- maintain session continuity
- provide consistent answers:
  - what did I do
  - what am I doing
  - what should I do next

Constraints:

- simple structure
- deterministic
- no embeddings
- no LLM dependency required

Definition of Done:

System answers consistently across sessions
without losing context.

=====================================================================
PHASE 1.6 — CONTEXT GRAPH (MIND MAP LAYER)
=====================================================================

Goal:
Enable structured idea navigation and context recovery

Purpose:

Prevent loss of ideas due to linear chat structure
and allow fast retrieval of conceptual context.

Architecture:

Val0 / ValPrime (SQLite):

- nodes table
- edges table

Schema:

nodes:
- id
- title
- tags
- created_at
- last_accessed

edges:
- id
- from_node
- to_node
- type

Capabilities:

- store key ideas as nodes
- link related concepts
- enable retrieval via:
  - similarity
  - recency
  - connection strength

User Commands:

- "where were we"
- "resume topic X"

Output:

System proposes top 2–4 likely contexts

Constraints:

- deterministic storage
- no automatic hallucinated linking
- links must be explicit or validated

UI Layer (External):

- Obsidian used as visualization layer
- markdown-based node representation
- graph view used for human navigation

Definition of Done:

User can recover context without scrolling chat

=====================================================================
PHASE 1.7 — PM LOOP (CRITICAL)
=====================================================================

Goal:
Convert ValPrime from passive state system → active project manager

Responsibilities:

ValPrime must:

always know:
current focus
next action
priority order
enforce:
focus discipline
task sequencing
roadmap alignment
Capabilities:

When user inputs ANYTHING:

ValPrime must classify:

1) Is this aligned with current focus?
2) Is this a distraction?
3) Is this a future-phase idea?
4) Is this critical now?
Output Behavior:

ValPrime must respond with:

- Current focus
- Evaluation of input
- Decision:
    - DO NOW
    - DEFER
    - DISCARD
- Next action (explicit)
Example:

User:

“let’s work on personality system”

ValPrime:

Current focus: Session memory

Evaluation:
Personality system = valid but Phase 6

Decision:
DEFER

Next action:
Implement session memory storage (step 1)
Constraints:
must follow roadmap strictly
must not reorder phases without explicit user override
must enforce discipline over creativity
Definition of Done:

User cannot drift without being corrected

System always provides next action without being asked

=====================================================================
STATE AUTHORITY (VALPRIME)
=====================================================================

ValPrime maintains operational state of execution.

State is derived from:

- tasks.md
- current_state.md
- done_log.md

State represents:

- what is currently being worked on
- what has been completed
- what is pending

Rules:

- state must be internally consistent
- state must not contradict done_log.md
- state must not assume completion without explicit confirmation
- state is advisory but must remain deterministic

Hierarchy:

- roadmap.md → defines plan
- state files → define execution reality
- Val0 → defines canonical external truth

=====================================================================
WRITE AUTHORITY RULES
=====================================================================

File Ownership:

- tasks.md → updated only via explicit user commands
- current_state.md → updated by ask.py
- done_log.md → append-only via ask.py
- roadmap.md → read-only (manual updates only)
- architecture.md → read-only

ask.py MUST NOT:

- rewrite roadmap.md
- modify architecture.md
- infer completed tasks without explicit confirmation
- delete or overwrite done_log.md entries

Principle:

All persistent state mutations must be:

- explicit
- traceable
- deterministic

No silent inference is allowed for state changes.

=====================================================================
RESPONSE DISCIPLINE RULE
=====================================================================

All responses must prioritize:

1. correctness over speed  
2. verification over assumption  
3. clarity over completeness  
4. adherence over improvisation  

Failure to meet these criteria must be treated as system degradation.

=====================================================================
COMPLETION RULE
=====================================================================

A task is considered DONE only when:

- explicitly marked by user
- OR confirmed via explicit command

NO automatic completion inference allowed.

=====================================================================
CONFLICT RULE
=====================================================================

If ValPrime suggestion conflicts with Val0 state:

- Val0 canonical data ALWAYS wins
- ValPrime must mark suggestion as advisory
- ValPrime must never assume authority

=====================================================================
PHASE 2 — MP3 INGESTION + STRUCTURED PROCESSING
=====================================================================

Goal:
Enable audio → structured intelligence pipeline

Flow:

Val0 (Telegram / Drive)
→ receives audio
→ sends job to Forge

Forge:
- transcription (API or local)
- summary
- structured extraction:
  - tasks
  - deadlines
  - entities
  - topics
- classification:
  - idea
  - task
  - meeting
  - case-related
  - low-value / noise

Routing:

Outputs must be assigned to:

- personal inbox
- project context
- case context
- archive

Constraints:

- all ingested data stored in ValPrime advisory memory
- NO automatic mutation of Val0 canonical records

Ingestion Integration Rules:

- extracted tasks must NOT be auto-added to tasks.md
- extracted items must be proposed as suggestions
- user must explicitly confirm task creation

- ingestion may update notes.md automatically
- ingestion may NOT update current_state.md directly

- all ingestion outputs must be classified before any action

Definition of Done:

- audio → transcript + summary + classification returned automatically

=====================================================================
PHASE 2.1 — SHARED EXECUTION LAYER
=====================================================================

Goal:
Enable Val0 to act across users and contexts

Capabilities:

- send documents to contacts
- share context across participants
- synchronize information state

Examples:

- "send this to Sofía"
- "share this with Miguel"

Constraints:

- explicit user confirmation required
- no implicit data sharing
- maintain auditability

Definition of Done:

Val0 performs real-world multi-user actions

=====================================================================
PHASE 3 — MEMORY + EMBEDDINGS
=====================================================================

Goal:
Enable contextual recall and deeper system awareness

Location:
Forge ONLY

Capabilities:

- embed notes / transcripts / roadmap
- retrieve relevant context
- support advisory reasoning

Constraints:

- read-only enhancement
- no canonical mutation

=====================================================================
PHASE 4 — VALPRIME ↔ VAL0 BRIDGE
=====================================================================

Goal:
Enable controlled communication between layers

Capabilities:

- Val0 asks Forge:
  "what’s next?"
- Forge returns PM guidance

Rules:

- Val0 = execution authority
- ValPrime = advisory authority
- Val0 may accept or ignore suggestions

=====================================================================
PHASE 5 — ADVISORY INTELLIGENCE (STRUCTURED OUTPUT)
=====================================================================

All outputs MUST explicitly separate:

- FACT
- UNKNOWN
- INFERENCE
- OPTIONS
- NEXT QUESTIONS

Constraints:

- no blending of categories
- no implicit assumptions presented as facts
- no skipping UNKNOWN when uncertainty exists

=====================================================================
PHASE 6 — PERSONALITY LAYER (VAL0 MOUTHPIECE)
=====================================================================

Goal:
Develop Val0 as the controlled mouthpiece of the system

Rules:

- personality is rendering only
- must not override determinism
- must not alter truth
- must not bypass flows

Timing:

Begin design after Phase 4 stability  
Implement only after system reliability is proven  

=====================================================================
PHASE 6.1 — PERSONALITY CONTROL (KNOB SYSTEM)
=====================================================================

Goal:
Enable controlled personality variation without affecting system integrity

Concept:

Personality is a rendering layer applied AFTER deterministic output

Parameters:

- tone (neutral, direct, sarcastic, aggressive)
- verbosity (low, medium, high)
- humor (none, light, heavy)
- profanity (none, moderate, high)

Modes:

- Operator
- Deadpool
- Advisor
- Soft

Rules:

- personality must NOT:
  - alter facts
  - alter execution
  - override constraints

- personality must:
  - adapt to user preference
  - remain consistent per session unless changed

Definition of Done:

User can switch personality modes without affecting system reliability

=====================================================================
DRIFT MANAGEMENT
=====================================================================

Drift = deviation from roadmap or priorities

Phase 1:
- manual query

Phase 2:
- Val0 queries Forge

Phase 3:
- Forge prepares alerts
- Val0 delivers them

=====================================================================
APRIL TARGET — MIGUEL MVP
=====================================================================

Goal:
Real-world usable system

Required:

- Val0 stable
- email working
- onboarding working
- PM layer functional
- state continuity working
- MP3 ingestion (optional bonus)

Definition:

System is used daily without fallback.

=====================================================================
CHANGE CONTROL
=====================================================================

All structural changes must:

1. be documented here first
2. preserve determinism
3. remain testable
4. respect layer separation

---

## 2026-04-12 — PM Loop + Session Continuity MVP Update

### Status
Implemented and working at MVP level.

### Delivered
- PM focus persistence
- PM decision logging
- Heuristic PM classifier:
  - `DO_NOW`
  - `DEFER`
  - `DISCARD`
- PM drift surfacing
- Session message persistence for inbound/outbound turns
- Recent-message trimming
- Deterministic focus-query override

### Files touched
- `/opt/val0/memory_store.py`
- `/opt/val0/bot.py`

### Runtime assumptions confirmed
- live service: `val0-bot.service`
- live DB: `/opt/val0/val0_memory.enc.db`
- runtime source of truth comes from systemd, not `/opt/val0/system/*.service`

### Design rules preserved
- SQLite / SQLCipher only
- no embeddings added
- no mutation of canonical case tables for PM
- no mutation of reminder canonical flow for PM
- no overengineering beyond MVP

### Compatibility note
Current SQLCipher build did not accept:
- `ON CONFLICT (...) DO UPDATE`

Working replacement used:
- `INSERT OR IGNORE`
- then `UPDATE`

### Deferred by design
- embeddings-based recall improvements
- full ValPrime orchestration engine
- app/UI work
- watch-native UX
- multi-device sync
- advanced privacy layer
- richer PM planner logic

### Next recommended step
- continuity polish pass
- follow-up carryover testing
- active-context continuity testing
- torch-pass recovery doc