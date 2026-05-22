# APPOINTMENT_CLEANUP_AUDIT — Karen

Purpose:
Track legacy appointment-like records and classify them safely.

---

## Audit 2026-05-21

Clean agenda records:

- #85 appointment — Friday May 29, 3:00 PM — cita con Nora.
- #86 reminder — Friday May 29, 2:00 PM — preparar la cita con Nora. parent_ref=APPOINTMENT:85

Legacy / appointment-like case notes observed:

### case_note #464

Source:
case_appointment_v0

Text:
Cita / agenda del caso:

tengo cita con Nora el 28 a las 3pm

Initial classification:
mark_as_legacy_duplicate_candidate

Reason:
Created during same-day routing bug before the active appointment save route was correctly inserted before the legacy Karen appointment handler.

Action:
Do not delete. Keep as audit evidence for now.

---

## Open questions

- Should legacy case appointment notes remain visible in legal/case history summaries?
- Should Val agenda lookup ignore `case_appointment_v0` notes by default unless user asks for legal/case history?
- Should future cleanup add `superseded_by` metadata somewhere, or only markdown audit?

