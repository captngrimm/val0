import re
import logging
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

from memory_store import _get_conn

logger = logging.getLogger("val0-bot")

def _clean(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

async def try_case_summary(update, chat_id, text) -> bool:
    """
    Handles: 'Resumen del expediente <id>'
    Returns True if it responded and should short-circuit the pipeline.
    """
    if not update or not getattr(update, "message", None):
        return False

    cleaned = _clean(text)
    m = re.search(r"\bresumen\s+del\s+expediente\s+([\w\-]+)\b", cleaned)
    if not m:
        return False

    expediente = m.group(1).strip()

    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, expediente, client_name, created_at, updated_at "
            "FROM cases WHERE chat_id=? AND lower(expediente)=lower(?)",
            (int(chat_id), expediente),
        )
        row = cur.fetchone()
        if not row:
            await update.message.reply_text(f"No encuentro el expediente {expediente} en tu base de datos.")
            conn.close()
            return True

        case_id = row["id"]
        client_name = row["client_name"] or "—"

        cur.execute(
            "SELECT event_text, start_date, deadline_date, term_days, created_at "
            "FROM case_events WHERE chat_id=? AND case_id=? "
            "ORDER BY id DESC LIMIT 10",
            (int(chat_id), int(case_id)),
        )
        events = cur.fetchall() or []
        conn.close()

        lines = []
        lines.append(f"📁 Expediente {row['expediente']} | Cliente: {client_name}")
        lines.append("Últimos movimientos (máx 10):")

        if not events:
            lines.append("- (sin eventos registrados todavía)")
        else:
            for e in events:
                et = (e["event_text"] or "").strip()
                sd = e["start_date"] or ""
                dd = e["deadline_date"] or ""
                td = e["term_days"]
                bits = [et] if et else ["(evento)"]
                if td is not None:
                    bits.append(f"{td} días")
                if sd:
                    bits.append(f"inicio {sd}")
                if dd:
                    bits.append(f"vence {dd}")
                lines.append("- " + " | ".join(bits))

        await update.message.reply_text("\n".join(lines))
        return True

    except Exception as e:
        logger.exception(f"[CASE MVP] try_case_summary failed: {e}")
        await update.message.reply_text("Se cayó el resumen del expediente. Reviso logs.")
        return True


async def try_due_today(update, chat_id, text) -> bool:
    """
    Handles: 'Qué vence hoy?'
    Returns True if it responded and should short-circuit the pipeline.
    """
    if not update or not getattr(update, "message", None):
        return False

    cleaned = _clean(text)
    if not re.search(r"\b(que|qué)\s+vence\s+hoy\b", cleaned):
        return False

    tz = ZoneInfo("America/Panama")
    today = datetime.now(tz).date().isoformat()

    try:
        conn = _get_conn()
        cur = conn.cursor()

        # Pull case deadlines where deadline_date == today
        cur.execute(
            "SELECT c.expediente, ce.event_text, ce.deadline_date "
            "FROM case_events ce "
            "JOIN cases c ON c.id = ce.case_id "
            "WHERE ce.chat_id=? AND ce.deadline_date=? "
            "ORDER BY c.expediente ASC, ce.id ASC",
            (int(chat_id), today),
        )
        rows = cur.fetchall() or []
        conn.close()

        if not rows:
            await update.message.reply_text("Hoy no tengo vencimientos registrados en tu base de datos.")
            return True

        lines = [f"⏰ Vence hoy ({today}):"]
        for r in rows:
            exp = r["expediente"]
            et = (r["event_text"] or "").strip() or "(evento)"
            lines.append(f"- {exp}: {et}")

        await update.message.reply_text("\n".join(lines))
        return True

    except Exception as e:
        logger.exception(f"[CASE MVP] try_due_today failed: {e}")
        await update.message.reply_text("Se cayó el chequeo de vencimientos de hoy. Reviso logs.")
        return True
