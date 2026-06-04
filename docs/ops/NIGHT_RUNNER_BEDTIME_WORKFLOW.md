# Night Runner Bedtime Workflow

## Purpose

This is the operator-friendly wrapper around Night Runner v0. It gives the human one safe bedtime command and one morning report path, without giving Night Runner permission to code autonomously, commit, restart production, or touch live client data.

## Bedtime Command

Run from `/opt/val0`:

```bash
python3 scripts/ops/night_runner_dry_run.py docs/ops/night_runner_bedtime_packet.yaml --run-tests
```

The packet is intentionally boring:

- report-only unless validation passes
- no commits
- no restarts
- no destructive commands
- no live data mutation
- no external APIs
- only approved diagnostics/tests from `tests_to_run`

## Morning Report Path

Default workspace report:

```text
tmp/night_runner/morning_report.md
```

Launchpad-friendly pull:

```bash
cat tmp/night_runner/morning_report.md
```

If an operator needs `/root/LAUNCHPAD/VAL0_output.txt`, copy the report manually after review. Night Runner v0 does not write there by default because the safer default is to keep output inside the repo workspace.

## What The Morning Report Shows

- `PASS_DRY_RUN` or `REFUSED`
- branch and head
- git status summary
- refusal reasons or `none`
- tests listed in the bedtime packet
- commands actually run when `--run-tests` is used
- pass/fail/rejected summary
- command output excerpts
- live-data warning when protected files are dirty
- exact next morning action

## Expected Current Behavior

If these live files are dirty, Night Runner refuses before running tests:

- `clients/karen/CLIENT_GROCERY.md`
- `clients/karen/CLIENT_FOLDERS.json`

That refusal is correct. The report should tell the operator that live Karen data is dirty and must remain unstaged/uncommitted. Night Runner should not clean, reset, stage, or ignore those files on its own.

## Safe Packet

The canonical packet lives at:

```text
docs/ops/night_runner_bedtime_packet.yaml
```

It writes only to:

```text
tmp/night_runner/morning_report.md
```

## Stop Conditions

Stop and read the refusal report if:

- branch does not match the packet
- forbidden/live files are dirty or staged
- staged changes exist
- packet asks for commit/restart/destructive behavior
- packet asks for files outside `allowed_files`
- a command is rejected by the allow-list
- a listed test fails

## Next Improvement

The next safe improvement would be an explicit `--launchpad-output` flag that copies an already-generated report to `/root/LAUNCHPAD/VAL0_output.txt`, with its own path guard and smoke coverage. That should remain opt-in and should not be required for normal tests.
