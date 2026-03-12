import sys
import os
import asyncio

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(THIS_DIR)

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.case_mvp import try_case_timeline_for_case


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
        print('Usage: python test_case_timeline.py <chat_id> "<query>"')
        sys.exit(1)

    chat_id = int(sys.argv[1])
    text = sys.argv[2]

    update = DummyUpdate()

    handled = await try_case_timeline_for_case(update, chat_id, text)

    print("\n[handled=%s]" % handled)
    print("[reply_count=%s]" % len(update.message.replies))


if __name__ == "__main__":
    asyncio.run(main())
