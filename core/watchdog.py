from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from memory_store import _get_conn
import logging

logger = logging.getLogger(__name__)


async def deadline_watchdog(context):
    """
    Runs every scheduler tick.
    Alerts when deadlines are within 48h.
    Persists sent alerts in DB so restarts do not resend them.
    Respects proactive mode: quiet / tactical / war.
    """
    logger.info("[WATCHDOG] deadline_watchdog tick")

    try:
        mode = "normal"

        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT c.client_name, e.deadline_date, e.event_text
            FROM case_events e
            JOIN cases c ON c.expediente = CAST(e.case_id AS TEXT)
            WHERE c.chat_id=?
              AND e.deadline_date IS NOT NULL
            ORDER BY e.deadline_date ASC
            """,
            (1789350565,),
        )

        rows = cur.fetchall() or []

        now = datetime.now(ZoneInfo("America/Panama"))
        limit = now + timedelta(hours=48)

        alerts = []

        for row in rows:
            client_name = row["client_name"] if hasattr(row, "keys") else row[0]
            deadline_date = row["deadline_date"] if hasattr(row, "keys") else row[1]
            event_text = row["event_text"] if hasattr(row, "keys") else row[2]

            if not deadline_date:
                continue

            try:
                due_dt = datetime.strptime(deadline_date, "%Y-%m-%d").replace(
                    tzinfo=ZoneInfo("America/Panama")
                )
            except Exception:
                continue

            if not (now <= due_dt <= limit):
                continue

            alert_key = f"deadline_48h|{client_name}|{deadline_date}|{event_text}"

            cur.execute(
                """
                SELECT 1
                FROM watchdog_alerts
                WHERE alert_key=?
                LIMIT 1
                """,
                (alert_key,),
            )
            already_sent = cur.fetchone()

            if already_sent:
                continue

            # skip reminder-style events; this alert is only for legal/procedural deadlines
            if (event_text or "").strip().upper().startswith("RECORDATORIO:"):
                continue

            alerts.append((client_name, deadline_date, event_text, alert_key))

        if not alerts:
            conn.close()
            return

        logger.info(f"[WATCHDOG] alerts_found={len(alerts)}")

        msg = "⚠️ Boss — términos por vencer (48h)\n\n"
        for client_name, deadline_date, event_text, _alert_key in alerts:
            msg += f"• {client_name} — {deadline_date} | {event_text}\n"

        await context.bot.send_message(chat_id=1789350565, text=msg)

        for _client_name, _deadline_date, _event_text, alert_key in alerts:
            cur.execute(
                """
                INSERT OR IGNORE INTO watchdog_alerts(alert_key, alert_type)
                VALUES(?, ?)
                """,
                (alert_key, "deadline_48h"),
            )

        conn.commit()
        conn.close()

    except Exception as e:
        logger.exception(f"[WATCHDOG] failed: {e}")

