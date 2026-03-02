import os
import time
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from memory_store import reminder_stats, list_reminders


# tick telemetry for /health (optional)
_VAL0_LAST_TICK_TS = None
_VAL0_LAST_TICK_DUE = None


def _now_local_str() -> str:
    # Keep it dependency-free: show UTC + TZ label
    tz = os.getenv("VAL0_TZ", "America/Panama")
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC") + f" (TZ={tz})"


def _reminder_poll_seconds() -> int:
    # must match bot.py semantics
    try:
        return int(os.getenv("VAL0_REMINDER_POLL_SECONDS", "30"))
    except Exception:
        return 30


async def ops_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        stats = reminder_stats()
        interval = _reminder_poll_seconds()
        db_path = os.getenv("VAL0_DB_PATH", "")
        gcal = os.getenv("VAL0_GCAL_ENABLED", "0")
        include_unbound = os.getenv("VAL0_GCAL_INCLUDE_UNBOUND", "0")

        lines = [
            "OPS",
            f"- time: {_now_local_str()}",
            f"- db_path: {db_path}",
            f"- gcal_enabled: {gcal}  include_unbound: {include_unbound}",
            f"- reminder_poll_seconds: {interval}",
            f"- reminders: total={stats.get('total')} pending={stats.get('pending')} due_now={stats.get('due_now')} sending={stats.get('sending')} sent={stats.get('sent')}",
        ]
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"OPS\n- time: {_now_local_str()}\n- error: {e}")


async def reminders_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Usage: /reminders [N]
    n = 25
    try:
        parts = (update.message.text or "").strip().split()
        if len(parts) >= 2:
            n = int(parts[1])
    except Exception:
        n = 25
    n = max(1, min(50, n))

    try:
        rows = list_reminders(statuses=["pending", "sending"], limit=n)
        if not rows:
            await update.message.reply_text("REMINDERS\n- none (pending/sending)")
            return

        lines = ["REMINDERS (pending/sending)"]
        for r in rows:
            rid = r.get("id")
            due = r.get("due_at_utc")
            st = r.get("status")
            txt = (r.get("text") or "").replace("\n", " ").strip()
            if len(txt) > 60:
                txt = txt[:60] + "…"
            lines.append(f"- #{rid} | {due} | {st} | {txt}")
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"REMINDERS\n- error: {e}")


async def health_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    interval = _reminder_poll_seconds()
    db_path = os.getenv("VAL0_DB_PATH", "")
    key_file = os.getenv("VAL0_DB_KEY_FILE", "")

    # last tick signals (optional if you wire it later)
    global _VAL0_LAST_TICK_TS, _VAL0_LAST_TICK_DUE
    last_ts = _VAL0_LAST_TICK_TS if isinstance(_VAL0_LAST_TICK_TS, int) else None
    age = (int(time.time()) - last_ts) if last_ts else None

    db_ok = True
    db_err = ""
    stats = {}
    try:
        stats = reminder_stats()
    except Exception as e:
        db_ok = False
        db_err = str(e)

    lines = [
        "HEALTH",
        f"- time: {_now_local_str()}",
        f"- db_path: {db_path}",
        f"- db_key_file: {key_file}",
        f"- reminder_poll_seconds: {interval}",
        f"- db_ok: {db_ok}" + (f" ({db_err})" if db_err else ""),
    ]
    if stats:
        lines.append(
            f"- reminders: total={stats.get('total')} pending={stats.get('pending')} due_now={stats.get('due_now')} sending={stats.get('sending')} sent={stats.get('sent')}"
        )
    if age is None:
        lines.append("- last_tick: unknown")
    else:
        lines.append(f"- last_tick_age_seconds: {age}  last_tick_due: {_VAL0_LAST_TICK_DUE}")

    await update.message.reply_text("\n".join(lines))

