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
- It does not prove Night Runner can commit or push.
- It does not prove Night Runner can restart production.
- It does not prove any live database or Telegram workflow is safe to change.
- It does not permit access to OAuth, token, systemd, `/etc/val0`, or secret contents.

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
