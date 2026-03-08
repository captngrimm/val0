# VAL0 — Sprint 12  
## Case-Linked Timeline (parent_ref system)

Date: 2026-03-07  
Branch: miguel-mvp-v2

---

# Objective

Allow Val to answer:


qué tengo del caso <id>


by retrieving reminders and tasks linked to a case.

The system should support:

• timeline by day  
• timeline by case  
• reminder delivery unchanged  
• deterministic queries (no LLM involvement)

---

# Architecture

Sprint 12 introduces a lightweight relational linking field:


parent_ref


Example:


entity_type = reminder
parent_ref = CASE:524242024


This allows different entity types to attach to the same case.

Entities that can link:


reminder
task
note
event


All are stored in the same reminders timeline system.

---

# Write Path

Reminder creation now extracts case references.

Example message:


Recuérdame revisar el caso 524242024 mañana a las 3pm


Extraction:


CASE_RE → 524242024


Stored row:


entity_type = reminder
parent_ref = CASE:524242024


---

# Read Path

New deterministic query:


qué tengo del caso <id>


Implementation:


fetch_timeline_for_parent(
parent_ref="CASE:<id>"
)


Returns timeline rows grouped by date.

Example response:


🗂️ CASE:524242024

📅 2026-03-08

15:00 | revisar el caso 524242024


---

# Idempotent Reminder Insert

The reminders table contains a unique constraint:


UNIQUE(chat_id, due_at_utc, text)


Previously duplicate reminders caused a crash.

Fix:

`insert_reminder()` now catches the duplicate error and returns the existing row id instead of failing.

Result:

Reminder creation is now idempotent.

---

# Reminder Gate Integration

Reminder parsing is now part of the main DM pipeline:


_process_text_pipeline
→ reminder gate
→ case timeline gates
→ note capture
→ model


This ensures reminders are processed before timeline queries.

---

# Current Capabilities

Val can now answer:


qué tengo hoy
qué tengo mañana
qué tengo esta semana
qué tengo del caso <id>


All from the same deterministic timeline system.

---

# Architectural Outcome

Sprint 12 establishes the first **entity linking layer**.

Cases now act as a parent object for timeline items.

This creates a simple relational knowledge graph using SQLite rows.

Future entities can attach using the same pattern.

---

# Next Steps

Sprint 12.1

Timeline output normalization.

Improve rendering:

Current:


15:00 | 524242024: revisar el caso 524242024


Target:


15:00 | Recordatorio — revisar el caso


---

Sprint 13 (planned)

Case knowledge expansion:


CASE → notes
CASE → filings
CASE → hearings
CASE → documents


All using the same `parent_ref` system.

---

# Result

Val now has a deterministic case-linked timeline engine.

This is the first step toward a unified legal memory system.