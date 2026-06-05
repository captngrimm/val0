# Night Runner Bedtime Workflow v2

## Purpose

Bedtime Workflow v2 is the manual operator packet for safe sleep-mode work. It lets Boss choose one scoped non-runtime task before sleep, run guarded diagnostics, and review a morning report before deciding what happens next.

This workflow packages the guardrails Night Runner has already proven: protected file checks, explicit allowed files, forbidden files, safe diagnostics, report paths under `tmp/night_runner`, and no autonomous commits or restarts.

## What It Allows

- one scoped non-runtime task
- explicit `allowed_files`
- explicit `forbidden_files`
- allowlisted diagnostics and smokes only
- a report under `tmp/night_runner`
- morning review by the operator

## What It Forbids

- runtime bot/core work is forbidden at this stage
- `bot.py` edits
- `core/**` edits
- client data edits
- `clients/karen/CLIENT_GROCERY.md` edits
- `clients/karen/CLIENT_FOLDERS.json` edits
- live DB writes or migrations
- production restarts
- commits unless explicitly approved later
- OAuth, token, systemd, `/etc/val0`, or secret inspection

## Bedtime Manual Flow

1. Choose one scoped non-runtime task.
2. List the exact `allowed_files`.
3. List forbidden files, including protected live client files.
4. List safe diagnostics in `tests_to_run`.
5. Set `report_path` under `tmp/night_runner`.
6. Run the guarded Night Runner command.
7. Read the morning report.
8. Decide: approve, discard, continue, or ask ValPrime.

## Morning Report

The morning report should include:

- packet lane id and task name
- branch and head
- changed-file status
- protected live-data status from git metadata only
- tests run and exit codes
- pass/fail/refusal decision
- proof that protected files stayed unstaged
- proof that runtime files were not touched
- exact next action

## Morning Decisions

Approve when the report shows only intended non-runtime changes, all checks passed, and protected files stayed dirty-but-unstaged.

Discard when the report shows unintended changes, failed checks, or scope drift.

Continue when the report is safe but the task needs another scoped non-runtime lane.

Ask ValPrime when the next action is ambiguous, strategic, or touches memory/continuity decisions.

## Morning Review / ValPrime Handoff

Use this paste-ready shape when handing the morning report to ValPrime:

```text
Decision: approve / discard / continue / ask_valprime

Lane identity:
- lane id:
- task name:
- branch:
- head:

Work summary:
- attempted:
- files changed:
- report artifact path:

Test summary:
- tests run:
- pass/fail:
- exit codes:

Safety summary:
- protected live-data status: git metadata only
- staged files:
- runtime/client/core touched:
- commits allowed:
- restarts allowed:
- live writes allowed:

Next action:
- recommended next lane or review decision:
- anti-drift note: after NR26, High Command must force a return-to-product decision unless explicitly approving more infrastructure.
```

## Protected Live Files

`clients/karen/CLIENT_GROCERY.md` and `clients/karen/CLIENT_FOLDERS.json` may be dirty because they are live user data. Night Runner must treat that state as protected, not as cleanup work.

They must remain dirty-but-unstaged unless the operator explicitly scopes a live-data action, which this workflow does not allow.

## Runtime Boundary

Runtime bot/core work is forbidden at this stage because Bedtime Workflow v2 is proving packaging and review, not production behavior changes. Any `bot.py` or `core/**` patch needs a later lane with a stricter runtime-specific approval model.

## Next Safe Lane

Recommended next lane:

```text
NIGHT-RUNNER-18 — Manual Bedtime Trial
```
