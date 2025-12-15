PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users (
    chat_id TEXT PRIMARY KEY,
    username TEXT,
    preferred_language TEXT,
    favorite_color TEXT,
    main_goal TEXT,
    updated_ts INTEGER
);

CREATE TABLE IF NOT EXISTS user_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT,
    key TEXT,
    value TEXT,
    created_ts INTEGER
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT,
    content TEXT,
    created_ts INTEGER
);

CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    content,
    note_id UNINDEXED
);

CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT,
    label TEXT,
    lat REAL,
    lon REAL,
    created_ts INTEGER
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT,
    filename TEXT,
    stored_path TEXT,
    created_ts INTEGER
);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT,
    text TEXT,
    due_ts INTEGER,
    created_ts INTEGER,
    status TEXT
);
