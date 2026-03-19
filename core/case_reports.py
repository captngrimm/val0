from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging

from memory_store import _get_conn
from core.case_mvp import _clean

logger = logging.getLogger("val0-bot")


async def try_idle_cases(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")

    if "sin movimiento" not in t and "casos inactivos" not in t:
        return False

    try:
        conn = _get_conn()
        cur = conn.cursor()

        now = datetime.now(ZoneInfo("America/Panama"))

        cur.execute(
            """
            SELECT
                c.client_name,
                c.expediente,
                MAX(
                    COALESCE(n.created_at, e.created_at)
                ) as last_activity
            FROM cases c
            LEFT JOIN case_notes n
                ON CAST(n.case_id AS TEXT) = CAST(c.expediente AS TEXT)
            LEFT JOIN case_events e
                ON CAST(e.case_id AS TEXT) = CAST(c.expediente AS TEXT)
            WHERE c.chat_id=?
            GROUP BY c.expediente, c.client_name
            """,
            (int(chat_id),),
        )

        rows = cur.fetchall() or []
        conn.close()

        idle = []

        for r in rows:
            client_name = r["client_name"] if hasattr(r, "keys") else r[0]
            expediente = r["expediente"] if hasattr(r, "keys") else r[1]
            last_activity = r["last_activity"] if hasattr(r, "keys") else r[2]

            if not last_activity:
                continue

            parsed = None

            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    parsed = datetime.strptime(last_activity, fmt)
                    break
                except Exception:
                    pass

            if parsed is None:
                try:
                    parsed = datetime.fromisoformat(last_activity)
                except Exception:
                    continue

            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=ZoneInfo("America/Panama"))
            else:
                parsed = parsed.astimezone(ZoneInfo("America/Panama"))

            days_idle = (now.date() - parsed.date()).days

            if days_idle >= 2:
                idle.append((client_name, expediente, days_idle))

        if not idle:
            await update.message.reply_text("🟢 Todo activo, Boss.")
            return True

        idle.sort(key=lambda x: x[2], reverse=True)

        msg = "⚠️ Boss — casos sin movimiento\n\n"
        for client_name, expediente, days_idle in idle[:10]:
            msg += f"• {client_name} — sin actividad en {days_idle} días\n"

        await update.message.reply_text(msg)
        return True

    except Exception as e:
        logger.exception(f"[IDLE_CASES] failed: {e}")
        await update.message.reply_text("No pude revisar los casos inactivos.")
        return True


async def try_daily_work_summary(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")

    if "resumen de trabajo" not in t and "trabajo de hoy" not in t:
        return False

    try:
        conn = _get_conn()
        cur = conn.cursor()

        today = datetime.now(ZoneInfo("America/Panama")).date()

        # --- Notes today ---
        cur.execute(
            """
            SELECT COUNT(*)
            FROM case_notes
            WHERE chat_id=?
              AND DATE(created_at)=?
            """,
            (int(chat_id), str(today)),
        )
        notes_today = cur.fetchone()[0]

        # --- Events today ---
        cur.execute(
            """
            SELECT COUNT(*)
            FROM case_events
            WHERE chat_id=?
              AND DATE(created_at)=?
            """,
            (int(chat_id), str(today)),
        )
        events_today = cur.fetchone()[0]

        # --- Cases touched today ---
        cur.execute(
            """
            SELECT DISTINCT c.client_name
            FROM case_notes n
            JOIN cases c ON c.expediente = n.case_id
            WHERE n.chat_id=?
              AND DATE(n.created_at)=?
            """,
            (int(chat_id), str(today)),
        )
        touched_cases = [r[0] for r in cur.fetchall()]

        # --- Upcoming deadlines (48h) ---
        cur.execute(
            """
            SELECT c.client_name, e.deadline_date, e.event_text
            FROM case_events e
            JOIN cases c ON c.expediente = CAST(e.case_id AS TEXT)
            WHERE c.chat_id=?
              AND e.deadline_date IS NOT NULL
            ORDER BY e.deadline_date ASC
            """,
            (int(chat_id),),
        )

        rows = cur.fetchall() or []

        now = datetime.now(ZoneInfo("America/Panama"))
        limit = now + timedelta(hours=48)

        upcoming = []

        for r in rows:
            name = r[0]
            d = r[1]
            txt = r[2]

            try:
                due_dt = datetime.strptime(d, "%Y-%m-%d").replace(
                    tzinfo=ZoneInfo("America/Panama")
                )
            except Exception:
                continue

            if now <= due_dt <= limit:
                upcoming.append((name, d, txt))

        conn.close()

        msg = "⚖️ Trabajo de hoy\n\n"

        msg += "📊 Actividad\n"
        msg += f"• Notas creadas: {notes_today}\n"
        msg += f"• Eventos registrados: {events_today}\n\n"

        if upcoming:
            msg += "⏳ Vencimientos próximos (48h)\n"
            for u in upcoming:
                msg += f"• {u[0]} — {u[1]} | {u[2]}\n"
            msg += "\n"

        if touched_cases:
            msg += "📁 Casos tocados hoy\n"
            for c in touched_cases:
                msg += f"• {c}\n"

        await update.message.reply_text(msg)
        return True

    except Exception as e:
        logger.exception(f"[DAILY_SUMMARY] failed: {e}")
        await update.message.reply_text("No pude generar el resumen de hoy.")
        return True

