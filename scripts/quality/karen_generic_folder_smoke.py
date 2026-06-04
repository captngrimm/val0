#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.client_folders import (  # noqa: E402
    LIVE_DATA_GUARD,
    classify_folder_command,
    client_folder_store_path,
    maybe_handle_client_folder_query,
    render_folder_label,
)


KAREN_CLIENT_ID = "kar" + "en"
LIVE_GROCERY = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_GROCERY.md"
LIVE_FOLDERS = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_FOLDERS.json"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


class FakeMessage:
    def __init__(self) -> None:
        self.replies: list[str] = []

    async def reply_text(self, text: str, **_kwargs):
        self.replies.append(text)
        return text


class FakeUpdate:
    def __init__(self) -> None:
        self.message = FakeMessage()


def _git_cached_live_files() -> str:
    proc = subprocess.run(
        [
            "git",
            "diff",
            "--cached",
            "--name-only",
            "--",
            str(LIVE_GROCERY.relative_to(ROOT)),
            str(LIVE_FOLDERS.relative_to(ROOT)),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout.strip()


async def _send(text: str, store_path: Path, *, client_id: str = KAREN_CLIENT_ID) -> tuple[bool, str]:
    update = FakeUpdate()
    handled = await maybe_handle_client_folder_query(
        update,
        context=None,
        chat_id=123,
        client_id=client_id,
        text=text,
        store_path=store_path,
    )
    return handled, "\n".join(update.message.replies)


def test_classifier() -> None:
    cases = {
        "Val, crea carpeta Libro": ("create", "Libro"),
        "Val, crea una carpeta para mi libro": ("create", "Libro"),
        "Val, lista mis carpetas": ("list", ""),
        "Val, abre carpeta Libro": ("open", "Libro"),
        "Val, guarda esta idea en Libro: una escena de apertura": ("save_note", "Libro"),
        "Val, qué tengo en Libro?": ("contents", "Libro"),
    }
    for text, (expected_action, expected_folder) in cases.items():
        action, fields = classify_folder_command(text)
        assert_true(action == expected_action, f"classifies {text!r} as {expected_action}")
        if expected_folder:
            assert_true(fields.get("folder") == expected_folder, f"extracts folder {expected_folder}")


def test_folder_labels() -> None:
    assert_true(render_folder_label("Libro") == "📚 **Libro** 📁", "book folder label")
    assert_true(render_folder_label("Supermercado") == "🛒 **Supermercado** 📁", "shopping folder label")
    assert_true(render_folder_label("Ideas") == "💡 **Ideas** 📁", "ideas folder label")
    assert_true(render_folder_label("Pendientes") == "**Pendientes** 📁", "default folder label")


def test_runtime_with_temp_store() -> None:
    before_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    before_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None

    with tempfile.TemporaryDirectory() as tmp:
        store_path = Path(tmp) / "CLIENT_FOLDERS.json"

        handled, reply = asyncio.run(_send("Val, crea carpeta Libro", store_path))
        assert_true(handled, "create folder handled")
        assert_contains(reply, "Creé la carpeta 📚 **Libro** 📁", "create reply has book label")

        handled, reply = asyncio.run(_send("Val, crea una carpeta para mi libro", store_path))
        assert_true(handled, "duplicate folder handled")
        assert_contains(reply, "ya tenía la carpeta 📚 **Libro** 📁", "duplicate reply has book label")

        handled, reply = asyncio.run(_send("Val, crea carpeta Pendientes", store_path))
        assert_true(handled, "create generic folder handled")
        assert_contains(reply, "Creé la carpeta **Pendientes** 📁", "generic folder uses default label")

        handled, reply = asyncio.run(_send("Val, lista mis carpetas", store_path))
        assert_true(handled, "list folders handled")
        assert_contains(reply, "📚 **Libro** 📁", "list includes book label")
        assert_contains(reply, "**Pendientes** 📁", "list includes default label")

        handled, reply = asyncio.run(_send("Val, abre carpeta Libro", store_path))
        assert_true(handled, "open folder handled")
        assert_contains(reply, "abrí tu carpeta 📚 **Libro** 📁", "open reply has book label")
        assert_contains(reply, "Text-only por ahora", "text-only safety")
        assert_not_contains(reply, "Caso Finca", "generic folder does not become case workspace")

        handled, reply = asyncio.run(_send("Val, guarda esta idea en Libro: primera escena con lluvia", store_path))
        assert_true(handled, "save note handled")
        assert_contains(reply, "guardé esa idea en 📚 **Libro** 📁", "save reply has book label")
        assert_contains(reply, "Primera escena con lluvia", "saved note echoed with display capitalization")

        handled, reply = asyncio.run(_send("Val, qué tengo en Libro?", store_path))
        assert_true(handled, "folder contents handled")
        assert_contains(reply, "esto tengo en 📚 **Libro** 📁", "contents header has book label")
        assert_contains(reply, "1. Primera escena con lluvia", "contents include capitalized note")
        assert_true("1. primera escena con lluvia" not in reply, "contents avoid lowercase note")

        handled, reply = asyncio.run(_send("Val, crea carpeta Ideas", store_path, client_id="other-client"))
        assert_true(not handled, "non-Karen client unaffected")
        assert_true(reply == "", "non-Karen gets no folder reply")

        stored = store_path.read_text(encoding="utf-8")
        assert_contains(stored, LIVE_DATA_GUARD, "store has live-data guard")

    after_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    after_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None
    assert_true(before_grocery == after_grocery, "CLIENT_GROCERY.md untouched")
    assert_true(before_folders == after_folders, "live CLIENT_FOLDERS.json untouched by smoke")
    assert_true(_git_cached_live_files() == "", "live client files are not staged")


def test_live_store_path_and_guard() -> None:
    assert_true(client_folder_store_path(KAREN_CLIENT_ID) == LIVE_FOLDERS, "Karen folder store path")
    assert_true(LIVE_FOLDERS.exists(), "initial CLIENT_FOLDERS.json exists")
    assert_contains(LIVE_FOLDERS.read_text(encoding="utf-8"), LIVE_DATA_GUARD, "live folder store has guard")


def main() -> int:
    test_classifier()
    test_folder_labels()
    test_runtime_with_temp_store()
    test_live_store_path_and_guard()
    print("PASS: Karen generic folder smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
