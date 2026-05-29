# Val0 Karen RC Milestone Map — 2026-05-29

Status: Karen founder-beta / RC orientation map  
Branch: val0-post-m41-conversationality-memory-lab-2026-05-25  
Purpose: Explain the big picture, macro lanes, current sprint status, and what M3/M4/M5 mean.

## 1. Big Picture

Val0 / Valdía is being built as a personal operating system over Telegram.

The goal is not just chat. The goal is an operator layer that helps a user manage:

- documents
- agenda
- Google Calendar events
- Val reminders
- Val tasks
- personal context
- case/family/legal-admin context
- future folders/topics/projects
- voice/text interaction
- client-specific preferences

Karen is client-zero / founder-beta. Her live use defines the first real Personal OS behavior profile.

## 2. Current Product Phase

Current phase:

Karen RC / Week-1 Founder Beta

Current objective:

Make Val useful and safe for Karen’s first real week of use.

This means:

- documents can be uploaded and summarized
- agenda is understandable
- Google Calendar events can be created/deleted safely
- Val reminders work
- Val tasks work
- actions by number work
- Val uses Karen’s preferred name
- Val answers in Spanish by default
- Val does not fake success
- Val asks before destructive actions

## 3. Macro Lanes

| Lane | Meaning | Current Status |
|---|---|---|
| Documents / Finca / Case | Upload, inventory, summarize, alias, document number, latest document | Advanced / near RC |
| Agenda / Google Calendar | Read agenda, create events, delete events by number | Live PASS |
| Val Reminders | Telegram reminders, numbered delete, vencidos cleanup | Live PASS |
| Val Tasks | Pending actions, list, mark done, separate from reminders | Functional basic |
| Karen Operator Profile | Preferred name, Spanish, UX preferences, numbering, tone | Started / documented |
| Voice / Audio | Voice should behave like text when possible | Observed, not fully solved |
| Folders / Topics / Personal OS Memory | Finca, Proyectos, Pendientes, future organization layer | Designed, not fully runtime |
| Multi-client Isolation | Remove Karen hardcodes, reusable client architecture | Pending before scale |
| Personality / LLM Layer | Warmer, more human responses without breaking safety | Partial |

## 4. What M3 / M4 / M5 Mean

These are not the master roadmap. They are lab blocks inside the Karen RC sprint.

### M3 — Document Flow

Human meaning:

Make documents usable.

Covered:

- document intake
- no-caption upload support
- latest document context
- summarize this document
- summarize document by number
- fuzzy filename matching
- suggested names/aliases/tags
- saved alias metadata
- document inventory polish

Status:

PASS / near RC. Needs continued live Karen document testing.

### M4 — Reminders and Tasks

Human meaning:

Make Val reminders and tasks manageable without slash commands.

Covered:

- numbered reminders
- delete reminders by number
- vencidos/expired reminders
- delete expired reminders
- task list
- mark task done
- distinguish reminder-like tasks
- safer action context
- avoid stale deletes

Status:

PASS for core flows. Direct reminder editing remains fallback.

### M5 — Google Calendar + UX + Personalization

Human meaning:

Make calendar real, clean the agenda model, and fix Karen-facing identity/personality basics.

Covered:

- Google Calendar event creation
- GCal creation confirmation isolation
- GCal event deletion by number
- agenda labels:
  - Eventos de Google Calendar
  - Recordatorios de Val
  - Tareas de Val
- removed routine read-only footer
- Karen preferred name baseline: Tany
- preferred-name guard against recent-memory drift
- registered nickname copy polish

Status:

Live PASS for create/delete/name/copy.

## 5. Latest Confirmed PASS Items

### Google Calendar

PASS:

- Val can create Google Calendar events after confirmation.
- Val can show events in agenda.
- Val can delete Google Calendar events by visible number after confirmation.
- Val does not confuse GCal events with Val reminders/tasks.

### Agenda Labels

PASS:

- 📅 Eventos de Google Calendar
- ⏰ Recordatorios de Val
- 📌 Tareas de Val

### Karen Name

PASS:

- Registered nickname response:
  “Tu apodo registrado es: Tany. Lo estoy usando con y griega.”
- Normal greeting:
  “Tany, ¿qué movida seguimos hoy?”
- No Insanity/Tani drift in those direct routes.

### Documents

PASS so far:

- latest document context
- document inventory
- numbered documents
- summaries when text is extracted
- alias/name suggestion

Still needs:

- more real Karen document testing

## 6. Current Known Dirty / Technical Debt

Known dirty file:

- clients/karen/CLIENT_GROCERY.md

Known audit warnings:

- literal_karen warnings remain
- acceptable for Karen MVP
- must be migrated before multi-client expansion

Known caveats:

- direct reminder editing is not fully implemented
- OCR/photo/handwritten extraction still limited
- voice may fail separately from text logic
- some older specialized legal/document copy may still contain legacy wording/personality issues

## 7. RC Blockers vs Polish

### Blockers

These block RC if broken:

- documents cannot be uploaded/summarized by latest/number
- agenda mixes events/reminders/tasks incorrectly
- GCal create/delete acts on wrong item
- destructive actions happen without confirmation
- Val reverts to wrong name in core identity routes
- Val answers in English unexpectedly in normal Karen use
- Val fakes success

### Polish / Non-blockers

These do not block RC if explained:

- some wording still slightly robotic
- direct reminder editing uses fallback
- OCR/manual review limitations
- voice inconsistency if text works
- older legal/doc copy needs future personality pass

## 8. Immediate Next Work Options

### Option A — Let Karen test

Best if Karen is available.

Ask her to test:

- agenda
- documents
- reminders
- tasks
- voice vs text
- apodo/personality

### Option B — Build RC Manual Test Pack

Docs-only.

Create a clean checklist Karen can follow.

### Option C — Runtime polish only if blocker appears

Do not open new runtime work unless Karen exposes a real blocker.

### Option D — Multi-client debt later

Not today unless sprint shifts.

## 9. Recommended Next Step

Create Karen RC Manual Test Pack and send Karen a short human version.

Then wait for live feedback.

Do not start another feature lane until live testing identifies a blocker.
