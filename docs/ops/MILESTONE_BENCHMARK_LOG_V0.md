# MILESTONE_BENCHMARK_LOG_V0

Purpose:
Track milestone estimates versus real execution time so future ETAs become less vague.

This is an operator log, not a performance scoreboard. The point is to learn which kinds of milestones are quick, which ones sprawl, and where estimates need wider ranges.

---

## 1. Purpose

Use this log after each milestone or commit-sized delivery to record:

- what was estimated
- what actually happened
- what type of work it was
- what slowed it down
- what made it predictable
- what ETA confidence was appropriate

Over time, this creates a small local benchmark library for Val0 work instead of relying on vibes.

---

## 2. Fields To Record

Minimum fields:

- milestone
- commit or planning marker
- date
- work type
- scope summary
- initial ETA
- ETA confidence
- start time
- stop time
- actual elapsed time
- result
- files changed
- tests/checks run
- blockers
- surprises
- notes for future estimates

Optional fields:

- planned file count
- actual file count
- runtime touched yes/no
- docs only yes/no
- external services touched yes/no
- user interruption/context switch yes/no
- rework required yes/no
- commit hash

---

## 3. Milestone Type Categories

Use one primary category and optional secondary tags.

Primary categories:

- `planning_inspection`: read-only inspection/report
- `docs_only`: documentation artifact, no runtime behavior
- `core_renderer`: pure core output/rendering logic
- `route_wiring`: route/order behavior in `bot.py` or router
- `smoke_test`: test/checklist creation or update
- `runtime_debug`: process/log/system inspection
- `client_delivery`: client-facing handoff/manual/packet
- `product_design`: reusable product/architecture design doc
- `ops_process`: workflow, estimation, benchmark, or operations process

Secondary tags:

- `karen_client_zero`
- `daily_operator`
- `documents`
- `lawyer_prep`
- `roadmap`
- `founder_beta`
- `calendar`
- `client_isolation`
- `risk_boundary`

---

## 4. Start / Stop Rules

Start time:

- Start when implementation or inspection actually begins, after the request is understood enough to act.
- For a commit task, start before first file read/tool call.
- For planning-only work, start before first source read.
- If the task resumes after a long pause, record a second segment.

Stop time:

- For committed work, stop after commit hash and final `git status` are captured.
- For planning-only work, stop after final report is sent.
- For testing work, stop after required checks have passed or the blocker is reported.

Pause time:

- Exclude long waits for user approval or external blockers if clearly separated.
- Include normal test/runtime command time.
- If context is switched mid-task, note it instead of overfitting the number.

Rule:

```text
Measure useful elapsed work time, not calendar drama.
```

---

## 5. ETA Confidence Levels

Use confidence levels with a time range, not a single magic number.

### High

Use when:

- docs-only or single small file
- no runtime behavior
- no unknown test surface
- scope is already familiar

Example:

```text
ETA: 10-20 min, high confidence.
```

### Medium

Use when:

- 1-3 files
- known code path
- tests exist
- route/order risk is limited
- some inspection needed

Example:

```text
ETA: 30-60 min, medium confidence.
```

### Low

Use when:

- route ordering is sensitive
- live/runtime behavior may differ from source
- external services/process state may matter
- tests are missing or brittle
- scope may split into multiple commits

Example:

```text
ETA: 1-3 hours, low confidence until inspection.
```

### Unknown

Use when:

- root cause is unclear
- production/runtime state must be inspected first
- real client data or external systems would be required but are out of scope

Example:

```text
ETA: unknown until precheck; first checkpoint in 20 min.
```

---

## 6. Sample Rows For Recent Milestones 20-24

These rows seed the log. They are approximate and should be replaced or refined when exact times are available.

| Milestone | Category | Scope Summary | Initial ETA | Confidence | Actual Elapsed | Result | Commit | Notes |
|---|---|---|---:|---|---:|---|---|---|
| M20 Commit A | `runtime_debug` + `core_renderer` | Inspect duplicate bot runtime, compact default document inventory, preserve technical mode | not recorded | medium after precheck | not recorded | pass | `1817866` | Runtime precheck found one active bot process; logs showed multi-prompt smoke as likely confusion source. |
| M20 Commit B | `route_wiring` | Route lawyer/advisor prep prompt to checklist before document summary | not recorded | medium | not recorded | pass | `11a2ec3` | Narrow route/helper fix; added focused smoke for checklist and non-matching doc routes. |
| M21 Commit 1 | `client_delivery` + `docs_only` | Karen Tuesday handoff message/script | not recorded | high | not recorded | pass | `11d4ee8` | Single client-facing doc; no runtime. |
| M22 Commit 1 | `client_delivery` + `docs_only` | Karen week-1 test manual | not recorded | high | not recorded | pass | `fe7dc60` | Single client-facing manual; no runtime. |
| M23 Commit 1 | `client_delivery` + `docs_only` | Karen final delivery pack | not recorded | high | not recorded | pass | `c4bca29` | Combined handoff, test flow, known limits, operator rules. |
| M24 Commit 1 | `product_design` + `docs_only` | Roadmap Answer Mode design | not recorded | high | not recorded | pass | `d72a927` | Reusable product design doc; no runtime. |

Template row:

| Milestone | Category | Scope Summary | Initial ETA | Confidence | Actual Elapsed | Result | Commit | Notes |
|---|---|---|---:|---|---:|---|---|---|
| MXX Commit Y | `docs_only` | short summary | 15-30 min | high | 22 min | pass | `abc1234` | what changed estimate quality |

---

## 7. How To Update After Each Milestone

After every milestone:

1. Add or update one row.
2. Record the initial ETA exactly as given, if one was given.
3. Record actual elapsed time using the start/stop rules above.
4. Add the commit hash or report marker.
5. Note blockers and surprises.
6. Add one sentence about what this teaches future estimates.

If no ETA was given:

```text
Initial ETA: not recorded.
Future lesson: start recording ETA before similar work.
```

If work split into multiple commits:

- Record each commit separately.
- Add a parent row only if useful for the whole milestone.

If a task was blocked:

- Record time spent before blocker.
- Mark result as `blocked`.
- Record what precheck would have revealed it earlier.

---

## 8. How To Use Data To Improve Future Planning

Review every 5-10 milestones.

Look for patterns:

- docs-only single file average time
- docs-only packet average time
- route wiring average time
- core renderer plus smoke average time
- runtime debug precheck overhead
- audit/test time overhead
- rework sources

Update planning defaults:

- If docs-only single-file commits consistently take 10-20 min, use that as the high-confidence range.
- If route wiring often doubles due to hidden route order, give medium/low confidence until source inspection.
- If runtime debug prechecks add 10-20 min but prevent bad fixes, include them in the ETA.
- If tests are missing, add time for a smoke test instead of pretending the implementation is done.

Useful planning language:

```text
Based on recent docs-only commits, ETA 15-25 min high confidence.
```

```text
Because this touches route ordering, ETA 45-90 min medium confidence after inspection.
```

```text
Runtime issue: ETA unknown until 15-20 min precheck is complete.
```

---

## 9. Operator Notes

- Do not punish accurate wider ranges.
- Prefer an honest range over a precise guess.
- Record why an ETA was wrong while the context is fresh.
- Separate coding time from verification time.
- If the user asks for "1s" or pauses, note interruption only if it changes actual elapsed work.
- Keep this log lightweight enough to actually maintain.

The win is not perfect prediction. The win is less hand-wavy planning every week.

