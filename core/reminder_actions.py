import re
from datetime import datetime, timedelta

from memory_store import _get_conn


def parse_reminder_action(text: str):
    if not text:
        return None

    t = text.lower().strip()

    if t in ("done", "hecho", "listo"):
        return {"action": "done"}

    if any(x in t for x in ["now", "ahora", "i'll do it now", "lo hago ahora"]):
        return {"action": "now"}

    if t in ("later", "luego"):
        return {"action": "snooze", "minutes": 30}

    m = re.search(r"(?:snooze|in)\s*(\d+)", t)
    if m:
        return {"action": "snooze", "minutes": int(m.group(1))}

    if "tonight" in t or "esta noche" in t:
        return {"action": "move", "target": "tonight"}

    if "tomorrow" in t or "mañana" in t:
        return {"action": "move", "target": "tomorrow"}

    return None


def apply_reminder_action(chat_id: int, parsed: dict):
    if not parsed:
        return None

    conn = _get_conn()
    cur = conn.cursor()

    # Detect available columns safely
    cols = cur.execute("PRAGMA table_info(commitments)").fetchall()
    col_names = set()
    for c in cols:
        try:
            col_names.add(c[1])
        except Exception:
            pass

    select_cols = ["id", "raw_input"]
    if "target" in col_names:
        select_cols.append("target")
    if "source" in col_names:
        select_cols.append("source")

    row = cur.execute(
        f"""
        SELECT {", ".join(select_cols)}
        FROM commitments
        WHERE chat_id=? AND status='open'
        ORDER BY id DESC
        LIMIT 1
        """,
        (chat_id,),
    ).fetchone()

    if not row:
        conn.close()
        return None

    row_vals = list(row)
    cid = row_vals[0]
    raw = row_vals[1]
    idx = 2

    target = None
    source = None

    if "target" in col_names:
        target = row_vals[idx]
        idx += 1

    if "source" in col_names:
        source = row_vals[idx]
        idx += 1

    # LEGAL SAFETY GUARD
    is_legal = False
    try:
        if target and str(target).lower().startswith("case"):
            is_legal = True
        if source and str(source).lower() in ("case", "legal"):
            is_legal = True
    except Exception:
        pass

    if is_legal:
        conn.close()
        return (
            "⚖️ This looks like a case-related item.\n"
            "Confirm action (done / move / snooze) explicitly."
        )

    if parsed["action"] == "done":
        cur.execute(
            """
            UPDATE commitments
            SET status='done'
            WHERE id=?
            """,
            (cid,),
        )
        conn.commit()
        conn.close()
        return f"✅ Done:\n- {raw}"

    if parsed["action"] == "now":
        conn.close()
        return f"🔥 Good. Go handle it:\n- {raw}"

    if parsed["action"] == "snooze":
        mins = parsed["minutes"]
        due = datetime.utcnow() + timedelta(minutes=mins)

        cur.execute(
            """
            UPDATE commitments
            SET due_date=?
            WHERE id=?
            """,
            (due.isoformat(), cid),
        )
        conn.commit()
        conn.close()
        return f"⏳ Snoozed {mins}m:\n- {raw}"

    if parsed["action"] == "move":
        now = datetime.utcnow()

        if parsed["target"] == "tonight":
            due = now.replace(hour=20, minute=0, second=0, microsecond=0)
            if due <= now:
                due = due + timedelta(days=1)
        elif parsed["target"] == "tomorrow":
            due = (now + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
        else:
            conn.close()
            return None

        cur.execute(
            """
            UPDATE commitments
            SET due_date=?
            WHERE id=?
            """,
            (due.isoformat(), cid),
        )
        conn.commit()
        conn.close()
        return f"📅 Moved:\n- {raw}"

    conn.close()
    return None

