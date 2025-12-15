# memory/memory_engine.py
from .database import get_db
import time

# -------------------------
# USERS / PROFILE
# -------------------------

def upsert_user(chat_id, username=None, preferred_language=None,
                favorite_color=None, main_goal=None):
    ts = int(time.time())
    with get_db() as db:
        db.execute("""
            INSERT INTO users (chat_id, username, preferred_language, favorite_color, main_goal, updated_ts)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                username=excluded.username,
                preferred_language=excluded.preferred_language,
                favorite_color=excluded.favorite_color,
                main_goal=excluded.main_goal,
                updated_ts=excluded.updated_ts
        """, (chat_id, username, preferred_language, favorite_color, main_goal, ts))

def get_user(chat_id):
    with get_db() as db:
        cur = db.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
        return cur.fetchone()


# -------------------------
# FACTS
# -------------------------

def add_fact(chat_id, key, value):
    ts = int(time.time())
    with get_db() as db:
        db.execute("""
            INSERT INTO user_facts (chat_id, key, value, created_ts)
            VALUES (?, ?, ?, ?)
        """, (chat_id, key, value, ts))

def get_facts(chat_id):
    with get_db() as db:
        cur = db.execute("SELECT key, value FROM user_facts WHERE chat_id = ?", (chat_id,))
        return cur.fetchall()


# -------------------------
# NOTES
# -------------------------

def add_note(chat_id, content):
    ts = int(time.time())
    with get_db() as db:
        # main table
        cur = db.execute("""
            INSERT INTO notes (chat_id, content, created_ts)
            VALUES (?, ?, ?)
        """, (chat_id, content, ts))
        note_id = cur.lastrowid

        # FTS mirror
        db.execute("""
            INSERT INTO notes_fts (content, note_id)
            VALUES (?, ?)
        """, (content, note_id))

def search_notes(chat_id, query):
    with get_db() as db:
        cur = db.execute("""
            SELECT notes.id, notes.content, notes.created_ts
            FROM notes_fts
            JOIN notes ON notes.id = notes_fts.note_id
            WHERE notes.chat_id = ?
            AND notes_fts MATCH ?
            ORDER BY notes.created_ts DESC
            LIMIT 10
        """, (chat_id, query))
        return cur.fetchall()


# -------------------------
# LOCATIONS
# -------------------------

def add_location(chat_id, label, lat, lon):
    ts = int(time.time())
    with get_db() as db:
        db.execute("""
            INSERT INTO locations (chat_id, label, lat, lon, created_ts)
            VALUES (?, ?, ?, ?, ?)
        """, (chat_id, label.lower(), lat, lon, ts))

def get_location(chat_id, label):
    with get_db() as db:
        cur = db.execute("""
            SELECT * FROM locations
            WHERE chat_id = ?
            AND label = ?
        """, (chat_id, label.lower()))
        return cur.fetchone()


# -------------------------
# FILE REGISTRY
# -------------------------

def register_file(chat_id, filename, stored_path):
    ts = int(time.time())
    with get_db() as db:
        db.execute("""
            INSERT INTO files (chat_id, filename, stored_path, created_ts)
            VALUES (?, ?, ?, ?)
        """, (chat_id, filename, stored_path, ts))

def list_files(chat_id):
    with get_db() as db:
        cur = db.execute("""
            SELECT * FROM files
            WHERE chat_id = ?
            ORDER BY created_ts DESC
        """, (chat_id,))
        return cur.fetchall()


# -------------------------
# REMINDERS (BASIC ALPHA)
# -------------------------

def add_reminder(chat_id, text, due_ts):
    ts = int(time.time())
    with get_db() as db:
        cur = db.execute("""
            INSERT INTO reminders (chat_id, text, due_ts, created_ts, status)
            VALUES (?, ?, ?, ?, 'pending')
        """, (chat_id, text, due_ts, ts))
        return cur.lastrowid

def get_pending_reminders():
    with get_db() as db:
        cur = db.execute("""
            SELECT * FROM reminders
            WHERE status = 'pending'
            ORDER BY due_ts ASC
        """)
        return cur.fetchall()

def mark_reminder_sent(reminder_id):
    with get_db() as db:
        db.execute("""
            UPDATE reminders SET status = 'sent' WHERE id = ?
        """, (reminder_id,))
