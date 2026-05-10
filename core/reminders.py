import time
import logging
from telegram.error import Forbidden

from memory_store import (
    fetch_due_reminders,
    claim_reminder,
    mark_reminder_sent,
    mark_reminder_failed,
    revert_reminder_pending,
    watchdog_reset_stuck_reminders,
)

logger = logging.getLogger("val0-bot")

_VAL0_LAST_TICK_LOG_TS = None


def _reminder_batch_limit() -> int:
    return 50


async def reminder_tick(context):
    global _VAL0_LAST_TICK_LOG_TS

    try:
        # --- Phase 1 Hardening: reset reminders stuck in 'sending' ---
        try:
            reset_count = int(watchdog_reset_stuck_reminders(max_age_seconds=300) or 0)
            if reset_count > 0:
                logger.warning("ReminderWatchdog: reset stuck reminders=%d", reset_count)
        except Exception as e:
            logger.exception("ReminderWatchdog failed: %s", e)

        due = fetch_due_reminders(limit=_reminder_batch_limit())

        # tick telemetry for /health
        import bot as bot_module
        bot_module._VAL0_LAST_TICK_TS = int(time.time())
        bot_module._VAL0_LAST_TICK_DUE = len(due)

        # throttle tick log
        now_ts = int(time.time())
        if _VAL0_LAST_TICK_LOG_TS is None or (now_ts - _VAL0_LAST_TICK_LOG_TS) >= 600:
            logger.info("ReminderRunner tick: due=%d", len(due))
            _VAL0_LAST_TICK_LOG_TS = now_ts

        if due:
            for r in due:
                rid = int(r.get("id"))
                chat_id = int(r.get("chat_id"))
                text = (r.get("text") or "").strip()

                # empty reminder text -> mark sent to avoid clogging
                if not text:
                    if claim_reminder(rid):
                        mark_reminder_sent(rid)
                    continue

                # claim the reminder first to prevent double-send
                if not claim_reminder(rid):
                    continue

                try:
                    # User-facing reminder message should not arrive as raw orphan text.
                    # Keep it simple for v0: clear label + original reminder text.
                    rendered = f"⏰ Recordatorio:\n{text}"
                    await context.bot.send_message(chat_id=chat_id, text=rendered)
                    mark_reminder_sent(rid)
                    logger.info("ReminderRunner: sent id=%s chat_id=%s", rid, chat_id)
                except Exception as e:
                    if isinstance(e, Forbidden):
                        logger.warning(
                            "ReminderRunner: user blocked bot id=%s chat_id=%s",
                            rid,
                            chat_id,
                        )
                        mark_reminder_failed(rid, reason="blocked")
                    else:
                        logger.exception(
                            "ReminderRunner: send failed id=%s chat_id=%s err=%s",
                            rid,
                            chat_id,
                            e,
                        )
                        revert_reminder_pending(rid)

    except Exception as e:
        logger.exception("ReminderRunner tick crashed: %s", e)

    logger.info("[WATCHDOG_CALL] before import")
    try:
        from core.watchdog import deadline_watchdog
        logger.info("[WATCHDOG_CALL] import ok")
        await deadline_watchdog(context)
        logger.info("[WATCHDOG_CALL] after await")
    except Exception as e:
        logger.exception("Deadline watchdog crashed: %s", e)

