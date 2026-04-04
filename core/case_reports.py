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
            await update.message.reply_text("🟢 Todo activo.")
            return True

        idle.sort(key=lambda x: x[2], reverse=True)

        msg = "⚠️ Casos sin movimiento\n\n"
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

async def try_priority_dashboard(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")

    # --- normalization (local slang) ---
    t = t.replace(" pa ", " para ")
    t = t.replace(" pa'", " para ")
    t = t.replace(" pa", " para")

    # --- trigger detection ---
    if not (
        "que debo hacer" in t
        or "qué debo hacer" in t
        or "prioridades" in t
        or "que tengo pendiente" in t
        or "que tengo" in t
        or "qué tengo" in t
        or "que hay" in t
        or "qué hay" in t
    ):
        return False

    # --- horizon detection ---
    horizon = "today"
    if "mañana" in t or "manana" in t:
        horizon = "tomorrow"
    elif "semana" in t:
        horizon = "week"

    now = datetime.now(ZoneInfo("America/Panama"))

    if horizon == "today":
        limit = now + timedelta(hours=24)
        title = "🎯 Prioridades de hoy"
    elif horizon == "tomorrow":
        start = now + timedelta(days=1)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        limit = start + timedelta(days=1)
        title = "🎯 Prioridades de mañana"
    else:
        limit = now + timedelta(days=7)
        title = "🎯 Prioridades de la semana"

    try:
        conn = _get_conn()
        cur = conn.cursor()

        # --- deadlines ---
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

        urgent = []
        attention = []

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

            if horizon == "today":
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = today_start + timedelta(days=1)

                if not (today_start <= due_dt < today_end):
                    continue

            elif horizon == "tomorrow":
                if not (start <= due_dt < limit):
                    continue

            else:  # week
                if not (now <= due_dt <= limit):
                    continue

            if horizon == "today":
                delta = (due_dt - now).total_seconds()
                if delta <= 86400:
                    urgent.append((name, d, txt))
                else:
                    attention.append((name, d, txt))

            elif horizon == "tomorrow":
                urgent.append((name, d, txt))

            else:  # week
                delta = (due_dt - now).total_seconds()
                if delta <= 86400:
                    urgent.append((name, d, txt))
                else:
                    attention.append((name, d, txt))

        # --- idle cases ---
        cur.execute(
            """
            SELECT
                c.client_name,
                MAX(COALESCE(n.created_at, e.created_at)) as last_activity
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

        idle = []

        for r in rows:
            name = r[0]
            last_activity = r[1]

            if not last_activity:
                continue

            try:
                parsed = datetime.fromisoformat(last_activity)
            except Exception:
                continue

            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=ZoneInfo("America/Panama"))

            days_idle = (now.date() - parsed.date()).days

            if days_idle >= 2:
                idle.append((name, days_idle))

        conn.close()

        # --- build message ---
        msg = f"{title}\n\n"

        if urgent:
            msg += "🔴 Urgente (≤24h)\n"
            for u in urgent[:5]:
                msg += f"• {u[0]} — {u[1]} | {u[2]}\n"
            msg += "\n"

        if attention:
            msg += "🟡 Atención\n"
            for a in attention[:5]:
                msg += f"• {a[0]} — {a[1]} | {a[2]}\n"
            msg += "\n"

        if horizon == "week" and idle:
            msg += "⚪ Inactivos\n"
            for i in sorted(idle, key=lambda x: x[1], reverse=True)[:5]:
                msg += f"• {i[0]} — sin actividad en {i[1]} días\n"

        if not urgent and not attention:
            if horizon == "today":
                msg += "🟢 Nada urgente para hoy."
            elif horizon == "tomorrow":
                msg += "🟢 Nada urgente para mañana."
            else:
                msg += "🟢 Nada urgente esta semana."

        await update.message.reply_text(msg)
        return True

    except Exception as e:
        logger.exception(f"[PRIORITY_DASHBOARD] failed: {e}")
        await update.message.reply_text("No pude calcular las prioridades.")
        return True