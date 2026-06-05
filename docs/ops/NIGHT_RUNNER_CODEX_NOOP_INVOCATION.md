# Night Runner Codex No-op Invocation

## Purpose

NIGHT-RUNNER-07 proves Night Runner can invoke local Codex exactly once in a harmless no-op/report mode.

This is not autonomous coding. It is a guarded invocation that asks Codex for a short readiness note and then verifies the repo did not change.

## Boundaries

Allowed:

- one Codex `exec` invocation,
- read-only sandbox,
- ephemeral session,
- no-op/report prompt only,
- report under `tmp/night_runner`.

Not allowed:

- file edits,
- commits or pushes,
- production restarts,
- live DB writes or migrations,
- OAuth/token/systemd work,
- reading or printing secret contents,
- staging or resetting protected live client files.

## Command

```bash
python3 scripts/ops/night_runner_codex_noop_invoke.py --packet docs/ops/night_runner_codex_noop_packet.yaml
```

## Packet

```text
docs/ops/night_runner_codex_noop_packet.yaml
```

The packet requires:

- `task_mode: noop_report`
- `allow_codex_execute: true`
- `allow_file_edits: false`
- `allow_commit: false`
- `allow_restart: false`
- protected Karen live files listed in `forbidden_files`
- `report_path` under `tmp/night_runner`

## Post-run Verification

The wrapper snapshots before and after:

- git head,
- git status,
- protected live file hashes.

The run is considered unsafe if:

- git head changes,
- git status changes,
- staged files appear,
- protected live file hashes change,
- Codex exits nonzero.

## Next Lane

If this is green, the next lane should still be conservative:

```text
NIGHT-RUNNER-08 — Branch-only Codex Read-only Planning Packet
```

That should ask Codex for a plan/report only, still with no file edits or commits.
