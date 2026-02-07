import os
import sqlite3
import threading
import logging
from typing import List, Dict, Optional, Any, Tuple

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

            # User facts: structured memory (e.g., preferred_language)
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

            # Notes: free-form notes per chat (for /note, /notes)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            # Daily logs: one summary per day per chat (for /daily, /dailies)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, date)
                );
                """
            )

            
            # Reminders: scheduled nudges per chat (for /remind, /reminders)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    due_at_utc TEXT NOT NULL,
                    text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP,
                    status TEXT DEFAULT 'pending'
                );
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(status, due_at_utc);"
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
                DO UPDATE SET fact_value = excluded.fact_value, updated_at = CURRENT_TIMESTAMP
                """,
                (chat_id, fact_key, fact_value),
            )
            conn.commit()
        finally:
            conn.close()


def get_facts(chat_id: int) -> Dict[str, str]:
    """Return all facts for a chat_id."""
    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT fact_key, fact_value
                FROM user_facts
                WHERE chat_id = ?
                ORDER BY updated_at DESC
                """,
                (chat_id,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()

    out: Dict[str, str] = {}
    for r in rows:
        out[str(r["fact_key"])] = str(r["fact_value"])
    return out



# -----------------------------
# Compatibility wrappers (bot.py expects these names)
# -----------------------------
def get_fact(chat_id: int, fact_key: str) -> str:
    """Return a single fact value for a key, or empty string."""
    facts = get_facts(chat_id)
    return (facts.get((fact_key or "").strip()) or "").strip()

def get_all_facts(chat_id: int) -> Dict[str, str]:
    """Alias for get_facts(chat_id)."""
    return get_facts(chat_id)


def add_note(chat_id: int, content: str) -> int:
    content = (content or "").strip()
    if not content:
        return -1

    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO notes (chat_id, content) VALUES (?, ?)",
                (chat_id, content),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

# -----------------------------
# Reminders helpers (Runner support)
# -----------------------------
def fetch_due_reminders(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Return due reminders (pending + due_at_utc <= CURRENT_TIMESTAMP).
    Assumes due_at_utc stored as 'YYYY-MM-DD HH:MM:SS' UTC (SQLite-friendly).
    """
    limit = max(1, min(100, int(limit or 20)))
    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, chat_id, due_at_utc, text
                FROM reminders
                WHERE status = 'pending'
                  AND due_at_utc <= CURRENT_TIMESTAMP
                ORDER BY due_at_utc ASC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

def claim_due_reminders(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Atomically claim a batch of due reminders (pending -> sending) and return them.
    This prevents double-sends even if multiple runners overlap.
    """
    limit = max(1, min(100, int(limit or 20)))
    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()

            # 1) Find due pending reminders
            cur.execute(
                """
                SELECT id, chat_id, due_at_utc, text
                FROM reminders
                WHERE status = 'pending'
                  AND due_at_utc <= CURRENT_TIMESTAMP
                ORDER BY due_at_utc ASC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()
            if not rows:
                return []

            ids = [int(r["id"]) for r in rows]

            # 2) Claim them in the same transaction
            placeholders = ",".join(["?"] * len(ids))
            cur.execute(
                f"""
                UPDATE reminders
                SET status = 'sending'
                WHERE status = 'pending'
                  AND id IN ({placeholders})
                """,
                tuple(ids),
            )
            conn.commit()

            # 3) Return only what we intended to send
            return [dict(r) for r in rows]
        finally:
            conn.close()


def claim_reminder(reminder_id: int) -> bool:
    """
    Atomic-ish claim: pending -> sending. Returns True only if we claimed it.
    Prevents double-send if runner overlaps.
    """
    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE reminders
                SET status = 'sending'
                WHERE id = ? AND status = 'pending'
                """,
                (int(reminder_id),),
            )
            conn.commit()
            return cur.rowcount == 1
        finally:
            conn.close()

def mark_reminder_sent(reminder_id: int) -> None:
    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE reminders
                SET status = 'sent',
                    sent_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (int(reminder_id),),
            )
            conn.commit()
        finally:
            conn.close()

def revert_reminder_pending(reminder_id: int) -> None:
    """
    If send fails, revert sending -> pending so it can retry.
    """
    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE reminders
                SET status = 'pending'
                WHERE id = ? AND status = 'sending'
                """,
                (int(reminder_id),),
            )
            conn.commit()
        finally:
            conn.close()

def get_notes(chat_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, chat_id, content, created_at
                FROM notes
                WHERE chat_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (chat_id, limit),
            )
            rows = cur.fetchall()
        finally:
            conn.close()

    return [dict(r) for r in rows]


def search_notes(chat_id: int, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    query = (query or "").strip()
    if not query:
        return []

    like = f"%{query}%"
    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, chat_id, content, created_at
                FROM notes
                WHERE chat_id = ?
                  AND content LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (chat_id, like, limit),
            )
            rows = cur.fetchall()
        finally:
            conn.close()

    return [dict(r) for r in rows]


# -----------------------------
# Daily logs (long-term summary)
# -----------------------------
def upsert_daily_log(chat_id: int, date: str, summary: str) -> Tuple[bool, str]:
    """
    Insert or replace a daily summary for a chat_id on a given date (YYYY-MM-DD).
    Returns (ok, msg).
    """
    date = (date or "").strip()
    summary = (summary or "").strip()
    if not date or not summary:
        return (False, "Missing date or summary")

    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO daily_logs (chat_id, date, summary)
                VALUES (?, ?, ?)
                ON CONFLICT(chat_id, date)
                DO UPDATE SET summary = excluded.summary, created_at = CURRENT_TIMESTAMP
                """,
                (chat_id, date, summary),
            )
            conn.commit()
            return (True, "saved")
        finally:
            conn.close()


def get_daily_logs(chat_id: int, limit: int = 7) -> List[Dict[str, Any]]:
    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, chat_id, date, summary, created_at
                FROM daily_logs
                WHERE chat_id = ?
                ORDER BY date DESC
                LIMIT ?
                """,
                (chat_id, limit),
            )
            rows = cur.fetchall()
        finally:
            conn.close()

    return [dict(r) for r in rows]


def search_daily_logs(chat_id: int, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    query = (query or "").strip()
    if not query:
        return []

    like = f"%{query}%"
    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, chat_id, date, summary, created_at
                FROM daily_logs
                WHERE chat_id = ?
                  AND summary LIKE ?
                ORDER BY date DESC
                LIMIT ?
                """,
                (chat_id, like, limit),
            )
            rows = cur.fetchall()
        finally:
            conn.close()

    return [dict(r) for r in rows]

# -----------------------------
# Daily Logs (long-term summary)
# -----------------------------

