import re
from datetime import datetime, timedelta, timezone

from memory_store import insert_reminder

try:
    from zoneinfo import ZoneInfo  # py3.9+
except Exception:
    ZoneInfo = None


# Deterministic reminder grammar (DM only):
# - recuerdame / recuérdame / acuerdame / acuérdame / recordame
# - "en N minutos" / "en N horas"
# - "hoy a las HH:MM" / "a las 6pm"
# - "mañana a las HH:MM" / "mañana 3pm"
_VERB = r"(?:recu[eé]rdame|acu[eé]rdame|acuerdame|recordame)"

_RE_MIN = re.compile(
    rf"(?is)^\s*{_VERB}\s+(?P<what>.+?)\s+en\s+(?P<n>\d{{1,4}})\s+minutos?\s*$"
)
_RE_HOUR = re.compile(
    rf"(?is)^\s*{_VERB}\s+(?P<what>.+?)\s+en\s+(?P<n>\d{{1,4}})\s+horas?\s*$"
)

# time token supports: 15:30, 3pm, 3 pm, 3:15pm, 03:05
_TIME_TOKEN = r"(?P<t>(?:\d{1,2}:\d{2})|(?:\d{1,2}(?::\d{2})?\s*(?:am|pm)))"

_RE_TODAY_AT = re.compile(
    rf"(?is)^\s*{_VERB}\s+(?P<what>(?:(?!\bma[nñ]ana\b).)+?)\s+(?:hoy\s+)?a\s+las?\s+{_TIME_TOKEN}\s*$"
)

# allow both: "mañana a las 3pm" and "mañana 15:30"
_RE_TOMORROW_AT = re.compile(
    rf"(?is)^\s*{_VERB}\s+(?P<what>.+?)\s+ma[nñ]ana\s+(?:a\s+las?\s+)?{_TIME_TOKEN}\s*$"
)

# Cancel by id: "cancela 28" / "olvida el recordatorio #28"
_RE_CANCEL = re.compile(
    r"(?is)^\s*(?:olvida|cancela|borra)\s+(?:el\s+)?(?:recordatorio\s+)?#?(?P<rid>\d{1,9})\s*$"
)

_CASE_RE = re.compile(r"\b(?:expediente|exp|caso|case)\s*[:#]?\s*(?P<cid>\d{4,})\b", re.IGNORECASE)

def _extract_case_parent_ref(text: str) -> str | None:
    """
    If the reminder text mentions a case/expediente number, link it as CASE:<id>.
    """
    t = (text or "").strip()
    if not t:
        return None

    m = _CASE_RE.search(t)
    if not m:
        return None

    cid = (m.group("cid") or "").strip()
    if not cid:
        return None

    return f"CASE:{cid}"

def _tz_local():
    tz_name = "America/Panama"
    try:
        import os

        tz_name = os.getenv("VAL0_TZ", tz_name)
    except Exception:
        pass

    if ZoneInfo:
        try:
            return ZoneInfo(tz_name)
        except Exception:
            return timezone.utc
    return timezone.utc


def _now_local() -> datetime:
    return datetime.now(_tz_local())


def _to_utc_iso(dt: datetime) -> str:
    # store as sqlite-friendly UTC string
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _parse_time_token(token: str):
    """
    Returns (hour, minute) or None.
    Accepts:
      - HH:MM (24h)
      - Hpm / Ham
      - H:MMpm / H:MM am
    """
    s = (token or "").strip().lower().replace(" ", "")
    if not s:
        return None

    # 24h HH:MM
    if re.fullmatch(r"\d{1,2}:\d{2}", s):
        hh, mm = s.split(":")
        h = int(hh)
        m = int(mm)
        if 0 <= h <= 23 and 0 <= m <= 59:
            return h, m
        return None

    # am/pm
    m = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?(am|pm)", s)
    if not m:
        return None

    h = int(m.group(1))
    minute = int(m.group(2) or "0")
    ap = m.group(3)

    if not (1 <= h <= 12) or not (0 <= minute <= 59):
        return None

    # convert to 24h
    if ap == "am":
        h = 0 if h == 12 else h
    else:
        h = 12 if h == 12 else (h + 12)

    return h, minute


async def try_cancel_reminder(update, chat_id: int, text: str, audit_fn=None) -> bool:
    """
    Deterministic reminder cancel (DM only). Returns True if handled.
    Matches: "olvida 28", "cancela #28", "borra el recordatorio 28"
    """
    # Never cancel reminders in groups (same rule as create)
    try:
        if int(chat_id) < 0:
            return False
    except Exception:
        pass

    t = (text or "").strip()
    t = re.sub(r"[.!?]+$", "", t).strip()
    if not t:
        return False

    m = _RE_CANCEL.match(t)
    if not m:
        return False

    rid = int(m.group("rid") or "0")
    if rid <= 0:
        await update.message.reply_text("ID inválido, Boss.")
        return True

    # Only cancel pending/sending, and only for this chat_id (enforced in DB layer)
    try:
        from memory_store import cancel_reminder

        ok = cancel_reminder(chat_id=int(chat_id), rid=rid)
    except Exception:
        ok = False

    if audit_fn:
        audit_fn(
            chat_id=int(chat_id),
            action="CMD_REMINDER_CANCEL",
            entity_type="reminder",
            entity_id=str(rid),
            payload=f"rid={rid} ok={ok}"[:200],
            source="dm",
        )

    if ok:
        await update.message.reply_text(f"Listo, Boss. Cancelé el recordatorio #{rid}.")
    else:
        await update.message.reply_text(
            f"No pude cancelar #{rid}. Puede que no exista, no sea tuyo, o ya esté enviado/cancelado."
        )
    return True


async def try_create_reminder(update, chat_id: int, text: str, audit_fn=None) -> bool:
    """
    Deterministic reminder creator (DM only). Returns True if handled.
    audit_fn signature: audit_fn(chat_id, action, entity_type=None, entity_id=None, payload=None, source=None)
    """
    # Never create reminders in groups
    try:
        if int(chat_id) < 0:
            return False
    except Exception:
        pass

    t = (text or "").strip()
    t = re.sub(r"[.!?]+$", "", t).strip()
    if not t:
        return False

    # 1) "en N minutos"
    m = _RE_MIN.match(t)
    if m:
        what = (m.group("what") or "").strip()
        n = int(m.group("n") or "0")
        if n <= 0 or n > 1440:
            await update.message.reply_text("Dame minutos entre 1 y 1440, Boss.")
            return True
        if not what:
            await update.message.reply_text("¿Qué quieres que recuerde, Boss? Ej: Recuérdame pagar X en 10 minutos.")
            return True

        due_utc = datetime.now(timezone.utc) + timedelta(minutes=n)
        due_str = _to_utc_iso(due_utc)
        parent_ref = _extract_case_parent_ref(what)
        rid = insert_reminder(
            chat_id=int(chat_id),
            due_at_utc=due_str,
            text=what,
            status="pending",
            entity_type="reminder",
            parent_ref=parent_ref,
        )

        if audit_fn:
            audit_fn(
                chat_id=int(chat_id),
                action="CMD_REMINDER_CREATE",
                entity_type="reminder",
                entity_id=str(rid),
                payload=f"mode=minutes | due_at_utc={due_str} | text={what}"[:500],
                source="dm",
            )

        await update.message.reply_text(f"Listo, Boss. Te lo recuerdo en {n} minuto(s).")
        return True

    # 2) "en N horas"
    m = _RE_HOUR.match(t)
    if m:
        what = (m.group("what") or "").strip()
        n = int(m.group("n") or "0")
        if n <= 0 or n > 24:
            await update.message.reply_text("Dame horas entre 1 y 24, Boss.")
            return True
        if not what:
            await update.message.reply_text("¿Qué quieres que recuerde, Boss? Ej: Acuérdame X en 2 horas.")
            return True

        due_utc = datetime.now(timezone.utc) + timedelta(hours=n)
        due_str = _to_utc_iso(due_utc)
        parent_ref = _extract_case_parent_ref(what)
        rid = insert_reminder(
            chat_id=int(chat_id),
            due_at_utc=due_str,
            text=what,
            status="pending",
            entity_type="reminder",
            parent_ref=parent_ref,
        )

        if audit_fn:
            audit_fn(
                chat_id=int(chat_id),
                action="CMD_REMINDER_CREATE",
                entity_type="reminder",
                entity_id=str(rid),
                payload=f"mode=hours | due_at_utc={due_str} | text={what}"[:500],
                source="dm",
            )

        await update.message.reply_text(f"Listo, Boss. Te lo recuerdo en {n} hora(s).")
        return True

    # 3) "mañana ..."
    m = _RE_TOMORROW_AT.match(t)
    if m:
        what = (m.group("what") or "").strip()
        tok = (m.group("t") or "").strip()
        hm = _parse_time_token(tok)
        if not what:
            await update.message.reply_text("¿Qué quieres que recuerde, Boss? Ej: Recuérdame X mañana a las 3pm.")
            return True
        if not hm:
            await update.message.reply_text("Hora inválida. Usa HH:MM (24h) o 3pm / 3:15pm.")
            return True

        h, minute = hm
        nowL = _now_local()
        dueL = (nowL + timedelta(days=1)).replace(hour=h, minute=minute, second=0, microsecond=0)
        due_str = _to_utc_iso(dueL)
        parent_ref = _extract_case_parent_ref(what)
        rid = insert_reminder(
            chat_id=int(chat_id),
            due_at_utc=due_str,
            text=what,
            status="pending",
            entity_type="reminder",
            parent_ref=parent_ref,
        )

        if audit_fn:
            audit_fn(
                chat_id=int(chat_id),
                action="CMD_REMINDER_CREATE",
                entity_type="reminder",
                entity_id=str(rid),
                payload=f"mode=tomorrow_at | due_at_utc={due_str} | local={dueL.isoformat()} | text={what}"[:500],
                source="dm",
            )

        await update.message.reply_text(f"Listo, Boss. Te lo recuerdo mañana a las {h:02d}:{minute:02d}.")
        return True

    # 4) "hoy a las ..." / "a las ..."
    m = _RE_TODAY_AT.match(t)
    if m:
        what = (m.group("what") or "").strip()
        tok = (m.group("t") or "").strip()
        hm = _parse_time_token(tok)
        if not what:
            await update.message.reply_text("¿Qué quieres que recuerde, Boss? Ej: Recuérdame X a las 18:00.")
            return True
        if not hm:
            await update.message.reply_text("Hora inválida. Usa HH:MM (24h) o 6pm / 6:15pm.")
            return True

        h, minute = hm
        nowL = _now_local()
        dueL = nowL.replace(hour=h, minute=minute, second=0, microsecond=0)

        # If the time already passed today, refuse (deterministic + avoids surprise)
        if dueL <= nowL:
            await update.message.reply_text("Esa hora ya pasó hoy, Boss. Usa 'mañana' o 'en N minutos'.")
            return True

        due_str = _to_utc_iso(dueL)
        parent_ref = _extract_case_parent_ref(what)
        rid = insert_reminder(
            chat_id=int(chat_id),
            due_at_utc=due_str,
            text=what,
            status="pending",
            entity_type="reminder",
            parent_ref=parent_ref,
        )

        if audit_fn:
            audit_fn(
                chat_id=int(chat_id),
                action="CMD_REMINDER_CREATE",
                entity_type="reminder",
                entity_id=str(rid),
                payload=f"mode=today_at | due_at_utc={due_str} | local={dueL.isoformat()} | text={what}"[:500],
                source="dm",
            )

        await update.message.reply_text(f"Listo, Boss. Te lo recuerdo hoy a las {h:02d}:{minute:02d}.")
        return True

    return False