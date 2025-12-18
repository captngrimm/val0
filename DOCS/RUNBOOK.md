# VAL0 RUNBOOK

## Start bot
systemctl restart val0-bot
systemctl status val0-bot

## View logs
journalctl -u val0-bot -n 200 --no-pager

## Rollback to last stable
git checkout v0.1-baseline

## Current working directory
/opt/val0

## Python environment
.venv (must be activated if running manually)

If something breaks:
1. Stop bot
2. Roll back to last tag
3. Restart bot
