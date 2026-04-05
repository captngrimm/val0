from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional

from memory_store import _get_conn


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _safe_fetchall(conn, query: str, params: tuple = ()) -> List[Any]:
    try:
        cur = conn.execute(query, params)
        return cur.fetchall()
    except Exception:
        return []


def _safe_fetchone(conn, query: str, params: tuple = ()) -> Optional[Any]:
    try:
        cur = conn.execute(query, params)
        return cur.fetchone()
    except Exception:
        return None


def _trim(text: str, limit: int = 220) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _norm_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {
        "1", "true", "yes", "y", "done", "completed", "working"
    }


def _detect_table(conn, candidates: List[str]) -> Optional[str]:
    for name in candidates:
        row = _safe_fetchone(
            conn,
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        )
        if row:
            return name
    return None


def _detect_columns(conn, table_name: str) -> List[str]:
    rows = _safe_fetchall(conn, f"PRAGMA table_info({table_name})")
    cols: List[str] = []
    for row in rows:
        try:
            cols.append(row["name"])
        except Exception:
            try:
                cols.append(row[1])
            except Exception:
                pass
    return cols


def _pick(cols: List[str], names: List[str]) -> Optional[str]:
    for n in names:
        if n in cols:
            return n
    return None

def _task_fingerprint(text: str) -> str:
    t = (text or "").strip().lower()

    # normalize accents
    import unicodedata
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))

    # strip punctuation
    import re
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    # light stopword cleanup for better near-match grouping
    stopwords = {
        "el", "la", "los", "las", "un", "una", "al", "del",
        "que", "de", "para", "por", "con", "y",
    }
    words = [w for w in t.split() if w not in stopwords]

    return " ".join(words)


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            ins = curr[j - 1] + 1
            dele = prev[j] + 1
            sub = prev[j - 1] + (0 if ca == cb else 1)
            curr.append(min(ins, dele, sub))
        prev = curr
    return prev[-1]


def _looks_like_near_duplicate(a: str, b: str) -> bool:
    fa = _task_fingerprint(a)
    fb = _task_fingerprint(b)

    if not fa or not fb:
        return False

    if fa == fb:
        return True

    # token overlap
    sa = set(fa.split())
    sb = set(fb.split())
    if sa and sb:
        overlap = len(sa & sb) / max(1, min(len(sa), len(sb)))
        if overlap >= 0.8:
            return True

    # fuzzy distance for small STT variations like test / tess
    dist = _levenshtein(fa, fb)
    max_len = max(len(fa), len(fb))
    if max_len <= 0:
        return False

    similarity = 1 - (dist / max_len)
    return similarity >= 0.88

def _load_open_commitments(conn, chat_id: int, limit: int = 8) -> List[str]:
    table = _detect_table(conn, ["commitments"])
    if not table:
        return []

    cols = _detect_columns(conn, table)
    chat_col = _pick(cols, ["chat_id", "user_id"])
    raw_col = _pick(cols, ["raw_input", "task_text", "text", "content", "title"])
    action_col = _pick(cols, ["action"])
    target_col = _pick(cols, ["target"])
    due_col = _pick(cols, ["due_date", "due_at", "deadline"])
    status_col = _pick(cols, ["status"])
    created_col = _pick(cols, ["created_at", "ts", "timestamp", "id"])

    if not raw_col:
        return []

    where_parts = []
    params: List[Any] = []

    if chat_col:
        where_parts.append(f"{chat_col}=?")
        params.append(chat_id)

    if status_col:
        where_parts.append(f"COALESCE({status_col}, 'open')='open'")

    where_sql = ""
    if where_parts:
        where_sql = "WHERE " + " AND ".join(where_parts)

    if due_col:
        order_sql = f"ORDER BY CASE WHEN {due_col} IS NULL OR {due_col}='' THEN 1 ELSE 0 END, {due_col} ASC"
    elif created_col:
        order_sql = f"ORDER BY {created_col} DESC"
    else:
        order_sql = ""

    rows = _safe_fetchall(
        conn,
        f"""
        SELECT * FROM {table}
        {where_sql}
        {order_sql}
        LIMIT 50
        """,
        tuple(params),
    )

    out: List[str] = []
    seen_exact = set()
    chosen_clean_texts: List[str] = []

    for row in rows:
        raw_val = row[raw_col]
        if not raw_val:
            continue

        clean = _trim(str(raw_val).replace("\n", " "), 140)
        exact_norm = clean.lower().rstrip(".!?")

        if not clean:
            continue

        if exact_norm in seen_exact:
            continue

        is_dup = False
        for prev in chosen_clean_texts:
            if _looks_like_near_duplicate(clean, prev):
                is_dup = True
                break

        if is_dup:
            continue

        seen_exact.add(exact_norm)
        chosen_clean_texts.append(clean)

        due_val = row[due_col] if due_col else None
        if due_val:
            out.append(f"- {clean} ({str(due_val).strip()})")
        else:
            out.append(f"- {clean}")

        if len(out) >= limit:
            break

    return out

def _load_open_tasks(conn, chat_id: int, limit: int = 8) -> List[str]:
    table = _detect_table(conn, ["tasks", "task_items", "todo_items"])
    if not table:
        return []

    cols = _detect_columns(conn, table)
    chat_col = _pick(cols, ["chat_id", "user_id"])
    text_col = _pick(cols, ["task_text", "text", "content", "title", "task"])
    status_col = _pick(cols, ["status", "done", "completed", "is_done"])
    due_col = _pick(cols, ["due_date", "due_at", "due_ts", "deadline"])
    created_col = _pick(cols, ["created_at", "ts", "timestamp", "created_ts", "id"])

    if not text_col:
        return []

    where_parts = []
    params: List[Any] = []

    if chat_col:
        where_parts.append(f"{chat_col}=?")
        params.append(chat_id)

    if status_col:
        where_parts.append(
            f"(COALESCE({status_col}, '') NOT IN ('done', 'completed', '1', 'true', 'yes'))"
        )

    where_sql = ""
    if where_parts:
        where_sql = "WHERE " + " AND ".join(where_parts)

    if due_col:
        order_sql = f"ORDER BY CASE WHEN {due_col} IS NULL OR {due_col}='' THEN 1 ELSE 0 END, {due_col} ASC"
    elif created_col:
        order_sql = f"ORDER BY {created_col} DESC"
    else:
        order_sql = ""

    rows = _safe_fetchall(
        conn,
        f"""
        SELECT * FROM {table}
        {where_sql}
        {order_sql}
        LIMIT 50
        """,
        tuple(params),
    )

    out: List[str] = []
    seen_exact = set()
    chosen_clean_texts: List[str] = []

    junk_phrases = [
        "follow up action detected from audio",
        "audio follow up",
        "follow-up action detected from audio",
        "ok, ¿puedo seguir hablando contigo en primer plano?",
        "ok, puedo seguir hablando contigo en primer plano?",
    ]

    for row in rows:
        text_val = row[text_col]
        if not text_val:
            continue

        raw = str(text_val).strip()
        low = raw.lower()

        if any(j in low for j in junk_phrases):
            continue

        clean = _trim(raw.replace("\n", " "), 140)
        exact_norm = clean.lower().rstrip(".!?")

        if not clean:
            continue

        if exact_norm in seen_exact:
            continue

        # near-duplicate suppression
        is_dup = False
        for prev in chosen_clean_texts:
            if _looks_like_near_duplicate(clean, prev):
                is_dup = True
                break

        if is_dup:
            continue

        seen_exact.add(exact_norm)
        chosen_clean_texts.append(clean)

        due_val = row[due_col] if due_col else None
        if due_val:
            out.append(f"- {clean} ({str(due_val).strip()})")
        else:
            out.append(f"- {clean}")

        if len(out) >= limit:
            break

    return out


def _load_recent_signals(conn, chat_id: int, limit: int = 6) -> List[str]:
    out: List[str] = []

    table = _detect_table(conn, ["memory_entries", "memory", "messages", "chat_memory"])
    if table:
        cols = _detect_columns(conn, table)
        chat_col = _pick(cols, ["chat_id", "user_id"])
        role_col = _pick(cols, ["role", "speaker", "message_role"])
        text_col = _pick(cols, ["content", "text", "message", "input", "body"])
        ts_col = _pick(cols, ["created_at", "timestamp", "ts", "message_ts", "id"])

        if text_col:
            where_parts = []
            params: List[Any] = []

            if chat_col:
                where_parts.append(f"{chat_col}=?")
                params.append(chat_id)

            if role_col:
                where_parts.append(f"{role_col} IN ('user', 'human')")

            where_sql = ""
            if where_parts:
                where_sql = "WHERE " + " AND ".join(where_parts)

            if ts_col:
                order_sql = f"ORDER BY {ts_col} DESC"
            else:
                order_sql = ""

            rows = _safe_fetchall(
                conn,
                f"""
                SELECT * FROM {table}
                {where_sql}
                {order_sql}
                LIMIT {int(limit * 6)}
                """,
                tuple(params),
            )

            seen = set()

            for row in rows:
                text_val = row[text_col]
                if not text_val:
                    continue

                clean = _trim(str(text_val).replace("\n", " "), 140)
                low = clean.lower()

                if low in seen:
                    continue

                keep = any(
                    phrase in low
                    for phrase in [
                        "tengo que",
                        "llamar",
                        "hoy",
                        "mañana",
                        "después",
                        "luego",
                        "remember",
                        "remind",
                        "need to",
                        "important",
                        "importante",
                        "priority",
                    ]
                )

                if keep:
                    out.append(f"- {clean}")
                    seen.add(low)

                if len(out) >= limit:
                    return out

    facts_table = _detect_table(conn, ["user_facts", "facts", "memory_facts", "kv_store"])
    if not facts_table:
        return out

    cols = _detect_columns(conn, facts_table)
    chat_col = _pick(cols, ["chat_id", "user_id"])
    key_col = _pick(cols, ["fact_key", "key", "name"])
    val_col = _pick(cols, ["fact_value", "value", "content"])

    if not key_col or not val_col:
        return out

    where_parts = []
    params: List[Any] = []

    if chat_col:
        where_parts.append(f"{chat_col}=?")
        params.append(chat_id)

    where_parts.append(
        f"{key_col} IN ('current_priority', 'main_goal', 'preferred_name', 'preferred_language')"
    )

    where_sql = "WHERE " + " AND ".join(where_parts)

    rows = _safe_fetchall(
        conn,
        f"""
        SELECT * FROM {facts_table}
        {where_sql}
        LIMIT 20
        """,
        tuple(params),
    )

    seen = {x.lower() for x in out}

    for row in rows:
        k = str(row[key_col]).strip()
        v = str(row[val_col] or "").strip()
        if not v:
            continue

        line = f"- {k}: {_trim(v, 120)}"
        if line.lower() in seen:
            continue

        out.append(line)
        seen.add(line.lower())

        if len(out) >= limit:
            break

    return out


def _load_fact_lines(conn, chat_id: int, mapping: dict[str, str]) -> List[str]:
    table = _detect_table(conn, ["user_facts", "facts", "memory_facts", "kv_store"])
    if not table:
        return []

    cols = _detect_columns(conn, table)
    chat_col = _pick(cols, ["chat_id", "user_id"])
    key_col = _pick(cols, ["fact_key", "key", "name"])
    val_col = _pick(cols, ["fact_value", "value", "content"])

    if not key_col or not val_col:
        return []

    where_parts = [f"{key_col} IN ({','.join(['?'] * len(mapping))})"]
    params: List[Any] = list(mapping.keys())

    if chat_col:
        where_parts.append(f"{chat_col}=?")
        params.append(chat_id)

    rows = _safe_fetchall(
        conn,
        f"""
        SELECT * FROM {table}
        WHERE {' AND '.join(where_parts)}
        """,
        tuple(params),
    )

    found = {}
    for row in rows:
        k = str(row[key_col]).strip()
        v = row[val_col]
        found[k] = _norm_bool(v)

    out: List[str] = []
    for key, label in mapping.items():
        if found.get(key):
            out.append(f"- {label}")
    return out


def _load_priority(conn, chat_id: int) -> List[str]:
    table = _detect_table(conn, ["user_facts", "facts", "memory_facts", "kv_store"])
    if not table:
        return []

    cols = _detect_columns(conn, table)
    chat_col = _pick(cols, ["chat_id", "user_id"])
    key_col = _pick(cols, ["fact_key", "key", "name"])
    val_col = _pick(cols, ["fact_value", "value", "content"])

    if not key_col or not val_col:
        return []

    where_parts = [f"{key_col}='current_priority'"]
    params: List[Any] = []

    if chat_col:
        where_parts.append(f"{chat_col}=?")
        params.append(chat_id)

    row = _safe_fetchone(
        conn,
        f"""
        SELECT * FROM {table}
        WHERE {' AND '.join(where_parts)}
        ORDER BY rowid DESC
        LIMIT 1
        """,
        tuple(params),
    )

    if not row:
        return []

    raw = str(row[val_col] or "").strip()
    if not raw:
        return []

    parts = [p.strip(" -•\n\r\t") for p in raw.splitlines() if p.strip()]
    if len(parts) <= 1 and ";" in raw:
        parts = [p.strip() for p in raw.split(";") if p.strip()]

    return [f"- {_trim(p, 140)}" for p in parts[:6]]


def _fallback_priority() -> List[str]:
    return [
        "- preserve continuity across chats",
        "- refine /context into better handoff/state snapshot",
        "- then continue with post-Sunday continuity / persistent interface work",
    ]


def build_context_snapshot(
    chat_id: int,
    build_status_lines: Optional[List[str]] = None,
    priority_lines: Optional[List[str]] = None,
) -> str:
    conn = _get_conn()
    conn.row_factory = getattr(conn, "row_factory", None) or __import__("sqlite3").Row

    try:
        open_tasks = _load_open_commitments(conn, chat_id) or _load_open_tasks(conn, chat_id)
        recent_signals = _load_recent_signals(conn, chat_id)
        priority = priority_lines or _load_priority(conn, chat_id) or _fallback_priority()
        build_status = build_status_lines or ["- status facts unavailable"]

        lines: List[str] = []
        lines.append("🧠 CONTEXT SNAPSHOT")
        lines.append("")
        lines.append(f"Generated: {_utc_now_iso()}")
        lines.append("")

        lines.append("OPEN TASKS:")
        lines.extend(open_tasks or ["- none"])
        lines.append("")

        lines.append("RECENT SIGNALS:")
        lines.extend(recent_signals or ["- none"])
        lines.append("")

        lines.append("CURRENT BUILD STATUS:")
        lines.extend(build_status)
        lines.append("")

        lines.append("CURRENT PRIORITY:")
        lines.extend(priority or ["- none"])
        lines.append("")

        lines.append("HANDOFF DIRECTIVE:")
        lines.append("- Continue from current PX01 Val0 state without re-planning completed systems.")
        lines.append("- Prioritize continuity preservation, /context refinement, and persistent interface work.")
        lines.append("- Treat unresolved open tasks and recent commitments as live.")

        return "\n".join(lines).strip()
    finally:
        conn.close()


