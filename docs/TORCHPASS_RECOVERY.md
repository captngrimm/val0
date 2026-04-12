# TORCHPASS RECOVERY — VAL0

## Runtime source of truth
- live service: `val0-bot.service`
- systemd fragment: `/etc/systemd/system/val0-bot.service`
- entrypoint: `/opt/val0/.venv/bin/python /opt/val0/bot.py`
- working directory: `/opt/val0`
- live DB: `/opt/val0/val0_memory.enc.db`
- DB mode: SQLCipher / encrypted
- DB key file: `/etc/val0/db_key`

## Not source of truth
These files were audited and are empty stubs:
- `/opt/val0/system/val0.service`
- `/opt/val0/system/service_start.sh`

## Files changed for PM/session continuity MVP
- `/opt/val0/memory_store.py`
- `/opt/val0/bot.py`

## What was added

### In `memory_store.py`
- PM tables:
  - `pm_current_focus`
  - `pm_decisions`
- helper functions:
  - `trim_messages_for_chat(...)`
  - `set_pm_focus(...)`
  - `get_pm_focus(...)`
  - `log_pm_decision(...)`
  - `evaluate_pm_input(...)`

### In `bot.py`
- imports for PM/session helpers
- helper functions:
  - `_is_pm_drift_candidate(...)`
  - `_build_pm_system_block(...)`
  - `focus_cmd(...)`
  - `showfocus_cmd(...)`
- inbound session message persistence inside `_process_text_pipeline(...)`
- PM evaluation inside `_process_text_pipeline(...)`
- PM drift surfacing inside `_process_text_pipeline(...)`
- PM block injection into system rules
- deterministic PM focus query override
- outbound assistant message persistence inside `_send_reply(...)`
- handler registrations:
  - `/focus`
  - `/showfocus`

## Key behavior now working
- `/focus` updates PM focus
- `/showfocus` reads PM focus
- PM is computed on every user input
- drift can surface as:
  - current focus
  - decision
  - next action
- inbound/outbound messages persist to `messages`
- recent messages are trimmed to last 12
- “What are we working on?” resolves from PM focus deterministically
- “What is the current focus?” resolves from PM focus deterministically

## Important compatibility note
Current SQLCipher build did not accept:
- `ON CONFLICT (...) DO UPDATE`

Working pattern:
- `INSERT OR IGNORE`
- then `UPDATE`

## Important isolation rule
PM tables are advisory/control only.
Do NOT mutate canonical:
- case records
- reminder records
- legal timeline records

## Existing live features confirmed during audit
- Telegram voice input pipeline
- Whisper transcription
- voice reply mode via `/voice`
- TTS reply path in `_send_reply()`
- background Forge ingest for voice
- centralized prompt assembly in `_process_text_pipeline()`
- final model gateway in `call_val_openai(...)`
- `_ACTIVE_NODE` / `retoma` flow
- legal/case/reminder routing
- reminder runner / polling loop
- existing recent-memory / semantic-memory hooks

## Smoke tests

### Compile
    cd /opt/val0 || exit 1
    /opt/val0/.venv/bin/python -m compileall -q /opt/val0

### Restart
    sudo systemctl restart val0-bot.service
    sudo systemctl status val0-bot.service --no-pager -l | sed -n '1,80p'

### PM focus test
In Telegram:
    /focus Miguel demo readiness | Implement PM loop + session continuity in Val0 | Defer watch/UI/device work until after MVP

Then:
    Let's redesign the watch UX first.

Expected:
    Current focus: Miguel demo readiness
    Decision: DEFER
    Next action: Log it for later and continue: Miguel demo readiness

### Focus query test
In Telegram:
    What are we working on?

Expected:
    Foco actual: Miguel demo readiness
    Resumen: Implement PM loop + session continuity in Val0
    Roadmap: Defer watch/UI/device work until after MVP

## Known caveat
Generic conversation can still pick up noise from older reminder/task/case layers unless intercepted deterministically or improved in a later continuity polish pass.
