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
        cur.execute("CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(status, due_at_utc);")

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

def claim_reminder(reminder_id: int):
    return None

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
