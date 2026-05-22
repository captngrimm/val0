# KAREN_APPOINTMENT_CLEANUP_PROTOCOL_V0

Purpose:
Define how to safely clean or classify duplicate/legacy Karen appointment records without deleting useful legal/admin history.

---

## Context

Karen now has a working internal agenda flow:

- natural appointment save
- date lookup
- anchored reminder before appointment
- richer agenda list

Current clean agenda records live in `reminders`:

- appointment records use `entity_type='appointment'`
- reminders use `entity_type='reminder'`
- anchored reminders use `parent_ref='APPOINTMENT:<id>'`

Legacy appointment-like records may exist in `case_notes` from older handlers such as:

- `source='case_appointment_v0'`
- `source='case_appointment_reschedule_v0'`

These may be useful case history and must not be deleted casually.

---

## Current observed clean records

- Appointment #85:
  - text: cita con Nora.
  - due_at_utc: 2026-05-29 20:00:00
  - local time: Friday May 29, 3:00 PM Panama
  - entity_type: appointment
  - parent_ref: CLIENT:karen:agenda

- Reminder #86:
  - text: preparar la cita con Nora.
  - due_at_utc: 2026-05-29 19:00:00
  - local time: Friday May 29, 2:00 PM Panama
  - entity_type: reminder
  - parent_ref: APPOINTMENT:85

---

## Current observed legacy appointment-like notes

Known examples:

- case_note #464:
  - source: case_appointment_v0
  - text includes: tengo cita con Nora el 28 a las 3pm
  - created during routing bug before active appointment save route was inserted

Other older case_notes mention Nora/citas/reuniones and may represent real case history.

---

## Cleanup rule

Do not delete case_notes by default.

Classify first:

### keep_as_case_history

Use when the note describes a real past event, reschedule, legal step, document delivery, or contextual case history.

### mark_as_legacy_duplicate_candidate

Use when the note was created by a known routing bug and duplicates a clean agenda/reminder record or test input.

### migrate_to_agenda_candidate

Use when the note contains a real future appointment that should become a structured agenda item but is not already in `reminders`.

### ignore_for_agenda

Use when it mentions Nora/cita/reunion but is not actually an appointment.

---

## Safe dedup process

1. List appointment-like case_notes.
2. Compare each note against clean `reminders` appointments.
3. Classify each note using the categories above.
4. Do not delete records automatically.
5. If needed, add a separate audit note or markdown file marking classification.
6. Only after review, optionally:
   - create missing structured appointment
   - mark legacy note as duplicate in an audit file
   - leave original note untouched

---

## Promotion rule

Cleanup automation can only be implemented after a manual classification pass proves safe.

No automatic deletion in v0.

