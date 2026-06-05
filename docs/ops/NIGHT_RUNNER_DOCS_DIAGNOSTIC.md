# Night Runner Docs Diagnostic

## Purpose

NIGHT-RUNNER-09 is the first controlled file-edit lane for Night Runner/Codex.

It proves a tiny branch-only docs-only edit can be made, reviewed, and verified without touching runtime code, client data, production state, services, secrets, or protected live files.

## What This Lane Proves

- Codex can make one intentionally scoped documentation change.
- The change can be restricted to a single allowed docs path.
- The operator can verify before/after state with normal repo checks.
- Protected live Karen data can remain dirty but untouched and unstaged.
- A lane can be useful without enabling autonomous coding, commits, restarts, or runtime behavior changes.

## What This Lane Does Not Prove

- It does not prove Codex can safely edit runtime code.
- It does not prove runtime/code edits are safe.
- It does not prove Night Runner can commit or push.
- It does not prove Night Runner can restart production.
- It does not prove any live database or Telegram workflow is safe to change.
- It does not permit access to OAuth, token, systemd, `/etc/val0`, or secret contents.

## Tiny Docs Patch With Smoke

NIGHT-RUNNER-10 proves Codex can make a controlled docs-only edit and add a focused smoke in the same branch-only lane.

The smoke verifies this document keeps the required guardrail language, including docs-only scope, no runtime behavior, protected live-file references, and the warning that this still does not prove runtime/code edits are safe.

This lane still does not prove runtime/code edits are safe. It only proves that a small docs patch plus a smoke can be reviewed without touching runtime behavior, protected client data, live databases, services, or secrets.

The next lane should be a tiny safe branch task only after this docs-plus-smoke pattern passes and the operator confirms no protected live files were staged or changed.

## Reported Patch Guard

NIGHT-RUNNER-14 proves the tiny task runner records exactly what changed during a branch-only patch lane and compares that list with the packet's `allowed_files`.

The guard treats any changed forbidden file as a refusal, keeps runtime/client/live data edits out of scope, and verifies protected live files remain unstaged and hash-unchanged.

This still does not allow runtime code edits, client-data edits, commits, restarts, live writes, database migrations, or secret inspection. It only proves that a tiny non-runtime patch can be reported and checked against an explicit allowlist.

The next lane can attempt another tiny non-runtime patch under the same guard after the operator reviews the report and confirms the changed-file list matches the packet.

NIGHT-RUNNER-15 uses that guard for a tiny useful readiness-summary patch, still outside runtime and client data.

NIGHT-RUNNER-16 adds a patch-review diagnostic so the operator can see what the first useful non-runtime patch proved before moving toward bedtime workflow packets.

NIGHT-RUNNER-17 packages Bedtime Workflow v2 so the operator can prepare one scoped packet before sleep and review a guarded morning report without enabling runtime or live-data work.

NIGHT-RUNNER-18 runs that workflow manually end to end with safe diagnostics only, producing a report while still forbidding runtime, client-data, commit, restart, and live-write actions.

NIGHT-RUNNER-19 polishes the bedtime report into a clearer morning-review artifact with Decision, Task, Tests Run, Changed Files, Safety Status, Protected Live Data, and Recommended Next Step sections.

## Allowed Edit Scope

Allowed for this lane:

- `docs/ops/NIGHT_RUNNER_DOCS_DIAGNOSTIC.md`

Optional in future docs-diagnostic lanes:

- a focused smoke under `scripts/quality/` only when the lane explicitly asks for one.

## Forbidden Files And Actions

Forbidden files:

- `clients/karen/CLIENT_GROCERY.md`
- `clients/karen/CLIENT_FOLDERS.json`
- any other `clients/karen/` live data file
- `val0_memory.enc.db`
- `*.db`
- `*.sqlite`
- `/etc/val0`
- systemd unit/runtime files
- OAuth, token, config, or secret files

Forbidden actions:

- reset, discard, stage, or casually commit protected live data
- write runtime code
- mutate client data
- run production restarts
- run live DB migrations
- inspect or print secret contents
- commit or push from Night Runner

## Required Checks Before Editing

Before a docs-only diagnostic lane edits anything:

```bash
find .. -name AGENTS.md -print
sed -n '1,240p' AGENTS.md
sed -n '1,260p' docs/architecture/CLIENT_ISOLATION_CONTRACT_V0.md
git status --short --branch
```

Confirm:

- only expected protected live files are dirty,
- no protected live files are staged,
- the requested allowed docs path is explicit,
- no runtime/client files are in scope.

## Required Checks After Editing

After the docs-only edit:

```bash
python3 scripts/quality/client_isolation_audit.py
git diff --check
git diff --cached --name-only
git status --short --branch
```

Expected:

- client isolation audit passes,
- whitespace/diff hygiene passes,
- no staged files,
- only the intended docs artifact is newly changed by the lane,
- protected live files remain untouched from their pre-lane state.

## Morning Report Expectations

A Night Runner morning report for a docs-only diagnostic lane should include:

- lane id and branch,
- exact allowed file path,
- changed files,
- confirmation that no runtime behavior changed,
- confirmation that no client/live files were touched,
- confirmation that no commits, pushes, restarts, or DB migrations happened,
- checks run,
- final git status,
- recommended next lane.

## Next Safe Lane

Recommended next lane:

```text
NIGHT-RUNNER-10 — Branch-only Tiny Docs Patch With Smoke
```

That lane may add one docs file plus one focused smoke if explicitly scoped, but should still avoid runtime code, client data, commits, restarts, and live persistence.

## Manual Overnight Trial

NIGHT-RUNNER-20 adds the first manual overnight-style report path. It still allows no runtime behavior, no client data edits, no commits, no restarts, no live writes, and no Codex execution; it only proves that the polished bedtime packet can produce both the standard bedtime report and a trial-specific morning review artifact under `tmp/night_runner/`.

## Overnight Candidate Summary

NIGHT-RUNNER-21 adds the first tiny useful non-runtime overnight candidate summary. It remains non-runtime and does not allow client data edits, restarts, live writes, commits, or Codex execution.

## Tiny Useful Candidate Review

NIGHT-RUNNER-22 proves the first tiny useful overnight candidate can pass through reported-patch review with a reviewable docs-only change. The review must confirm changed files are allowed, protected Karen live data stays dirty-but-unstaged and untouched, runtime files remain out of scope, diagnostics pass, and no commit is performed.

## Dedicated Report Artifact

NIGHT-RUNNER-23 requires a dedicated report artifact under `tmp/night_runner/` for the tiny candidate review. The artifact should state the lane id, candidate chosen, changed files, protected live-data status from git metadata only, tests run, pass/fail result, limitations, suggested commit message, and that no commit was performed.

## Controlled Codex Attempt Guard

NIGHT-RUNNER-24 documents the guard conditions required before any future controlled one-lane Codex execution can be enabled. It does not execute Codex, does not weaken the current dry-run wrapper refusal, and keeps commits, restarts, runtime edits, live writes, and client data out of scope.

## Morning Review / ValPrime Handoff

NIGHT-RUNNER-25 adds a paste-ready morning handoff shape for ValPrime review. The handoff must include decision, lane identity, changed files, test results, safety status, protected live-data status from git metadata only, report artifact path, next action, and the anti-drift note that after NR26 High Command must force a return-to-product decision unless more infrastructure is explicitly approved.
