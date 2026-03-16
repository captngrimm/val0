import re
import os
import logging
import unicodedata
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Dict, List, Any, Optional, Tuple

from memory_store import (
    _get_conn,
    fetch_timeline_between,
    fetch_timeline_for_parent,
    list_reminders_for_chat,
    fetch_case_notes
)

logger = logging.getLogger("val0-bot")

async def send_msg(msg_obj, text: str):
    """
    Unified message sender for Val.
    Ensures consistent formatting across the bot.
    """
    try:
        await msg_obj.reply_text(
            text,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except Exception:
        # fallback if Markdown formatting breaks
        await msg_obj.reply_text(text)

def format_human_timestamp(ts: str) -> str:
    """
    Converts DB timestamp into human friendly format.

    Today:
        5:28 PM

    Older:
        Vie 13 Mar · 5:28 PM
    """

    from datetime import datetime
    from zoneinfo import ZoneInfo

    if not ts:
        return ""

    tz = ZoneInfo("America/Panama")

    try:
        dt = datetime.fromisoformat(ts)
    except Exception:
        return ts

    now = datetime.now(tz)

    weekdays = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
              "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

    time_str = dt.strftime("%I:%M %p").lstrip("0")

    if dt.date() == now.date():
        return time_str

    weekday = weekdays[dt.weekday()]
    month = months[dt.month - 1]

    return f"{weekday} {dt.day} {month} · {time_str}"

def classify_human_recency(ts: str) -> str:
    """
    Classifies a DB timestamp into a simple human bucket.
    """
    if not ts:
        return "Anterior"

    tz = ZoneInfo("America/Panama")

    try:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone(tz)
    except Exception:
        return "Anterior"

    now = datetime.now(tz)
    days_diff = (now.date() - dt.date()).days

    if days_diff == 0:
        return "Hoy"
    if 0 < days_diff <= 7:
        return "Esta semana"
    return "Anterior"

def _clean(s: str) -> str:
    s = (s or "").strip().lower()

    # Remove accents / diacritics (qué → que, próximas → proximas)
    s = "".join(
        ch for ch in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(ch)
    )

    s = re.sub(r"\s+", " ", s)
    return s


def _dt_local_from_item(it: Dict[str, Any], tz: ZoneInfo) -> Optional[datetime]:
    """
    Deterministic local datetime for an item.
    Prefer due_ts (UTC seconds). Fallback to parsing due_local if present.
    """
    try:
        ts = it.get("due_ts")
        if ts is not None:
            ts_i = int(ts)
            return datetime.fromtimestamp(ts_i, tz=timezone.utc).astimezone(tz)
    except Exception:
        pass

    # Fallback: due_local like "YYYY-MM-DD HH:MM"
    dl = (it.get("due_local") or "").strip()
    if dl:
        try:
            # interpret as local time already
            dt = datetime.strptime(dl, "%Y-%m-%d %H:%M")
            return dt.replace(tzinfo=tz)
        except Exception:
            return None

    return None


def _group_items_by_local_date(
    items: List[Dict[str, Any]],
    tz: ZoneInfo,
) -> List[Tuple[str, List[Dict[str, Any]]]]:
    """
    Group items by local YYYY-MM-DD. Deterministic ordering:
    - group keys sorted ascending
    - within group sorted by (due_ts asc, source asc, title asc)
    """
    buckets: Dict[str, List[Dict[str, Any]]] = {}

    for it in items:
        dt_local = _dt_local_from_item(it, tz)
        if dt_local is None:
            # shove unknowns into a special bucket
            key = "—"
        else:
            key = dt_local.date().isoformat()

        buckets.setdefault(key, []).append(it)

    def _sort_key(it: Dict[str, Any]) -> Tuple[int, str, str]:
        try:
            ts = int(it.get("due_ts") or 0)
        except Exception:
            ts = 0
        src = str(it.get("source") or "")
        title = str(it.get("title") or "")
        return (ts, src, title)

    grouped: List[Tuple[str, List[Dict[str, Any]]]] = []
    for day in sorted(buckets.keys()):
        group = buckets[day]
        group_sorted = sorted(group, key=_sort_key)
        grouped.append((day, group_sorted))

    return grouped


SPANISH_WEEKDAYS = [
    "Lunes", "Martes", "Miércoles", "Jueves",
    "Viernes", "Sábado", "Domingo",
]

SPANISH_MONTHS = [
    "", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
]

def _render_due_grouped(
    *,
    header: str,
    items: List[Dict[str, Any]],
    tz: ZoneInfo,
) -> str:
    """
    Render grouped-by-date, deterministic.

    Normalized display:
    - HH:MM | evento       | vence mañana
    - HH:MM | nota         | juez sugirió conciliación
    - HH:MM | recordatorio | revisar el caso 524242024
    """
    def _normalize_title(src: str, title: str, case_id: str) -> str:
        t = (title or "").strip()

        # Strip obvious CASE / expediente duplication from event rows
        if src == "event":
            if case_id:
                t = re.sub(rf"(?i)^\s*{re.escape(case_id)}\s*:\s*", "", t)
                t = re.sub(rf"(?i)\bCASE\s*:\s*{re.escape(case_id)}\s*", "", t)
                t = re.sub(rf"(?i)\bcaso\s*:?[\s#]*{re.escape(case_id)}\s*", "", t)
                t = re.sub(rf"(?i)\bexpediente\s*:?[\s#]*{re.escape(case_id)}\s*", "", t)
            t = re.sub(r"\s{2,}", " ", t).strip(" :-|")
            return t or "(evento)"

        # Notes/reminders/tasks should display raw useful text only
        if src in ("note", "reminder", "task"):
            if case_id:
                t = re.sub(rf"(?i)^\s*{re.escape(case_id)}\s*:\s*", "", t)
            t = re.sub(r"\s{2,}", " ", t).strip(" :-|")
            return t or "(sin texto)"

        return t or "(evento)"

    def _label_for_source(src: str) -> str:
        """
        Deterministic source labeling for timeline entries.
        Ensures stable UX and supports Sprint 12.3 source trace.
        """

        src = (src or "").strip().lower()

        if src in ("note", "case_note"):
            return "nota"

        if src in ("reminder", "reminders"):
            return "recordatorio"

        if src in ("task", "tasks"):
            return "tarea"

        if src in ("event", "case_event", "calendar"):
            return "evento"

        if src in ("transcript", "voice"):
            return "transcripción"

        return "item"

    lines: List[str] = [header]

    grouped = _group_items_by_local_date(items, tz)
    for day, group in grouped:
        count = len(group)

        if day == "—":
            pretty_day = "Sin fecha"
        else:
            try:
                dt_day = datetime.strptime(day, "%Y-%m-%d").date()
                today_local = datetime.now(tz).date()
                tomorrow_local = today_local + timedelta(days=1)

                weekday = SPANISH_WEEKDAYS[dt_day.weekday()]
                month = SPANISH_MONTHS[dt_day.month]
                base_day = f"{weekday} {dt_day.day} {month}"

                if dt_day == today_local:
                    pretty_day = f"Hoy ({base_day})"
                elif dt_day == tomorrow_local:
                    pretty_day = f"Mañana ({base_day})"
                else:
                    pretty_day = base_day
            except Exception:
                pretty_day = day

        lines.append(f"\n📅 {pretty_day}")

        if count >= 2:
            lines.append(f"⚠️ {count} términos / eventos ese día")

        for it in group:
            src = (it.get("source") or "db").strip().lower()
            case_id = (it.get("case_id") or "").strip()
            title = _normalize_title(src, (it.get("title") or "").strip(), case_id)

            dt_local = _dt_local_from_item(it, tz)
            hhmm = dt_local.strftime("%H:%M") if dt_local else "--:--"
            label = _label_for_source(src)

            lines.append(f"- {hhmm} | {label:<11} | {title}")

    return "\n".join(lines)

def _render_due_conflicts(conflicts: List[Dict[str, Any]]) -> str:
    """
    Render deterministic user-facing conflict warnings.
    """
    if not conflicts:
        return ""

    lines: List[str] = ["\n⚠️ Ojo: encontré discrepancias entre expediente y calendario"]

    for c in conflicts:
        case_id = (c.get("case_id") or "—").strip()
        db_due = (c.get("db_due_local") or "—").strip()
        gcal_due = (c.get("gcal_due_local") or "—").strip()
        db_title = (c.get("db_title") or "(evento)").strip()
        gcal_title = (c.get("gcal_title") or "(evento)").strip()

        lines.append(f"\nCASE:{case_id}")
        lines.append(f"• expediente: {db_due} — {db_title}")
        lines.append(f"• calendario: {gcal_due} — {gcal_title}")

    return "\n".join(lines)

def _render_due_conflicts(conflicts: List[Dict[str, Any]]) -> str:
    """
    Render deterministic user-facing conflict warnings.
    """
    if not conflicts:
        return ""

    lines: List[str] = ["\n⚠️ Ojo: encontré discrepancias entre expediente y calendario"]

    for c in conflicts:
        case_id = (c.get("case_id") or "—").strip()
        db_due = (c.get("db_due_local") or "—").strip()
        gcal_due = (c.get("gcal_due_local") or "—").strip()
        db_title = (c.get("db_title") or "(evento)").strip()
        gcal_title = (c.get("gcal_title") or "(evento)").strip()

        lines.append(f"\nCASE:{case_id}")
        lines.append(f"• expediente: {db_due} — {db_title}")
        lines.append(f"• calendario: {gcal_due} — {gcal_title}")

    return "\n".join(lines)

def _audit_merge(*, gate: str, chat_id: int, label: str, items: list) -> None:
    """Phase 1 audit: read-only per-query merge summary."""
    try:
        import logging
        from collections import Counter

        items = items or []
        total = len(items)
        sources = Counter((it.get("source") or "unknown") for it in items)

        # case_ids: unique bound case identifiers (strings)
        case_ids = sorted({str(it.get("case_id")) for it in items if it.get("case_id")})

        # case_items: count of items that are bound to a case_id (not unique)
        case_item_count = sum(1 for it in items if it.get("case_id"))

        logging.getLogger("val0-bot").info(
            "[AUDIT] gate=%s chat_id=%s label=%s total=%d db=%d gcal=%d case_items=%d case_ids=%d",
            gate,
            int(chat_id),
            label,
            total,
            int(sources.get("db", 0)),
            int(sources.get("gcal", 0)),
            int(case_item_count),
            int(len(case_ids)),
        )
    except Exception:
        pass

def generate_case_cockpit(chat_id: int, case_id: str) -> str:
    """
    Builds a compact cockpit summary for a case.
    """

    from memory_store import fetch_case_notes
    from memory_store import get_reminders_range

    case_id = (case_id or "").strip()
    if not case_id:
        return "No puedo identificar el caso."

    notes = fetch_case_notes(chat_id, case_id, limit=3)

    notes_lines = []
    for n in notes:
        txt = (n.get("note_text") or "").strip()
        if txt:
            notes_lines.append(f"- {txt}")

    if not notes_lines:
        notes_lines.append("- sin notas registradas")

    # next tasks/events
    try:
        tasks = get_reminders_range(chat_id, limit=3)
    except Exception:
        tasks = []

    task_lines = []
    for t in tasks:
        txt = (t.get("text") or "").strip()
        if txt:
            task_lines.append(f"- {txt}")

    if not task_lines:
        task_lines.append("- ninguno")

    out = []

    out.append(f"📁 Caso {case_id}")
    out.append("")
    out.append("Notas recientes")
    out.extend(notes_lines)
    out.append("")
    out.append("Próximos eventos / tareas")
    out.extend(task_lines)

    return "\n".join(out)

def format_human_timestamp(ts: str) -> str:
    """
    Converts DB timestamp into human friendly format.

    Today:
        5:28 PM

    Older:
        Vie 13 Mar · 5:28 PM
    """
    if not ts:
        return ""

    tz = ZoneInfo("America/Panama")

    try:
        dt_utc = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        dt = dt_utc.astimezone(tz)
    except Exception:
        return ts

    now = datetime.now(tz)

    weekdays = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
              "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

    time_str = dt.strftime("%I:%M %p").lstrip("0")

    if dt.date() == now.date():
        return time_str

    weekday = weekdays[dt.weekday()]
    month = months[dt.month - 1]

    return f"{weekday} {dt.day} {month} · {time_str}"

def _window_bounds_local(window: str, tz: ZoneInfo):
    now = datetime.now(tz)

    if window == "today":
        start_local = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=tz)
        end_local = datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=tz)
        return start_local, end_local

    if window == "week":
        start_local = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=tz) - timedelta(days=6)
        end_local = datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=tz)
        return start_local, end_local

    return None, None


def generate_case_timeline_window(chat_id: int, case_id: str, window: str) -> str:
    """
    Builds a compact timeline-only view for a case in a time window.
    window: 'today' or 'week'
    """
    case_id = (case_id or "").strip()
    if not case_id:
        return "No puedo identificar el caso."

    tz = ZoneInfo("America/Panama")
    start_local, end_local = _window_bounds_local(window, tz)
    if not start_local or not end_local:
        return "Ventana no soportada."

    parent_ref = f"CASE:{case_id}"

    notes = fetch_case_notes(chat_id, case_id, limit=50)
    rows = []

    for row in notes:
        txt = (row.get("note_text") or "").strip()
        created_at = (row.get("created_at") or "").strip()
        if not txt or not created_at:
            continue

        try:
            dt_utc = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            dt_local = dt_utc.astimezone(tz)
        except Exception:
            continue

        if start_local <= dt_local <= end_local:
            txt = txt.replace("desde harness", "").strip()
            rows.append((dt_local, txt, "note"))

    timeline = fetch_timeline_for_parent(
        chat_id=chat_id,
        parent_ref=parent_ref,
        entity_types=["reminder", "task"],
        statuses=["pending", "sent", "cancelled"],
        limit=50,
    )

    for row in timeline:
        txt = (row.get("text") or "").strip()
        due_ts = row.get("due_ts")
        if not txt or due_ts is None:
            continue

        try:
            dt_local = datetime.fromtimestamp(int(due_ts), tz=tz)
        except Exception:
            continue

        if start_local <= dt_local <= end_local:
            rows.append((dt_local, txt, "reminder"))

    rows.sort(key=lambda x: x[0], reverse=True)

    label = "hoy" if window == "today" else "esta semana"
    lines = [f"🕒 <b>Actividad del caso ({label})</b>", ""]

    if not rows:
        lines.append("— Sin actividad registrada —")
        return "\n".join(lines)

    today_rows = []
    week_rows = []

    for dt_local, txt, kind in rows[:8]:
        now_local = datetime.now(tz)

        weekdays = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

        time_str = dt_local.strftime("%I:%M %p").lstrip("0")

        if dt_local.date() == now_local.date():
            label = time_str
        else:
            weekday = weekdays[dt_local.weekday()]
            month = months[dt_local.month - 1]
            label = f"{weekday} {dt_local.day} {month} · {time_str}"

        if "·" not in label:  # today entries
            today_rows.append((label, txt, kind))
        else:
            week_rows.append((label, txt, kind))

    if today_rows:
        lines.append("Hoy")
        for label, txt, kind in today_rows:
            icon = "📝" if kind == "note" else "⏰"
            lines.append(f"• {icon} {label} | {txt}")
        lines.append("")

    if week_rows:
        lines.append("Esta semana")
        for label, txt, kind in week_rows:
            icon = "📝" if kind == "note" else "⏰"
            lines.append(f"• {icon} {label} | {txt}")

    return "\n".join(lines)

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

        lines: List[str] = []
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

async def try_case_status(update, chat_id, text) -> bool:
    """
    Handles natural-language case status / summary requests, e.g.:
    - resumen del caso 524242024
    - dame un resumen del caso 524242024
    - estado del caso 524242024
    - cómo va el caso 524242024
    - por donde va el caso 524242024
    - situación actual del caso 524242024
    """
    if not update or not getattr(update, "message", None):
        return False

    cleaned = _clean(text)

    # First try direct expediente-based status queries
    m = re.search(
        r"\b("
        r"resumen|"
        r"dame\s+un\s+resumen|"
        r"estado|status|"
        r"como\s+va|cómo\s+va|"
        r"como\s+vamos\s+con|cómo\s+vamos\s+con|"
        r"por\s+donde\s+va|por\s+dónde\s+va|"
        r"situacion\s+actual|situación\s+actual"
        r")\s+"
        r"(?:del\s+|el\s+|de[l]?\s+|con\s+)?"
        r"(?:caso|expediente)\s+"
        r"(\d{4,})\b",
        cleaned,
    )

    case_id = None

    if m:
        case_id = m.group(2).strip()
    else:
        # Then try client-name based queries:
        # cómo va el caso de Leticia
        # estado del caso de Leticia
        # resumen del caso de Leticia
        m_name = re.search(
            r"\b("
            r"resumen|"
            r"dame\s+un\s+resumen|"
            r"estado|status|"
            r"como\s+va|cómo\s+va|"
            r"como\s+vamos\s+con|cómo\s+vamos\s+con|"
            r"por\s+donde\s+va|por\s+dónde\s+va|"
            r"situacion\s+actual|situación\s+actual"
            r")\s+"
            r"(?:del\s+|el\s+|de[l]?\s+|con\s+)?"
            r"(?:caso|expediente)\s+de\s+(.+?)\s*$",
            cleaned,
        )
        if not m_name:
            return False

        client_name = (m_name.group(2) or "").strip()
        if not client_name:
            return False

        from memory_store import get_case_by_client_name

        row = get_case_by_client_name(int(chat_id), client_name)
        if not row:
            await update.message.reply_text(
                f"No encontré un caso registrado para cliente {client_name}."
            )
            return True

        case_id = str(row.get("expediente") or "").strip()
        if not case_id:
            await update.message.reply_text(
                f"Encontré un registro para {client_name}, pero no tiene expediente usable."
            )
            return True

    parent_ref = f"CASE:{case_id}"
    tz = ZoneInfo(os.getenv("VAL0_TZ", "America/Panama"))

    # Fetch client name for cockpit display
    client_name = None
    try:
        from memory_store import _get_conn
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT client_name
            FROM cases
            WHERE chat_id=? AND expediente=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (int(chat_id), case_id),
        )
        row = cur.fetchone()
        conn.close()
        if row:
            client_name = row["client_name"] if hasattr(row, "keys") else row[0]
    except Exception:
        client_name = None

    conn = _get_conn()
    cur = conn.cursor()

    # latest note (skip polluted old query-like rows)
    cur.execute(
        """
        SELECT note_text, created_at
        FROM case_notes
        WHERE chat_id=? AND case_id=?
        ORDER BY id DESC
        LIMIT 10
        """,
        (int(chat_id), case_id),
    )
    rows = cur.fetchall() or []

    recent_notes = []
    for row in rows:
        txt = (row["note_text"] if hasattr(row, "keys") else row[0]) or ""
        ts = (row["created_at"] if hasattr(row, "keys") else row[1]) or ""
        txt = txt.strip()
        low = txt.lower()

        if (
            low.startswith("registrar caso")
            or low.startswith("registrar expediente")
            or low.startswith("cómo va el caso")
            or low.startswith("como va el caso")
            or low.startswith("cómo vamos con el caso")
            or low.startswith("como vamos con el caso")
            or low.startswith("por donde va el caso")
            or low.startswith("por dónde va el caso")
            or low.startswith("resumen del caso")
            or low.startswith("dame un resumen del caso")
            or low.startswith("estado del caso")
            or low.startswith("situacion actual del caso")
            or low.startswith("situación actual del caso")
        ):
            continue

        if txt and ts:
            try:
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                recent_notes.append((format_human_timestamp(ts), txt, ts))
            except Exception:
                continue

    last_note = recent_notes[0] if recent_notes else None

    # next pending reminder
    cur.execute(
        """
        SELECT text, due_at_utc
        FROM reminders
        WHERE chat_id=? AND parent_ref=? AND status='pending'
        ORDER BY due_at_utc ASC
        LIMIT 1
        """,
        (int(chat_id), parent_ref),
    )
    row = cur.fetchone()

    next_rem = None
    if row:
        txt = (row["text"] if hasattr(row, "keys") else row[0]) or ""
        ts = (row["due_at_utc"] if hasattr(row, "keys") else row[1]) or ""
        txt = txt.strip()
        if txt and ts:
            try:
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                next_rem = (dt.astimezone(tz).strftime("%H:%M"), txt)
            except Exception:
                pass

    # counts
    cur.execute(
        "SELECT COUNT(*) FROM case_notes WHERE chat_id=? AND case_id=?",
        (int(chat_id), case_id),
    )
    note_count = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*)
        FROM reminders
        WHERE chat_id=? AND parent_ref=? AND status='pending'
        """,
        (int(chat_id), parent_ref),
    )
    rem_count = cur.fetchone()[0]

    conn.close()

    if not last_note and not next_rem and note_count == 0 and rem_count == 0:
        await update.message.reply_text(
            f"No tengo actividad registrada para CASE:{case_id}.",
            parse_mode="Markdown",
        )
        return True

    lines = [f"🗂️ <b>CASE:{case_id}</b>", ""]

    if client_name:
        lines.append("👤 <u>Cliente</u>")
        lines.append(f"{client_name}")
        lines.append("")

    lines.append("📌 <u>Resumen</u>")

    if last_note:
        lines.append(f"• Última nota: {last_note[1]}")
    else:
        lines.append("• Última nota: —")

    if next_rem:
        lines.append(f"• Próximo pendiente: {next_rem[0]} | {next_rem[1]}")
    else:
        lines.append("• Próximo pendiente: —")

    if recent_notes:
        lines.append("")
        lines.append("🕒 <u>Actividad reciente</u>")

        grouped = {"Hoy": [], "Esta semana": [], "Anterior": []}

        for hhmm, txt, raw_ts in recent_notes[:5]:
            txt = txt.replace("desde harness", "").strip()
            bucket = classify_human_recency(raw_ts)
            grouped[bucket].append(f"• {hhmm} | {txt}")

        if grouped["Hoy"]:
            lines.append("")
            lines.append("Hoy")
            lines.extend(grouped["Hoy"])

        if grouped["Esta semana"]:
            lines.append("")
            lines.append("Esta semana")
            lines.extend(grouped["Esta semana"])

        if grouped["Anterior"]:
            lines.append("")
            lines.append("Anterior")
            lines.extend(grouped["Anterior"])

    lines.append("")
    lines.append("📊 <u>Estado</u>")
    lines.append(f"• Notas: {note_count}")
    lines.append(f"• Pendientes: {rem_count}")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    return True

async def try_case_cockpit(update, chat_id, text) -> bool:
    """
    Natural-language gate for case cockpit summary.
    """

    if not update or not getattr(update, "message", None):
        return False

    import re

    t = (text or "").strip().lower()

    m = re.search(r"caso\s+(\d{4,})", t)
    if not m:
        return False

    case_id = m.group(1)

    if "como va" in t or "cómo va" in t or "estado" in t:
        out = generate_case_cockpit(int(chat_id), case_id)
        await send_msg(update.message, out)
        return True

    return False

async def try_case_add_note(update, chat_id, text) -> bool:
    """
    Handles:
    guarda esto en el caso de <cliente>: <nota>
    guarda esto en el caso <expediente>: <nota>
    """

    if not update or not getattr(update, "message", None):
        return False

    import re
    t = (text or "").strip()

    if "guarda esto en el caso" not in t.lower():
        return False

    # split command
    parts = t.split(":", 1)
    if len(parts) != 2:
        await update.message.reply_text("Falta el texto de la nota.")
        return True

    left, note_text = parts
    note_text = note_text.strip()

    case_id = None

    # numeric expediente
    m = re.search(r"caso\s+(\d{4,})", left, re.IGNORECASE)
    if m:
        case_id = m.group(1)

    # client name
    if not case_id and "caso de " in left.lower():
        client_name = left.lower().split("caso de ", 1)[1].strip()

        try:
            conn = _get_conn()
            cur = conn.cursor()

            cur.execute(
                """
                SELECT expediente
                FROM cases
                WHERE chat_id=?
                AND lower(client_name)=lower(?)
                ORDER BY id DESC
                LIMIT 1
                """,
                (int(chat_id), client_name),
            )

            row = cur.fetchone()
            conn.close()

            if row:
                case_id = row["expediente"] if hasattr(row, "keys") else row[0]

        except Exception:
            case_id = None

    if not case_id:
        await update.message.reply_text("No encuentro ese caso.")
        return True

    from memory_store import insert_case_note

    insert_case_note(
        chat_id=int(chat_id),
        case_id=str(case_id),
        note_text=note_text,
        source="text"
    )

    await update.message.reply_text(f"Nota guardada en CASE:{case_id}.")
    return True

def generate_case_timeline_since_last_hearing(chat_id: int, case_id: str) -> str:
    """
    Shows case activity after the most recent hearing-like event/note.
    """
    tz = ZoneInfo("America/Panama")
    case_id = (case_id or "").strip()
    if not case_id:
        return "No puedo identificar el caso."

    parent_ref = f"CASE:{case_id}"

    notes = fetch_case_notes(chat_id, case_id, limit=100)
    rows = []

    for row in notes:
        txt = (row.get("note_text") or "").strip()
        created_at = (row.get("created_at") or "").strip()
        if not txt or not created_at:
            continue

        try:
            dt_utc = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            dt_local = dt_utc.astimezone(tz)
        except Exception:
            continue

        txt_clean = txt.replace("desde harness", "").strip()
        rows.append((dt_local, txt_clean, "note"))

    timeline = fetch_timeline_for_parent(
        chat_id=chat_id,
        parent_ref=parent_ref,
        entity_types=["reminder", "task"],
        statuses=["pending", "sent", "cancelled"],
        limit=100,
    )

    for row in timeline:
        txt = (row.get("text") or "").strip()
        due_ts = row.get("due_ts")
        if not txt or due_ts is None:
            continue

        try:
            dt_local = datetime.fromtimestamp(int(due_ts), tz=timezone.utc).astimezone(tz)
        except Exception:
            continue

        rows.append((dt_local, txt, "reminder"))

    rows.sort(key=lambda x: x[0], reverse=True)

    # Find the latest hearing-like anchor
    anchor_dt = None
    for dt_local, txt, kind in rows:
        low = _clean(txt)
        if low.startswith("audiencia") or low.startswith("hearing") or low.startswith("vista"):
            anchor_dt = dt_local
            break
    lines = ["🕒 <b>Actividad desde la última audiencia</b>", ""]

    if anchor_dt is None:
        lines.append("— No encuentro una audiencia registrada para usar como referencia —")
        return "\n".join(lines)

    filtered = [(dt, txt, kind) for dt, txt, kind in rows if dt > anchor_dt]

    if not filtered:
        lines.append("— No hay actividad posterior a la última audiencia —")
        return "\n".join(lines)

    for dt_local, txt, kind in filtered[:8]:
        now_local = datetime.now(tz)
        weekdays = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                  "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

        time_str = dt_local.strftime("%I:%M %p").lstrip("0")
        if dt_local.date() == now_local.date():
            label = time_str
        else:
            weekday = weekdays[dt_local.weekday()]
            month = months[dt_local.month - 1]
            label = f"{weekday} {dt_local.day} {month} · {time_str}"

        icon = "📝" if kind == "note" else "⏰"
        lines.append(f"• {icon} {label} | {txt}")

    return "\n".join(lines)

def generate_case_health(chat_id: int, case_id: str) -> str:
    tz = ZoneInfo("America/Panama")
    case_id = (case_id or "").strip()
    if not case_id:
        return "No puedo identificar el caso."

    parent_ref = f"CASE:{case_id}"

    notes = fetch_case_notes(chat_id, case_id, limit=50)
    timeline = fetch_timeline_for_parent(
        chat_id=chat_id,
        parent_ref=parent_ref,
        entity_types=["reminder", "task"],
        statuses=["pending", "sent"],
        limit=50,
    )

    latest_dt = None

    # notes
    for row in notes:
        created_at = (row.get("created_at") or "").strip()
        if not created_at:
            continue
        try:
            dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone(tz)
            if latest_dt is None or dt > latest_dt:
                latest_dt = dt
        except Exception:
            pass

    # reminders
    for row in timeline:
        due_ts = row.get("due_ts")
        if due_ts is None:
            continue
        try:
            dt = datetime.fromtimestamp(int(due_ts), tz=timezone.utc).astimezone(tz)
            if latest_dt is None or dt > latest_dt:
                latest_dt = dt
        except Exception:
            pass

    if latest_dt is None:
        return "⚠️ <b>Salud del caso</b>\n\n• Sin actividad registrada"

    now_local = datetime.now(tz)
    days_idle = (now_local.date() - latest_dt.date()).days

    if days_idle <= 3:
        status = "normal"
    elif days_idle <= 14:
        status = "atención"
    else:
        status = "inactivo"

    now_local = datetime.now(tz)

    weekdays = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

    time_str = latest_dt.strftime("%I:%M %p").lstrip("0")

    if latest_dt.date() == now_local.date():
        latest_label = f"Hoy · {time_str}"
    else:
        weekday = weekdays[latest_dt.weekday()]
        month = months[latest_dt.month - 1]
        latest_label = f"{weekday} {latest_dt.day} {month} · {time_str}"

    lines = [
        "⚠️ <b>Salud del caso</b>",
        "",
        f"• Última actividad: {latest_label}",
        f"• Días sin actividad: {days_idle}",
        "",
        "Estado sugerido",
        f"• {status}",
    ]

    return "\n".join(lines)    

def generate_cases_requiring_attention(chat_id: int) -> str:
    tz = ZoneInfo("America/Panama")

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT expediente, client_name
        FROM cases
        WHERE chat_id=?
        ORDER BY id DESC
        """,
        (int(chat_id),),
    )
    cases = cur.fetchall() or []
    conn.close()

    items = []

    for row in cases:
        expediente = (row["expediente"] if hasattr(row, "keys") else row[0]) or ""
        client_name = (row["client_name"] if hasattr(row, "keys") else row[1]) or ""

        notes = fetch_case_notes(chat_id, str(expediente), limit=20)
        parent_ref = f"CASE:{expediente}"
        timeline = fetch_timeline_for_parent(
            chat_id=chat_id,
            parent_ref=parent_ref,
            entity_types=["reminder", "task"],
            statuses=["pending", "sent"],
            limit=20,
        )

        latest_dt = None

        for n in notes:
            created_at = (n.get("created_at") or "").strip()
            if not created_at:
                continue
            try:
                dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone(tz)
                if latest_dt is None or dt > latest_dt:
                    latest_dt = dt
            except Exception:
                pass

        for t in timeline:
            due_ts = t.get("due_ts")
            if due_ts is None:
                continue
            try:
                dt = datetime.fromtimestamp(int(due_ts), tz=timezone.utc).astimezone(tz)
                if latest_dt is None or dt > latest_dt:
                    latest_dt = dt
            except Exception:
                pass

        if latest_dt is None:
            days_idle = 999
        else:
            days_idle = (datetime.now(tz).date() - latest_dt.date()).days

        if days_idle <= 3:
            status = "normal"
            icon = "🟢"
        elif days_idle <= 14:
            status = "atención"
            icon = "🟡"
        else:
            status = "inactivo"
            icon = "🔴"

        if status != "normal":
            label = client_name.strip() or f"CASE:{expediente}"
            items.append((days_idle, f"{icon} {label} — {days_idle} días sin actividad"))

    items.sort(key=lambda x: x[0], reverse=True)

    lines = ["⚠️ <b>Casos que requieren atención</b>", ""]
    if not items:
        lines.append("🟢 No veo casos que requieran atención ahora mismo.")
        return "\n".join(lines)

    for _, line in items[:20]:
        lines.append(f"• {line}")

    return "\n".join(lines)

async def try_case_timeline_window(update, chat_id, text) -> bool:
    """
    Natural-language gate for case timeline windows.

    Examples:
    - qué pasó hoy en el caso 524242024
    - qué pasó esta semana en el caso de Leticia
    - actividad del caso de Leticia esta semana
    """

    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")
    logger.info("[TIMELINE_WINDOW] FUNCTION ENTERED")
    logger.info(f"[CASE_TIMELINE_WINDOW] raw={text!r} cleaned={t!r}")

    # --- intent detection ---
    if "caso" not in t:
        return False

    if not any(x in t for x in ("que paso", "actividad", "movimiento")):
        return False

    if "hoy" in t:
        window = "today"
    elif "esta semana" in t or "semana" in t:
        window = "week"
    else:
        return False
    # --- end intent detection ---

    case_id = None

    # Case by numeric id
    m = re.search(r"caso\s+(\d{4,})", t)
    if m:
        case_id = (m.group(1) or "").strip()

    # Case by client name
    if not case_id and ("caso de " in t or "caso de" in t or "en el caso de " in t):

        if "en el caso de " in t:
            client_name = t.split("en el caso de ", 1)[1]
        else:
            client_name = t.split("caso de ", 1)[1]

        # Remove time words
        client_name = re.sub(r"\b(hoy|esta semana|semana)\b", "", client_name)

        # Remove punctuation
        client_name = re.sub(r"[^\w\s]", "", client_name)

        client_name = client_name.strip()

        if client_name:
            try:
                conn = _get_conn()
                cur = conn.cursor()

                cur.execute(
                    """
                    SELECT expediente
                    FROM cases
                    WHERE chat_id=?
                      AND lower(client_name)=lower(?)
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (int(chat_id), client_name),
                )

                row = cur.fetchone()
                conn.close()

                if row:
                    case_id = (row["expediente"] if hasattr(row, "keys") else row[0]) or ""
                    case_id = str(case_id).strip()

            except Exception as e:
                logger.exception(f"[CASE_TIMELINE_WINDOW] client lookup failed: {e}")
                case_id = None

    if not case_id:
        logger.info("[CASE_TIMELINE_WINDOW] gate hit but case unresolved")
        return False

    logger.info(f"[CASE_TIMELINE_WINDOW] HIT window={window} case_id={case_id}")

    out = generate_case_timeline_window(int(chat_id), case_id, window)

    await update.message.reply_text(out, parse_mode="HTML")

    return True

async def try_case_timeline_since_last_hearing(update, chat_id, text) -> bool:
    """
    Handles:
    - qué pasó desde la última audiencia en el caso ...
    - que paso desde la ultima audiencia en el caso ...
    """
    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")

    if "caso" not in t:
        return False

    if "desde la ultima audiencia" not in t:
        return False

    case_id = None

    m = re.search(r"caso\s+(\d{4,})", t)
    if m:
        case_id = (m.group(1) or "").strip()

    if not case_id and ("caso de " in t or "en el caso de " in t):
        if "en el caso de " in t:
            client_name = t.split("en el caso de ", 1)[1]
        else:
            client_name = t.split("caso de ", 1)[1]

        client_name = re.sub(r"\b(desde la ultima audiencia|hoy|esta semana|semana)\b", "", client_name)
        client_name = re.sub(r"[^\w\s]", "", client_name).strip()

        if client_name:
            try:
                conn = _get_conn()
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT expediente
                    FROM cases
                    WHERE chat_id=?
                      AND lower(client_name)=lower(?)
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (int(chat_id), client_name),
                )
                row = cur.fetchone()
                conn.close()
                if row:
                    case_id = (row["expediente"] if hasattr(row, "keys") else row[0]) or ""
                    case_id = str(case_id).strip()
            except Exception:
                case_id = None

    if not case_id:
        await update.message.reply_text("No encuentro ese caso en tu base de datos.")
        return True

    out = generate_case_timeline_since_last_hearing(int(chat_id), case_id)
    await update.message.reply_text(out, parse_mode="HTML")
    return True

async def try_case_health(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")

    if "caso" not in t:
        return False

    if not any(x in t for x in ("salud del caso", "estado del caso", "riesgo del caso")):
        return False

    case_id = None

    m = re.search(r"caso\s+(\d{4,})", t)
    if m:
        case_id = (m.group(1) or "").strip()

    if not case_id and "caso de " in t:
        client_name = t.split("caso de ", 1)[1]
        client_name = re.sub(r"[^\w\s]", "", client_name).strip()

        if client_name:
            try:
                conn = _get_conn()
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT expediente
                    FROM cases
                    WHERE chat_id=?
                      AND lower(client_name)=lower(?)
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (int(chat_id), client_name),
                )
                row = cur.fetchone()
                conn.close()

                if row:
                    case_id = (row["expediente"] if hasattr(row, "keys") else row[0])
                    case_id = str(case_id).strip()
            except Exception:
                case_id = None

    if not case_id:
        await update.message.reply_text("No encuentro ese caso.")
        return True

    out = generate_case_health(int(chat_id), case_id)
    await update.message.reply_text(out, parse_mode="HTML")
    return True

async def try_case_health_legend(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")

    if "estado del caso" not in t and "salud del caso" not in t:
        return False

    if not any(x in t for x in ("que significa", "qué significa", "significa")):
        return False

    out = "\n".join([
        "📊 <b>Estados de salud del caso</b>",
        "",
        "🟢 <b>Normal</b>",
        "Actividad en los últimos 3 días.",
        "",
        "🟡 <b>Atención</b>",
        "Entre 4 y 14 días sin actividad.",
        "",
        "🔴 <b>Inactivo</b>",
        "15 días o más sin actividad.",
    ])

    await update.message.reply_text(out, parse_mode="HTML")
    return True

async def try_timeline_for_case(update, chat_id, text) -> bool:
    """
    Handles: 'qué tengo del caso 524242024'
    Reads linked timeline rows from reminders via parent_ref = CASE:<id>.
    Returns True if it responded and should short-circuit the pipeline.
    """
    if not update or not getattr(update, "message", None):
        return False

    cleaned = _clean(text)
    m = re.search(r"\b(que|qué)\s+tengo\s+del\s+(caso|expediente)\s+(\d{4,})\b", cleaned)
    if not m:
        return False

    case_id = m.group(3).strip()
    parent_ref = f"CASE:{case_id}"

    try:
        rows = fetch_timeline_for_parent(
            chat_id=int(chat_id),
            parent_ref=parent_ref,
            entity_types=["reminder", "task"],
            statuses=["pending", "sending"],
            limit=50,
        )

        tz = ZoneInfo(os.getenv("VAL0_TZ", "America/Panama"))

        items: List[Dict[str, Any]] = []
        for r in rows:
            due_str = (r.get("due_at_utc") or "").strip()
            if not due_str:
                continue

            due_dt_utc = datetime.strptime(due_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            due_ts = int(due_dt_utc.timestamp())

            entity_type = (r.get("entity_type") or "reminder").strip().lower()
            src = "task" if entity_type == "task" else "reminder"

            items.append(
                {
                    "due_ts": due_ts,
                    "title": (r.get("text") or "").strip() or "(sin texto)",
                    "case_id": case_id,
                    "source": src,
                    "external_id": str(r.get("id")),
                }
            )

        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, note_text, created_at
            FROM case_notes
            WHERE chat_id = ?
              AND case_id = ?
            ORDER BY id DESC
            LIMIT 20
            """,
            (int(chat_id), str(case_id)),
        )
        note_rows = cur.fetchall() or []
        conn.close()

        for r in note_rows:
            note_id = r["id"] if hasattr(r, "keys") else r[0]
            note_text = (r["note_text"] if hasattr(r, "keys") else r[1]) or ""
            created_at = (r["created_at"] if hasattr(r, "keys") else r[2]) or ""
            if not note_text or not created_at:
                continue

            note_text = note_text.strip()
            low = note_text.lower()

            # Filter polluted historical rows captured by older generic note path
            if (
                low.startswith("case:")
                or low.startswith("qué tengo")
                or low.startswith("que tengo")
                or low.startswith("recuérdame")
                or low.startswith("recuerdame")
                or low.startswith("acuérdame")
                or low.startswith("acuerdame")
                or low.startswith("recordame")
                or low.startswith("nota caso")
                or low.startswith("nota expediente")
            ):
                continue

            try:
                note_dt_utc = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except Exception:
                continue

            items.append(
                {
                    "due_ts": int(note_dt_utc.timestamp()),
                    "title": note_text,
                    "case_id": case_id,
                    "source": "note",
                    "external_id": str(note_id),
                }
            )

        if not items:
            await update.message.reply_text(f"No tengo recordatorios, tareas o notas ligadas a {parent_ref}.")
            return True

        msg = _render_due_grouped(
            header=f"🗂️ {parent_ref}:",
            items=items,
            tz=tz,
        )

        await update.message.reply_text(msg)
        return True

    except Exception as e:
        logger.exception(f"[CASE MVP] try_timeline_for_case failed: {e}")
        await update.message.reply_text("Se cayó el timeline ligado al caso. Reviso logs.")
        return True

async def try_case_timeline_for_case(update, chat_id, text) -> bool:
    """
    Handles:
      - qué tengo del caso <expediente>
      - qué ha pasado en el caso <expediente>

    Reads entity-linked reminders + notes for:
      parent_ref = CASE:<expediente>

    Renders via _render_due_grouped().
    """
    if not update or not getattr(update, "message", None):
        return False

    cleaned = _clean(text)

    m = re.search(
        r"\b((que|qué)\s+tengo\s+del\s+|(que|qué)\s+ha\s+pasado\s+en\s+(el\s+)?)(caso|expediente)\s+(\d{4,})\b",
        cleaned,
    )
    if not m:
        return False

    expediente = (m.group(6) or "").strip()
    if not expediente:
        return False

    parent_ref = f"CASE:{expediente}"
    tz = ZoneInfo(os.getenv("VAL0_TZ", "America/Panama"))

    try:
        conn = _get_conn()
        cur = conn.cursor()

        items: List[Dict[str, Any]] = []

        cur.execute(
            """
            SELECT id, text, due_at_utc
            FROM reminders
            WHERE chat_id = ?
              AND status = 'pending'
              AND parent_ref = ?
            ORDER BY due_at_utc ASC, id ASC
            """,
            (int(chat_id), parent_ref),
        )
        reminder_rows = cur.fetchall() or []

        for row in reminder_rows:
            rid = row["id"] if hasattr(row, "keys") else row[0]
            txt = row["text"] if hasattr(row, "keys") else row[1]
            due_at_utc = row["due_at_utc"] if hasattr(row, "keys") else row[2]

            txt = (txt or "").strip() or "(sin texto)"
            due_at_utc = due_at_utc or ""

            try:
                due_dt_utc = datetime.strptime(due_at_utc, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                due_ts = int(due_dt_utc.timestamp())
            except Exception:
                due_ts = 0

            items.append(
                {
                    "title": txt,
                    "due_ts": due_ts,
                    "case_id": expediente,
                    "source": "reminder",
                    "external_id": str(rid),
                }
            )

        cur.execute(
            """
            SELECT id, note_text, created_at
            FROM case_notes
            WHERE chat_id = ?
              AND case_id = ?
            ORDER BY id ASC
            """,
            (int(chat_id), expediente),
        )
        note_rows = cur.fetchall() or []
        conn.close()

        for row in note_rows:
            nid = row["id"] if hasattr(row, "keys") else row[0]
            txt = row["note_text"] if hasattr(row, "keys") else row[1]
            created_at = row["created_at"] if hasattr(row, "keys") else row[2]

            txt = (txt or "").strip() or "(sin texto)"
            created_at = created_at or ""

            try:
                note_dt_utc = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                due_ts = int(note_dt_utc.timestamp())
            except Exception:
                due_ts = 0

            items.append(
                {
                    "title": txt,
                    "due_ts": due_ts,
                    "case_id": expediente,
                    "source": "note",
                    "external_id": str(nid),
                }
            )

        if not items:
            await update.message.reply_text(f"No tengo recordatorios, tareas o notas ligadas a {parent_ref}.")
            return True

        msg = _render_due_grouped(
            header=f"📅 CASE TIMELINE: {expediente}",
            items=items,
            tz=tz,
        )
        await update.message.reply_text(msg)
        return True

    except Exception as e:
        logger.exception(f"[CASE MVP] try_case_timeline_for_case failed: {e}")
        await update.message.reply_text("Se cayó el timeline del caso. Reviso logs.")
        return True
    
async def try_pending_list(update, chat_id, text) -> bool:
    """
    Handles:
      - qué pendientes tengo
      - que pendientes tengo
      - pendientes

    Reads only pending reminders for the current chat.
    Deterministic, no model.
    """
    if not update or not getattr(update, "message", None):
        return False

    cleaned = _clean(text)

    if not (
        re.search(r"\b(que|qué)\s+pendientes\s+tengo\b", cleaned)
        or cleaned == "pendientes"
    ):
        return False

    tz = ZoneInfo(os.getenv("VAL0_TZ", "America/Panama"))

    try:
        rows = list_reminders_for_chat(
            int(chat_id),
            statuses=["pending"],
            limit=50,
        )

        lines: List[str] = ["📌 Pendientes", ""]

        if not rows:
            lines.append("- no tienes pendientes")
            await update.message.reply_text("\n".join(lines))
            return True

        for r in rows:
            txt = (r.get("text") or "").strip() or "(sin texto)"
            due_at_utc = (r.get("due_at_utc") or "").strip()

            try:
                due_dt_utc = datetime.strptime(due_at_utc, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                hhmm = due_dt_utc.astimezone(tz).strftime("%H:%M")
            except Exception:
                hhmm = "--:--"

            lines.append(f"- {hhmm} | {txt}")

        await update.message.reply_text("\n".join(lines))
        return True

    except Exception as e:
        logger.exception(f"[CASE MVP] try_pending_list failed: {e}")
        await update.message.reply_text("Se cayó la lista de pendientes. Reviso logs.")
        return True

async def try_timeline_today(update, chat_id, text) -> bool:
    """
    Handles: 'qué tengo hoy'
    Unified read path from reminders table (reminders + tasks).
    Returns True if it responded and should short-circuit the pipeline.
    """
    if not update or not getattr(update, "message", None):
        return False

    cleaned = _clean(text)
    if not re.search(r"\b(que|qué)\s+tengo\s+hoy\b", cleaned):
        return False

    tz = ZoneInfo(os.getenv("VAL0_TZ", "America/Panama"))
    today_date = datetime.now(tz).date()
    start_local = datetime(today_date.year, today_date.month, today_date.day, 0, 0, 0, tzinfo=tz)
    end_local = datetime(today_date.year, today_date.month, today_date.day, 23, 59, 59, tzinfo=tz)

    start_utc = start_local.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    end_utc = end_local.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    try:
        rows = fetch_timeline_between(
            chat_id=int(chat_id),
            start_utc=start_utc,
            end_utc=end_utc,
            entity_types=["reminder", "task"],
            statuses=["pending", "sending"],
        )

        if not rows:
            await update.message.reply_text("Hoy no tengo recordatorios o tareas registrados.")
            return True

        items: List[Dict[str, Any]] = []
        for r in rows:
            due_str = (r.get("due_at_utc") or "").strip()
            if not due_str:
                continue

            due_dt_utc = datetime.strptime(due_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            due_ts = int(due_dt_utc.timestamp())

            entity_type = (r.get("entity_type") or "reminder").strip().lower()
            src = "task" if entity_type == "task" else "reminder"

            items.append(
                {
                    "due_ts": due_ts,
                    "title": (r.get("text") or "").strip() or "(sin texto)",
                    "case_id": None,
                    "source": src,
                    "external_id": str(r.get("id")),
                }
            )

        if not items:
            await update.message.reply_text("Hoy no tengo recordatorios o tareas registrados.")
            return True

        msg = _render_due_grouped(
            header="🗓️ Hoy:",
            items=items,
            tz=tz,
        )

        await update.message.reply_text(msg)
        return True

    except Exception as e:
        logger.exception(f"[CASE MVP] try_timeline_today failed: {e}")
        await update.message.reply_text("Se cayó el timeline de hoy. Reviso logs.")
        return True

async def try_due_today(update, chat_id, text) -> bool:
    """
    Handles: 'Qué vence hoy?'
    Returns True if it responded and should short-circuit the pipeline.
    """
    if not update or not getattr(update, "message", None):
        return False

    cleaned = _clean(text)
    if not re.search(r"\b(que|qué)\s+(vence|tengo)\s+hoy\b", cleaned):
        return False

    tz = ZoneInfo(os.getenv("VAL0_TZ", "America/Panama"))
    today = datetime.now(tz).date().isoformat()

    try:
        conn = _get_conn()
        cur = conn.cursor()

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

        # --- deterministic merge: DB + optional Google Calendar (no model) ---
        from core.due_merge import merge_due_items

        # compute date parts once (fixes y referenced-before-assignment edge cases)
        y, m, d = map(int, today.split("-"))

        db_items: List[Dict[str, Any]] = []
        for r in rows:
            exp = r["expediente"]
            et = (r["event_text"] or "").strip() or "(evento)"

            # Deterministic rule: DB deadlines treated as 09:00 local on deadline_date
            local_dt = datetime(y, m, d, 9, 0, 0, tzinfo=tz)
            due_ts = int(local_dt.astimezone(timezone.utc).timestamp())

            db_items.append({
                "due_ts": due_ts,
                "title": et,
                "case_id": exp,      # expediente as stable case identifier
                "source": "db",
                "external_id": None,
            })

        # Merge range for "today": [00:00, 23:59:59] local → UTC
        start_local = datetime(y, m, d, 0, 0, 0, tzinfo=tz)
        end_local = datetime(y, m, d, 23, 59, 59, tzinfo=tz)

        
        merged = merge_due_items(
            db_items=db_items,
            range_start_utc=start_local.astimezone(timezone.utc),
            range_end_utc=end_local.astimezone(timezone.utc),
        )
        items = merged["items"]
        conflicts = merged["conflicts"]

        _audit_merge(gate="due_today", chat_id=int(chat_id), label=f"{today}", items=items)
        if not items:
            await update.message.reply_text("Hoy no tengo vencimientos registrados.")
            return True

        msg = _render_due_grouped(
            header=f"⏰ Vence hoy ({today}):",
            items=items,
            tz=tz,
        )

        if conflicts:
            msg = msg + "\n" + _render_due_conflicts(conflicts)

        await update.message.reply_text(msg)
        return True

        msg = _render_due_grouped(
            header=f"⏰ Vence hoy ({today}):",
            items=items,
            tz=tz,
        )

        if conflicts:
            msg = msg + "\n" + _render_due_conflicts(conflicts)

        await update.message.reply_text(msg)
        return True

    except Exception as e:
        logger.exception(f"[CASE MVP] try_due_today failed: {e}")
        await update.message.reply_text("Se cayó el chequeo de vencimientos de hoy. Reviso logs.")
        return True

async def try_due_tomorrow(update, chat_id, text) -> bool:
    """
    Handles: 'qué tengo mañana', 'qué vence mañana', 'agenda mañana'
    Returns True if it responded and should short-circuit the pipeline.
    """
    if not update or not getattr(update, "message", None):
        return False

    cleaned = _clean(text)
    if not re.search(r"\b(mañana|manana)\b", cleaned):
        return False

    tz = ZoneInfo(os.getenv("VAL0_TZ", "America/Panama"))
    tomorrow = (datetime.now(tz).date() + timedelta(days=1)).isoformat()

    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT c.expediente, ce.event_text, ce.deadline_date "
            "FROM case_events ce "
            "JOIN cases c ON c.id = ce.case_id "
            "WHERE ce.chat_id=? AND ce.deadline_date=? "
            "ORDER BY c.expediente ASC, ce.id ASC",
            (int(chat_id), tomorrow),
        )

        rows = cur.fetchall() or []
        conn.close()

        from core.due_merge import merge_due_items

        y, m, d = map(int, tomorrow.split("-"))

        db_items: List[Dict[str, Any]] = []
        for r in rows:
            exp = r["expediente"]
            et = (r["event_text"] or "").strip() or "(evento)"

            local_dt = datetime(y, m, d, 9, 0, 0, tzinfo=tz)
            due_ts = int(local_dt.astimezone(timezone.utc).timestamp())

            db_items.append({
                "due_ts": due_ts,
                "title": et,
                "case_id": exp,
                "source": "db",
                "external_id": None,
            })

        start_local = datetime(y, m, d, 0, 0, 0, tzinfo=tz)
        end_local = datetime(y, m, d, 23, 59, 59, tzinfo=tz)

        merged = merge_due_items(
            db_items=db_items,
            range_start_utc=start_local.astimezone(timezone.utc),
            range_end_utc=end_local.astimezone(timezone.utc),
        )

        items = merged["items"]
        conflicts = merged["conflicts"]

        _audit_merge(gate="due_tomorrow", chat_id=int(chat_id), label=f"{tomorrow}", items=items)

        if not items:
            await update.message.reply_text("Mañana no tengo vencimientos registrados.")
            return True

        weekday = datetime.now(tz).date() + timedelta(days=1)
        WEEKDAY_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        weekday_name = WEEKDAY_ES[weekday.weekday()]

        msg = _render_due_grouped(
            header=f"📅 {weekday_name.capitalize()}:",
            items=items,
            tz=tz,
        )

        if conflicts:
            msg = msg + "\n" + _render_due_conflicts(conflicts)

        await update.message.reply_text(msg)
        return True

    except Exception as e:
        logger.exception(f"[CASE MVP] try_due_tomorrow failed: {e}")
        await update.message.reply_text("Se cayó el chequeo de diligencias de mañana. Reviso logs.")
        return True

async def try_due_range(update, chat_id, text) -> bool:
    """
    Handles:
      - 'Qué vence esta semana?'
      - 'Qué vence en 2 semanas?' / 'Qué vence en dos semanas?'
      - 'Qué vence en las próximas 2 semanas?'
    Returns True if it responded and should short-circuit the pipeline.
    """
    if not update or not getattr(update, "message", None):
        return False

    cleaned = _clean(text)

    days: Optional[int] = None
    weeks: Optional[int] = None

    if re.search(r"\b(que|qué)\s+vence\s+esta\s+semana\b", cleaned):
        weeks = 1
        days = 7
    else:
        # digits: "... 2 semanas", "... proximas 3 semanas", etc.
        m = re.search(
            r"\b(que|qué)\s+vence(?:\s+en(?:\s+las)?)?(?:\s+las)?(?:\s+(?:proximas|próximas))?\s+(\d+)\s+semanas?\b",
            cleaned,
        )
        if m:
            weeks = int(m.group(2))
            days = weeks * 7
        else:
            # words: "dos semanas", "tres semanas", etc.
            word_map = {
                "uno": 1, "una": 1,
                "dos": 2,
                "tres": 3,
                "cuatro": 4,
                "cinco": 5,
                "seis": 6,
                "siete": 7,
                "ocho": 8,
            }
            m = re.search(
                r"\b(que|qué)\s+vence(?:\s+en(?:\s+las)?)?(?:\s+las)?(?:\s+(?:proximas|próximas))?\s+(uno|una|dos|tres|cuatro|cinco|seis|siete|ocho)\s+semanas?\b",
                cleaned,
            )
            if m:
                weeks = word_map.get(m.group(2))
                if weeks is not None:
                    days = weeks * 7

    if days is None:
        return False

    tz = ZoneInfo(os.getenv("VAL0_TZ", "America/Panama"))
    start_date = datetime.now(tz).date()
    end_date = start_date + timedelta(days=days)
    start_s = start_date.isoformat()
    end_s = end_date.isoformat()

    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT c.expediente, ce.event_text, ce.deadline_date "
            "FROM case_events ce "
            "JOIN cases c ON c.id = ce.case_id "
            "WHERE ce.chat_id=? AND ce.deadline_date >= ? AND ce.deadline_date <= ? "
            "ORDER BY ce.deadline_date ASC, c.expediente ASC, ce.id ASC",
            (int(chat_id), start_s, end_s),
        )
        rows = cur.fetchall() or []
        conn.close()

        # --- deterministic merge: DB + optional Google Calendar (no model) ---
        from core.due_merge import merge_due_items

        w = weeks or (days // 7)
        label = "esta semana" if days == 7 else f"las próximas {w} semanas"

        db_items: List[Dict[str, Any]] = []
        for r in rows:
            exp = r["expediente"]
            dd = r["deadline_date"] or ""
            et = (r["event_text"] or "").strip() or "(evento)"

            if not dd:
                continue

            # deadline_date treated as 09:00 local
            y, m, d = map(int, dd.split("-"))
            local_dt = datetime(y, m, d, 9, 0, 0, tzinfo=tz)
            due_ts = int(local_dt.astimezone(timezone.utc).timestamp())

            db_items.append({
                "due_ts": due_ts,
                "title": et,
                "case_id": exp,              # expediente as stable case identifier
                "deadline_date": dd,         # kept for possible future rendering
                "source": "db",
                "external_id": None,
            })

        # Merge range (local) → UTC
        start_local = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, tzinfo=tz)
        end_local = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=tz)

        merged = merge_due_items(
            db_items=db_items,
            range_start_utc=start_local.astimezone(timezone.utc),
            range_end_utc=end_local.astimezone(timezone.utc),
        )
        items = merged["items"]
        conflicts = merged["conflicts"]

        _audit_merge(gate="due_range", chat_id=int(chat_id), label=f"{start_s}->{end_s}", items=items)
        if not items:
            await update.message.reply_text(f"No tengo vencimientos registrados para {label}.")
            return True

        msg = _render_due_grouped(
            header=f"⏰ Vence {label} ({start_s} → {end_s}):",
            items=items,
            tz=tz,
        )

        if conflicts:
            msg = msg + "\n" + _render_due_conflicts(conflicts)

        await update.message.reply_text(msg)
        return True

    except Exception as e:
        logger.exception(f"[CASE MVP] try_due_range failed: {e}")
        await update.message.reply_text("Se cayó el chequeo de vencimientos por rango. Reviso logs.")
        return True
    