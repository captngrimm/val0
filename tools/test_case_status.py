import sys
import os
import asyncio

# Make repository root importable when running this file directly
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(THIS_DIR)

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.case_mvp import try_case_status


class DummyMessage:
    def __init__(self):
        self.replies = []

    async def reply_text(self, text):
        self.replies.append(text)
        print(text)


class DummyUpdate:
    def __init__(self):
        self.message = DummyMessage()


async def main():
    if len(sys.argv) < 3:
        print('Usage: /opt/val0/.venv/bin/python /opt/val0/tools/test_case_status.py <chat_id> "<query>"')
        sys.exit(1)

    chat_id = int(sys.argv[1])
    text = sys.argv[2]

    update = DummyUpdate()
    handled = await try_case_status(update, chat_id, text)

    print(f"\n[handled={handled}]")
    print(f"[reply_count={len(update.message.replies)}]")


if __name__ == "__main__":
    asyncio.run(main())
