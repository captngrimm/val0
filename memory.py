import sqlite3
import threading
from typing import Optional, List, Tuple
import time

# Thread-safe global lock
_db_lock = threading.Lock()

DB_PATH = "/opt/val0/val0_memory.db"


def init_db() -> None:
    """Initialize SQLite database with WAL mode and messages table."""
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                model_used TEXT,
                telegram_message_id TEXT,
                created_at REAL NOT NULL
            );
        """)
        conn.commit()
        conn.close()


def save_message(
    chat_id: str,
    role: str,
    content: str,
    model_used: Optional[str] = None,
    telegram_message_id: Optional[str] = None
) -> None:
    """Store a message in SQLite."""
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT INTO messages (chat_id, role, content, model_used, telegram_message_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (chat_id, role, content, model_used, telegram_message_id, time.time()))
        conn.commit()
        conn.close()


def get_recent_messages(chat_id: str, limit: int = 6) -> List[Tuple[str, str]]:
    """
    Return last N messages for context reconstruction.
    Output format: [(role, content), ...]
    """
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("""
            SELECT role, content
            FROM messages
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT ?;
        """, (chat_id, limit)).fetchall()
        conn.close()

    # Return chronological order
    return rows[::-1]
