import re
import os
import logging
import unicodedata

logger = logging.getLogger("val0-bot")
logger.setLevel(logging.INFO)

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
    case_id = (case_id or "").strip()
    if not case_id:
        return "No puedo identificar el caso."

    tz = ZoneInfo("America/Panama")
    parent_ref = f"CASE:{case_id}"

    # client name
    client_name = None
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT client_name
            FROM cases
            WHERE chat_id=?
              AND expediente=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (int(chat_id), str(case_id)),
        )
        row = cur.fetchone()
        conn.close()
        if row:
            client_name = (row["client_name"] if hasattr(row, "keys") else row[0]) or None
    except Exception:
        client_name = None

    # notes
    notes_rows = fetch_case_notes(chat_id, case_id, limit=20)
    recent_notes = []

    for row in notes_rows:
        txt = (row.get("note_text") or "").strip()
        ts = (row.get("created_at") or "").strip()
        if not txt or not ts:
            continue

        try:
            dt_utc = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            dt_local = dt_utc.astimezone(tz)
        except Exception:
            continue

        txt = txt.replace("desde harness", "").strip()
        recent_notes.append((dt_local, txt))

    recent_notes.sort(key=lambda x: x[0], reverse=True)

    # next reminder / tasks from linked timeline
    next_rem = None
    try:
        timeline_rows = fetch_timeline_for_parent(
            chat_id=int(chat_id),
            parent_ref=parent_ref,
            entity_types=["reminder", "task"],
            statuses=["pending", "sent"],
            limit=20,
        )
    except Exception:
        timeline_rows = []

    pending_rows = []
    for row in timeline_rows:
        txt = (row.get("text") or "").strip()
        due_ts = row.get("due_ts")
        if not txt or due_ts is None:
            continue
        try:
            dt_local = datetime.fromtimestamp(int(due_ts), tz=timezone.utc).astimezone(tz)
            pending_rows.append((dt_local, txt))
        except Exception:
            continue

    pending_rows.sort(key=lambda x: x[0])

    if pending_rows:
        dt_local, txt = pending_rows[0]
        due_label = dt_local.strftime("%Y-%m-%d")
        next_rem = (due_label, txt)

    # active terms / dated events
    active_terms = []
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT event_text, deadline_date, created_at
            FROM case_events
            WHERE chat_id=?
              AND case_id=?
              AND deadline_date IS NOT NULL
            ORDER BY deadline_date ASC
            LIMIT 10
            """,
            (int(chat_id), int(case_id)),
        )
        active_terms = cur.fetchall() or []
        conn.close()
    except Exception:
        active_terms = []

    # health
    latest_dt = recent_notes[0][0] if recent_notes else None
    if latest_dt is None:
        health_icon = "⚪"
        health_label = "Sin actividad"
    else:
        days_idle = (datetime.now(tz).date() - latest_dt.date()).days
        if days_idle <= 3:
            health_icon = "🟢"
            health_label = "Normal"
        elif days_idle <= 14:
            health_icon = "🟡"
            health_label = "Atención"
        else:
            health_icon = "🔴"
            health_label = "Inactivo"

    lines = [f"🗂️ <b>CASE:{case_id}</b>", ""]

    if client_name:
        lines.append("👤 <u>Cliente</u>")
        lines.append(f"{client_name}")
        lines.append("")

    lines.append("📊 <u>Salud</u>")
    lines.append(f"{health_icon} {health_label}")
    lines.append("")

    lines.append("📌 <u>Resumen</u>")

    if recent_notes:
        lines.append(f"• Última nota: {recent_notes[0][1]}")
    else:
        lines.append("• Última nota: —")

    # split legal terms vs reminder-style events
    legal_terms = []
    reminder_terms = []

    for row in active_terms:
        term_text = (row["event_text"] if hasattr(row, "keys") else row[0]) or ""
        if term_text.strip().upper().startswith("RECORDATORIO:"):
            reminder_terms.append(row)
        else:
            legal_terms.append(row)

    if legal_terms:
        first_term = legal_terms[0]
        term_text = (first_term["event_text"] if hasattr(first_term, "keys") else first_term[0]) or "—"
        term_deadline = (first_term["deadline_date"] if hasattr(first_term, "keys") else first_term[1]) or "—"
        lines.append(f"• Próximo término: {term_text} ({term_deadline})")
    else:
        lines.append("• Próximo término: —")

    if next_rem:
        lines.append(f"• Próximo recordatorio: {next_rem[0]} | {next_rem[1]}")
    elif reminder_terms:
        first_rem = reminder_terms[0]
        rem_text = (first_rem["event_text"] if hasattr(first_rem, "keys") else first_rem[0]) or "—"
        rem_deadline = (first_rem["deadline_date"] if hasattr(first_rem, "keys") else first_rem[1]) or "—"
        lines.append(f"• Próximo recordatorio: {rem_deadline} | {rem_text}")
    else:
        lines.append("• Próximo recordatorio: —")

    if legal_terms:
        lines.append("")
        lines.append("⏳ <u>Términos activos</u>")

        tz_today = datetime.now(tz).date()

        active_list = []
        completed_list = []

        for row in legal_terms:
            term_text = (row["event_text"] if hasattr(row, "keys") else row[0]) or "—"
            term_deadline = (row["deadline_date"] if hasattr(row, "keys") else row[1]) or None

            if term_deadline:
                try:
                    d = datetime.strptime(term_deadline, "%Y-%m-%d").date()
                    if d < tz_today:
                        completed_list.append((term_deadline, term_text))
                    else:
                        active_list.append((term_deadline, term_text))
                except Exception:
                    active_list.append((term_deadline, term_text))
            else:
                active_list.append((term_deadline, term_text))

        # Active terms
        for d, txt in active_list:
            lines.append(f"• {d} | {txt}")

        # Completed terms (limit to last 5)
        if completed_list:
            lines.append("")
            lines.append("🕓 <u>Términos cumplidos</u>")

            completed_list.sort(key=lambda x: x[0], reverse=True)

            for d, txt in completed_list[:5]:
                lines.append(f"• <s>{d} | {txt}</s>")

    if recent_notes:
        today_rows = []
        week_rows = []

        for dt_local, txt in recent_notes[:5]:
            weekdays = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
            months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                      "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

            time_str = dt_local.strftime("%I:%M %p").lstrip("0")
            if dt_local.date() == datetime.now(tz).date():
                label = time_str
            else:
                weekday = weekdays[dt_local.weekday()]
                month = months[dt_local.month - 1]
                label = f"{weekday} {dt_local.day} {month} · {time_str}"

            if "·" not in label:
                today_rows.append((label, txt))
            else:
                week_rows.append((label, txt))

        lines.append("")
        lines.append("🕒 <u>Actividad reciente</u>")

        if today_rows:
            lines.append("")
            lines.append("Hoy")
            for label, txt in today_rows:
                lines.append(f"• 📝 {label} | {txt}")

        if week_rows:
            lines.append("")
            lines.append("Esta semana")
            for label, txt in week_rows:
                lines.append(f"• 📝 {label} | {txt}")

    lines.append("")
    # --- Phase 2: cached summary (non-authoritative, additive) ---
    try:
        from core.case_summary import refresh_case_summary
        from memory_store import get_case_summary

        # Force refresh so cockpit always reflects latest canonical data
        refresh_case_summary(int(chat_id), str(case_id))
        summary_row = get_case_summary(int(chat_id), str(case_id))

        if summary_row:
            cached_text = (summary_row.get("summary_text") or "").strip()

            if cached_text:
                lines.append("")
                lines.append("🧠 <u>Resumen (cache)</u>")
                lines.append(cached_text)

    except Exception:
        # Never break cockpit if cache fails
        pass
    lines.append("📊 <u>Estado</u>")
    lines.append(f"• Notas: {len(notes_rows)}")
    lines.append(f"• Pendientes: {len(pending_rows)}")

    return "\n".join(lines)

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

            txt_clean = txt
            low = _clean(txt)

            if any(x in low for x in ("audiencia", "vista", "hearing")):
                txt_clean = f"⚖️ {txt_clean}"
            elif any(x in low for x in ("termino", "término", "plazo", "vence", "vencimiento")):
                txt_clean = f"⏳ {txt_clean}"
            elif any(x in low for x in ("fallo", "sentencia", "auto", "recurso")):
                txt_clean = f"📄 {txt_clean}"

            lines.append(f"• {icon} {label} | {txt_clean}")
        lines.append("")

    if week_rows:
        lines.append("Esta semana")
        for label, txt, kind in week_rows:
            icon = "📝" if kind == "note" else "⏰"

            txt_clean = txt
            low = _clean(txt)

            if any(x in low for x in ("audiencia", "vista", "hearing")):
                txt_clean = f"⚖️ {txt_clean}"
            elif any(x in low for x in ("termino", "término", "plazo", "vence", "vencimiento")):
                txt_clean = f"⏳ {txt_clean}"
            elif any(x in low for x in ("fallo", "sentencia", "auto", "recurso")):
                txt_clean = f"📄 {txt_clean}"

            lines.append(f"• {icon} {label} | {txt_clean}")

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
    Handles:
    - caso 524242024
    - expediente 524242024
    - qué tienes del caso 524242024
    - que tienes del caso 524242024
    - dame todo del caso 524242024
    - cómo va el caso 524242024
    - como va el caso 524242024
    - estado del caso 524242024
    - resumen del caso 524242024
    - cómo va el caso de Leticia
    - estado del caso de Leticia
    - dame todo del caso de Leticia
    """

    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")
    from core.control import pop_debug_mode

    logger.info(f"[CASE_STATUS] raw={text!r}")
    logger.info(f"[CASE_STATUS] cleaned={t!r}")

    # must reference case/expediente somehow
    if "caso" not in t and "expediente" not in t:
        return False

    # allow simple numeric case lookups and natural phrasing
    allowed_patterns = (
        "caso ",
        "expediente ",
        "como va el caso",
        "estado del caso",
        "resumen del caso",
        "situacion actual del caso",
        "por donde va el caso",
        "que tienes del caso",
        "qué tienes del caso",
        "dame todo del caso",
        "ver caso",
        "ver expediente",
        "info del caso",
        "informacion del caso",
        "información del caso",
    )

    if not any(x in t for x in allowed_patterns):
        return False

    case_id = None

    # numeric expediente path
    m = re.search(r"(?:caso|expediente)\s+([0-9][0-9\-]{3,})", t)
    if m:
        case_id = (m.group(1) or "").strip()

    # client name path
    if not case_id and ("caso de " in t or "del caso de " in t or "expediente de " in t):
        if "del caso de " in t:
            client_name = t.split("del caso de ", 1)[1]
        elif "expediente de " in t:
            client_name = t.split("expediente de ", 1)[1]
        else:
            client_name = t.split("caso de ", 1)[1]

        client_name = re.sub(
            r"\b(como va|estado|resumen|situacion actual|por donde va|que tienes|dame todo|ver|info|informacion|del caso|caso|expediente)\b",
            "",
            client_name,
        )
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
                      AND lower(client_name) LIKE lower(?)
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (int(chat_id), f"%{client_name}%"),
                )
                row = cur.fetchone()
                conn.close()

                if row:
                    case_id = (row["expediente"] if hasattr(row, "keys") else row[0]) or ""
                    case_id = str(case_id).strip()

            except Exception:
                case_id = None

    logger.info(f"[CASE_STATUS] resolved_case_id={case_id!r}")

    if not case_id:
        await update.message.reply_text("No encuentro ese caso en tu base de datos.")
        return True

    logger.info("[CASE_STATUS] HIT")

    debug_active = pop_debug_mode(int(chat_id))
    if debug_active:
        debug_msg = (
            "🧠 Debug\n\n"
            f"Handler: try_case_status\n"
            f"Cleaned: {t}\n"
            f"Resolved: {case_id}\n"
            f"Action: generate_case_cockpit"
        )
        await update.message.reply_text(debug_msg)

    out = generate_case_cockpit(int(chat_id), case_id)
    await update.message.reply_text(out, parse_mode="HTML")
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

async def try_case_create(update, chat_id, text) -> bool:
    """
    Supports:
    crea el caso 12345 para Leticia
    crear caso 12345 para Leticia

    NEW (natural):
    crear caso de Leticia expediente 12345
    crea caso de Leticia expediente 12345
    """

    if not update or not getattr(update, "message", None):
        return False

    import re

    t = (text or "").strip()
    low = _clean(t)

    # --- quick gate ---
    if not (
        low.startswith("crea el caso ")
        or low.startswith("crear caso ")
        or low.startswith("crear caso de ")
        or low.startswith("crea caso de ")
    ):
        return False

    expediente = None
    client_name = None

    # --- pattern 1 (existing) ---
    # crea el caso 12345 para Leticia
    m = re.search(r"(?:crea el caso|crear caso)\s+(\d{4,})\s+para\s+(.+)$", low)
    if m:
        expediente = m.group(1).strip()
        client_name = m.group(2).strip()

    # --- pattern 2 (new natural) ---
    # crear caso de Leticia expediente 12345
    if not expediente:
        m = re.search(r"(?:crear|crea)\s+caso\s+de\s+(.+?)\s+expediente\s+(\d{4,})", low)
        if m:
            client_name = m.group(1).strip()
            expediente = m.group(2).strip()

    if not expediente or not client_name:
        await update.message.reply_text(
            "Usa:\n"
            "• crea el caso <expediente> para <cliente>\n"
            "• crear caso de <cliente> expediente <expediente>"
        )
        return True

    try:
        from memory_store import upsert_case

        row_id = upsert_case(
            chat_id=int(chat_id),
            expediente=expediente,
            client_name=client_name.title(),
            client_alias=None,
        )

        await update.message.reply_text(
            f"🗂️ Caso creado\n\nExpediente: {expediente}\nCliente: {client_name.title()}"
        )
        return True

    except Exception:
        await update.message.reply_text("No pude crear el caso.")
        return True

async def try_case_register_term(update, chat_id, text) -> bool:
    """
    Supports:
    registra termino en el caso de Leticia: vence contestacion el 20 de marzo
    registra término en el caso 524242024: vence apelación el 21 de marzo

    NEW (natural):
    anota término en el caso de Leticia: vence contestación el 20 de marzo
    termino en Leticia: vence contestación el 20 de marzo
    término en Leticia: vence contestación el 20 de marzo
    vencimiento en Leticia: vence contestación el 20 de marzo
    """

    if not update or not getattr(update, "message", None):
        return False

    import re

    t = (text or "").strip()
    low = _clean(t)

    if not (
        "registra termino en el caso" in low
        or low.startswith("anota termino en el caso de ")
        or low.startswith("termino en ")
        or low.startswith("vencimiento en ")
        or low.startswith("val termino en ")
        or low.startswith("val vencimiento en ")
    ):
        return False

    parts = t.split(":", 1)
    if len(parts) != 2:
        await update.message.reply_text(
            "Usa:\n"
            "• registra término en el caso de <cliente>: <detalle>\n"
            "• término en <cliente>: <detalle>"
        )
        return True

    left, event_text = parts
    event_text = event_text.strip()

    left_clean = _clean(left)

    case_id = None
    client_name = None

    # numeric expediente
    m = re.search(r"caso\s+(\d{4,})", left_clean, re.IGNORECASE)
    if m:
        case_id = m.group(1)

    # client-name patterns
    if not case_id:
        patterns = [
            r"caso\s+de\s+(.+)$",
            r"anota\s+termino\s+en\s+el\s+caso\s+de\s+(.+)$",
            r"termino\s+en\s+(.+)$",
            r"vencimiento\s+en\s+(.+)$",
            r"val\s+termino\s+en\s+(.+)$",
            r"val\s+vencimiento\s+en\s+(.+)$",
        ]

        for pat in patterns:
            m = re.search(pat, left_clean, re.IGNORECASE)
            if m:
                client_name = m.group(1)
                break

        if client_name:
            client_name = re.sub(r"[^\w\s]", "", client_name).strip()

            try:
                conn = _get_conn()
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT expediente
                    FROM cases
                    WHERE chat_id=?
                      AND lower(client_name) LIKE lower(?)
                    ORDER BY id DESC
                    LIMIT 5
                    """,
                    (int(chat_id), f"%{client_name}%"),
                )
                rows = cur.fetchall() or []
                conn.close()

                if rows:
                    row = rows[0]
                    case_id = row["expediente"] if hasattr(row, "keys") else row[0]
            except Exception:
                case_id = None

    if not case_id:
        await update.message.reply_text("No encuentro ese caso.")
        return True

    deadline_date = None

    m_date = re.search(
        r"\b(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\b",
        low,
    )
    if m_date:
        day = int(m_date.group(1))
        month_name = m_date.group(2)

        month_map = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
            "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
            "septiembre": 9, "setiembre": 9, "octubre": 10,
            "noviembre": 11, "diciembre": 12,
        }
        month = month_map[month_name]
        year = datetime.now(ZoneInfo("America/Panama")).year
        deadline_date = f"{year:04d}-{month:02d}-{day:02d}"

    try:
        from memory_store import insert_case_event

        # --- DEDUPE CHECK ---
        dup = False
        try:
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id
                FROM case_events
                WHERE chat_id=?
                  AND case_id=?
                  AND event_text=?
                  AND IFNULL(deadline_date,'') = IFNULL(?, '')
                ORDER BY id DESC
                LIMIT 1
                """,
                (
                    int(chat_id),
                    int(case_id),
                    event_text,
                    deadline_date,
                ),
            )
            row = cur.fetchone()
            conn.close()
            if row:
                dup = True
        except Exception:
            dup = False

        if dup:
            await update.message.reply_text(
                f"⚠️ Término duplicado detectado en CASE:{case_id}."
            )
            return True

        # --- INSERT ---
        insert_case_event(
            chat_id=int(chat_id),
            case_id=int(case_id),
            event_text=event_text,
            deadline_date=deadline_date,
        )

        msg = f"⏳ Término registrado en CASE:{case_id}"
        if deadline_date:
            msg += f"\nVence: {deadline_date}"

        await update.message.reply_text(msg)
        return True

        insert_case_event(
            chat_id=int(chat_id),
            case_id=int(case_id),
            event_text=event_text,
            deadline_date=deadline_date,
        )

        msg = f"⏳ Término registrado en CASE:{case_id}"
        if deadline_date:
            msg += f"\nVence: {deadline_date}"
        await update.message.reply_text(msg)
        return True

    except Exception:
        await update.message.reply_text("No pude registrar el término.")
        return True

async def try_set_mode(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")

    if not t.startswith("val modo"):
        return False

    if "quiet" in t:
        mode = "quiet"
    elif "war" in t:
        mode = "war"
    else:
        mode = "tactical"

    from memory_store import set_proactive_mode
    set_proactive_mode(int(chat_id), mode)

    # HARD DETERMINISTIC RESPONSE (no personality layer)
    await update.message.reply_text(f"Modo cambiado a: {mode.upper()}")

    return True

async def try_case_add_note(update, chat_id, text) -> bool:
    """
    Supports:
    guarda esto en el caso de <cliente>: <nota>
    guarda esto en el caso <expediente>: <nota>

    NEW (natural):
    anota en el caso de <cliente>: <nota>
    anota en <cliente>: <nota>
    nota en el caso de <cliente>: <nota>
    """

    if not update or not getattr(update, "message", None):
        return False

    import re

    t = (text or "").strip()
    low = _clean(t)
    logger.info(f"[CASE_ADD_NOTE] raw={text!r}")

    if not (
        "guarda esto en el caso" in low
        or low.startswith("anota en el caso de ")
        or low.startswith("anota en ")
        or low.startswith("nota en el caso de ")
    ):
        return False

    parts = t.split(":", 1)
    if len(parts) != 2:
        await update.message.reply_text("Falta el texto de la nota.")
        return True

    left, note_text = parts
    note_text = note_text.strip()

    logger.info(f"[CASE_ADD_NOTE] left={left!r}")
    logger.info(f"[CASE_ADD_NOTE] note_text={note_text!r}")

    case_id = None

    # numeric expediente
    m = re.search(r"caso\s+(\d{4,})", left, re.IGNORECASE)
    if m:
        case_id = m.group(1)

    client_name = None

    if not case_id:
        patterns = [
            r"caso\s+de\s+(.+)$",          # guarda esto en el caso de X
            r"anota\s+en\s+el\s+caso\s+de\s+(.+)$",
            r"nota\s+en\s+el\s+caso\s+de\s+(.+)$",
            r"anota\s+en\s+(.+)$",         # anota en X
        ]

        for pat in patterns:
            m = re.search(pat, left, re.IGNORECASE)
            if m:
                client_name = m.group(1)
                break

        if client_name:
            logger.info(f"[CASE_ADD_NOTE] client_name_raw={client_name!r}")

            client_name = _clean(client_name)
            client_name = re.sub(r"[^\w\s]", "", client_name).strip()

            logger.info(f"[CASE_ADD_NOTE] client_name_clean={client_name!r}")

            try:
                conn = _get_conn()
                cur = conn.cursor()

                cur.execute(
                    """
                    SELECT expediente, client_name
                    FROM cases
                    WHERE chat_id=?
                    AND lower(client_name) LIKE lower(?)
                    ORDER BY id DESC
                    LIMIT 5
                    """,
                    (int(chat_id), f"%{client_name}%"),
                )

                rows = cur.fetchall() or []
                conn.close()

                logger.info(f"[CASE_ADD_NOTE] match_count={len(rows)}")
                for r in rows:
                    expediente = r["expediente"] if hasattr(r, "keys") else r[0]
                    cname = r["client_name"] if hasattr(r, "keys") else r[1]
                    logger.info(f"[CASE_ADD_NOTE] candidate expediente={expediente!r} client_name={cname!r}")

                if rows:
                    row = rows[0]
                    case_id = row["expediente"] if hasattr(row, "keys") else row[0]

            except Exception as e:
                logger.exception(f"[CASE_ADD_NOTE] lookup failed: {e}")
                case_id = None

    logger.info(f"[CASE_ADD_NOTE] resolved_case_id={case_id!r}")

    if not case_id:
        await update.message.reply_text("No encuentro ese caso.")
        return True

    from memory_store import insert_case_note

    dup = False
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id
            FROM case_notes
            WHERE chat_id=?
            AND case_id=?
            AND note_text=?
            AND created_at >= datetime('now','-60 seconds')
            ORDER BY id DESC
            LIMIT 1
            """,
            (int(chat_id), str(case_id), note_text),
        )
        row = cur.fetchone()
        conn.close()
        if row:
            dup = True
    except Exception:
        dup = False

    if dup:
        await update.message.reply_text(f"⚠️ Nota duplicada detectada. Ya existía en CASE:{case_id}.")
        return True

    note_id = insert_case_note(
        chat_id=int(chat_id),
        case_id=str(case_id),
        note_text=note_text,
        source="text"
    )

    from bot import _LAST_ACTION
    _LAST_ACTION[int(chat_id)] = {
        "type": "note_insert",
        "id": note_id,
    }

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

        txt_clean = txt
        low = _clean(txt)

        if any(x in low for x in ("audiencia", "vista", "hearing")):
            txt_clean = f"⚖️ {txt_clean}"
        elif any(x in low for x in ("termino", "término", "plazo", "vence", "vencimiento")):
            txt_clean = f"⏳ {txt_clean}"
        elif any(x in low for x in ("fallo", "sentencia", "auto", "recurso")):
            txt_clean = f"📄 {txt_clean}"

        lines.append(f"• {icon} {label} | {txt_clean}")

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

    status_map = {
        "normal": "🟢 Normal",
        "atención": "🟡 Atención",
        "inactivo": "🔴 Inactivo",
    }

    lines = [
        "⚠️ <b>Salud del caso</b>",
        "",
        f"• Última actividad: {latest_label}",
        f"• Días sin actividad: {days_idle}",
        "",
        "📊 <b>Estado sugerido</b>",
        f"{status_map.get(status, status)}",
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
            continue

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

async def try_cases_requiring_attention(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")

    if not any(x in t for x in (
        "que casos requieren atencion",
        "qué casos requieren atención",
        "casos que requieren atencion",
        "casos que requieren atención",
    )):
        return False

    out = generate_cases_requiring_attention(int(chat_id))
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


async def try_terms_due_this_week(update, chat_id, text) -> bool:
    """
    Handles:
    - qué vence esta semana
    - que vence esta semana
    - términos que vencen esta semana
    """

    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")

    if "vence esta semana" not in t and "vencen esta semana" not in t:
        return False

    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT c.client_name, e.deadline_date, e.event_text
            FROM case_events e
            JOIN cases c ON c.expediente = CAST(e.case_id AS TEXT)
            WHERE c.chat_id=?
              AND e.deadline_date BETWEEN date('now') AND date('now','+7 days')
            ORDER BY e.deadline_date ASC
            """,
            (int(chat_id),),
        )

        rows = cur.fetchall() or []
        conn.close()

    except Exception as e:
        logger.exception(f"[TERMS_WEEK] failed: {e}")
        await update.message.reply_text("No pude consultar los vencimientos.")
        return True

    if not rows:
        await update.message.reply_text("🟢 No hay vencimientos esta semana.")
        return True

    lines = ["⏳ <b>Vencimientos esta semana</b>", ""]

    for r in rows:
        client = r["client_name"] if hasattr(r, "keys") else r[0]
        deadline = r["deadline_date"] if hasattr(r, "keys") else r[1]
        event_text = r["event_text"] if hasattr(r, "keys") else r[2]

        lines.append(f"• {deadline} | {client} | {event_text}")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    return True 

async def try_cases_due_this_week(update, chat_id, text) -> bool:
    """
    Handles:
    - qué casos tienen vencimientos esta semana
    """

    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")

    if "casos" not in t or "esta semana" not in t:
        return False

    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT c.client_name, e.deadline_date, e.event_text
            FROM case_events e
            JOIN cases c ON c.expediente = CAST(e.case_id AS TEXT)
            WHERE c.chat_id=?
              AND e.deadline_date BETWEEN date('now') AND date('now','+7 days')
            ORDER BY e.deadline_date ASC
            """,
            (int(chat_id),),
        )

        rows = cur.fetchall() or []
        conn.close()

    except Exception as e:
        logger.exception(f"[CASES_WEEK] failed: {e}")
        await update.message.reply_text("No pude consultar los vencimientos.")
        return True

    if not rows:
        await update.message.reply_text("🟢 No veo casos con vencimientos esta semana.")
        return True

    lines = ["⏳ <b>Casos con vencimientos esta semana</b>", ""]

    for r in rows:
        client = r["client_name"]
        deadline = r["deadline_date"]
        event_text = r["event_text"]

        lines.append(f"• {client} — {deadline} | {event_text}")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

    return True

async def try_terms_due_this_week_for_case(update, chat_id, text) -> bool:
    """
    Handles:
    - qué vence esta semana en el caso de X
    """

    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")

    if "vence esta semana en el caso" not in t:
        return False

    import re

    m = re.search(r"caso\s+de\s+(.+)$", t)
    if not m:
        return False

    client_name = re.sub(r"[^\w\s]", "", m.group(1)).strip()

    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT expediente, client_name
            FROM cases
            WHERE chat_id=?
            AND lower(client_name) LIKE lower(?)
            ORDER BY id DESC
            LIMIT 1
            """,
            (int(chat_id), f"%{client_name}%"),
        )

        case = cur.fetchone()

        if not case:
            conn.close()
            await update.message.reply_text("No encuentro ese caso.")
            return True

        case_id = case["expediente"]
        client_name = case["client_name"]

        cur.execute(
            """
            SELECT deadline_date, event_text
            FROM case_events
            WHERE case_id=?
            AND deadline_date BETWEEN date('now') AND date('now','+7 days')
            ORDER BY deadline_date ASC
            """,
            (str(case_id),),
        )

        rows = cur.fetchall()
        conn.close()

    except Exception as e:
        logger.exception(f"[TERMS_WEEK_CASE] failed: {e}")
        await update.message.reply_text("No pude consultar los vencimientos.")
        return True

    if not rows:
        await update.message.reply_text(
            f"🟢 No hay vencimientos esta semana en el caso de {client_name}."
        )
        return True

    lines = [f"⏳ <b>Vencimientos esta semana — {client_name}</b>", ""]

    for r in rows:
        deadline = r["deadline_date"]
        event_text = r["event_text"]

        lines.append(f"• {deadline} | {event_text}")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

    return True

async def try_terms_due_today(update, chat_id, text) -> bool:
    """
    Handles:
    - qué vence hoy
    - que vence hoy
    """

    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")

    if "vence hoy" not in t:
        return False

    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT c.client_name, e.deadline_date, e.event_text
            FROM case_events e
            JOIN cases c ON c.expediente = CAST(e.case_id AS TEXT)
            WHERE c.chat_id=?
              AND e.deadline_date = date('now')
            ORDER BY e.deadline_date ASC
            """,
            (int(chat_id),),
        )

        rows = cur.fetchall() or []
        conn.close()

    except Exception as e:
        logger.exception(f"[TERMS_TODAY] failed: {e}")
        await update.message.reply_text("No pude consultar los vencimientos de hoy.")
        return True

    if not rows:
        await update.message.reply_text("🟢 No hay vencimientos hoy.")
        return True

    lines = ["⏳ <b>Vencimientos hoy</b>", ""]

    for r in rows:
        client = r["client_name"] if hasattr(r, "keys") else r[0]
        deadline = r["deadline_date"] if hasattr(r, "keys") else r[1]
        event_text = r["event_text"] if hasattr(r, "keys") else r[2]

        lines.append(f"• {deadline} | {client} | {event_text}")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    return True

async def try_terms_due_tomorrow(update, chat_id, text) -> bool:
    """
    Handles:
    - qué vence mañana
    - que vence mañana
    """

    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")

    if "vence manana" not in t and "vence mañana" not in t:
        return False

    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT c.client_name, e.deadline_date, e.event_text
            FROM case_events e
            JOIN cases c ON c.expediente = CAST(e.case_id AS TEXT)
            WHERE c.chat_id=?
              AND e.deadline_date = date('now','+1 day')
            ORDER BY e.deadline_date ASC
            """,
            (int(chat_id),),
        )

        rows = cur.fetchall() or []
        conn.close()

    except Exception as e:
        logger.exception(f"[TERMS_TOMORROW] failed: {e}")
        await update.message.reply_text("No pude consultar los vencimientos de mañana.")
        return True

    if not rows:
        await update.message.reply_text("🟢 No hay vencimientos mañana.")
        return True

    lines = ["⏳ <b>Vencimientos mañana</b>", ""]

    for r in rows:
        client = r["client_name"] if hasattr(r, "keys") else r[0]
        deadline = r["deadline_date"] if hasattr(r, "keys") else r[1]
        event_text = r["event_text"] if hasattr(r, "keys") else r[2]

        lines.append(f"• {deadline} | {client} | {event_text}")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    return True 

async def try_delete_last_note(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")

    if not any(x in t for x in (
        "borra la ultima nota",
        "elimina la ultima nota",
        "borrar la ultima nota",
        "eliminar la ultima nota",
    )):
        return False

    case_id = None

    # numeric
    m = re.search(r"caso\s+(\d{4,})", t)
    if m:
        case_id = (m.group(1) or "").strip()

    # name
    if not case_id and ("caso de " in t or "del caso de " in t):
        if "del caso de " in t:
            client_name = t.split("del caso de ", 1)[1]
        else:
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
                      AND lower(client_name) LIKE lower(?)
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (int(chat_id), f"%{client_name}%"),
                )
                row = cur.fetchone()
                conn.close()

                if row:
                    case_id = str(row[0]).strip()
            except Exception:
                case_id = None

    if not case_id:
        await update.message.reply_text("No encontré el caso.")
        return True

    try:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, note_text
            FROM case_notes
            WHERE chat_id=?
              AND case_id=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (int(chat_id), str(case_id)),
        )
        row = cur.fetchone()

        if not row:
            conn.close()
            await update.message.reply_text("No hay notas para borrar.")
            return True

        import __main__

        note_id = row["id"] if hasattr(row, "keys") else row[0]
        note_text = row["note_text"] if hasattr(row, "keys") else row[1]

        getattr(__main__, "_LAST_ACTION", {})[int(chat_id)] = {
            "type": "note_delete",
            "id": note_id,
            "note_text": note_text,
            "chat_id": int(chat_id),
            "case_id": str(case_id),
            "source": "text",
        }

        cur.execute("DELETE FROM case_notes WHERE id=?", (note_id,))
        conn.commit()
        conn.close()

        from core.case_summary import refresh_case_summary
        refresh_case_summary(int(chat_id), str(case_id))

        await update.message.reply_text(
            f"🗑️ Eliminé la última nota del caso {case_id}:\n\"{note_text[:80]}\""
        )
        return True

    except Exception as e:
        logger.exception(f"[DELETE_LAST_NOTE] failed: {e}")
        await update.message.reply_text("No pude borrar la nota.")
        return True

async def try_undo_last_action(update, chat_id, text) -> bool:
    import __main__

    if not update or not getattr(update, "message", None):
        return False

    t = _clean(text or "")

    undo_commands = (
        "deshacer",
        "deshacer ultima accion",
        "deshacer última acción",
        "undo",
        "undo last action",
    )

    if t not in undo_commands:
        return False

    action = getattr(__main__, "_LAST_ACTION", {}).get(int(chat_id))
    if not action:
        await update.message.reply_text("No hay nada para deshacer.")
        return True

    try:
        conn = _get_conn()
        cur = conn.cursor()

        undo_msg = "↩️ Última acción deshecha."

        # --- NOTE INSERT ---
        if action["type"] == "note_insert":
            cur.execute("DELETE FROM case_notes WHERE id=?", (action["id"],))
            undo_msg = "↩️ Eliminé la última nota que acababas de guardar."

        # --- NOTE DELETE (restore) ---
        elif action["type"] == "note_delete":
            cur.execute(
                """
                INSERT INTO case_notes (chat_id, case_id, note_text, source)
                VALUES (?, ?, ?, ?)
                """,
                (
                    action["chat_id"],
                    action["case_id"],
                    action["note_text"],
                    action["source"],
                ),
            )
            undo_msg = "↩️ Restauré la última nota eliminada."

        # --- TERM INSERT ---
        elif action["type"] == "term_insert":
            cur.execute("DELETE FROM case_events WHERE id=?", (action["id"],))
            undo_msg = "↩️ Eliminé el último término registrado."

        # --- REMINDER INSERT ---
        elif action["type"] == "reminder_insert":
            cur.execute("DELETE FROM case_events WHERE id=?", (action["id"],))
            undo_msg = "↩️ Eliminé el último recordatorio registrado."

        conn.commit()
        conn.close()

        getattr(__main__, "_LAST_ACTION", {}).pop(int(chat_id), None)

        case_id = action.get("case_id")
        if case_id:
            from core.case_summary import refresh_case_summary
            refresh_case_summary(int(chat_id), str(case_id))

        await update.message.reply_text(undo_msg)
        return True

    except Exception as e:
        logger.exception(f"[UNDO] failed: {e}")
        await update.message.reply_text("No pude deshacer la acción.")
        return True                  