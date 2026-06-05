# PRODUCT-RETURN-02 Caso Finca Q&A Demo Coverage Review

## Current Source-Of-Truth State

- Current sealed head before this review: `ece9432 Add Night Runner morning decision flow`.
- This lane is non-runtime only.
- Protected live data remains out of scope:
  - `clients/karen/CLIENT_FOLDERS.json`
  - `clients/karen/CLIENT_GROCERY.md`
- No runtime behavior changed.

## Existing Caso Finca Q&A Assets

- `docs/product/CASO_FINCA_CONVERSATIONAL_QA_DESIGN_V1.md`
  - Defines bounded Caso Finca Q&A.
  - Explicitly rejects open-domain ChatGPT behavior.
  - Requires source grounding, legal boundary, context-aware routing, no raw OCR dumps, and no internal IDs in normal answers.
- `scripts/quality/caso_finca_conversational_qa_smoke.py`
  - Protects question classification and renderer output.
  - Covers overview, needs-review, known-vs-uncertain, Nora questions, plain-language explanation, document explanation, next action, and document-priority aliases.
  - Verifies legal boundary, no VFMS/internal ID leakage, no raw OCR body, no stale contamination, no founder-limitation hijack, and route ordering.

## Existing Demo / Readiness Assets

- `docs/product/FOUNDER_DEMO_READINESS_V1.md`
  - Canonical founder-demo path includes Caso Finca workspace, document list, and document 1 summary.
  - States do-not-promise boundaries: no legal conclusions, no perfect OCR, no full autonomy.
- `docs/demo/KAREN_DEMO_SCRIPT_V0.md`
  - Older Karen demo flow focuses on what Val can do, grocery/list, idea capture, roadmap/status, and optional legal/admin support.
  - Legal/admin section is intentionally optional.
- `docs/product/DEMO_SMOKE_TEST_SCRIPT_V0.md`
  - Includes finca memory and documents as demo smoke areas.

## Existing Fixtures / Smokes

Fixtures:

- `tests/fixtures/karen/caso_finca_workspace.json`
  - Source-labeled Caso Finca workspace fixture.
  - Includes what-we-know facts, confirmation needs, four document records, one timeline seed, Nora questions, pending items, and next actions.
- Related Karen fixtures exist for agenda, calendar, reminders, and tasks, but Caso Finca Q&A appears centered on the single workspace fixture.

Smokes:

- `scripts/quality/caso_finca_workspace_smoke.py`
  - Protects workspace phrase detection, compact first screen, full workspace, document list, technical document details, numbered document summaries, timeline, timeline gaps, route aliases, and no live file mutation.
- `scripts/quality/caso_finca_conversational_qa_smoke.py`
  - Protects bounded Q&A packets, answers, route priority, context-aware phrases, founder limitation separation, and generic what-now separation.
- Timeline/storage smokes exist for draft previews, fixture JSON store, temp SQLite store, confirmation wiring, read renderer, export diagnostic, live guard, and migration dry-run.
- `scripts/quality/client_fixture_smoke.py --client karen`
  - Protects the broader Karen fixture surface.
- `scripts/quality/karen_rc_full_smoke.py --keep-going`
  - Protects the wider Karen release-candidate behavior, including product/demo adjacent flows.

## Coverage Gaps

- Demo readiness does not yet appear to have a small focused smoke that checks the founder-demo Caso Finca path as a sequence:
  1. open compact dashboard,
  2. list documents,
  3. summarize document 1,
  4. ask a natural Q&A question,
  5. verify legal boundary and no internal IDs.
- The Q&A smoke covers many natural phrases, but the founder-demo doc does not enumerate the newer grounded Q&A v2 phrases as a demo-safe script.
- The workspace fixture has one timeline seed; it is enough for current read-only behavior, but thin for demo questions about chronology, contradictions, and missing dates.
- There is no docs-only mapping table that says which exact Karen demo phrases are protected by which smoke.
- There is no focused fixture/demo review smoke for the PRODUCT-RETURN lane itself.

## Recommended Next Product Lane

`PRODUCT-RETURN-03 — Caso Finca Founder Demo Q&A Phrase Coverage`

Purpose:

Create a narrow non-runtime product/demo coverage lane that adds a docs/demo phrase matrix and, if safe, a focused smoke for the founder-demo Caso Finca Q&A sequence.

## Safe First Task

Add a docs-only phrase coverage matrix first:

- canonical phrase,
- natural Karen phrase,
- expected route/surface,
- smoke that protects it today,
- missing smoke/doc gap,
- legal/safety boundary expected.

Do not edit runtime until the matrix shows a specific unprotected trust-killer.

## Allowed Files

Recommended for `PRODUCT-RETURN-03`:

- `docs/product/FOUNDER_DEMO_READINESS_V1.md`
- `docs/demo/KAREN_DEMO_SCRIPT_V0.md`
- `docs/product/PRODUCT_RETURN_03_CASO_FINCA_DEMO_PHRASE_MATRIX.md`
- `scripts/quality/caso_finca_conversational_qa_smoke.py` only if adding non-runtime smoke coverage is explicitly approved.
- `scripts/quality/caso_finca_workspace_smoke.py` only if adding non-runtime smoke coverage is explicitly approved.
- `tests/fixtures/karen/caso_finca_workspace.json` only for fixture-safe additions, not live data.

## Forbidden Files

- `bot.py`
- `core/**`
- `clients/**`
- live DB files
- OAuth/token/systemd files
- production restart actions
- live data mutation

## Suggested Tests

For this review lane:

- `python3 scripts/quality/caso_finca_conversational_qa_smoke.py`
- `python3 scripts/quality/caso_finca_workspace_smoke.py`
- `python3 scripts/quality/client_fixture_smoke.py --client karen`
- `python3 scripts/quality/karen_rc_full_smoke.py --keep-going`
- `python3 scripts/quality/client_isolation_audit.py`
- `git diff --check`
- `git status --short --branch`

For the next lane, add a focused docs/smoke test only after the phrase matrix is created.

## Risks / Guardrails

- Do not broaden Q&A into open-domain chat.
- Preserve context-aware routing; generic "qué falta revisar" must not globally mean Caso Finca.
- Keep legal boundary visible: Val organizes and summarizes; Nora/la abogada confirms legal effect.
- Do not expose VFMS/internal IDs in normal user-facing answers.
- Do not dump raw OCR or private document bodies into docs, tests, or reports.
- Do not mutate `clients/karen/CLIENT_FOLDERS.json` or `clients/karen/CLIENT_GROCERY.md`.
- Keep demo coverage narrow; avoid turning this into another infrastructure lane.

## Explicit Runtime Statement

No runtime behavior changed in PRODUCT-RETURN-02.
