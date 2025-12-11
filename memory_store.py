import os
import sqlite3
import threading
import time
from typing import Optional, List, Dict

# Where the DB lives (can override with VAL0_DB_PATH env var later)
DB_PATH = os.getenv("VAL0_DB_PATH", os.path.join(os.path.dirname(__file__), "val0_memory.db"))
_LOCK = threading.Lock()


def _get_connection() -> sqlite3.Connection:
    """Create a new SQLite connection with WAL mode enabled."""
    conn = sqlite3.connect(DB_PATH, timeout=5, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the messages table if it does not exist."""
    with _LOCK:
        conn = _get_connection()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    telegram_message_id INTEGER,
                    model_used TEXT
                )
                """
            )
            conn.commit()
        finally:
            conn.close()


def save_message(
    chat_id: int,
    role: str,
    content: str,
    telegram_message_id: Optional[int] = None,
    model_used: Optional[str] = None,
) -> int:
    """Insert a message row and return its ID."""
    ts = time.time()
    with _LOCK:
        conn = _get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO messages (
                    chat_id, role, content, created_at, telegram_message_id, model_used
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (chat_id, role, content, ts, telegram_message_id, model_used),
            )
            conn.commit()
            return int(cur.lastrowid)
        finally:
            conn.close()


def get_recent_messages(chat_id: int, limit: int = 20) -> List[Dict]:
    """Return the last N messages for a given chat, oldest first."""
    with _LOCK:
        conn = _get_connection()
        try:
            cur = conn.execute(
                """
                SELECT
                    id,
                    chat_id,
                    role,
                    content,
                    created_at,
                    telegram_message_id,
                    model_used
                FROM messages
                WHERE chat_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (chat_id, limit),
            )
            rows = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    # reverse so caller gets oldest → newest
    rows.reverse()
    return rows
