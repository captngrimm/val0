# Sprint 04 — Calendar Merge MVP 1.2 Verification

Updated: 2026-03-05

## Goal

Verify and harden the deterministic Google Calendar merge subsystem used by the
due query gates.

This sprint does **not introduce new architecture**.  
It validates and documents the existing merge pipeline already present in the system.

Calendar merge must remain:

- deterministic
- read-only
- feature-flag controlled
- query-time only
- safe to disable without affecting core operation

---

# A) Due Gate Calendar Merge Verification

## Problem

The due query gates (`due_today`, `due_range`) must be able to include
Google Calendar events without introducing instability or nondeterministic behavior.

The system already contains merge logic, but this sprint verifies that:

- the merge boundary is correct
- the feature flag behaves correctly
- failure scenarios degrade safely

## Implementation

Due gates live in:
core/case_mvp.py


Functions:


try_due_today()
try_due_range()


Both gates construct deterministic DB deadline objects and then call:


merge_due_items()


from:


core/due_merge.py


The merge helper receives:


db_items
range_start_utc
range_end_utc


and returns normalized merged results.

No model reasoning is involved.

---

# B) Calendar Client Integration

Calendar reads are performed through:


core/gcal_client.py


Primary helper:


get_events_between(start_utc, end_utc)


Credentials are isolated outside the repository:


/etc/val0/gcal/


Required files:


client_secret.json
refresh_token
calendar_id


Calendar access scope:


calendar.readonly


No database mutation occurs.

---

# C) Feature Flag Control

Calendar merge is gated behind the environment variable:


VAL0_GCAL_ENABLED


Flag behavior:

| Flag | Behavior |
|-----|---------|
0 / unset | DB-only due queries |
1 | DB + GCAL merge |

Implementation location:


core/due_merge.py


Helper:


gcal_enabled()


Calendar events are only fetched when the flag evaluates to true.

---

# D) Merge Behavior

Merge occurs entirely inside:


core/due_merge.py


Pipeline:


DB deadlines
→ normalized objects
→ optional GCAL fetch
→ normalization
→ deterministic merge
→ collision detection
→ deterministic sort


Output schema:


{
due_ts
due_local
due_date
title
case_id
source ("db" | "gcal")
external_id
}


Sorting rule:


ascending due_ts


DB items always remain authoritative in conflicts.

---

# E) Conflict Detection

The merge engine logs collisions between:

- DB deadlines
- Google Calendar events

Detection rules compare:


case_id
due_date
normalized title


Conflict stats are logged via the merge logger.

No automatic DB mutation occurs.

---

# F) Failure Degradation

If the calendar client fails at any stage:

- OAuth failure
- API error
- missing credentials

The merge system:

1. Logs the failure
2. Skips calendar events
3. Returns DB results only

User-facing behavior remains stable.

No crash should occur.

---

# G) Unbound Event Handling

Calendar events without CASE bindings are considered **unbound events**.

By default these are ignored.

Controlled by:


VAL0_GCAL_INCLUDE_UNBOUND


Default:


OFF


Purpose:

Prevent noise from general calendar items unrelated to legal cases.

---

# H) Tests

Feature flag OFF:

Ask:


Qué vence hoy


Expected:

Only DB deadlines returned.

---

Feature flag ON:

Enable:


VAL0_GCAL_ENABLED=1


Ask:


Qué vence hoy
Qué vence esta semana


Expected:

DB + GCAL merged results.

---

Failure simulation:

Break calendar credentials.

Expected:

DB deadlines still return.

No crash.

---

# Definition of Done

Due gates verified to include optional GCAL events.

Feature flag behavior confirmed.

Merge remains deterministic.

Calendar failures degrade safely.

No modification to reminder or case pipelines.

Docs updated to reflect verified subsystem.

---

# Notes

This sprint verifies existing merge functionality rather than introducing new logic.

The merge engine was already implemented but required confirmation
of deterministic behavior and operational boundaries.

---

END OF SPRINT 04