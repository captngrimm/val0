# ROUTER-05 Shadow Observation Playbook

## Purpose

Use this playbook to observe Intent Router v2 predictions against the legacy handlers that actually consume Karen RC messages.

Shadow mode is diagnostic only:

- It does not change routing.
- It does not handle messages.
- It does not replace existing Karen RC hard gates.
- It is used before Router Refactor Mode to collect examples of predicted intent vs actual handler labels.

## Safety Rules

- Shadow mode must default OFF.
- Enable it only for short observation windows.
- Disable it after the test window.
- Do not run it during sensitive user sessions unless the session is explicitly a router observation test.
- Do not use one mismatch to change runtime behavior immediately.
- Karen RC full smoke must pass before and after observation:

```bash
python3 scripts/quality/karen_rc_full_smoke.py --keep-going
```

## Enable Shadow Mode

Use a systemd drop-in for the bot service. Do not edit `.env`.

Create or update:

```text
/etc/systemd/system/val0-bot.service.d/intent-router-shadow.conf
```

with:

```ini
[Service]
Environment="VAL0_INTENT_ROUTER_V2_SHADOW=true"
```

Then reload and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart val0-bot.service
sudo systemctl status val0-bot.service --no-pager
```

The helper command `sudo scripts/ops/router_shadow_mode.sh status` is safe to use for observation: status output redacts secret-like environment values such as keys, tokens, passwords, credentials, and `RESEND_API_KEY`. Do not paste raw systemd environment output externally.

## Disable Shadow Mode

Remove the drop-in or set the value to false. The preferred cleanup is to remove the drop-in:

```bash
sudo rm -f /etc/systemd/system/val0-bot.service.d/intent-router-shadow.conf
sudo systemctl daemon-reload
sudo systemctl restart val0-bot.service
sudo systemctl status val0-bot.service --no-pager
```

Verify that new shadow logs stop appearing:

```bash
sudo journalctl -u val0-bot.service -n 100 --no-pager | grep -F "[INTENT_ROUTER_V2_SHADOW]"
```

No new `[INTENT_ROUTER_V2_SHADOW]` lines should appear after disable and restart.

Shadow mode should be disabled after every observation test window.

## Suggested Test Commands

Send a small, intentional set of Karen-style commands:

- `Val que tareas tengo activas?`
- `Val, qué tengo mañana?`
- `Val agenda prueba calendario mañana a las 10am`
- `Val elimina el evento 1`
- `Recuérdame en 10 minutos llamar a Mabel`
- `Val resume el último documento`
- `Val resume con OCR el último documento`
- `Qué tengo guardado del caso del terreno`

Use commands that are safe for the current test window. Avoid destructive commands unless the operator has a disposable test event or reminder ready.

## Log Inspection

Prediction logs:

```bash
sudo journalctl -u val0-bot.service --since "15 minutes ago" --no-pager | grep -F "[INTENT_ROUTER_V2_SHADOW]"
```

Actual legacy handler labels:

```bash
sudo journalctl -u val0-bot.service --since "15 minutes ago" --no-pager | grep -F "[INTENT_ROUTER_V2_ACTUAL]"
```

Predicted vs actual comparison:

```bash
sudo journalctl -u val0-bot.service --since "15 minutes ago" --no-pager | grep -F "[INTENT_ROUTER_V2_COMPARE]"
```

Last 100 comparison lines:

```bash
sudo journalctl -u val0-bot.service --no-pager | grep -F "[INTENT_ROUTER_V2_COMPARE]" | tail -100
```

## Interpretation

- `match=True` means the shadow router prediction agrees with the legacy handler label.
- `match=False` means the phrase is a candidate for future router refactor work or route-priority review.
- Do not automatically change runtime behavior based on one mismatch.
- Collect examples with the phrase category, predicted intent, actual handler, and whether Karen saw correct behavior.

Useful comparison shape:

```text
[INTENT_ROUTER_V2_COMPARE] predicted=task_query actual=task_query match=True confidence=0.95
```

## Rollback

1. Disable the shadow environment drop-in.
2. Reload systemd.
3. Restart `val0-bot.service`.
4. Confirm no new `[INTENT_ROUTER_V2_SHADOW]` logs appear.
5. Run the full RC smoke:

```bash
python3 scripts/quality/karen_rc_full_smoke.py --keep-going
```

If the service does not restart cleanly, keep shadow disabled and use normal Launchpad/runtime recovery steps.
