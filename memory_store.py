import os
import threading
import logging
from typing import List, Dict, Optional, Any

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


# bot.py expects this name

def insert_reminder(chat_id: int, due_at_utc: str, text: str, status: str = "pending") -> int:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO reminders(chat_id, due_at_utc, text, status) VALUES(?,?,?,?)",
            (chat_id, due_at_utc, text, status),
        )
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return rid

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

def fetch_due_reminders(limit: int = 10) -> List[Dict[str, Any]]:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, chat_id, due_at_utc, text, status, sent_at "
            "FROM reminders "
            "WHERE status='pending' AND due_at_utc <= datetime('now') "
            "ORDER BY due_at_utc ASC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
    return [dict(r) for r in rows]


def mark_reminder_sent(reminder_id: int) -> None:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE reminders SET status='sent', sent_at=datetime('now') WHERE id=?",
            (reminder_id,),
        )
        conn.commit()
        conn.close()


def mark_reminder_failed(reminder_id: int, reason: str = "failed") -> None:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE reminders SET status='failed', sent_at=datetime('now') WHERE id=?",
            (reminder_id,),
        )
        conn.commit()
        conn.close()

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


def upsert_fact(chat_id: int, fact_key: str, fact_value: str,
                source: str = "auto", confidence: float = 1.0) -> None:
    """
    bot.py expects this.
    Stores durable user facts (lightweight "infinite memory" seed).
    """
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        _ensure_user_facts_table(cur)

        cur.execute("""
        INSERT INTO user_facts (chat_id, fact_key, fact_value, source, confidence, updated_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(chat_id, fact_key) DO UPDATE SET
            fact_value=excluded.fact_value,
            source=excluded.source,
            confidence=excluded.confidence,
            updated_at=datetime('now');
        """, (chat_id, fact_key, fact_value, source, confidence))

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

# ==========================================================
# COMPATIBILITY LAYER — keep old bot.py alive
# ==========================================================


# ---- FACTS ------------------------------------------------

def upsert_fact(chat_id: int, key: str, value: str):
    return None  # temporary stub

def get_fact(chat_id: int, key: str):
    return None

def get_all_facts(chat_id: int):
    return []


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
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE reminders
            SET status='sending'
            WHERE id=?
              AND status='pending'
              AND sent_at IS NULL
            """,
            (reminder_id,),
        )
        conn.commit()
        return cur.rowcount == 1
    

def revert_reminder_pending(reminder_id: int):
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE reminders SET status='pending', sent_at=NULL WHERE id=?",
            (reminder_id,),
        )
        conn.commit()
        conn.close()

# ==========================================================
# MISSING EXPORT SHIMS — bot.py expects these names
# ==========================================================

def get_fact(chat_id: int, fact_key: str):
    # If your real function is named differently, swap it here.
    return fetch_fact(chat_id, fact_key) if "fetch_fact" in globals() else None

def upsert_fact(chat_id: int, fact_key: str, fact_value: str):
    return save_fact(chat_id, fact_key, fact_value) if "save_fact" in globals() else None

def get_all_facts(chat_id: int):
    return fetch_all_facts(chat_id) if "fetch_all_facts" in globals() else []

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


def list_reminders(statuses: Optional[List[str]] = None, limit: int = 25) -> List[Dict[str, Any]]:
    """
    List reminders filtered by statuses (default pending+sending).
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
      WHERE status IN ({placeholders})
      ORDER BY due_at_utc ASC
      LIMIT ?
    """
    cur.execute(sql, [*statuses, limit])
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


def insert_case_note(
    chat_id: int,
    case_id: str,
    note_text: str,
    source: str = "text",
    telegram_message_id: int | None = None,
) -> int:
    """
    Inserts a case note into case_notes. Returns new row id.
    case_notes columns: id, chat_id, case_id, note_text, source, telegram_message_id, created_at
    """
    case_id = (case_id or "").strip()
    note_text = (note_text or "").strip()
    source = (source or "").strip() or "text"
    if not case_id or not note_text:
        return 0

    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO case_notes(chat_id, case_id, note_text, source, telegram_message_id) VALUES(?,?,?,?,?)",
            (int(chat_id), case_id, note_text, source, telegram_message_id),
        )
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return int(rid)


def fetch_case_notes(chat_id: int, case_id: str, limit: int = 20) -> list[dict]:
    """
    Fetch recent notes for a case, newest first.
    """
    case_id = (case_id or "").strip()
    if not case_id:
        return []
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, chat_id, case_id, note_text, source, telegram_message_id, created_at "
            "FROM case_notes WHERE chat_id=? AND case_id=? ORDER BY id DESC LIMIT ?",
            (int(chat_id), case_id, int(limit)),
        )
        rows = cur.fetchall() or []
        conn.close()
    return [dict(r) for r in rows]
