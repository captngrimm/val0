from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple
from zoneinfo import ZoneInfo

from memory_store import _get_conn


def _tz() -> ZoneInfo:
    name = os.getenv("VAL0_TZ", "America/Panama").strip() or "America/Panama"
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("UTC")


def _local(dt_utc: datetime) -> datetime:
    return dt_utc.astimezone(_tz())


def _fmt_local(dt_utc: datetime) -> str:
    return _local(dt_utc).strftime("%H:%M")


def _parse_utc(dt_str: str) -> datetime | None:
    if not dt_str:
        return None
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _load_gcal_events_for_day(day_local: datetime.date) -> List[Dict[str, Any]]:
    """
    Returns normalized Google Calendar events for one local day.
    Schema:
    {
      "title": str,
      "start_utc": datetime,
      "end_utc": datetime,
      "source": "gcal",
    }
    """
    try:
        from core.gcal_client import get_events_between
    except Exception:
        return []

    tz = _tz()
    start_local = datetime(day_local.year, day_local.month, day_local.day, 0, 0, 0, tzinfo=tz)
    end_local = datetime(day_local.year, day_local.month, day_local.day, 23, 59, 59, tzinfo=tz)

    try:
        rows = get_events_between(
            start_local.astimezone(timezone.utc),
            end_local.astimezone(timezone.utc),
            limit=250,
        )
    except Exception:
        return []

    out: List[Dict[str, Any]] = []

    for ev in rows or []:
        title = (ev.get("summary") or "(sin título)").strip()

        start_raw = ev.get("start") or ""
        end_raw = ev.get("end") or ""

        start_utc = _parse_utc(start_raw)
        end_utc = _parse_utc(end_raw)

        # all-day fallback
        if start_utc is None and len(start_raw) == 10:
            start_utc = datetime(day_local.year, day_local.month, day_local.day, 9, 0, 0, tzinfo=tz).astimezone(timezone.utc)

        if end_utc is None and start_utc is not None:
            end_utc = start_utc + timedelta(hours=1)

        if start_utc is None or end_utc is None:
            continue

        out.append({
            "title": title,
            "start_utc": start_utc,
            "end_utc": end_utc,
            "source": "gcal",
        })

    out.sort(key=lambda x: x["start_utc"])
    return out


def _load_db_due_items_for_day(chat_id: int, day_local: datetime.date) -> List[Dict[str, Any]]:
    """
    DB deadlines are modeled as 09:00 local unless later you store real times.
    """
    conn = _get_conn()
    cur = conn.cursor()

    day_s = day_local.isoformat()

    cur.execute(
        """
        SELECT c.expediente, c.client_name, ce.event_text, ce.deadline_date
        FROM case_events ce
        JOIN cases c ON c.id = ce.case_id
        WHERE ce.chat_id=?
          AND ce.deadline_date=?
        ORDER BY c.expediente ASC, ce.id ASC
        """,
        (int(chat_id), day_s),
    )
    rows = cur.fetchall() or []
    conn.close()

    tz = _tz()
    start_local = datetime(day_local.year, day_local.month, day_local.day, 9, 0, 0, tzinfo=tz)
    end_local = start_local + timedelta(minutes=30)

    out: List[Dict[str, Any]] = []

    for r in rows:
        expediente = r["expediente"] if hasattr(r, "keys") else r[0]
        client_name = r["client_name"] if hasattr(r, "keys") else r[1]
        event_text = r["event_text"] if hasattr(r, "keys") else r[2]

        out.append({
            "title": f"{client_name} | {event_text}",
            "case_id": str(expediente),
            "start_utc": start_local.astimezone(timezone.utc),
            "end_utc": end_local.astimezone(timezone.utc),
            "source": "db",
        })

    return out


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def build_conflict_report_for_tomorrow(chat_id: int) -> str:
    tz = _tz()
    tomorrow = (datetime.now(tz) + timedelta(days=1)).date()

    gcal_events = _load_gcal_events_for_day(tomorrow)
    db_items = _load_db_due_items_for_day(int(chat_id), tomorrow)

    overlaps: List[str] = []
    warnings: List[str] = []

    # 1) event/event overlaps
    for i in range(len(gcal_events)):
        for j in range(i + 1, len(gcal_events)):
            a = gcal_events[i]
            b = gcal_events[j]

            if _overlaps(a["start_utc"], a["end_utc"], b["start_utc"], b["end_utc"]):
                overlaps.append(
                    f"• {_fmt_local(a['start_utc'])}-{_fmt_local(a['end_utc'])} | {a['title']}\n"
                    f"  choca con {_fmt_local(b['start_utc'])}-{_fmt_local(b['end_utc'])} | {b['title']}"
                )

    # 2) DB due item inside calendar event window
    for d in db_items:
        for ev in gcal_events:
            if _overlaps(d["start_utc"], d["end_utc"], ev["start_utc"], ev["end_utc"]):
                warnings.append(
                    f"• {_fmt_local(d['start_utc'])} | vencimiento CASE:{d.get('case_id','?')} "
                    f"cae durante {ev['title']} ({_fmt_local(ev['start_utc'])}-{_fmt_local(ev['end_utc'])})"
                )

    # 3) crowded schedule heuristic
    if len(gcal_events) >= 4:
        warnings.append(f"• Tienes {len(gcal_events)} eventos mañana. Día potencialmente cargado.")

    weekday = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][tomorrow.weekday()]
    month = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"][tomorrow.month]
    pretty = f"{weekday} {tomorrow.day} {month}"

    lines: List[str] = [f"⚠️ Conflictos detectados — mañana ({pretty})", ""]

    if not overlaps and not warnings:
        lines.append("🟢 No veo conflictos claros mañana.")
        return "\n".join(lines)

    if overlaps:
        lines.append("🔴 Choques de horario")
        lines.extend(overlaps)
        lines.append("")

    if warnings:
        lines.append("🟡 Alertas")
        lines.extend(warnings)

    return "\n".join(lines)


async def try_conflicts_tomorrow(update, chat_id, text) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    t = (text or "").strip().lower()

    triggers = (
        "revisa conflictos mañana",
        "revisa conflicto mañana",
        "conflictos mañana",
        "choques mañana",
        "choque mañana",
    )

    if not any(x in t for x in triggers):
        return False

    try:
        out = build_conflict_report_for_tomorrow(int(chat_id))
        await update.message.reply_text(out)
        return True
    except Exception:
        await update.message.reply_text("No pude revisar los conflictos de mañana.")
        return True
