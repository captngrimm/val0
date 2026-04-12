import os
import threading
import logging
import unicodedata
from typing import List, Dict, Optional, Any

import re

_WS_RE = re.compile(r"[ \t\f\v]+")
_LIT_ESC_RE = re.compile(r"\\[nrt]")  # literal \n \r \t sequences

def sanitize_reminder_text(s: str) -> str:
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)

    # normalize CRLF/CR then remove actual newlines
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("\n", " ")

    # remove literal escape fragments like "\\n"
    s = _LIT_ESC_RE.sub(" ", s)

    # collapse whitespace + trim
    s = _WS_RE.sub(" ", s).strip()

    # hard guard
    if "\n" in s or "\r" in s:
        raise ValueError("sanitize_reminder_text failed: newline fragment remains")

    return s

logger = logging.getLogger("val0-memory")

def _log_db_mode():
    try:
        key = _read_db_key()
        if key:
            logger.info(f"[DB CHECK] SQLCipher=ON | DB_PATH={DB_PATH}")
        else:
            if ALLOW_PLAINTEXT:
                logger.warning(f"[DB CHECK] SQLCipher=OFF (PLAINTEXT MODE) | DB_PATH={DB_PATH}")
            else:
                logger.error("[DB CHECK] No DB key and plaintext not allowed.")
    except Exception as e:
        logger.error(f"[DB CHECK] Failed to determine DB mode: {e}")


# Encrypted DB path (systemd sets this)
DB_PATH = os.getenv("VAL0_DB_PATH", "/opt/val0/val0_memory.enc.db")

# Prefer key file (systemd sets this). Env key is only for dev fallback.
DB_KEY_FILE = os.getenv("VAL0_DB_KEY_FILE", "").strip()
DB_KEY_ENV = os.getenv("VAL0_DB_KEY", "").strip()

# Default: do NOT allow plaintext fallback unless explicitly enabled
ALLOW_PLAINTEXT = os.getenv("VAL0_ALLOW_PLAINTEXT", "0").strip().lower() in ("1", "true", "yes")

_lock = threading.Lock()


def _read_db_key() -> str:
    if DB_KEY_FILE:
        with open(DB_KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    if DB_KEY_ENV:
        return DB_KEY_ENV
    return ""


def _get_conn():
    """
    Encrypted-first DB connection.
    If a key exists => SQLCipher (pysqlcipher3)
    If no key => refuse unless VAL0_ALLOW_PLAINTEXT=1
    """
    key = _read_db_key()

    if key:
        from pysqlcipher3 import dbapi2 as sqlcipher
        conn = sqlcipher.connect(DB_PATH)
        conn.row_factory = sqlcipher.Row
        cur = conn.cursor()

        # Escape single quotes just in case
        key_esc = key.replace("'", "''")
        cur.execute(f"PRAGMA key='{key_esc}';")
        cur.execute("PRAGMA cipher_compatibility=4;")
        return conn

    if not ALLOW_PLAINTEXT:
        raise RuntimeError(
            "No DB key provided. Set VAL0_DB_KEY_FILE (recommended) or VAL0_DB_KEY. "
            "If you want plaintext dev mode, set VAL0_ALLOW_PLAINTEXT=1."
        )

    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Create tables if they don't exist.
    IMPORTANT: schema must match the already-live DB used by bot.py.
    """
    with _lock:
        _log_db_mode()
        conn = _get_conn()
        cur = conn.cursor()

        # messages (matches your live table: id, chat_id, role, content, telegram_message_id, model_used, created_at)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            telegram_message_id INTEGER,
            model_used TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);")

        # reminders
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            due_at_utc TEXT NOT NULL,
            text TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            sent_at TEXT
        );
        """)

        # legal audit log (deterministic trace layer)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS legal_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            gate_name TEXT NOT NULL,
            action_type TEXT NOT NULL,
            metadata_json TEXT,
            source TEXT,
            severity TEXT DEFAULT 'info',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_legal_audit_chat_id ON legal_audit_log(chat_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_legal_audit_gate ON legal_audit_log(gate_name);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_legal_audit_created_at ON legal_audit_log(created_at);")

        # chat_prefs: per-chat toggles (voice mode, etc)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_prefs (
          chat_id INTEGER PRIMARY KEY,
          voice_enabled INTEGER DEFAULT 0,
          updated_at TEXT DEFAULT (datetime('now'))
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(status, due_at_utc);")

        # timeline extension (unified reminders/tasks/events)
        # Columns migrated manually via SQLCipher ALTER TABLE for now.
        pass

        # audit_log: immutable operational trace
        cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            chat_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id TEXT,
            payload TEXT,
            source TEXT
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_chat ON audit_log(chat_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at);")

        # --------------------------------------------------
        # Phase 2: case summary cache (derived, non-authoritative)
        # --------------------------------------------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS case_summaries (
            chat_id INTEGER NOT NULL,
            case_id TEXT NOT NULL,
            summary_text TEXT NOT NULL DEFAULT '',
            last_event_at TEXT,
            last_note_at TEXT,
            next_deadline TEXT,
            open_reminders_count INTEGER NOT NULL DEFAULT 0,
            last_summary_refresh TEXT,
            summary_version INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (chat_id, case_id)
        );
        """)

        # --------------------------------------------------
        # PM loop tables (isolated from canonical case/reminder data)
        # --------------------------------------------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS pm_current_focus (
            chat_id INTEGER PRIMARY KEY,
            focus_title TEXT NOT NULL,
            focus_summary TEXT DEFAULT '',
            roadmap_note TEXT DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS pm_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_input TEXT NOT NULL,
            decision TEXT NOT NULL,
            reason TEXT DEFAULT '',
            next_action TEXT DEFAULT '',
            surfaced_to_user INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pm_decisions_chat_id ON pm_decisions(chat_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pm_decisions_created_at ON pm_decisions(created_at);")

        conn.commit()
        conn.close()
        logger.info(f"SQLite DB initialized at {DB_PATH}")


def insert_message(
    chat_id: int,
    role: str,
    content: str,
    telegram_message_id: Optional[int] = None,
    model_used: Optional[str] = None,
) -> None:
    """
    Clean version. No legacy positional guessing.
    """

    if not role or not content:
        raise ValueError("insert_message requires role and content")

    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages(chat_id, role, content, telegram_message_id, model_used) VALUES(?,?,?,?,?)",
            (chat_id, role, content, telegram_message_id, model_used),
        )
        conn.commit()
        conn.close()


def fetch_recent_messages(chat_id: int, limit: int = 30) -> List[Dict[str, Any]]:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, chat_id, role, content, telegram_message_id, model_used, created_at "
            "FROM messages WHERE chat_id=? ORDER BY id DESC LIMIT ?",
            (chat_id, limit),
        )
        rows = cur.fetchall()
        conn.close()
    return [dict(r) for r in reversed(rows)]

def trim_messages_for_chat(chat_id: int, keep_last: int = 12) -> None:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            DELETE FROM messages
            WHERE chat_id = ?
              AND id NOT IN (
                SELECT id
                FROM messages
                WHERE chat_id = ?
                ORDER BY id DESC
                LIMIT ?
              )
            """,
            (int(chat_id), int(chat_id), int(keep_last)),
        )
        conn.commit()
        conn.close()


def set_pm_focus(chat_id: int, focus_title: str, focus_summary: str = "", roadmap_note: str = "") -> None:
    focus_title = (focus_title or "").strip() or "General execution"
    focus_summary = (focus_summary or "").strip()
    roadmap_note = (roadmap_note or "").strip()

    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            "INSERT OR IGNORE INTO pm_current_focus(chat_id, focus_title, focus_summary, roadmap_note, updated_at) VALUES(?,?,?,?,datetime('now'))",
            (int(chat_id), focus_title, focus_summary, roadmap_note),
        )

        cur.execute(
            """
            UPDATE pm_current_focus
            SET focus_title = ?,
                focus_summary = ?,
                roadmap_note = ?,
                updated_at = datetime('now')
            WHERE chat_id = ?
            """,
            (focus_title, focus_summary, roadmap_note, int(chat_id)),
        )

        conn.commit()
        conn.close()


def get_pm_focus(chat_id: int) -> Dict[str, Any]:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT chat_id, focus_title, focus_summary, roadmap_note, updated_at
            FROM pm_current_focus
            WHERE chat_id = ?
            """,
            (int(chat_id),),
        )
        row = cur.fetchone()
        conn.close()

    if row:
        return dict(row)

    return {
        "chat_id": int(chat_id),
        "focus_title": "General execution",
        "focus_summary": "",
        "roadmap_note": "",
        "updated_at": None,
    }


def log_pm_decision(
    chat_id: int,
    user_input: str,
    decision: str,
    reason: str,
    next_action: str,
    surfaced_to_user: bool = False,
) -> None:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO pm_decisions(chat_id, user_input, decision, reason, next_action, surfaced_to_user)
            VALUES(?,?,?,?,?,?)
            """,
            (
                int(chat_id),
                (user_input or "").strip(),
                (decision or "").strip(),
                (reason or "").strip(),
                (next_action or "").strip(),
                1 if surfaced_to_user else 0,
            ),
        )
        conn.commit()
        conn.close()


def get_last_non_drift_user_input(chat_id: int, limit: int = 20) -> str:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT user_input
            FROM pm_decisions
            WHERE chat_id = ?
              AND decision = 'DO_NOW'
              AND TRIM(COALESCE(user_input, '')) <> ''
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(chat_id), int(limit)),
        )
        rows = cur.fetchall()
        conn.close()

    for row in rows:
        val = row["user_input"] if hasattr(row, "keys") else row[0]
        if val and str(val).strip():
            return str(val).strip()

    return ""
    

def evaluate_pm_input(chat_id: int, user_input: str) -> Dict[str, str]:
    text = (user_input or "").strip()
    low = text.lower()
    focus = get_pm_focus(int(chat_id))

    do_now_markers = (
        "memory", "memoria", "context", "contexto", "telegram", "prompt",
        "bot.py", "pipeline", "continuity", "continuidad", "session",
        "sesion", "sesión", "miguel", "demo", "focus", "recordatorio",
        "reminder", "calendar", "calendario",
    )
    defer_markers = (
        "watch", "wear", "alexa", "ui", "interfaz", "theme", "tema",
        "app", "aplicacion", "aplicación", "multidevice", "device",
        "voice playback", "speaker", "audio flow", "book", "newspaper",
    )
    discard_markers = (
        "rewrite everything", "start over", "rebuild from scratch",
        "change the whole stack", "cambiar todo", "empezar de cero",
    )

    decision = "DO_NOW"
    reason = "No drift detected."
    next_action = f"Continue current focus: {focus['focus_title']}"

    if any(x in low for x in discard_markers):
        decision = "DISCARD"
        reason = "Destabilizing scope or reset-risk input."
        next_action = f"Ignore this and continue: {focus['focus_title']}"
    elif any(x in low for x in defer_markers):
        decision = "DEFER"
        reason = "Useful, but outside the current MVP critical path."
        next_action = f"Log it for later and continue: {focus['focus_title']}"
    elif any(x in low for x in do_now_markers):
        decision = "DO_NOW"
        reason = "Directly supports the active MVP path."
        next_action = f"Advance current focus: {focus['focus_title']}"

    return {
        "current_focus": focus["focus_title"],
        "focus_summary": focus.get("focus_summary", "") or "",
        "roadmap_note": focus.get("roadmap_note", "") or "",
        "decision": decision,
        "reason": reason,
        "next_action": next_action,
    }

# bot.py expects this name

def insert_reminder(
    chat_id: int,
    due_at_utc: str,
    text: str,
    status: str = "pending",
    entity_type: str = "reminder",
    parent_ref: str | None = None,
) -> int:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        text = sanitize_reminder_text(text)

        try:
            cur.execute(
                "INSERT INTO reminders(chat_id, due_at_utc, text, status, entity_type, parent_ref) VALUES(?,?,?,?,?,?)",
                (chat_id, due_at_utc, text, status, entity_type, parent_ref),
            )
            conn.commit()
            rid = cur.lastrowid
            conn.close()
            return rid

        except Exception as e:
            msg = str(e or "")
            if "UNIQUE constraint failed" not in msg:
                conn.close()
                raise

            cur.execute(
                """
                SELECT id
                FROM reminders
                WHERE chat_id = ?
                  AND due_at_utc = ?
                  AND text = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (chat_id, due_at_utc, text),
            )
            row = cur.fetchone()
            conn.close()

            if row is None:
                raise

            return int(row["id"] if hasattr(row, "keys") else row[0])

def upsert_case(chat_id: int, expediente: str, client_name: str = None, client_alias: str = None) -> int:
    """
    Create or update a case registry row for this chat.
    """
    expediente = (expediente or "").strip()
    client_name = (client_name or "").strip() or None
    client_alias = (client_alias or "").strip() or None

    if not expediente:
        raise ValueError("expediente is required")

    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id
            FROM cases
            WHERE chat_id=? AND expediente=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (int(chat_id), expediente),
        )
        row = cur.fetchone()

        if row:
            case_id = int(row["id"] if hasattr(row, "keys") else row[0])
            cur.execute(
                """
                UPDATE cases
                SET client_name = COALESCE(?, client_name),
                    client_alias = COALESCE(?, client_alias)
                WHERE id = ?
                """,
                (client_name, client_alias, case_id),
            )
            conn.commit()
            conn.close()
            return case_id

        cur.execute(
            """
            INSERT INTO cases(chat_id, expediente, client_name, client_alias)
            VALUES(?,?,?,?)
            """,
            (int(chat_id), expediente, client_name, client_alias),
        )
        conn.commit()
        case_id = cur.lastrowid
        conn.close()
        return int(case_id)


def get_case_by_client_name(chat_id: int, client_name: str):
    """
    Resolve a case by client_name or client_alias inside the same chat.
    Returns dict row or None.
    """
    name = (client_name or "").strip()
    if not name:
        return None

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, expediente, client_name, client_alias, created_at
        FROM cases
        WHERE chat_id=?
          AND (
            lower(client_name)=lower(?)
            OR lower(client_alias)=lower(?)
          )
        ORDER BY id DESC
        LIMIT 1
        """,
        (int(chat_id), name, name),
    )
    row = cur.fetchone()
    conn.close()

    return dict(row) if row else None

def insert_audit(
    chat_id: int,
    action: str,
    entity_type: str = None,
    entity_id: str = None,
    payload: str = None,
    source: str = None,
) -> None:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO audit_log(chat_id, action, entity_type, entity_id, payload, source)
            VALUES(?,?,?,?,?,?)
            """,
            (chat_id, action, entity_type, entity_id, payload, source),
        )
        conn.commit()
        conn.close()

def log_reminder_state_change(chat_id: int, rid: int, old_state: str, new_state: str, source: str = "reminder_state") -> None:
    """
    Immutable audit entry for reminder state transitions.
    """
    from datetime import datetime, timezone

    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    payload = f"rid={int(rid)}\nold={old_state}\nnew={new_state}\ntimestamp={ts}"
    insert_audit(
        chat_id=int(chat_id),
        action="REMINDER_STATE_CHANGE",
        entity_type="reminder",
        entity_id=str(int(rid)),
        payload=payload,
        source=source,
    )

def fetch_due_reminders(limit: int = 10) -> List[Dict[str, Any]]:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, chat_id, due_at_utc, text, status, sent_at, entity_type, parent_ref "
            "FROM reminders "
            "WHERE status='pending' "
            "AND COALESCE(entity_type, 'reminder')='reminder' "
            "AND due_at_utc <= datetime('now') "
            "ORDER BY due_at_utc ASC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
    return [dict(r) for r in rows]


def mark_reminder_sent(reminder_id: int) -> None:
    audit_chat_id = None
    audit_old_state = None
    changed = False

    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT chat_id, status FROM reminders WHERE id=?",
            (reminder_id,),
        )
        row = cur.fetchone()
        if row:
            audit_chat_id = int(row[0])
            audit_old_state = (row[1] or "").strip().lower()

        cur.execute(
            "UPDATE reminders SET status='sent', sent_at=datetime('now') WHERE id=?",
            (reminder_id,),
        )
        changed = (cur.rowcount == 1)

        conn.commit()
        conn.close()

    if changed and audit_chat_id is not None:
        log_reminder_state_change(
            chat_id=audit_chat_id,
            rid=reminder_id,
            old_state=audit_old_state or "sending",
            new_state="sent",
            source="mark_reminder_sent",
        )


def mark_reminder_failed(reminder_id: int, reason: str = "failed") -> None:
    audit_chat_id = None
    audit_old_state = None
    changed = False

    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT chat_id, status FROM reminders WHERE id=?",
            (reminder_id,),
        )
        row = cur.fetchone()
        if row:
            audit_chat_id = int(row[0])
            audit_old_state = (row[1] or "").strip().lower()

        cur.execute(
            "UPDATE reminders SET status='failed', sent_at=datetime('now') WHERE id=?",
            (reminder_id,),
        )
        changed = (cur.rowcount == 1)

        conn.commit()
        conn.close()

    if changed and audit_chat_id is not None:
        src = f"mark_reminder_failed:{reason}" if reason else "mark_reminder_failed"
        log_reminder_state_change(
            chat_id=audit_chat_id,
            rid=reminder_id,
            old_state=audit_old_state or "sending",
            new_state="failed",
            source=src,
        )

def _ensure_user_facts_table(cur) -> None:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_facts';")
    if cur.fetchone():
        return

    # Create table if missing (keeps MVP working; encryption already handled at connection level)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        fact_key TEXT NOT NULL,
        fact_value TEXT NOT NULL,
        source TEXT,
        confidence REAL,
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE(chat_id, fact_key)
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_user_facts_chat ON user_facts(chat_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_user_facts_key ON user_facts(chat_id, fact_key);")

def _ensure_action_logs_table(cur):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS action_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        action_type TEXT,
        payload TEXT,
        status TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_action_logs_chat ON action_logs(chat_id);")

def log_action(chat_id: int, action_type: str, payload: str, status: str = "ok"):
    try:
        with _lock:
            conn = _get_conn()
            cur = conn.cursor()
            _ensure_action_logs_table(cur)

            cur.execute(
                """
                INSERT INTO action_logs (chat_id, action_type, payload, status)
                VALUES (?, ?, ?, ?);
                """,
                (chat_id, action_type, payload, status),
            )

            conn.commit()
            conn.close()
    except Exception:
        pass    

def _ensure_processed_events_table(cur):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS processed_events (
        event_key TEXT PRIMARY KEY,
        event_type TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_processed_events_type ON processed_events(event_type);")


def has_processed_event(event_key: str) -> bool:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        _ensure_processed_events_table(cur)
        row = cur.execute(
            "SELECT 1 FROM processed_events WHERE event_key=? LIMIT 1;",
            (event_key,),
        ).fetchone()
        conn.close()
        return row is not None


def mark_processed_event(event_key: str, event_type: str) -> None:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        _ensure_processed_events_table(cur)
        cur.execute(
            """
            INSERT OR IGNORE INTO processed_events (event_key, event_type)
            VALUES (?, ?);
            """,
            (event_key, event_type),
        )
        conn.commit()
        conn.close()


def mark_processed_event_once(event_key: str, event_type: str) -> bool:
    """
    Returns True if this call inserted the event for the first time.
    Returns False if the event already existed.
    """
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        _ensure_processed_events_table(cur)
        cur.execute(
            """
            INSERT OR IGNORE INTO processed_events (event_key, event_type)
            VALUES (?, ?);
            """,
            (event_key, event_type),
        )
        inserted = cur.rowcount == 1
        conn.commit()
        conn.close()
        return inserted    

def upsert_fact(chat_id: int, fact_key: str, fact_value: str,
                source: str = "auto", confidence: float = 1.0) -> None:
    """
    bot.py expects this.
    Stores durable user facts (lightweight "infinite memory" seed).

    Uses INSERT OR IGNORE + UPDATE for compatibility with older SQLite/SQLCipher builds.
    """
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        _ensure_user_facts_table(cur)

        cur.execute(
            """
            INSERT OR IGNORE INTO user_facts
            (chat_id, fact_key, fact_value, source, confidence, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (chat_id, fact_key, fact_value, source, confidence),
        )

        cur.execute(
            """
            UPDATE user_facts
            SET fact_value=?,
                source=?,
                confidence=?,
                updated_at=datetime('now')
            WHERE chat_id=? AND fact_key=?
            """,
            (fact_value, source, confidence, chat_id, fact_key),
        )

        conn.commit()
        conn.close()


def get_facts(chat_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        _ensure_user_facts_table(cur)

        cur.execute("""
        SELECT fact_key, fact_value, source, confidence, updated_at
        FROM user_facts
        WHERE chat_id=?
        ORDER BY updated_at DESC
        LIMIT ?;
        """, (chat_id, limit))

        rows = cur.fetchall()
        conn.close()
    return [dict(r) for r in rows]


def delete_fact(chat_id: int, fact_key: str) -> None:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        _ensure_user_facts_table(cur)
        cur.execute("DELETE FROM user_facts WHERE chat_id=? AND fact_key=?;", (chat_id, fact_key))
        conn.commit()
        conn.close()

def save_fact(chat_id: int, fact_key: str, fact_value: str, _impl=upsert_fact):
    return _impl(chat_id=chat_id, fact_key=fact_key, fact_value=fact_value)


def fetch_fact(chat_id: int, fact_key: str):
    rows = get_facts(chat_id=chat_id, limit=500)
    for row in rows:
        try:
            if row.get("fact_key") == fact_key:
                return row.get("fact_value")
        except Exception:
            pass
    return None


def fetch_all_facts(chat_id: int):
    rows = get_facts(chat_id=chat_id, limit=500)
    out = {}
    for row in rows:
        try:
            k = row.get("fact_key")
            v = row.get("fact_value")
            if k:
                out[k] = v
        except Exception:
            pass
    return out

# ==========================================================
# NUDGE / FOLLOW-UP HELPERS (operator layer)
# ==========================================================

def get_last_nudge_at(chat_id: int, commitment_id: int):
    try:
        return get_fact(chat_id, f"last_nudge_at:{commitment_id}")
    except Exception:
        return None

def set_last_nudge_at(chat_id: int, commitment_id: int, iso_ts: str):
    try:
        upsert_fact(chat_id, f"last_nudge_at:{commitment_id}", iso_ts)
    except Exception:
        pass

def get_last_surface_commitment_id(chat_id: int):
    try:
        v = get_fact(chat_id, "last_surface_commitment_id")
        return int(v) if v else None
    except Exception:
        return None

def set_last_surface_commitment_id(chat_id: int, commitment_id: int):
    try:
        upsert_fact(chat_id, "last_surface_commitment_id", str(commitment_id))
    except Exception:
        pass    

# ==========================================================
# COMPATIBILITY LAYER — keep old bot.py alive
# ==========================================================


# ---- NOTES ------------------------------------------------

def add_note(chat_id: int, text: str):
    return None

def get_notes(chat_id: int):
    return []

def search_notes(chat_id: int, query: str):
    return []


# ---- DAILY LOGS -------------------------------------------

def upsert_daily_log(chat_id: int, text: str):
    return None

def get_daily_logs(chat_id: int):
    return []

def search_daily_logs(chat_id: int, query: str):
    return []


# ---- REMINDER EXTENSIONS ---------------------------------

def claim_due_reminders(limit: int = 10):
    return fetch_due_reminders(limit)

def claim_reminder(reminder_id: int) -> bool:
    """
    Atomically claim a pending reminder so only one runner instance sends it.
    Returns True if claimed, False otherwise.
    """
    audit_chat_id = None
    changed = False

    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT chat_id, status FROM reminders WHERE id=?",
            (reminder_id,),
        )
        row = cur.fetchone()
        if row:
            audit_chat_id = int(row[0])

        cur.execute(
            """
            UPDATE reminders
            SET status='sending'
            WHERE id=?
              AND status='pending'
              AND sent_at IS NULL
              AND COALESCE(entity_type, 'reminder')='reminder'
            """,
            (reminder_id,),
        )
        changed = (cur.rowcount == 1)

        conn.commit()
        conn.close()

    if changed and audit_chat_id is not None:
        log_reminder_state_change(
            chat_id=audit_chat_id,
            rid=reminder_id,
            old_state="pending",
            new_state="sending",
            source="claim_reminder",
        )

    return changed
    

def revert_reminder_pending(reminder_id: int):
    audit_chat_id = None
    audit_old_state = None
    changed = False

    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT chat_id, status FROM reminders WHERE id=?",
            (reminder_id,),
        )
        row = cur.fetchone()
        if row:
            audit_chat_id = int(row[0])
            audit_old_state = (row[1] or "").strip().lower()

        cur.execute(
            "UPDATE reminders SET status='pending', sent_at=NULL WHERE id=?",
            (reminder_id,),
        )
        changed = (cur.rowcount == 1)

        conn.commit()
        conn.close()

    if changed and audit_chat_id is not None:
        log_reminder_state_change(
            chat_id=audit_chat_id,
            rid=reminder_id,
            old_state=audit_old_state or "sending",
            new_state="pending",
            source="revert_reminder_pending",
        )

# ==========================================================
# MISSING EXPORT SHIMS — bot.py expects these names
# ==========================================================

def get_fact(chat_id: int, fact_key: str):
    rows = get_facts(chat_id=chat_id, limit=500)
    for row in rows:
        try:
            if row.get("fact_key") == fact_key:
                return row.get("fact_value")
        except Exception:
            pass
    return None


def upsert_fact(chat_id: int, fact_key: str, fact_value: str):
    return save_fact(chat_id, fact_key, fact_value)


def get_all_facts(chat_id: int):
    rows = get_facts(chat_id=chat_id, limit=500)
    out = {}
    for row in rows:
        try:
            k = row.get("fact_key")
            v = row.get("fact_value")
            if k:
                out[k] = v
        except Exception:
            pass
    return out

# --- Compat alias (tests + older callers) ---
def get_recent_messages(chat_id: int, limit: int = 30):
    return fetch_recent_messages(chat_id=chat_id, limit=limit)

# =========================
# OPS HELPERS (Reminders)
# =========================

def reminder_stats() -> Dict[str, int]:
    """
    Counts reminder states using the SQLCipher-backed connection.
    """
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
          COUNT(*) AS total,
          SUM(CASE WHEN status='pending' AND sent_at IS NULL THEN 1 ELSE 0 END) AS pending,
          SUM(CASE WHEN status='pending' AND sent_at IS NULL AND due_at_utc <= datetime('now') THEN 1 ELSE 0 END) AS due_now,
          SUM(CASE WHEN status='sending' THEN 1 ELSE 0 END) AS sending,
          SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) AS sent
        FROM reminders
        """
    )
    row = cur.fetchone()

    def _get(idx: int, key: str) -> int:
        try:
            if hasattr(row, "get"):
                return int(row.get(key) or 0)
            return int(row[idx] or 0)
        except Exception:
            return 0

    return {
        "total": _get(0, "total"),
        "pending": _get(1, "pending"),
        "due_now": _get(2, "due_now"),
        "sending": _get(3, "sending"),
        "sent": _get(4, "sent"),
    }


def list_reminders(
    statuses: Optional[List[str]] = None,
    limit: int = 25,
    chat_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    List reminders filtered by statuses (default pending+sending).
    If chat_id is provided, only return reminders for that chat_id.
    """
    if statuses is None:
        statuses = ["pending", "sending"]
    limit = max(1, min(100, int(limit or 25)))

    conn = _get_conn()
    cur = conn.cursor()

    placeholders = ",".join(["?"] * len(statuses))

    where_chat = ""
    params = [*statuses]
    if chat_id is not None:
        where_chat = " AND chat_id = ?"
        params.append(int(chat_id))

    sql = f"""
      SELECT id, chat_id, due_at_utc, status, created_at, sent_at, channel, target, text
      FROM reminders
      WHERE status IN ({placeholders}){where_chat}
      ORDER BY due_at_utc ASC
      LIMIT ?
    """
    params.append(limit)

    cur.execute(sql, params)
    rows = cur.fetchall() or []

    out: List[Dict[str, Any]] = []
    for r in rows:
        if hasattr(r, "keys"):
            out.append({k: r[k] for k in r.keys()})
        else:
            out.append(
                {
                    "id": r[0],
                    "chat_id": r[1],
                    "due_at_utc": r[2],
                    "status": r[3],
                    "created_at": r[4],
                    "sent_at": r[5],
                    "channel": r[6],
                    "target": r[7],
                    "text": r[8],
                }
            )
    return out

def watchdog_reset_stuck_reminders(max_age_seconds: int = 300) -> int:
    """
    Reset reminders stuck in 'sending' state.

    If a reminder has been 'sending' longer than max_age_seconds,
    it is assumed the worker crashed and the reminder should be retried.
    """

    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)

    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE reminders
        SET status='pending'
        WHERE status='sending'
        AND created_at < ?
        """,
        (cutoff.strftime("%Y-%m-%d %H:%M:%S"),)
    )

    reset_count = cur.rowcount

    conn.commit()
    conn.close()

    return reset_count    

def fetch_timeline_between(
    chat_id: int,
    start_utc: str,
    end_utc: str,
    entity_types: list[str] | None = None,
    statuses: list[str] | None = None,
) -> list[dict]:
    """
    Unified timeline read from reminders table.
    Temporary MVP base for reminders + tasks.
    """
    if entity_types is None:
        entity_types = ["reminder", "task"]
    if statuses is None:
        statuses = ["pending", "sending"]

    entity_types = [str(x).strip() for x in entity_types if str(x).strip()]
    statuses = [str(x).strip() for x in statuses if str(x).strip()]
    if not entity_types or not statuses:
        return []

    et_placeholders = ",".join("?" for _ in entity_types)
    st_placeholders = ",".join("?" for _ in statuses)

    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT
              id,
              chat_id,
              due_at_utc,
              status,
              created_at,
              sent_at,
              channel,
              target,
              text,
              COALESCE(entity_type, 'reminder') AS entity_type,
              parent_ref
            FROM reminders
            WHERE chat_id = ?
              AND due_at_utc >= ?
              AND due_at_utc <= ?
              AND COALESCE(entity_type, 'reminder') IN ({et_placeholders})
              AND status IN ({st_placeholders})
            ORDER BY due_at_utc ASC, id ASC
            """,
            [int(chat_id), str(start_utc), str(end_utc), *entity_types, *statuses],
        )
        rows = cur.fetchall() or []
        conn.close()

    out = []
    for r in rows:
        if isinstance(r, dict):
            out.append(dict(r))
        else:
            out.append(
                {
                    "id": r[0],
                    "chat_id": r[1],
                    "due_at_utc": r[2],
                    "status": r[3],
                    "created_at": r[4],
                    "sent_at": r[5],
                    "channel": r[6],
                    "target": r[7],
                    "text": r[8],
                    "entity_type": r[9],
                    "parent_ref": r[10],
                }
            )
    return out

def fetch_timeline_for_parent(
    chat_id: int,
    parent_ref: str,
    entity_types: list[str] | None = None,
    statuses: list[str] | None = None,
    limit: int = 50,
) -> list[dict]:
    """
    Unified timeline read for a linked entity via parent_ref.
    Temporary MVP base for reminders + tasks.
    """
    if entity_types is None:
        entity_types = ["reminder", "task"]
    if statuses is None:
        statuses = ["pending", "sending"]

    parent_ref = (parent_ref or "").strip()
    if not parent_ref:
        return []

    entity_types = [str(x).strip() for x in entity_types if str(x).strip()]
    statuses = [str(x).strip() for x in statuses if str(x).strip()]
    if not entity_types or not statuses:
        return []

    et_placeholders = ",".join("?" for _ in entity_types)
    st_placeholders = ",".join("?" for _ in statuses)

    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT
              id,
              chat_id,
              due_at_utc,
              status,
              created_at,
              sent_at,
              channel,
              target,
              text,
              COALESCE(entity_type, 'reminder') AS entity_type,
              parent_ref
            FROM reminders
            WHERE chat_id = ?
              AND parent_ref = ?
              AND COALESCE(entity_type, 'reminder') IN ({et_placeholders})
              AND status IN ({st_placeholders})
            ORDER BY due_at_utc ASC, id ASC
            LIMIT ?
            """,
            [int(chat_id), parent_ref, *entity_types, *statuses, int(limit)],
        )
        rows = cur.fetchall() or []
        conn.close()

    out = []
    for r in rows:
        if isinstance(r, dict):
            out.append(dict(r))
        else:
            out.append(
                {
                    "id": r[0],
                    "chat_id": r[1],
                    "due_at_utc": r[2],
                    "status": r[3],
                    "created_at": r[4],
                    "sent_at": r[5],
                    "channel": r[6],
                    "target": r[7],
                    "text": r[8],
                    "entity_type": r[9],
                    "parent_ref": r[10],
                }
            )
    return out

def list_reminders_for_chat(chat_id: int, statuses: Optional[List[str]] = None, limit: int = 25) -> List[Dict[str, Any]]:
    """
    List reminders for a single chat_id filtered by statuses (default pending+sending).
    This is what user-facing commands should use.
    """
    if statuses is None:
        statuses = ["pending", "sending"]
    limit = max(1, min(100, int(limit or 25)))

    conn = _get_conn()
    cur = conn.cursor()

    placeholders = ",".join(["?"] * len(statuses))
    sql = f"""
      SELECT id, chat_id, due_at_utc, status, created_at, sent_at, channel, target, text
      FROM reminders
      WHERE chat_id = ?
        AND status IN ({placeholders})
      ORDER BY due_at_utc ASC
      LIMIT ?
    """
    cur.execute(sql, [int(chat_id), *statuses, limit])
    rows = cur.fetchall() or []

    out: List[Dict[str, Any]] = []
    for r in rows:
        if hasattr(r, "keys"):
            out.append({k: r[k] for k in r.keys()})
        else:
            out.append(
                {
                    "id": r[0],
                    "chat_id": r[1],
                    "due_at_utc": r[2],
                    "status": r[3],
                    "created_at": r[4],
                    "sent_at": r[5],
                    "channel": r[6],
                    "target": r[7],
                    "text": r[8],
                }
            )
    return out

def cancel_reminder(chat_id: int, rid: int) -> bool:
    """
    Cancel a reminder by id, only if it belongs to chat_id
    and is currently pending or sending.
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT status
            FROM reminders
            WHERE id = ? AND chat_id = ?
            """,
            (int(rid), int(chat_id)),
        )
        row = cur.fetchone()
        if not row:
            return False

        old_state = (row[0] or "").lower().strip()
        if old_state not in ("pending", "sending"):
            return False

        cur.execute(
            """
            UPDATE reminders
            SET status = 'cancelled'
            WHERE id = ? AND chat_id = ?
            """,
            (int(rid), int(chat_id)),
        )
        changed = (cur.rowcount == 1)
        conn.commit()

        if changed:
            log_reminder_state_change(
                chat_id=int(chat_id),
                rid=int(rid),
                old_state=old_state,
                new_state="cancelled",
                source="cancel_reminder",
            )

        return changed

    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass

# =========================
# CHAT PREFS (Voice mode)
# =========================
def get_chat_voice_enabled(chat_id: int) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT voice_enabled FROM chat_prefs WHERE chat_id = ?", (int(chat_id),))
        row = cur.fetchone()
        if row is None:
            return False
        v = row[0] if not hasattr(row, "get") else row.get("voice_enabled")
        return bool(int(v or 0))
    except Exception:
        return False


def set_chat_voice_enabled(chat_id: int, enabled: bool) -> None:
    """Set per-chat voice mode.
    Uses INSERT OR IGNORE + UPDATE (works on older SQLite/SQLCipher builds).
    """
    conn = _get_conn()
    cur = conn.cursor()
    cid = int(chat_id)
    val = 1 if enabled else 0
    # Ensure row exists
    cur.execute(
        "INSERT OR IGNORE INTO chat_prefs (chat_id, voice_enabled, updated_at) VALUES (?, ?, datetime('now'))",
        (cid, val),
    )
    # Always update (covers existing + newly inserted)
    cur.execute(
        "UPDATE chat_prefs SET voice_enabled = ?, updated_at = datetime('now') WHERE chat_id = ?",
        (val, cid),
    )
    conn.commit()


# =========================
# CASE NOTES + ACTIVE CASE (Phase B0)
# =========================
def get_active_case_id(chat_id: int) -> str:
    """
    Returns active case_id for this chat (expediente), or "" if none.
    Stored in chat_prefs.active_case_id
    """
    try:
        with _lock:
            conn = _get_conn()
            cur = conn.cursor()
            # Column should exist (you already added it)
            cur.execute("SELECT active_case_id FROM chat_prefs WHERE chat_id=?", (int(chat_id),))
            row = cur.fetchone()
            conn.close()
        if not row:
            return ""
        val = row[0] if not isinstance(row, dict) else row.get("active_case_id")
        return (val or "").strip()
    except Exception:
        return ""


def set_active_case_id(chat_id: int, case_id: str) -> None:
    """
    Upserts active_case_id for this chat.
    """
    case_id = (case_id or "").strip()
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        # Ensure row exists
        cur.execute("INSERT OR IGNORE INTO chat_prefs(chat_id) VALUES(?)", (int(chat_id),))
        cur.execute(
            "UPDATE chat_prefs SET active_case_id=?, updated_at=datetime('now') WHERE chat_id=?",
            (case_id, int(chat_id)),
        )
        conn.commit()
        conn.close()

def insert_case_event(
    chat_id: int,
    case_id: int,
    event_text: str,
    term_days: int | None = None,
    start_date: str | None = None,
    deadline_date: str | None = None,
    raw_text: str | None = None,
    principal_id: str | None = None,
) -> int:
    """
    Insert a case event in a schema-compatible way across legacy deployments.
    Returns case_events.id
    """
    txt = (event_text or "").strip()
    if not txt:
        raise ValueError("insert_case_event: event_text required")

    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        # Ensure table exists (init_db should do this, but keep helper self-safe)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS case_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            case_id INTEGER NOT NULL,
            event_text TEXT,
            description TEXT,
            term_days INTEGER,
            start_date TEXT,
            deadline_date TEXT,
            raw_text TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            principal_id TEXT,
            FOREIGN KEY(case_id) REFERENCES cases(id)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS watchdog_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_key TEXT NOT NULL UNIQUE,
            alert_type TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            chat_id INTEGER PRIMARY KEY,
            proactive_mode TEXT NOT NULL DEFAULT 'tactical'
        );
        """)

        cols = set()
        cur.execute("PRAGMA table_info(case_events)")
        for r in cur.fetchall() or []:
            cols.add(r[1] if not hasattr(r, "keys") else r["name"])

        has_desc = "description" in cols
        has_event_text = "event_text" in cols
        has_chat = "chat_id" in cols
        has_principal = "principal_id" in cols

        # Idempotency guard: if same logical event already exists, return it
        if has_chat and has_event_text and "deadline_date" in cols:
            cur.execute(
                """
                SELECT id
                FROM case_events
                WHERE chat_id = ?
                  AND case_id = ?
                  AND COALESCE(event_text, '') = ?
                  AND COALESCE(deadline_date, '') = COALESCE(?, '')
                ORDER BY id DESC
                LIMIT 1
                """,
                (int(chat_id), int(case_id), txt, deadline_date),
            )
            existing = cur.fetchone()
            if existing:
                conn.close()
                return int(existing["id"] if hasattr(existing, "keys") else existing[0])    

        if has_chat and has_event_text and has_desc and has_principal:
            cur.execute("""
            INSERT INTO case_events(chat_id, case_id, event_text, description, term_days, start_date, deadline_date, raw_text, principal_id)
            VALUES(?,?,?,?,?,?,?,?,?)
            """, (chat_id, case_id, txt, txt, term_days, start_date, deadline_date, raw_text, principal_id))
        elif has_chat and has_event_text and has_principal:
            cur.execute("""
            INSERT INTO case_events(chat_id, case_id, event_text, term_days, start_date, deadline_date, raw_text, principal_id)
            VALUES(?,?,?,?,?,?,?,?)
            """, (chat_id, case_id, txt, term_days, start_date, deadline_date, raw_text, principal_id))
        elif has_chat and has_event_text:
            cur.execute("""
            INSERT INTO case_events(chat_id, case_id, event_text, term_days, start_date, deadline_date, raw_text)
            VALUES(?,?,?,?,?,?,?)
            """, (chat_id, case_id, txt, term_days, start_date, deadline_date, raw_text))
        elif has_desc and has_chat:
            cur.execute("""
            INSERT INTO case_events(chat_id, case_id, description, term_days, start_date, deadline_date)
            VALUES(?,?,?,?,?,?)
            """, (chat_id, case_id, txt, term_days, start_date, deadline_date))
        else:
            cur.execute("""
            INSERT INTO case_events(case_id, description, created_at)
            VALUES(?, ?, datetime('now'))
            """, (case_id, txt))

        eid = cur.lastrowid
        conn.commit()
        conn.close()
        return int(eid)

def get_proactive_mode(chat_id: int) -> str:
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT proactive_mode FROM user_settings WHERE chat_id=?",
        (chat_id,),
    )
    row = cur.fetchone()
    conn.close()

    if row:
        return row[0] if not hasattr(row, "keys") else row["proactive_mode"]

    return "tactical"


def set_proactive_mode(chat_id: int, mode: str):
    conn = _get_conn()
    cur = conn.cursor()

    # ensure table exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            chat_id INTEGER PRIMARY KEY,
            proactive_mode TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # SAFE UPSERT (no ON CONFLICT syntax issues)
    cur.execute("""
        SELECT chat_id FROM user_settings WHERE chat_id = ?
    """, (chat_id,))
    row = cur.fetchone()

    if row:
        cur.execute("""
            UPDATE user_settings
            SET proactive_mode = ?, updated_at = datetime('now')
            WHERE chat_id = ?
        """, (mode, chat_id))
    else:
        cur.execute("""
            INSERT INTO user_settings (chat_id, proactive_mode)
            VALUES (?, ?)
        """, (chat_id, mode))

    conn.commit()
    conn.close()

def insert_case_note(
    chat_id: int,
    case_id: str,
    note_text: str,
    source: str = "text",
    telegram_message_id: int | None = None,
) -> int:
    """
    Inserts a case note into case_notes. Idempotent by (chat_id, telegram_message_id).
    Returns row id (existing if duplicate).
    """
    if not case_id:
        raise ValueError("insert_case_note requires case_id")
    note_text = (note_text or "").strip()
    if not note_text:
        raise ValueError("insert_case_note requires note_text")

    parent_ref = f"CASE:{str(case_id).strip()}"

    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        # If we have a Telegram message id, make it idempotent.
        if telegram_message_id is not None:
            cur.execute(
                """
                INSERT OR IGNORE INTO case_notes(chat_id, case_id, parent_ref, note_text, source, telegram_message_id)
                VALUES(?,?,?,?,?,?)
                """,
                (
                    int(chat_id),
                    str(case_id),
                    parent_ref,
                    note_text,
                    str(source or "text"),
                    int(telegram_message_id),
                ),
            )
            conn.commit()

            # Return the existing row id (whether inserted now or already existed)
            cur.execute(
                """
                SELECT id FROM case_notes
                WHERE chat_id=? AND telegram_message_id=?
                ORDER BY id DESC LIMIT 1
                """,
                (int(chat_id), int(telegram_message_id)),
            )
            row = cur.fetchone()
            conn.close()
            return int(row[0]) if row else 0

        # Fallback path (no message id): dedupe within last 60 seconds
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
        if row:
            conn.close()
            return int(row[0]) if not hasattr(row, "keys") else int(row["id"])

        cur.execute(
            """
            INSERT INTO case_notes(chat_id, case_id, parent_ref, note_text, source, telegram_message_id)
            VALUES(?,?,?,?,?,?)
            """,
            (
                int(chat_id),
                str(case_id),
                parent_ref,
                note_text,
                str(source or "text"),
                None,
            ),
        )
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return int(rid)
    
def insert_task(chat_id, case_id, task_text, source="system", priority="normal"):
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO tasks (chat_id, case_id, task_text, source, priority)
        VALUES (?, ?, ?, ?, ?)
        """,
        (int(chat_id), case_id, task_text, source, priority),
    )

    task_id = cur.lastrowid
    conn.commit()
    conn.close()    


def fetch_case_notes(chat_id: int, case_id: str, limit: int = 20) -> list[dict]:
    """
    Fetch recent notes for a case, newest first.
    Uses parent_ref when available, with legacy fallback to case_id.
    """
    case_id = (case_id or "").strip()
    if not case_id:
        return []

    parent_ref = f"CASE:{case_id}"

    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, chat_id, case_id, parent_ref, note_text, source, telegram_message_id, created_at
            FROM case_notes
            WHERE chat_id=?
              AND (parent_ref=? OR case_id=?)
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(chat_id), parent_ref, case_id, int(limit)),
        )
        rows = cur.fetchall() or []
        conn.close()
    return [dict(r) for r in rows]

def get_recent_messages(chat_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Returns the most recent messages for a chat in chronological order.
    Used by bot.py for prompt context assembly.
    """
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT role, content
        FROM messages
        WHERE chat_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (int(chat_id), int(limit)),
    )

    rows = cur.fetchall()
    conn.close()

    # Reverse so oldest → newest for prompt assembly
    rows = list(rows)[::-1]

    return [
        {
            "role": r["role"],
            "content": r["content"],
        }
        for r in rows
    ]

def upsert_case_summary(
    chat_id: int,
    case_id: str,
    summary_text: str,
    last_event_at: str | None = None,
    last_note_at: str | None = None,
    next_deadline: str | None = None,
    open_reminders_count: int = 0,
    summary_version: int = 1,
):
    case_id = (case_id or "").strip()
    if not case_id:
        return

    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE case_summaries
        SET summary_text=?,
            last_event_at=?,
            last_note_at=?,
            next_deadline=?,
            open_reminders_count=?,
            last_summary_refresh=datetime('now'),
            summary_version=?
        WHERE chat_id=? AND case_id=?
        """,
        (
            summary_text,
            last_event_at,
            last_note_at,
            next_deadline,
            int(open_reminders_count),
            int(summary_version),
            int(chat_id),
            case_id,
        ),
    )

    if cur.rowcount == 0:
        cur.execute(
            """
            INSERT INTO case_summaries (
                chat_id, case_id, summary_text,
                last_event_at, last_note_at,
                next_deadline, open_reminders_count,
                last_summary_refresh, summary_version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
            """,
            (
                int(chat_id),
                case_id,
                summary_text,
                last_event_at,
                last_note_at,
                next_deadline,
                int(open_reminders_count),
                int(summary_version),
            ),
        )

    conn.commit()
    conn.close()

def get_case_summary(chat_id: int, case_id: str) -> dict | None:
    case_id = (case_id or "").strip()
    if not case_id:
        return None

    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM case_summaries
        WHERE chat_id=? AND case_id=?
        LIMIT 1
        """,
        (int(chat_id), case_id),
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return dict(row)  

def insert_memory_item(chat_id: int, bucket: str, raw_input: str, summary: str = ""):
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO memory_items (chat_id, bucket, raw_input, summary)
            VALUES (?, ?, ?, ?)
        """, (
            int(chat_id),
            bucket,
            raw_input,
            summary
        ))

        conn.commit()
        conn.close()

def fetch_recent_memory(chat_id: int, limit: int = 5):
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, bucket, raw_input, summary, created_at
            FROM memory_items
            WHERE chat_id=?
            ORDER BY id DESC
            LIMIT ?
        """, (
            int(chat_id),
            int(limit)
        ))

        rows = cur.fetchall()
        conn.close()
        return rows

def classify_memory_item(text: str, source: str = "text") -> tuple[str, str]:
    if not text:
        return ("memory", source)

    low = text.lower().strip()

    sensitive_keywords = (
        "clave",
        "password",
        "contraseña",
        "secret",
        "token",
        "api key",
        "private key",
        "access key",
    )

    if any(k in low for k in sensitive_keywords):
        return ("sensitive", source)

    high_task_markers = (
        "tengo que",
        "debo",
        "hay que",
        "recuérdame",
        "recordarme",
    )

    action_verbs = (
        "llamar",
        "enviar",
        "hacer",
        "comprar",
        "pagar",
        "agendar",
        "programar",
        "escribir",
        "responder",
        "revisar",
        "buscar",
        "hablar",
        "ir",
    )

    medium_task_markers = (
        "debería",
        "deberia",
        "tengo pendiente",
        "no se me puede olvidar",
        "sería bueno",
        "seria bueno",
        "quiero acordarme",
    )

    low_task_markers = (
        "quizá",
        "quizas",
        "quizás",
        "tal vez",
        "a lo mejor",
        "puede que",
        "podría",
        "podria",
        "me gustaría",
        "me gustaria",
    )

    if any(m in low for m in high_task_markers) and any(v in low for v in action_verbs):
        return ("task", "task_high")

    if any(m in low for m in high_task_markers):
        return ("task", "task_high")

    if any(m in low for m in medium_task_markers) and any(v in low for v in action_verbs):
        return ("task", "task_medium")

    if any(m in low for m in medium_task_markers):
        return ("task", "task_medium")

    if any(m in low for m in low_task_markers) and any(v in low for v in action_verbs):
        return ("task", "task_low")

    return ("memory", source)

def search_memory(chat_id: int, keyword: str, limit: int = 5, include_sensitive: bool = False):
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        if include_sensitive:
            cur.execute("""
                SELECT id, bucket, raw_input, summary, created_at
                FROM memory_items
                WHERE chat_id=?
                  AND raw_input LIKE ?
                ORDER BY id DESC
                LIMIT ?
            """, (
                int(chat_id),
                f"%{keyword}%",
                int(limit)
            ))
        else:
            cur.execute("""
                SELECT id, bucket, raw_input, summary, created_at
                FROM memory_items
                WHERE chat_id=?
                  AND raw_input LIKE ?
                  AND bucket != 'sensitive'
                ORDER BY id DESC
                LIMIT ?
            """, (
                int(chat_id),
                f"%{keyword}%",
                int(limit)
            ))

        rows = cur.fetchall()
        conn.close()
        return rows

def upsert_commitment(
    chat_id: int,
    raw_input: str,
    action: str = "",
    target: str = "",
    due_date: str | None = None,
    confidence: str = "medium",
):
    def _norm(s: str) -> str:
        s = (s or "").strip().lower()
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = re.sub(r"[^\w\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        norm_input = _norm(raw_input)
        norm_target = _norm(target)

        cur.execute("""
            SELECT id, raw_input, action, target, due_date
            FROM commitments
            WHERE chat_id=?
              AND status='open'
            ORDER BY id DESC
            LIMIT 20
        """, (int(chat_id),))

        rows = cur.fetchall()

        for r in rows:
            row = dict(r) if hasattr(r, "keys") else {
                "id": r[0],
                "raw_input": r[1],
                "action": r[2],
                "target": r[3],
                "due_date": r[4],
            }

            existing_norm = _norm(row["raw_input"])
            existing_target = _norm(row["target"])

            same_text = existing_norm == norm_input
            same_action_target = (
                action and row["action"] == action and
                norm_target and existing_target == norm_target
            )

            if same_text or same_action_target:
                cur.execute("""
                    UPDATE commitments
                    SET due_date = COALESCE(?, due_date),
                        confidence = ?
                    WHERE id = ?
                """, (
                    due_date,
                    confidence,
                    int(row["id"]),
                ))

                conn.commit()
                conn.close()
                return int(row["id"])

        cur.execute("""
            INSERT INTO commitments (chat_id, raw_input, action, target, due_date, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            int(chat_id),
            raw_input,
            action,
            target,
            due_date,
            confidence,
        ))

        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return int(rid)


def fetch_due_commitments(limit: int = 20):
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, chat_id, raw_input, action, target, due_date, confidence, status, last_nudged_at, created_at
            FROM commitments
            WHERE status='open'
              AND due_date IS NOT NULL
              AND datetime(substr(due_date, 1, 19)) <= CURRENT_TIMESTAMP
            ORDER BY datetime(substr(due_date, 1, 19)) ASC, id ASC
            LIMIT ?
        """, (int(limit),))

        rows = cur.fetchall()
        conn.close()
        return rows


def mark_commitment_nudged(commitment_id: int):
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute("""
            UPDATE commitments
            SET last_nudged_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (int(commitment_id),))

        conn.commit()
        conn.close()

def close_matching_commitment(chat_id: int, text: str):
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        low = (text or "").lower()

        action = None
        if "llam" in low:
            action = "llamar"
        elif "escrib" in low:
            action = "escribir"
        elif "habl" in low:
            action = "hablar"
        elif "envi" in low:
            action = "enviar"
        elif "revis" in low:
            action = "revisar"
        elif "pag" in low:
            action = "pagar"

        target = None
        import re
        m = re.search(r"\b(?:a|con)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ]+)\b", text or "")
        if m:
            target = (m.group(1) or "").strip()

        if action and target:
            cur.execute("""
                SELECT id, raw_input, action, target, due_date, confidence, status
                FROM commitments
                WHERE chat_id=?
                  AND status='open'
                  AND action=?
                  AND target=?
                ORDER BY id DESC
                LIMIT 1
            """, (
                int(chat_id),
                action,
                target,
            ))
        elif action:
            cur.execute("""
                SELECT id, raw_input, action, target, due_date, confidence, status
                FROM commitments
                WHERE chat_id=?
                  AND status='open'
                  AND action=?
                ORDER BY id DESC
                LIMIT 1
            """, (
                int(chat_id),
                action,
            ))
        else:
            conn.close()
            return None

        row = cur.fetchone()
        if not row:
            conn.close()
            return None

        commitment_id = row["id"] if hasattr(row, "keys") else row[0]

        cur.execute("""
            UPDATE commitments
            SET status='done',
                completed_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (int(commitment_id),))

        conn.commit()
        conn.close()

        return row
    
def count_memory_hits(chat_id: int, keyword: str, limit: int = 50) -> int:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT id
                FROM memory_items
                WHERE chat_id=?
                  AND bucket != 'sensitive'
                  AND raw_input LIKE ?
                ORDER BY id DESC
                LIMIT ?
            )
        """, (
            int(chat_id),
            f"%{keyword}%",
            int(limit),
        ))

        row = cur.fetchone()
        conn.close()

        if not row:
            return 0

        return int(row[0] if not hasattr(row, "keys") else list(row)[0])

def fetch_open_commitments(chat_id: int, limit: int = 10):
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, raw_input, action, target, due_date, confidence, status, last_nudged_at, created_at
            FROM commitments
            WHERE chat_id=?
              AND status='open'
            ORDER BY id DESC
            LIMIT ?
        """, (
            int(chat_id),
            int(limit),
        ))

        rows = cur.fetchall()
        conn.close()
        return rows


def fetch_recent_memory_by_bucket(chat_id: int, bucket: str = "memory", limit: int = 10):
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, bucket, raw_input, summary, created_at
            FROM memory_items
            WHERE chat_id=?
              AND bucket=?
            ORDER BY id DESC
            LIMIT ?
        """, (
            int(chat_id),
            bucket,
            int(limit),
        ))

        rows = cur.fetchall()
        conn.close()
        return rows  

def fetch_completed_commitments_for_target(chat_id: int, target: str, action: str = "", limit: int = 20):
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        if action:
            cur.execute("""
                SELECT id, raw_input, action, target, due_date, confidence, status, completed_at, created_at
                FROM commitments
                WHERE chat_id=?
                  AND status='done'
                  AND target=?
                  AND action=?
                  AND completed_at IS NOT NULL
                ORDER BY id DESC
                LIMIT ?
            """, (
                int(chat_id),
                target,
                action,
                int(limit),
            ))
        else:
            cur.execute("""
                SELECT id, raw_input, action, target, due_date, confidence, status, completed_at, created_at
                FROM commitments
                WHERE chat_id=?
                  AND status='done'
                  AND target=?
                  AND completed_at IS NOT NULL
                ORDER BY id DESC
                LIMIT ?
            """, (
                int(chat_id),
                target,
                int(limit),
            ))

        rows = cur.fetchall()
        conn.close()
        return rows


def infer_simple_time_pattern(chat_id: int, target: str, action: str = "", limit: int = 20) -> str:
    from datetime import datetime

    rows = fetch_completed_commitments_for_target(chat_id, target, action=action, limit=limit)
    if not rows or len(rows) < 2:
        return ""

    buckets = {"midday": 0, "night": 0, "other": 0}

    for r in rows:
        row = dict(r) if hasattr(r, "keys") else r
        completed_at = row["completed_at"] if isinstance(row, dict) else row[7]

        if not completed_at:
            continue

        try:
            dt = datetime.fromisoformat(str(completed_at).replace("Z", "+00:00"))
            hour = dt.hour
        except Exception:
            try:
                hour = int(str(completed_at)[11:13])
            except Exception:
                continue

        if 11 <= hour <= 14:
            buckets["midday"] += 1
        elif 18 <= hour or hour <= 2:
            buckets["night"] += 1
        else:
            buckets["other"] += 1

    best = max(buckets, key=buckets.get)
    if buckets[best] < 2:
        return ""

    return best      

def infer_time_windows(chat_id: int, target: str, action: str = "", limit: int = 20) -> dict:
    from datetime import datetime

    rows = fetch_completed_commitments_for_target(chat_id, target, action=action, limit=limit)

    result = {
        "midday_count": 0,
        "night_count": 0,
        "other_count": 0,
        "has_midday": False,
        "has_night": False,
    }

    if not rows:
        return result

    for r in rows:
        row = dict(r) if hasattr(r, "keys") else r
        completed_at = row["completed_at"] if isinstance(row, dict) else row[7]

        if not completed_at:
            continue

        try:
            dt = datetime.fromisoformat(str(completed_at).replace("Z", "+00:00"))
            hour = dt.hour
        except Exception:
            try:
                hour = int(str(completed_at)[11:13])
            except Exception:
                continue

        if 11 <= hour <= 14:
            result["midday_count"] += 1
        elif 18 <= hour or hour <= 2:
            result["night_count"] += 1
        else:
            result["other_count"] += 1

    result["has_midday"] = result["midday_count"] >= 2
    result["has_night"] = result["night_count"] >= 2

    return result    

def build_context_snapshot(chat_id: int, limit: int = 5) -> dict:
    conn = _get_conn()
    cur = conn.cursor()

    # Open commitments
    cur.execute("""
        SELECT action, target, due_date
        FROM commitments
        WHERE chat_id=? AND status='open'
        ORDER BY due_date ASC
        LIMIT ?
    """, (int(chat_id), limit))
    commitments = cur.fetchall() or []

    # Recent memory signals (dedup + filter)
    cur.execute("""
        SELECT raw_input
        FROM memory_items
        WHERE chat_id=?
          AND raw_input NOT LIKE 'cd %'
          AND raw_input NOT LIKE 'source %'
          AND raw_input NOT LIKE 'python3 %'
        ORDER BY id DESC
        LIMIT ?
    """, (int(chat_id), limit))

    raw_signals = cur.fetchall() or []

    seen = set()
    signals = []

    for r in raw_signals:
        text = r["raw_input"] if hasattr(r, "keys") else r[0]

        if text not in seen:
            signals.append(r)
            seen.add(text)

    conn.close()

    return {
        "commitments": commitments,
        "signals": signals,
    }