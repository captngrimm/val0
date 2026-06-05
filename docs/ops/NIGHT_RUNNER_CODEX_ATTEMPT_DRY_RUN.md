# Night Runner Codex Attempt Dry-Run

## Purpose

NIGHT-RUNNER-06 proves Night Runner can prepare a branch-only Codex attempt packet without executing Codex.

This is the first controlled step toward sleep-mode work. It is still report-only.

## What It Does

The dry-run script:

- loads a Codex attempt packet,
- verifies the current branch,
- verifies protected Karen live files are not staged,
- allows protected Karen live files to be dirty only when listed as forbidden,
- verifies the Codex binary path exists,
- builds the exact would-run command,
- refuses `allow_codex_execute: true`,
- refuses commits and restarts,
- writes a report under `tmp/night_runner`.

## What It Does Not Do

It does not:

- execute Codex,
- edit files,
- commit,
- push,
- restart production,
- write live DBs,
- migrate production SQLite,
- touch OAuth/tokens/systemd,
- read or print `~/.codex/auth.json` or `config.toml`,
- stage or reset protected live client files.

## Command

```bash
python3 scripts/ops/night_runner_codex_attempt_dry_run.py --packet docs/ops/night_runner_codex_attempt_packet.yaml
```

## Packet

```text
docs/ops/night_runner_codex_attempt_packet.yaml
```

The sample packet is a no-op readiness attempt. It does not represent a real product lane.

## Decisions

`PASS_DRY_RUN_CODEX_ATTEMPT_READY`

- Packet is safe.
- Branch matches.
- Codex binary exists.
- Protected live files are not staged and are listed as forbidden.
- Would-run command was built.
- Codex was not executed.

`REFUSE_PROTECTED_FILE_RISK`

- A protected live file is staged or not listed as forbidden.

`REFUSE_BRANCH_RISK`

- Packet branch does not match current branch.

`REFUSE_CODEX_MISSING`

- No Codex binary was found or the override path is invalid.

`REFUSE_UNSAFE_PACKET`

- Packet requests execution, commits, restarts, unsafe report paths, broad allowed files, or unsafe prompts.

## Next Lane

If this remains green, the next lane can be:

```text
NIGHT-RUNNER-07 — Branch-only Codex No-op Invocation
```

That lane should still use a no-op prompt first, keep commits disabled, and require a human to inspect the report before any real autonomous coding lane exists.
