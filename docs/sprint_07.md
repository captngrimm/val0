# Sprint 07 — Deadline Normalization Guardrails

## Objective

Ensure all deadline and due-time logic across the system uses a single deterministic time model.
Prevent inconsistencies between database deadlines, reminder scheduling, and calendar merges.

This sprint establishes strict rules for:

* Local vs UTC conversions
* Deadline normalization
* Merge window boundaries
* Rendering consistency

The goal is to guarantee that **the same event always resolves to the same timestamp everywhere in the system**.

---

# Problem Statement

Current system behavior:

| Source            | Time Representation                   |
| ----------------- | ------------------------------------- |
| DB case deadlines | `deadline_date` (local date, no time) |
| Reminders         | `due_at_utc`                          |
| Calendar events   | ISO timestamps                        |
| Rendering         | Local timezone                        |

This works but introduces potential drift if conversion rules are inconsistent.

Example risk scenarios:

* Case deadline stored as date only → ambiguous time
* Calendar event with timezone offset mismatch
* Reminder scheduling crossing midnight UTC/local boundary
* Merge windows missing events at edges

Sprint07 removes these ambiguities.

---

# Normalization Rules

## Rule 1 — Database Deadlines

Case deadlines stored as:

```
deadline_date = YYYY-MM-DD
```

Are **always interpreted as:**

```
09:00 local time
```

Reason:

* avoids midnight edge cases
* keeps legal deadlines safely within the day
* consistent across UI and backend logic

Implementation already exists in `case_mvp.py`:

```
local_dt = datetime(y, m, d, 9, 0, 0, tzinfo=tz)
due_ts = int(local_dt.astimezone(timezone.utc).timestamp())
```

Sprint07 formalizes this rule across the system.

---

## Rule 2 — Reminder Timestamps

All reminders must store:

```
due_at_utc
```

Never local timestamps.

Conversions happen only at:

* user input parsing
* message rendering

---

## Rule 3 — Merge Windows

Calendar merges operate on UTC windows derived from local time.

Example for “today”:

```
local: 00:00 → 23:59:59
converted to UTC
```

This prevents events from falling outside the merge range.

Implementation:

```
start_local = datetime(y, m, d, 0, 0, 0, tzinfo=tz)
end_local = datetime(y, m, d, 23, 59, 59, tzinfo=tz)
```

---

## Rule 4 — Display Formatting

User-visible time must always be rendered in the configured system timezone.

Environment variable:

```
VAL0_TZ=America/Panama
```

Rendering path:

```
UTC timestamp
→ convert to local tz
→ display HH:MM
```

---

# Guardrail Checks

Add defensive validation in the following locations:

| Component              | Check                               |
| ---------------------- | ----------------------------------- |
| reminder creation      | ensure UTC timestamp                |
| calendar ingestion     | reject events without timestamp     |
| DB deadline conversion | enforce 09:00 rule                  |
| merge pipeline         | enforce sorted deterministic output |

---

# Logging Enhancements

Extend audit logging for merge operations:

Example:

```
[AUDIT] time_norm db_deadline=2026-03-06 local=09:00 utc=14:00
```

This allows fast debugging of timezone mismatches.

---

# Expected Behavior

Example query:

```
Qué vence hoy
```

System pipeline:

```
DB deadlines (date)
→ normalized to 09:00 local
→ converted to UTC
→ merged with GCAL events
→ rendered local
```

User sees:

```
⏰ Vence hoy (2026-03-06)

📅 2026-03-06
- 524242024: Audiencia preliminar
- 14:30 | Reunión con cliente
```

No ambiguity.

---

# Validation Checklist

Sprint07 considered complete when:

* [ ] DB deadlines always convert to 09:00 local
* [ ] reminders remain UTC internally
* [ ] merge windows correctly capture boundary events
* [ ] no timezone-related crashes appear in logs
* [ ] deterministic ordering preserved

---

# Non-Goals

Sprint07 does **not** introduce:

* travel-time conflict logic
* location-aware scheduling
* assistant recommendations
* messaging automation

Those belong to future sprints.

Sprint07 strictly hardens the **temporal foundation**.

---

# Status

Planned — pending implementation.
