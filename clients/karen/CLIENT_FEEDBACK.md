# CLIENT_FEEDBACK — Karen / Val Personal

Purpose:
Track Karen founder-beta feedback, test results, friction, and next patches.

This file is for client-zero learning.
Do not store unnecessary sensitive personal details here.

---

## Feedback status

Current tester:
Karen

Current demo script:
docs/demo/KAREN_DEMO_SCRIPT_V0.md

Current test request sent:
- Ask “Val, ¿qué puedes hacer hoy?”
- Test grocery add/list/delete.
- Capture one idea.

Current status:
Waiting for Karen feedback.

---

## Feedback entry template

Date:
Source:
Tester:
Tested flows:
- what_can_do:
- grocery_add:
- grocery_list:
- grocery_delete:
- idea_capture:
- ideas_list:
- roadmap_status:
- legal_docs_optional:

Overall result:
PASS / PARTIAL / FAIL / WAITING

What worked:
-

What confused the tester:
-

What failed:
-

What did the tester expect:
-

Top friction:
1.
2.
3.

Decision:
- no patch needed
- patch wording
- patch routing
- patch memory/storage
- patch demo instructions
- defer

Next patch recommended:
-

Client-facing follow-up:
-

---

## Entry 2026-05-20 — Tester prompt sent

Date:
2026-05-20

Source:
WhatsApp / Frank to Karen

Tester:
Karen

Tested flows:
- what_can_do: waiting
- grocery_add: waiting
- grocery_list: waiting
- grocery_delete: waiting
- idea_capture: waiting
- ideas_list: not requested
- roadmap_status: not requested
- legal_docs_optional: only if Karen naturally asks

Overall result:
WAITING

What worked:
- pending

What confused the tester:
- pending

What failed:
- pending

What did the tester expect:
- pending

Top friction:
1. pending
2. pending
3. pending

Decision:
Wait for Karen feedback.

Next patch recommended:
TBD after Karen responds.

Client-facing follow-up:
Ask:
- ¿Qué te funcionó?
- ¿Qué te confundió?
- ¿Qué esperabas que hiciera y no hizo?
- ¿Qué sería lo más útil para ti esta semana?


---

## Entry 2026-05-21 — Karen live tester response

Date:
2026-05-21

Source:
Telegram / Karen live test pasted by Frank

Tester:
Karen

Tested flows:
- what_can_do: FAIL
- grocery_add: PARTIAL / FAIL on shortcut phrasing
- grocery_list: PASS with exact phrase
- grocery_delete: PASS
- idea_capture: PARTIAL
- ideas_list: not tested
- roadmap_status: not tested
- legal_docs_optional: PASS when legal context appears, but over-routes incorrectly
- agenda_reminder: PARTIAL
- appointment_lookup: FAIL

Overall result:
PARTIAL

What worked:
- Grocery list exact query worked:
  “Val, qué tengo en la lista del súper?”
- Grocery delete worked:
  “Borra jabón”
- Grocery state updated to:
  arroz, huevos
- Idea capture saved the dashboard/accesses idea.
- Legal/case memory recall still returns rich case facts.

What confused the tester / product friction:
- “Val dime lo que tienes registrado en supermercado” routed to legal/case instead of grocery.
- “Val, qué puedes hacer hoy?” routed to document/case attachment listing instead of capabilities.
- “Que cita tengo para el 28” routed to legal/case instead of agenda.
- “Agrega pan azúcar café” produced a friendly confirmation but did not persist items.
- Idea extraction kept a leading punctuation/artifact before the real idea.

What failed:
- Grocery add shortcut without “anota” did not persist.
- Generic supermarket query did not route to grocery.
- Capabilities query did not route to client_context_reader.
- Appointment lookup did not route to agenda/reminders.
- Legal/case route is too aggressive and hijacks unrelated questions.

What did the tester expect:
- Supermarket phrases should show or update grocery list.
- “Qué puedes hacer hoy” should explain Val’s current abilities.
- Appointment/date queries should show the saved meeting/reminder.
- Friendly confirmation should only happen when data was actually saved.

Top friction:
1. Legal/case routing hijacks unrelated generic queries.
2. Grocery add parser misses natural shortcut phrasing.
3. Agenda/reminder lookup is not reliable after appointment capture.

Decision:
Patch routing before adding new features.

Next patch recommended:
1. Add priority gates for grocery intent:
   - registrado en supermercado
   - lista del super/súper
   - agrega/add/quita/borra items
2. Add priority gate for capabilities:
   - qué puedes hacer hoy
   - qué sabes hacer
   - cómo me puedes ayudar
3. Add priority gate for agenda/date lookup:
   - qué cita tengo
   - qué tengo el [fecha]
   - cita para el 28
4. Reduce legal/case fallback aggressiveness so it only fires when legal/finca/caso/terreno terms appear.
5. Make grocery add response confirm only after persistence succeeds.

Client-facing follow-up:
Thank Karen and tell her the test was very useful because it found exactly where Val is confusing supermarket, agenda, and legal context. Tell her we will patch those routes before asking her to test again.


---

## Entry 2026-05-21 — Routing trust-killers patch PASS

Date:
2026-05-21

Source:
Telegram / Karen live retest

Tester:
Karen

Tested flows:
- what_can_do: PASS
- grocery_add: PASS
- grocery_list: PASS
- grocery_delete: PASS from earlier live test
- agenda_appointment_lookup: PARTIAL
- legal_docs_optional: PASS, but now less aggressive

Overall result:
PASS / with agenda lookup still partial

What worked:
- “Val, qué puedes hacer hoy?” now returns the Val Personal capabilities menu instead of CASE:KAREN-LAND-001 document inventory.
- “Val dime lo que tienes registrado en supermercado” returns grocery list.
- “Agrega pan azúcar café” persists items correctly.
- “Que tengo en la lista de super” shows updated list:
  arroz, huevos, pan, azúcar, café.
- Document inventory no longer hijacks the capabilities question.

What confused the tester:
- Appointment/date lookup still needs stronger implementation.
- “Que cita tengo para el 28” no longer routes to legal/case, but returns no pending reminders if none exist.

What failed:
- No current failure on tested grocery/capabilities routing after patch.
- Agenda lookup by arbitrary date remains incomplete.

Top friction resolved:
1. Document inventory hijacking “qué puedes hacer hoy”.
2. Grocery add shortcut not persisting items.
3. Generic supermarket query routing incorrectly.

Decision:
Routing trust-killers patch sealed.

Patch committed:
4b60468 Fix Karen routing trust killers

Next patch recommended:
Improve agenda/date lookup and/or create a safer appointment memory flow after current pass is checkpointed.

Client-facing follow-up:
Tell Karen the corrections were made and ask her to keep testing naturally, especially supermarket, “qué puedes hacer hoy”, and later agenda/citas.

---

## Entry 2026-05-21 — Agenda mini-loop PASS

Date:
2026-05-21

Source:
Telegram live test / Karen

Tester:
Karen

Tested flows:
- appointment_save: PASS
- agenda_date_lookup: PASS
- anchored_relative_reminder: PASS
- google_calendar_status_boundary: PASS

Overall result:
PASS

What worked:
- Karen said: “Val, tengo cita con Nora el 29 a las 3pm”.
- Val saved the appointment in internal agenda as Reminder/Appointment ID #85.
- Karen asked: “Val, qué cita tengo para el 29?”
- Val returned the Friday May 29 agenda and found the 3:00 PM Nora appointment.
- Karen said: “Val, recuérdame una hora antes de la cita con Nora”.
- Val created Reminder ID #86 at 2:00 PM, anchored to Appointment ID #85.
- Val clearly stated that Google Calendar is not connected yet and used internal Val memory/reminders only.

What confused the tester:
- None observed in this mini-loop.

What failed:
- Earlier same-day attempts were hijacked by legacy case appointment routing, saving the appointment as a case note instead of an internal agenda item.
- This was corrected by inserting the active appointment save route before the legacy Karen appointment/case-note handler.

What did the tester expect:
- Natural language appointment capture.
- Later date-based lookup.
- Reminder before the appointment without learning commands.

Top friction:
1. Duplicate/legacy routing zones in bot.py made the first patch appear connected while the live route still used the old handler.
2. Google Calendar is still not connected per-client, so appointments remain internal for now.
3. Need future dedup/cleanup for duplicate test appointments/notes.

Decision:
- patch memory/storage
- patch routing
- record evidence

Next patch recommended:
Choose one:
- appointment dedup/cleanup
- richer agenda list / agenda summary
- client-specific Google Calendar OAuth connection flow

Client-facing follow-up:
Tell Karen that the agenda mini-loop now works:
- she can save a cita naturally
- ask what she has on a date
- ask Val to remind her before the cita
- Google Calendar is still pending, so for now it lives in Val’s internal agenda.

