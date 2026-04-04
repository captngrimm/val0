CREATE TABLE IF NOT EXISTS commitments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    raw_input TEXT NOT NULL,
    action TEXT,
    target TEXT,
    due_date TEXT,
    confidence TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'open',
    last_nudged_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

