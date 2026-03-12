import sys
import os
import asyncio

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(THIS_DIR)

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from bot import _process_text_pipeline


class DummyMessage:
    _next_id = 1000

    def __init__(self, text):
        self.text = text
        self.message_id = DummyMessage._next_id
        DummyMessage._next_id += 1
        self.replies = []

    async def reply_text(self, text, *args, **kwargs):
        self.replies.append(text)
        print(text)

        class Sent:
            def __init__(self, message_id):
                self.message_id = message_id

        return Sent(self.message_id + 10000)


class DummyChat:
    def __init__(self, chat_id):
        self.id = chat_id


class DummyUpdate:
    def __init__(self, chat_id, text):
        self.effective_chat = DummyChat(chat_id)
        self.message = DummyMessage(text)
        self.effective_message = self.message


class DummyBot:
    async def send_chat_action(self, *args, **kwargs):
        return None

    async def send_message(self, *args, **kwargs):
        return None


class DummyContext:
    def __init__(self):
        self.bot = DummyBot()


async def main():
    if len(sys.argv) < 3:
        print('Usage: /opt/val0/.venv/bin/python /opt/val0/tools/test_case_note_cmd.py <chat_id> "nota caso <id>: <texto>"')
        sys.exit(1)

    chat_id = int(sys.argv[1])
    text = sys.argv[2]

    update = DummyUpdate(chat_id, text)
    context = DummyContext()

    await _process_text_pipeline(update, context, text)

    print(f"\n[reply_count={len(update.message.replies)}]")


if __name__ == "__main__":
    asyncio.run(main())
