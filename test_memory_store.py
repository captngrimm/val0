import unittest
import time

from memory_store import init_db, insert_message, get_recent_messages


class TestMemoryStore(unittest.TestCase):
    def test_insert_and_fetch_recent(self):
        init_db()

        chat_id = int(time.time())  # unique enough for test runs
        content = f"unit-test-{chat_id}"

        insert_message(
            chat_id=chat_id,
            role="user",
            content=content,
            telegram_message_id=None,
            model_used=None,
        )

        rows = get_recent_messages(chat_id=chat_id, limit=5)
        self.assertTrue(isinstance(rows, list))
        self.assertTrue(len(rows) >= 1)
        # newest should contain our content somewhere
        self.assertTrue(any((r.get("content") == content) for r in rows))


if __name__ == "__main__":
    unittest.main()
