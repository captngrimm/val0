# VAL0_LAB_PROTOCOL_V0

Purpose:
Create a safe experimental lane for Val0/Valdía ideas without contaminating active client production flows.

---

## Core rule

Lab is not production.

Nothing from Lab should affect Karen, Frank ops, or any client flow unless it passes review and is promoted.

---

## Lanes

### Production

Stable, tested, committed, and client-safe.

Examples:
- Karen agenda mini-loop
- grocery list v0
- legal document summary routes
- client calendar status boundary

### Lab

Experimental, prototype, or proof-of-concept.

Examples:
- Val Meetings + Whiteboard Copilot
- client-specific Google Calendar OAuth
- OCR/photo extraction bridge
- whiteboard/diagram generation
- live meeting notes
- voice/avatar demos
- open-source tool evaluations

### Parking Lot

Ideas worth keeping but not active.

### Roadmap Candidate

Ideas that have enough value/context to estimate and plan.

---

## Lab entry format

Name:
Status:
Owner:
Client impact:
Risk:
What it is:
What it does:
Why it matters:
Dependencies:
Fastest manual demo:
Automation path:
Exit criteria:
Promotion target:
Notes:

---

## Promotion rule

A Lab item can move toward production only after:

1. Clear use case.
2. Known client value.
3. Privacy boundary reviewed.
4. Failure modes understood.
5. Demo or test passed.
6. Rollback path exists.
7. It does not hijack active Karen/client routes.

---

## Current lab candidates

### Val Meetings + Whiteboard Copilot

Status:
Parking Lot / Lab candidate

What it is:
Future premium module where Val supports Zoom/Meet/client meetings as a silent cognitive copilot.

Fastest manual demo:
Use transcript/audio manually, then generate summary, decisions, tasks, follow-up, and a simple whiteboard/diagram.

Risk:
High distraction risk if pulled into current Karen MVP too early.

Promotion target:
Post-Karen MVP / Sol-NeWork commercial demo candidate.

### Client-specific Google Calendar OAuth

Status:
Lab candidate / future production connector

What it is:
Per-client Google Calendar authorization and sync layer.

Risk:
Privacy, OAuth complexity, account separation, write mistakes.

Promotion target:
Agenda Bridge production after read/write safety checks.

### OCR/photo extraction bridge

Status:
Lab candidate

What it is:
Convert client-uploaded images/PDFs into extracted text and structured records.

Risk:
Bad OCR, false confidence, legal/admin interpretation risk.

Promotion target:
Document ingestion pipeline after manual review boundaries are clear.

