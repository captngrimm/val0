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