# Karen RC Manual Test Pack — 2026-05-29

Status: Karen founder-beta / RC manual QA pack  
Branch: val0-post-m41-conversationality-memory-lab-2026-05-25  
Purpose: Give Karen a simple, human test script for Val0 Week-1 RC.

## 1. Main Testing Rule: Voice First, Text Second

Karen appears to use Val mostly by voice.

Default testing flow:

1. Try the command by voice first.
2. If Val responds strangely, does not understand, or does the wrong thing, repeat the exact same command by text.
3. Report both results.

This helps identify whether the problem is:

- voice transcription,
- Val understanding,
- routing logic,
- or the underlying feature.

Example:

Voice:
“Val, qué tengo mañana?”

If it fails, type:
“Val, qué tengo mañana?”

Then report:
- voice result
- text result
- what you expected

## 2. Mental Model

Val now separates three types of agenda items:

### 📅 Eventos de Google Calendar

These are real calendar events/citas stored in Google Calendar.

Google Calendar handles native notifications.

Examples:
- doctor appointment
- meeting with lawyer
- school pickup
- scheduled appointment

### ⏰ Recordatorios de Val

These are reminders sent by Val through Telegram.

Examples:
- remind me to call the court
- remind me in 10 minutes
- remind me tomorrow at 9

### 📌 Tareas de Val

These are pending actions or things to do.

Examples:
- ask the surveyor for a quote
- prepare documents
- review case notes

Tasks can have dates, but they are not the same as Google Calendar events.

## 3. Test Block A — Name / Personalization

Try by voice first, then text if needed.

Commands:

1. Val, ¿cuál es mi apodo registrado?
2. Val, salúdame como me llamarías normalmente.

Expected:

- Val says the registered nickname is Tany.
- Val uses Tany in the greeting.
- Val does not use the previous legacy nickname.
- Val does not say Tani.
- Val answers in Spanish.

Pass:

- Tany appears correctly.
- The answer feels natural enough.

Fail:

- Val uses the wrong name.
- Val answers in English without being asked.

## 4. Test Block B — Agenda

Command:

Val, qué tengo mañana?

Expected sections:

- 📅 Eventos de Google Calendar
- ⏰ Recordatorios de Val
- 📌 Tareas de Val

Expected behavior:

- Google Calendar events are under Eventos de Google Calendar.
- Val reminders are under Recordatorios de Val.
- Val tasks are under Tareas de Val.
- Items are numbered when useful.
- No “Modo: lectura solamente” footer.

Pass:

- The agenda is understandable.
- It is clear what is calendar, reminder, or task.

Fail:

- Events/reminders/tasks are mixed.
- Suggested actions do not work.
- Val uses confusing wording.

## 5. Test Block C — Google Calendar Event Create / Delete

Use only test events.

Create test event:

Val, agenda prueba calendario mañana a las 10am

Expected:

- Val shows the event details.
- Val asks for confirmation.
- Val says Google Calendar handles notifications.

Confirm:

Sí, confirma

Verify:

Val, qué tengo mañana?

Expected:

- The test event appears under Eventos de Google Calendar.

Delete:

Val, elimina el evento 1

Expected:

- Val asks confirmation before deleting.

Confirm:

Sí

Verify again:

Val, qué tengo mañana?

Expected:

- The test event is gone.
- Val did not touch reminders or tasks.

Pass:

- Create → verify → delete → verify works.

Fail:

- Val deletes without confirmation.
- Val deletes the wrong item.
- Val creates a reminder instead of a Google Calendar event.
- Val confirms an unrelated old action.

## 6. Test Block D — Val Reminders

Create test reminder:

Val, recuérdame en 10 minutos prueba temporal

List reminders:

Val, qué recordatorios tengo?

Expected:

- The reminder appears numbered.

Delete reminder:

Val, elimina el recordatorio 1

Expected:

- Val deletes the selected reminder.
- Val shows updated list.

Expired reminders:

Val, recordatorios vencidos

If expired reminders appear:

Val, elimina el recordatorio vencido 1

Expected:

- Val deletes the expired reminder by number.
- Val shows updated expired list or says none remain.

Pass:

- Reminder actions work naturally.
- Missing words like “el” do not break the command.

Fail:

- Val routes reminder deletion to Google Calendar.
- Val deletes the wrong item.
- Val cannot understand natural delete variants.

## 7. Test Block E — Val Tasks

Create test task:

Val, registra tarea: prueba temporal de tarea

List tasks:

Val, qué tareas activas tengo?

Expected:

- The task appears under Tareas de Val.

Mark done:

Val, marca la tarea 1 como hecha

Expected:

- Val marks the task done.
- Val does not touch Google Calendar or reminders.

Pass:

- Task appears and can be marked done.

Fail:

- Task becomes a reminder incorrectly.
- Val cannot identify the task number.
- Val touches calendar/reminders by mistake.

## 8. Test Block F — Documents Without Caption

Upload a document without a caption.

Then ask:

Val, qué fue lo último que subí?

Expected:

- Val identifies the latest uploaded document.

Then:

Val, resume este documento

Expected:

- Val summarizes it if text is available.
- If not, Val says OCR/manual review is needed.

Then:

Val, sugiere nombre para este documento

Expected:

- Val suggests a better name, tags, folder/case, and why it matters.

Then:

Val, guarda ese nombre

Expected:

- Val saves the alias/metadata.
- The original filename remains intact.

Pass:

- Karen does not need to dictate ugly filenames.
- “este documento” works.

Fail:

- Val cannot find the latest document.
- Val asks to upload again unnecessarily.
- Val invents content not in the document.

## 9. Test Block G — Numbered Documents

Command:

Val, qué documentos tengo?

Then:

Val, resume el documento 1

Then:

Val, sugiere nombre para el documento 1

Expected:

- Document 1 refers to the visible numbered list.
- Val does not require long filenames.

Pass:

- Numbered document references work.

Fail:

- Wrong document is summarized.
- Numbering is confusing or unstable.

## 10. What to Report if Something Fails

Please report:

1. What command you sent.
2. Whether it was voice or text.
3. What Val answered.
4. What you expected instead.
5. Whether the item was real or just a test.

Best format:

“Mandé por voz: [command]. Val respondió: [answer]. Luego lo escribí por texto y pasó/no pasó. Yo esperaba: [expected].”

## 11. RC Acceptance Criteria

Karen RC is acceptable if:

- Val uses Tany correctly.
- Val answers in Spanish by default.
- Agenda sections are clear.
- Google Calendar create/delete works with confirmation.
- Val reminders are manageable by number.
- Val tasks are manageable by number.
- Documents can be summarized by latest/number.
- Val does not fake success.
- Val does not delete without confirmation.
- Val does not mix events, reminders, and tasks.

## 12. Known Non-Blockers

Acceptable for current RC if communicated:

- Direct reminder editing may still use delete-and-recreate fallback.
- OCR/photo/handwritten extraction may be limited.
- Voice may fail because of transcription even if typed text works.
- Some older legal/document responses may still need personality polish.
