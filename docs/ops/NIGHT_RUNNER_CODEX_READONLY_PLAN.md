# Night Runner Codex Read-only Plan

## Purpose

NIGHT-RUNNER-08 proves Night Runner can invoke local Codex for a real scoped planning prompt while keeping the repo read-only.

This is planning only. It is not autonomous coding.

## Boundary

Allowed:

- one Codex `exec` invocation,
- read-only sandbox,
- ephemeral session,
- scoped planning prompt,
- report under `tmp/night_runner`.

Not allowed:

- file edits,
- commits or pushes,
- production restarts,
- live DB writes or migrations,
- touching protected Karen live files,
- OAuth/token/systemd work,
- reading or printing secret contents,
- staging files.

## Command

```bash
python3 scripts/ops/night_runner_codex_readonly_plan.py --packet docs/ops/night_runner_codex_readonly_plan_packet.yaml
```

## Packet

```text
docs/ops/night_runner_codex_readonly_plan_packet.yaml
```

The packet requires:

- `task_mode: readonly_plan`
- `allow_codex_execute: true`
- `allow_file_edits: false`
- `allow_commit: false`
- `allow_restart: false`
- protected Karen live files listed in `forbidden_files`
- `report_path` under `tmp/night_runner`

## Verification

The wrapper snapshots:

- git head,
- git status,
- protected live file hashes.

It reports failure if:

- git head changes,
- git status changes,
- staged files appear,
- protected live file hashes change,
- Codex exits nonzero.

## Next Lane

If this remains green, the next safe lane is:

```text
NIGHT-RUNNER-09 — Branch-only Codex Tiny Docs Patch Candidate
```

That lane should still require an isolated branch, explicit allowed files, no protected live files, no commits by Night Runner, and human review before any commit.
