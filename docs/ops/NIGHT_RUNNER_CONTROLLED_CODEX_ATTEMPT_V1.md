# Night Runner Controlled Codex Attempt v1

## Purpose

NIGHT-RUNNER-24 moves toward a controlled one-lane Codex attempt without enabling execution yet.

The existing attempt wrapper is still dry-run oriented and must continue to refuse `allow_codex_execute: true` until a later lane explicitly adds, tests, and reviews execution support.

## Minimal Guard Conditions Before Real Execution

A future controlled Codex execution lane must require all of these conditions before running Codex:

- `allow_codex_execute: true` is accepted only by a reviewed execution-capable wrapper, not the current dry-run wrapper.
- The task mode is a single scoped lane, not an autonomous loop.
- `allow_commit`, `allow_restart`, and live writes remain false.
- Protected live client files are forbidden, dirty-but-unstaged only, and hash-checked before and after.
- `allowed_files` lists exact non-runtime paths; broad entries such as `.` or `**/*` remain forbidden.
- Runtime files such as `bot.py` and `core/**` remain forbidden until a later explicit runtime lane.
- The report path is under `tmp/night_runner/`.
- The command uses a safe Codex sandbox mode and never prints token, OAuth, or `~/.codex` secret contents.
- The wrapper snapshots git head/status before and after and refuses if forbidden files change.
- A dedicated report artifact states whether Codex actually executed.

## NR24 Decision

For NIGHT-RUNNER-24, Codex execution is not enabled.

This lane only documents the guard conditions and produces a dedicated local report artifact so the operator can review the next step safely.

## Recommended Next Lane

```text
NIGHT-RUNNER-25 — Controlled Codex Attempt Guard Smoke
```

That lane can add a focused smoke for the guard conditions before any real Codex execution path is implemented.
