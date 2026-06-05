# Night Runner Codex Bridge Discovery

## Purpose

NIGHT-RUNNER-05 checks whether this server can safely bridge Night Runner to a local Codex invocation path.

This is discovery only. It does not run Codex on a task, edit code, commit, restart production, touch client data, or read secret file contents.

## Current Boundary

Night Runner remains a diagnostics/report runner.

Allowed in this lane:

- detect whether a `codex` binary is available,
- detect whether `~/.codex` exists,
- detect whether `auth.json` and `config.toml` are present without printing contents,
- report current branch/status,
- report protected live files as dirty/clean without modifying them,
- recommend the next safe operator lane.

Not allowed:

- autonomous coding,
- Codex task execution,
- commits or pushes,
- production restarts,
- OAuth/token/systemd work,
- live DB migrations,
- live Telegram persistence,
- touching `clients/karen/CLIENT_GROCERY.md`,
- touching `clients/karen/CLIENT_FOLDERS.json`.

## Command

Run from `/opt/val0`:

```bash
python3 scripts/ops/night_runner_codex_bridge_discovery.py
```

The output is safe to paste. It reports only file presence, never token contents.

## Decisions

`CODEX_LOCAL_READY`

- A local Codex binary was found.
- Codex config/auth presence was detected.
- Recommended next lane: `NIGHT-RUNNER-06 branch-only Codex attempt dry-run`.

`CODEX_CONFIG_PRESENT_BUT_BIN_MISSING`

- `~/.codex` exists and has config/auth presence.
- No local `codex` binary was found.
- Recommended next lane: `NIGHT-RUNNER-06A install/repair Codex CLI`.

`CODEX_NOT_CONFIGURED`

- `~/.codex` is missing.
- Recommended next lane: configure Codex locally or stay diagnostics-only.

`NIGHT_RUNNER_DIAGNOSTICS_ONLY`

- Codex is not ready enough for even a no-op local bridge.
- Recommended next lane: `NIGHT-RUNNER-06B diagnostics-only scheduled runner`.

## Bedtime Packet

Packet:

```text
docs/ops/night_runner_codex_bridge_packet.yaml
```

Command:

```bash
python3 scripts/ops/night_runner_dry_run.py docs/ops/night_runner_codex_bridge_packet.yaml --run-tests --allow-protected-dirty-readonly
```

Report path:

```text
tmp/night_runner/codex_bridge_report.md
```

The packet runs the discovery smoke and safety checks only. It does not run the discovery script as a Night Runner command because Night Runner v0 intentionally allows only diagnostics, quality smokes, `py_compile`, and `git diff --check`.

## Safety Notes

- `auth.json` and `config.toml` contents must never be printed.
- Protected live Karen files may be reported as dirty but must not be reset, staged, discarded, or casually committed.
- If a future lane attempts Codex invocation, it must be branch-only, dry-run/no-op first, and must keep Night Runner commits disabled.
