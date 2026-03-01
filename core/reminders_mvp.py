import re
import time
from datetime import datetime, timedelta, timezone

from memory_store import insert_reminder

# Minimal deterministic parser:
# "Recuérdame <thing> en <N> minutos"
_REM_RE = re.compile(
    r"(?is)^\s*recu[eé]rdame\s+(?P<what>.+?)\s+en\s+(?P<n>\d{1,4})\s+minutos?\s*$"
)

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

def _to_utc_iso(dt: datetime) -> str:
    # store as sqlite-friendly UTC string
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

async def try_create_reminder(update, chat_id: int, text: str, audit_fn=None) -> bool:
    """
    Deterministic reminder creator (DM only). Returns True if handled.
    audit_fn signature: audit_fn(chat_id, action, entity_type=None, entity_id=None, payload=None, source=None)
    """
    t = (text or "").strip()
    m = _REM_RE.match(t)
    if not m:
        return False

    what = (m.group("what") or "").strip()
    n = int(m.group("n") or "0")

    if n <= 0 or n > 1440:  # cap to 24h for MVP safety
        await update.message.reply_text("Dame minutos entre 1 y 1440, Boss.")
        return True

    if not what:
        await update.message.reply_text("¿Qué quieres que recuerde, Boss? Ej: Recuérdame pagar X en 10 minutos.")
        return True

    due = _utc_now() + timedelta(minutes=n)
    due_str = _to_utc_iso(due)

    rid = insert_reminder(chat_id=int(chat_id), due_at_utc=due_str, text=what, status="pending")

    if audit_fn:
        audit_fn(
            chat_id=int(chat_id),
            action="CMD_REMINDER_CREATE",
            entity_type="reminder",
            entity_id=str(rid),
            payload=f"due_at_utc={due_str} | text={what}"[:500],
            source="dm",
        )

    await update.message.reply_text(f"Listo, Boss. Te lo recuerdo en {n} minuto(s).")
    return True
