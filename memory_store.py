import os
import threading
import logging
from typing import List, Dict, Optional, Any, Tuple

logger = logging.getLogger("val0-memory")

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
    Compatible with both sqlite3 and SQLCipher.
    """
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        # messages
        cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_id INTEGER,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at_utc TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at_utc);")

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


def insert_message(chat_id: int, user_id: Optional[int], role: str, content: str) -> None:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages(chat_id, user_id, role, content) VALUES(?,?,?,?)",
            (chat_id, user_id, role, content),
        )
        conn.commit()
        conn.close()


def fetch_recent_messages(chat_id: int, limit: int = 30) -> List[Dict[str, Any]]:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, chat_id, user_id, role, content, created_at_utc "
            "FROM messages WHERE chat_id=? ORDER BY id DESC LIMIT ?",
            (chat_id, limit),
        )
        rows = cur.fetchall()
        conn.close()
    return [dict(r) for r in reversed(rows)]


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
