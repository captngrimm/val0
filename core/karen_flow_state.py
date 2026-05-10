import json
from typing import Any


def _ensure_table():
    from memory_store import _get_conn

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS karen_flow_state (
            chat_id INTEGER NOT NULL,
            flow_key TEXT NOT NULL,
            state_json TEXT NOT NULL,
            updated_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (chat_id, flow_key)
        )
        """
    )
    conn.commit()
    conn.close()


def save_flow_state(chat_id: int, flow_key: str, state: dict[str, Any]) -> None:
    from memory_store import _get_conn

    _ensure_table()

    payload = json.dumps(state or {}, ensure_ascii=False)
    chat_id = int(chat_id)
    flow_key = str(flow_key)

    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT chat_id
        FROM karen_flow_state
        WHERE chat_id=? AND flow_key=?
        LIMIT 1
        """,
        (chat_id, flow_key),
    )
    row = cur.fetchone()

    if row:
        cur.execute(
            """
            UPDATE karen_flow_state
            SET state_json=?, updated_at=datetime('now')
            WHERE chat_id=? AND flow_key=?
            """,
            (payload, chat_id, flow_key),
        )
    else:
        cur.execute(
            """
            INSERT INTO karen_flow_state(chat_id, flow_key, state_json, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            """,
            (chat_id, flow_key, payload),
        )

    conn.commit()
    conn.close()


def load_flow_state(chat_id: int, flow_key: str) -> dict[str, Any]:
    from memory_store import _get_conn

    _ensure_table()

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT state_json
        FROM karen_flow_state
        WHERE chat_id=? AND flow_key=?
        LIMIT 1
        """,
        (int(chat_id), str(flow_key)),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return {}

    raw = row["state_json"] if hasattr(row, "keys") else row[0]

    try:
        data = json.loads(raw or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def clear_flow_state(chat_id: int, flow_key: str) -> None:
    from memory_store import _get_conn

    _ensure_table()

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM karen_flow_state
        WHERE chat_id=? AND flow_key=?
        """,
        (int(chat_id), str(flow_key)),
    )
    conn.commit()
    conn.close()


def load_active_context_state(chat_id: int, context, user_data_key: str, flow_key: str) -> dict[str, Any]:
    """
    If context.user_data has active state, return it.
    Otherwise try DB and hydrate context.user_data.

    This lets active guided flows survive service restart.
    """
    state = context.user_data.get(user_data_key) or {}
    if state.get("active"):
        return state

    state = load_flow_state(int(chat_id), flow_key)
    if state.get("active"):
        context.user_data[user_data_key] = state
        return state

    return {}
