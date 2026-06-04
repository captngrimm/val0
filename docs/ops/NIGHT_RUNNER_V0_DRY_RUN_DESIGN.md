# Night Runner v0 Dry-Run Design

## 1. Purpose

Night Runner v0 is a paranoid, branch-only, dry-run/report-only tool concept for using overnight or dead time without multiplying chaos. Its first job is not to do work automatically. Its first job is to decide whether a lane packet is safe enough to consider, list what it would do, list what it refuses to do, and write a morning report plan.

The operator problem is simple: Val0 now has many small lanes, strong smokes, and live client data sitting beside code. Night Runner should help prepare bounded work while the human is away, but it must not become an unsupervised production actor.

## 2. Non-Goals

- Do not run Codex autonomously in v0.
- Do not modify runtime behavior.
- Do not restart production services.
- Do not touch OAuth, tokens, systemd, `/etc/val0`, or live client data.
- Do not commit, push, merge, reset, discard, or clean files.
- Do not execute destructive commands.
- Do not decide product strategy.
- Do not bypass Karen RC smokes or client isolation checks.
- Do not run live Telegram, Google Calendar writes, OCR on private PDFs, or external API calls.

## 3. Safety Rules

Night Runner v0 is dry-run first, dry-run last.

- Default mode: report-only.
- Required branch mode: a named branch must be supplied in the lane packet.
- Current branch must match the lane packet branch, or the tool refuses.
- If the working tree contains forbidden files, the tool refuses.
- If live data is dirty, the tool reports it and refuses any action beyond the dry report.
- If requested files are outside `allowed_files`, the tool refuses.
- If the lane packet allows commits, restarts, destructive commands, or production writes, v0 refuses.
- If uncertainty remains, the tool stops instead of guessing.

## 4. Lane Packet Format

Night Runner Lane Packet:

```yaml
lane_id:
branch_name:
task_prompt:
allowed_files:
forbidden_files:
tests_to_run:
commit_allowed: false
restart_allowed: false
destructive_commands_allowed: false
report_path:
stop_if_uncertain: true
```

Example:

```yaml
lane_id: NIGHT-RUNNER-DRY-001
branch_name: val0-post-m41-conversationality-memory-lab-2026-05-25
task_prompt: "Inspect the next planned lane and prepare a dry-run report."
allowed_files:
  - docs/ops/NIGHT_RUNNER_V0_DRY_RUN_REPORT.md
  - tmp/night_runner/
forbidden_files:
  - clients/karen/CLIENT_GROCERY.md
  - clients/karen/CLIENT_FOLDERS.json
  - /etc/val0
  - .env
tests_to_run:
  - python3 scripts/diagnostics/val0_milestone_radar.py
  - git diff --check
commit_allowed: false
restart_allowed: false
destructive_commands_allowed: false
report_path: tmp/night_runner/morning_report.md
stop_if_uncertain: true
```

## 5. Forbidden Files / Live Data Guard

Forbidden files are absolute stop conditions for v0. The first protected list should include:

- `clients/karen/CLIENT_GROCERY.md`
- `clients/karen/CLIENT_FOLDERS.json`
- `.env`
- files containing OAuth tokens, API keys, credentials, or cookies
- `/etc/val0`
- systemd unit/drop-in files
- live database files
- VFMS raw client document bodies

If any forbidden file is dirty, staged, or requested by the lane packet, Night Runner writes a refusal note. It does not attempt to fix the state.

## 6. Git Status Guard

Night Runner v0 should run:

```bash
git status --short --branch
git rev-parse --short HEAD
git branch --show-current
```

Refuse conditions:

- current branch differs from `branch_name`
- untracked or modified files exist outside `allowed_files`
- forbidden files are dirty or staged
- staged changes exist at all
- repository is mid-merge, mid-rebase, or has unresolved conflicts
- requested lane appears already sealed in the Alpha benchmark log

Allowed diagnostic dirt in v0 is narrow: a report under the requested `report_path`, or optional temporary output under `tmp/night_runner/`.

## 7. Allowed Command Categories

Allowed commands are read-only or test-only:

- `git status --short --branch`
- `git rev-parse --short HEAD`
- `git branch --show-current`
- `git diff --check`
- `python3 scripts/diagnostics/val0_milestone_radar.py`
- `python3 scripts/diagnostics/val0_alpha_brief.py`
- compile checks such as `./scripts/val0py -m py_compile <allowed script>`
- smoke tests explicitly listed in `tests_to_run`
- writing a report only to `report_path` or `tmp/night_runner/`

## 8. Forbidden Command Categories

Night Runner v0 must not run:

- `git reset`
- `git checkout -- <file>`
- `git clean`
- `git commit`
- `git push`
- `rm` against repo or live paths
- service restarts or `systemctl`
- OAuth/token commands
- production deploy commands
- live Telegram sends
- Google Calendar writes/deletes
- task/reminder/document mutations
- OCR over private live PDFs unless explicitly scoped in a later version
- network calls or package installs

## 9. Test Plan Selection

The lane packet controls the tests to list. Night Runner v0 may recommend tests based on lane type, but it should not add surprise heavy or live tests.

Suggested mappings:

- Docs/ops lane: `git diff --check`, relevant docs smoke if it exists.
- Router/intent lane: fixture smoke, router smoke, Karen RC full smoke if runtime touched.
- Caso Finca lane: Caso Finca smoke, client fixture smoke, client isolation audit, Karen RC full smoke.
- OCR/document lane: document/watermark/OCR smokes only, no live OCR unless explicitly approved.
- Runtime lane: compile, lane smoke, client isolation audit, Karen RC full smoke.

In v0, the report should say "would run" rather than "ran" unless the future implementation actually executes those listed tests in a controlled dry-run mode.

## 10. Report Format

Morning report should include:

- lane_id
- branch/head
- git status summary
- allowed_files
- forbidden_files
- safety decision: PASS_DRY_RUN / REFUSED
- reason for refusal if any
- proposed work summary
- tests it would run
- files it would be allowed to touch
- files it must not touch
- risks/watch items
- exact recommended morning action

## 11. Failure / Stop Conditions

Stop immediately if:

- forbidden files are dirty, staged, or requested
- branch mismatch
- lane packet is missing required fields
- `commit_allowed`, `restart_allowed`, or `destructive_commands_allowed` is true
- task prompt asks for production restart, live writes, OAuth/token work, or broad refactor
- allowed files are too broad, such as `.` or `**/*`
- tests require live external services
- current benchmark says a different lane is the recommended next action
- tool cannot tell whether a file is live data

The right failure behavior is a boring refusal with reasons. Boring is the point.

## 12. Morning Report Example

```text
Night Runner v0 Dry-Run Report
==============================

Lane: NIGHT-RUNNER-DRY-001
Branch: val0-post-m41-conversationality-memory-lab-2026-05-25
Head: 7e30215

Safety decision: REFUSED

Reason:
- Live Karen data is dirty: clients/karen/CLIENT_GROCERY.md, clients/karen/CLIENT_FOLDERS.json.
- v0 does not modify, stage, reset, or ignore live data automatically.

Would run if clean:
- python3 scripts/diagnostics/val0_milestone_radar.py
- git diff --check

Would write:
- tmp/night_runner/morning_report.md

Would not touch:
- clients/karen/CLIENT_GROCERY.md
- clients/karen/CLIENT_FOLDERS.json
- bot.py
- systemd
- tokens/OAuth files

Morning action:
- Ask the operator whether to continue Night Runner design or switch to A-025D shadow logging.
```

## 13. Future Phases

Phase 0: Design only.

Phase 1: Dry-run validator script.
- Parse a lane packet.
- Check branch and git status.
- Refuse forbidden/live data.
- Print and optionally write a report.
- No commands beyond diagnostics.

Phase 2: Controlled test-list dry run.
- Execute only explicitly listed read-only diagnostics/smokes.
- Store output under `tmp/night_runner/`.
- Still no commits/restarts/writes.

Phase 3: Branch-only report builder.
- Create a morning report with command outputs, failures, and suggested next action.
- Still no code edits.

Phase 4: Human-approved patch mode.
- Only after repeated dry-run PASS.
- Edits limited to `allowed_files`.
- No live data, no production restart, no commits unless explicitly approved in the lane packet and by the operator.

Phase 5: Optional commit mode.
- Requires separate design and stronger guardrails.
- Must never include live client files.

## 14. Smallest Implementation Lane After Design

Recommended next lane:

`NIGHT-RUNNER-01 — Dry-Run Validator Script`

Deliverable:

- `scripts/ops/night_runner_dry_run.py`
- accepts a lane packet path
- validates required fields
- checks current branch/head/status
- refuses forbidden/live data
- prints a dry-run safety report
- optionally writes `report_path`
- runs no autonomous Codex work
- performs no commits, restarts, destructive commands, or runtime mutations

Acceptance should be boring:

- dirty live data causes refusal
- clean temp fixture packet produces PASS_DRY_RUN
- forbidden file in `allowed_files` causes refusal
- commit/restart/destructive flags set to true cause refusal
- report clearly states what would and would not happen
