import re
from datetime import datetime, timedelta

from memory_store import _get_conn, log_action


def parse_reminder_action(text: str):
    if not text:
        return None

    t = text.lower().strip()

    if t in ("done", "hecho", "listo"):
        return {"action": "done"}

    if t.startswith("done "):
        return {"action": "done", "target_text": text[5:].strip()}

    if t in ("now", "ahora", "ya", "ya voy", "voy ahora", "lo hago ahora", "i'll do it now"):
        return {"action": "now"}

    if t.startswith("now "):
        return {"action": "now", "target_text": text[4:].strip()}

    if t in ("later", "luego"):
        return {"action": "snooze", "minutes": 30}

    if t.startswith("later "):
        return {"action": "snooze", "minutes": 30, "target_text": text[6:].strip()}

    m = re.match(r"^(?:snooze|in)\s*(\d+)(?:\s+(.+))?$", t)
    if m:
        out = {"action": "snooze", "minutes": int(m.group(1))}
        if m.group(2):
            out["target_text"] = text[m.start(2):].strip()
        return out

    if t in ("tonight", "esta noche", "hoy en la noche"):
        return {"action": "move", "target": "tonight"}

    if t.startswith("tonight "):
        return {"action": "move", "target": "tonight", "target_text": text[8:].strip()}

    if t.startswith("esta noche "):
        return {"action": "move", "target": "tonight", "target_text": text[11:].strip()}

    if t in ("tomorrow", "mañana"):
        return {"action": "move", "target": "tomorrow"}

    if t.startswith("tomorrow "):
        return {"action": "move", "target": "tomorrow", "target_text": text[9:].strip()}

    if t.startswith("mañana "):
        return {"action": "move", "target": "tomorrow", "target_text": text[7:].strip()}

    return None

def _normalize_target_text(s: str) -> str:
    s = (s or "").strip().lower()

    import unicodedata
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))

    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _find_open_commitment_by_target(cur, chat_id: int, select_cols, target_text: str):
    needle = _normalize_target_text(target_text)
    if not needle:
        return None

    rows = cur.execute(
        f"""
        SELECT {", ".join(select_cols)}
        FROM commitments
        WHERE chat_id=? AND status='open'
        ORDER BY id DESC
        LIMIT 50
        """,
        (chat_id,),
    ).fetchall()

    best_row = None
    best_score = 0

    for row in rows:
        try:
            raw = str(row[1] or "")
        except Exception:
            continue

        hay = _normalize_target_text(raw)
        if not hay:
            continue

        score = 0
        if needle == hay:
            score = 100
        elif needle in hay:
            score = 90
        else:
            needle_tokens = set(needle.split())
            hay_tokens = set(hay.split())
            overlap = len(needle_tokens & hay_tokens)
            if overlap > 0:
                score = overlap * 10

        if score > best_score:
            best_score = score
            best_row = row

    return best_row if best_score >= 10 else None

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

    select_cols = ["id", "raw_input", "status"]
    if "target" in col_names:
        select_cols.append("target")
    if "source" in col_names:
        select_cols.append("source")
    if "due_date" in col_names:
        select_cols.append("due_date")

    # Try last surfaced commitment first
    row = None

    # 1) Explicit named target wins first
    try:
        target_text = parsed.get("target_text")
        if target_text:
            row = _find_open_commitment_by_target(cur, chat_id, select_cols, target_text)
    except Exception:
        pass

    # 2) Then try last surfaced commitment
    if not row:
        try:
            from memory_store import get_fact

            last_id = get_fact(chat_id=chat_id, fact_key="last_surface_commitment_id")
            if last_id:
                row = cur.execute(
                    f"""
                    SELECT {", ".join(select_cols)}
                    FROM commitments
                    WHERE id=? AND chat_id=? AND status='open'
                    LIMIT 1
                    """,
                    (int(last_id), chat_id),
                ).fetchone()
        except Exception:
            pass

    # 3) Fallback to latest open
    if not row:
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
        return "No open reminder action to close."

    row_vals = list(row)
    idx = 0

    cid = row_vals[idx]
    idx += 1

    raw = row_vals[idx]
    idx += 1

    current_status = row_vals[idx]
    idx += 1

    target = None
    source = None
    current_due_date = None

    if "target" in col_names:
        target = row_vals[idx]
        idx += 1

    if "source" in col_names:
        source = row_vals[idx]
        idx += 1

    if "due_date" in col_names:
        current_due_date = row_vals[idx]
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

        verify = cur.execute(
            "SELECT status FROM commitments WHERE id=?",
            (cid,),
        ).fetchone()

        conn.close()

        if not verify or str(verify[0]).lower() != "done":
            log_action(chat_id, "reminder_done_verify_failed", raw, status="error")
            return "Could not verify closure."

        log_action(chat_id, "reminder_done", raw)
        return f"✅ Done:\n- {raw}"

    if parsed["action"] == "now":
        conn.close()
        log_action(chat_id, "reminder_now", raw)
        return f"🔥 Good. Go handle it:\n- {raw}"

    if parsed["action"] == "snooze":
        mins = parsed["minutes"]
        due = datetime.utcnow() + timedelta(minutes=mins)
        due_iso = due.isoformat()

        cur.execute(
            """
            UPDATE commitments
            SET due_date=?
            WHERE id=?
            """,
            (due_iso, cid),
        )
        conn.commit()

        verify = cur.execute(
            "SELECT due_date FROM commitments WHERE id=?",
            (cid,),
        ).fetchone()

        conn.close()

        if not verify or str(verify[0]) != due_iso:
            log_action(chat_id, "reminder_snooze_verify_failed", raw, status="error")
            return "Could not verify snooze."

        log_action(chat_id, "reminder_snoozed", raw)
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

        due_iso = due.isoformat()

        cur.execute(
            """
            UPDATE commitments
            SET due_date=?
            WHERE id=?
            """,
            (due_iso, cid),
        )
        conn.commit()

        verify = cur.execute(
            "SELECT due_date FROM commitments WHERE id=?",
            (cid,),
        ).fetchone()

        conn.close()

        if not verify or str(verify[0]) != due_iso:
            log_action(chat_id, "reminder_move_verify_failed", raw, status="error")
            return "Could not verify move."

        log_action(chat_id, "reminder_moved", raw)
        return f"📅 Moved:\n- {raw}"

    conn.close()
    return None

