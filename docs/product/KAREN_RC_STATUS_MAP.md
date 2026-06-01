# Karen RC Status Map

## What Karen RC Means

Karen RC is the current release-candidate stabilization lane for Karen as client-zero. It means the main founder-beta workflows are no longer treated as isolated labs; they are checked together as one client-facing product surface before larger architecture work resumes.

The RC target is practical reliability: Karen should be able to use Val for agenda, reminders, tasks, documents, OCR-assisted legal PDF review, and Spanish-first conversation without old routes leaking into the experience.

One-command RC health check:

```bash
python3 scripts/quality/karen_rc_full_smoke.py
```

Use `--keep-going` when you want a full failure list:

```bash
python3 scripts/quality/karen_rc_full_smoke.py --keep-going
```

## Macro Lanes

| Lane | Status | Notes |
| --- | --- | --- |
| Identity / Tany / Spanish | PASS | Deterministic guards keep Karen-facing nickname as Tany and Spanish-first responses stable. |
| Agenda / Google Calendar | PASS | Agenda reads Google Calendar, Val reminders, and Val tasks with current section naming. Google Calendar create/delete works with confirmation. |
| Val reminders | PASS | Natural reminders, relative reminders, numbered deletes, vencidos, and Monday parsing are covered by smokes. |
| Val tasks | PASS | Task hard gate, task list hygiene, completion, scheduling, and active-list cleanup are covered. |
| Documents / watermark guard | PASS | Document inventory, latest/numbered references, watermark detection, and saved-summary watermark guard are covered. |
| OCR / Registro Público PDFs | PASS / WATCH | On-demand OCR works for scanned/watermark PDFs and cached OCR UX is clear. Watch page-limit and OCR-quality edge cases. |
| Voice / transcription recovery | WATCH | Several voice variants are guarded, but voice normalization remains imperfect and should move into router architecture. |
| Router / intent priority | WATCH | Current RC uses hard gates for stability. This should be refactored into Intent Router v2 after RC. |

## Known Live-Tested PASS Items

- Google Calendar read/write is authorized and working.
- Google Calendar event create works with confirmation.
- Google Calendar event delete works with confirmation.
- Stale Google Calendar delete guard prevents deleting from an old numbered list.
- Relative reminders such as `recuérdame en 10 minutos...` create Val reminders.
- Monday reminder parsing creates the right Val reminder and agenda view.
- Task hard gate prevents task queries from falling into finca/case memory routes.
- Task data hygiene hides stale reminder-like tasks and deleted/closed items from active views.
- Document watermark guard refuses fake summaries from `Copia para propósitos informativos solamente`.
- On-demand OCR extracts useful legal text from Registro Público scanned PDFs.
- Cached OCR summaries now say when Val is showing a saved OCR reading.

## Known Debt

- `clients/karen/CLIENT_GROCERY.md` is intentionally dirty during Karen testing and must not be committed unless explicitly scoped.
- OCR is first-pass only and currently limited to the first pages for MVP responsiveness.
- OCR may still need manual review or a cleaner copy for poor scans, handwriting, stamps, or rotated pages.
- Voice normalization is still tactical and incomplete.
- Intent Router v2 is needed after RC to replace accumulated hard gates with a cleaner priority model.
- Multi-client hardcoded cleanup remains future work before broad expansion.

## Naming Model Going Forward

Stop using random M5/B3 labels for product communication. Use stable RC/architecture lanes:

- `RC-KAREN-01 Identity/Spanish`
- `RC-KAREN-02 Agenda/GCal`
- `RC-KAREN-03 Reminders`
- `RC-KAREN-04 Tasks`
- `RC-KAREN-05 Documents/OCR`
- `RC-KAREN-06 Full RC Smoke/Status`
- `ARCH-01 Intent Router v2`

## Operational Rule

After Karen RC PASS, shift from stabilization hard gates to the Intent Router v2 refactor plan. Do not add major features until that router/refactor plan exists unless an urgent Karen client blocker appears.

For RC verification, run:

```bash
python3 scripts/quality/karen_rc_full_smoke.py --keep-going
```

RC is considered healthy when compile, client-isolation audit, identity/language smokes, agenda/GCal smokes, reminders/tasks smokes, document/watermark smokes, and OCR runtime smokes all pass.
