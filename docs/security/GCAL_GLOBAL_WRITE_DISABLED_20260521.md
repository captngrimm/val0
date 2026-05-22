# GCAL_GLOBAL_WRITE_DISABLED_20260521

Status:
Applied on server / systemd.

Reason:
Global Google Calendar write access was enabled through systemd:

- VAL0_GCAL_ENABLED=1
- VAL0_CALENDAR_WRITE_ENABLED=true

This conflicts with the new client-specific Google Calendar plan, which requires:

- per-client calendar isolation
- read-only first
- no global/legacy token use for client calendars
- no write actions without explicit confirmation

Action taken:
Updated systemd drop-in:

/etc/systemd/system/val0-bot.service.d/zz-gcal-write.conf

From:
VAL0_CALENDAR_WRITE_ENABLED=true

To:
VAL0_CALENDAR_WRITE_ENABLED=false

Then ran:
- systemctl daemon-reload
- systemctl restart val0-bot.service

Verification:
- systemctl environment showed VAL0_CALENDAR_WRITE_ENABLED=false
- val0-bot.service was active/running after restart
- core.gcal_write.WRITE_ENABLED evaluated False

Tokens:
No tokens were deleted or modified.

Remaining risk:
Legacy global read paths still exist through /etc/val0/gcal.
Future Karen/client Google Calendar work must use /etc/val0/clients/<client_id>/gcal/ and read-only first.

Next recommended action:
Patch code documentation and/or runtime guards so global write cannot be accidentally re-enabled for client flows.
