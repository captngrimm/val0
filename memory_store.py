import os
import threading
import logging
from typing import List, Dict, Optional, Any, Tuple

logger = logging.getLogger("val0-memory")

# --------------------------------------------------
# DB CONFIG (SQLCipher-first)
# --------------------------------------------------
DB_PATH = os.getenv("VAL0_DB_PATH", "/opt/val0/val0_memory.enc.db")
DB_KEY_FILE = os.getenv("VAL0_DB_KEY_FILE", "").strip()
DB_KEY_ENV = os.getenv("VAL0_DB_KEY", "").strip()
ALLOW_PLAINTEXT = os.getenv("VAL0_ALLOW_PLAINTEXT", "0").strip().lower() in ("1", "true", "yes")

_lock = threading.Lock()


def _read_db_key() -> str:
    if DB_KEY_FILE:
        with open(DB_KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    if DB_KEY_ENV:
        return DB_KEY_ENV
    return ""


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


def _get_conn():
    """
    Encrypted-first DB connection.
    If key exists => SQLCipher (pysqlcipher3)
    If no key => refuse unless VAL0_ALLOW_PLAINTEXT=1
    """
    key = _read_db_key()

    if key:
        from pysqlcipher3 import dbapi2 as sqlcipher
        conn = sqlcipher.connect(DB_PATH)
        conn.row_factory = sqlcipher.Row
        cur = conn.cursor()

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


# --------------------------------------------------
# SCHEMA HELPERS / MIGRATIONS
# --------------------------------------------------
def _table_columns(cur, table: str) -> List[str]:
    cur.execute(f"PRAGMA table_info({table});")
    rows = cur.fetchall() or []
    return [r["name"] for r in rows]


def _ensure_column(cur, table: str, col: str, ddl: str) -> None:
    cols = _table_columns(cur, table)
    if col in cols:
        return
    cur.execute(f"ALTER TABLE {table} ADD COLUMN {ddl};")


def init_db() -> None:
    """
    Create tables if they don't exist + run safe migrations.
    """
    with _lock:
        _log_db_mode()
        conn = _get_conn()
        cur = conn.cursor()

        # -------------------------
        # USERS (principal identity)
        # -------------------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            principal_id TEXT NOT NULL UNIQUE,
            display_name TEXT,
            preferred_language TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_principal ON users(principal_id);")

        # Map principals to current routing targets (Telegram chat_id today, ValApp device token later)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            principal_id TEXT NOT NULL,
            channel TEXT NOT NULL,          -- 'telegram' | 'valapp'
            target TEXT NOT NULL,           -- telegram chat_id as text, or push token, etc.
            last_seen TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(principal_id, channel, target)
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_routes_principal ON user_routes(principal_id);")

        # -------------------------
        # MESSAGES (keep existing contract, add principal_id for future)
        # -------------------------
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

        # safe migration: add principal_id to messages
        _ensure_column(cur, "messages", "principal_id", "principal_id TEXT")

        # -------------------------
        # REMINDERS (add principal_id + channel/target for future ValApp)
        # -------------------------
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

        _ensure_column(cur, "reminders", "principal_id", "principal_id TEXT")
        _ensure_column(cur, "reminders", "channel", "channel TEXT DEFAULT 'telegram'")
        _ensure_column(cur, "reminders", "target", "target TEXT")

        # Backfill target for existing rows (best-effort)
        try:
            cur.execute("UPDATE reminders SET target=CAST(chat_id AS TEXT) WHERE target IS NULL;")
        except Exception:
            pass

        # -------------------------
        # USER FACTS (we keep your existing API keyed by chat_id for now,
        # but we ALSO store principal_id so we can migrate cleanly later.)
        # -------------------------
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

        _ensure_column(cur, "user_facts", "principal_id", "principal_id TEXT")

        # -------------------------
        # NOTES
        # -------------------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notes_chat ON notes(chat_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at);")
        _ensure_column(cur, "notes", "principal_id", "principal_id TEXT")

        # -------------------------
        # DAILY LOGS
        # -------------------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            summary TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(chat_id, date)
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_daily_logs_chat ON daily_logs(chat_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_daily_logs_date ON daily_logs(date);")
        _ensure_column(cur, "daily_logs", "principal_id", "principal_id TEXT")

        conn.commit()
        conn.close()
        logger.info(f"SQLite DB initialized at {DB_PATH}")


# --------------------------------------------------
# IDENTITY (principal_id + routes)
# --------------------------------------------------
def ensure_user(principal_id: str, display_name: Optional[str] = None, preferred_language: Optional[str] = None) -> None:
    if not principal_id:
        return
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute("SELECT principal_id FROM users WHERE principal_id=?;", (principal_id,))
        row = cur.fetchone()
        if not row:
            cur.execute(
                "INSERT INTO users(principal_id, display_name, preferred_language) VALUES(?,?,?);",
                (principal_id, display_name, preferred_language),
            )
        else:
            # keep it cheap; update only if values are provided
            if display_name or preferred_language:
                cur.execute(
                    "UPDATE users SET display_name=COALESCE(?, display_name), preferred_language=COALESCE(?, preferred_language), updated_at=datetime('now') WHERE principal_id=?;",
                    (display_name, preferred_language, principal_id),
                )

        conn.commit()
        conn.close()


def touch_route(principal_id: str, channel: str, target: str) -> None:
    if not principal_id or not channel or not target:
        return
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO user_routes(principal_id, channel, target, last_seen)
        VALUES(?,?,?,datetime('now'))
        ON CONFLICT(principal_id, channel, target) DO UPDATE SET last_seen=datetime('now');
        """, (principal_id, channel, target))
        conn.commit()
        conn.close()


# --------------------------------------------------
# MESSAGES
# --------------------------------------------------
def insert_message(
    chat_id: int,
    a,
    b=None,
    c=None,
    telegram_message_id: Optional[int] = None,
    model_used: Optional[str] = None,
    principal_id: Optional[str] = None,
) -> None:
    """
    Backwards compatible:
      - insert_message(chat_id, role, content)
      - insert_message(chat_id, user_id, role, content)   # legacy: user_id ignored
      - insert_message(chat_id, role, content, telegram_message_id, model_used)
      - insert_message(chat_id, role, content, telegram_message_id, model_used, principal_id="tg:123")
    """
    # Style 1: (chat_id, role, content)
    if c is None and b is not None and isinstance(a, str):
        role = a
        content = b
    # Style 2: (chat_id, user_id, role, content) legacy
    else:
        role = b
        content = c

    if role is None or content is None:
        raise ValueError("insert_message called with invalid args")

    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        # detect whether principal_id exists on messages
        cols = _table_columns(cur, "messages")
        if "principal_id" in cols:
            cur.execute(
                "INSERT INTO messages(chat_id, role, content, telegram_message_id, model_used, principal_id) VALUES(?,?,?,?,?,?)",
                (chat_id, role, content, telegram_message_id, model_used, principal_id),
            )
        else:
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


def get_recent_messages(chat_id: int, limit: int = 30) -> List[Dict[str, Any]]:
    return fetch_recent_messages(chat_id=chat_id, limit=limit)


# --------------------------------------------------
# REMINDERS
# --------------------------------------------------
def insert_reminder(
    chat_id: int,
    due_at_utc: str,
    text: str,
    status: str = "pending",
    principal_id: Optional[str] = None,
    channel: str = "telegram",
    target: Optional[str] = None,
) -> int:
    if target is None:
        target = str(chat_id)

    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        cols = _table_columns(cur, "reminders")
        if all(x in cols for x in ("principal_id", "channel", "target")):
            cur.execute(
                "INSERT INTO reminders(chat_id, due_at_utc, text, status, principal_id, channel, target) VALUES(?,?,?,?,?,?,?)",
                (chat_id, due_at_utc, text, status, principal_id, channel, target),
            )
        else:
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
            "FROM reminders WHERE status='pending' AND due_at_utc <= datetime('now') "
            "ORDER BY due_at_utc ASC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
    return [dict(r) for r in rows]


def claim_due_reminders(limit: int = 10):
    # Simple v0: no locking across processes; good enough for single bot instance.
    return fetch_due_reminders(limit)


def claim_reminder(reminder_id: int):
    return None  # reserved for multi-worker locking later


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


def revert_reminder_pending(reminder_id: int) -> None:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE reminders SET status='pending', sent_at=NULL WHERE id=?",
            (reminder_id,),
        )
        conn.commit()
        conn.close()


# --------------------------------------------------
# FACTS
# --------------------------------------------------
def upsert_fact(
    chat_id: int,
    fact_key: str,
    fact_value: str,
    source: str = "auto",
    confidence: float = 1.0,
    principal_id: Optional[str] = None,
) -> None:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()

        cols = _table_columns(cur, "user_facts")
        if "principal_id" in cols:
            cur.execute("""
            INSERT INTO user_facts (chat_id, fact_key, fact_value, source, confidence, updated_at, principal_id)
            VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
            ON CONFLICT(chat_id, fact_key) DO UPDATE SET
                fact_value=excluded.fact_value,
                source=excluded.source,
                confidence=excluded.confidence,
                updated_at=datetime('now'),
                principal_id=COALESCE(excluded.principal_id, user_facts.principal_id);
            """, (chat_id, fact_key, fact_value, source, confidence, principal_id))
        else:
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
        logger.info(f"Upserted fact chat_id={chat_id} key={fact_key} value={fact_value}")


def get_fact(chat_id: int, fact_key: str) -> Optional[str]:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT fact_value FROM user_facts WHERE chat_id=? AND fact_key=? LIMIT 1;",
            (chat_id, fact_key),
        )
        row = cur.fetchone()
        conn.close()
    return (row["fact_value"] if row else None)


def get_all_facts(chat_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
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


# --------------------------------------------------
# NOTES
# --------------------------------------------------
def add_note(chat_id: int, text: str, principal_id: Optional[str] = None) -> Optional[int]:
    if not text:
        return None
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cols = _table_columns(cur, "notes")
        if "principal_id" in cols:
            cur.execute("INSERT INTO notes(chat_id, text, principal_id) VALUES(?,?,?)", (chat_id, text, principal_id))
        else:
            cur.execute("INSERT INTO notes(chat_id, text) VALUES(?,?)", (chat_id, text))
        conn.commit()
        nid = cur.lastrowid
        conn.close()
        return nid


def get_notes(chat_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, chat_id, text, created_at FROM notes WHERE chat_id=? ORDER BY id DESC LIMIT ?;",
            (chat_id, limit),
        )
        rows = cur.fetchall()
        conn.close()
    return [dict(r) for r in rows]


def search_notes(chat_id: int, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, chat_id, text, created_at FROM notes WHERE chat_id=? AND text LIKE ? ORDER BY id DESC LIMIT ?;",
            (chat_id, f"%{q}%", limit),
        )
        rows = cur.fetchall()
        conn.close()
    return [dict(r) for r in rows]


# --------------------------------------------------
# DAILY LOGS
# --------------------------------------------------
def upsert_daily_log(chat_id: int, date: str, summary: str, principal_id: Optional[str] = None) -> Tuple[bool, str]:
    if not date or not summary:
        return False, "date/summary required"
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cols = _table_columns(cur, "daily_logs")
        if "principal_id" in cols:
            cur.execute("""
            INSERT INTO daily_logs(chat_id, date, summary, principal_id)
            VALUES(?,?,?,?)
            ON CONFLICT(chat_id, date) DO UPDATE SET summary=excluded.summary;
            """, (chat_id, date, summary, principal_id))
        else:
            cur.execute("""
            INSERT INTO daily_logs(chat_id, date, summary)
            VALUES(?,?,?)
            ON CONFLICT(chat_id, date) DO UPDATE SET summary=excluded.summary;
            """, (chat_id, date, summary))
        conn.commit()
        conn.close()
        return True, "ok"


def get_daily_logs(chat_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, chat_id, date, summary, created_at FROM daily_logs WHERE chat_id=? ORDER BY date DESC LIMIT ?;",
            (chat_id, limit),
        )
        rows = cur.fetchall()
        conn.close()
    return [dict(r) for r in rows]


def search_daily_logs(chat_id: int, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, chat_id, date, summary, created_at FROM daily_logs WHERE chat_id=? AND summary LIKE ? ORDER BY date DESC LIMIT ?;",
            (chat_id, f"%{q}%", limit),
        )
        rows = cur.fetchall()
        conn.close()
    return [dict(r) for r in rows]
