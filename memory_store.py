import os
import sqlite3
import threading
import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger("val0-memory")

DB_PATH = os.getenv("VAL0_DB_PATH", "/opt/val0/val0_memory.db")
_lock = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()

            # Messages table: one row per message (user or assistant)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    role TEXT NOT NULL,               -- 'user' or 'assistant'
                    content TEXT NOT NULL,
                    telegram_message_id INTEGER,
                    model_used TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # User facts: structured memory (e.g., favorite_color)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    fact_key TEXT NOT NULL,
                    fact_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, fact_key)
                );
                """
            )

            conn.commit()
            logger.info("SQLite DB initialized at %s", DB_PATH)
        finally:
            conn.close()


def insert_message(
    chat_id: int,
    role: str,
    content: str,
    telegram_message_id: Optional[int] = None,
    model_used: Optional[str] = None,
) -> int:
    """Insert a single message row and return its ID."""
    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO messages (chat_id, role, content, telegram_message_id, model_used)
                VALUES (?, ?, ?, ?, ?)
                """,
                (chat_id, role, content, telegram_message_id, model_used),
            )
            conn.commit()
            msg_id = cur.lastrowid
            logger.debug("Inserted message id=%s chat_id=%s role=%s", msg_id, chat_id, role)
            return msg_id
        finally:
            conn.close()


def get_recent_messages(chat_id: int, limit: int = 12) -> List[Dict[str, Any]]:
    """Return recent messages for this chat_id (oldest → newest)."""
    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, chat_id, role, content, telegram_message_id, model_used, created_at
                FROM messages
                WHERE chat_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (chat_id, limit),
            )
            rows = cur.fetchall()
        finally:
            conn.close()

    # Reverse to oldest→newest for context
    rows = list(rows)[::-1]
    return [dict(r) for r in rows]


def upsert_fact(chat_id: int, fact_key: str, fact_value: str) -> None:
    """Create or update a structured fact for this chat."""
    fact_key = fact_key.strip()
    fact_value = fact_value.strip()
    if not fact_key or not fact_value:
        return

    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO user_facts (chat_id, fact_key, fact_value)
                VALUES (?, ?, ?)
                ON CONFLICT(chat_id, fact_key)
                DO UPDATE SET
                    fact_value = excluded.fact_value,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (chat_id, fact_key, fact_value),
            )
            conn.commit()
            logger.info(
                "Upserted fact chat_id=%s key=%s value=%s",
                chat_id,
                fact_key,
                fact_value,
            )
        finally:
            conn.close()


def get_fact(chat_id: int, fact_key: str) -> Optional[str]:
    """Get the latest value for a structured fact."""
    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT fact_value
                FROM user_facts
                WHERE chat_id = ? AND fact_key = ?
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (chat_id, fact_key),
            )
            row = cur.fetchone()
        finally:
            conn.close()

    if row:
        return row["fact_value"]
    return None
