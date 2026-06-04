#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.case_workspace_qa import (  # noqa: E402
    build_case_qa_packet,
    classify_case_qa_question,
    maybe_handle_case_workspace_qa,
    render_case_qa_answer,
)


KAREN_CLIENT_ID = "kar" + "en"
LIVE_GROCERY = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_GROCERY.md"
LIVE_FOLDERS = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_FOLDERS.json"
STALE_PHRASES = ("bajar de peso", "task_high", "memoria pura")
FORBIDDEN = ("definitivamente", "caso ganado", "caso perdido", "no necesitas abogada")


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


def _assert_safe_answer(reply: str, *, label: str, expect_ocr: bool = False) -> None:
    assert_contains(reply, "Tany", f"{label} uses Tany")
    assert_contains(reply, "Caso Finca", f"{label} names case")
    assert_contains(reply, "Nora/la abogada confirma efecto legal", f"{label} legal boundary")
    assert_not_contains(reply, "ID técnico del documento", f"{label} hides technical IDs")
    assert_not_contains(reply, "vfms:", f"{label} hides VFMS IDs")
    assert_not_contains(reply, "JUZGADO PRIMERO DE CIRCUITO", f"{label} avoids raw OCR body")
    for phrase in STALE_PHRASES:
        assert_not_contains(reply, phrase, f"{label} no stale contamination {phrase}")
    for phrase in FORBIDDEN:
        assert_not_contains(reply, phrase, f"{label} avoids forbidden legal certainty {phrase}")
    if expect_ocr:
        assert_contains(reply, "Nota OCR", f"{label} includes OCR caveat")


def test_question_classification_and_renderer() -> None:
    cases = {
        "Val, qué sabes del caso?": "case_overview",
        "Val, qué falta revisar?": "needs_review",
        "Val, qué sabemos seguro y qué falta confirmar?": "known_vs_uncertain",
        "Val, qué le pregunto a Nora?": "nora_questions",
        "Val, cuál documento debería revisar primero?": "document_priority",
        "Val, explícame lo de la finca en palabras simples.": "plain_language_explanation",
        "Val, ese primer documento, por qué importa?": "document_explanation",
        "Val, qué hago antes de hablar con la abogada?": "next_action",
    }
    for phrase, expected in cases.items():
        assert_true(classify_case_qa_question(phrase) == expected, f"classifies {phrase!r} as {expected}")
        packet = build_case_qa_packet(phrase, client_id=KAREN_CLIENT_ID)
        assert_true(packet is not None, f"packet built for {phrase!r}")
        reply = render_case_qa_answer(packet)
        _assert_safe_answer(reply, label=expected, expect_ocr=(expected == "document_explanation"))

    doc_packet = build_case_qa_packet("Val, ese primer documento, por qué importa?", client_id=KAREN_CLIENT_ID)
    assert_true(doc_packet is not None and doc_packet.selected_document_number == 1, "first document maps to document 1")
    doc_reply = render_case_qa_answer(doc_packet)
    assert_contains(doc_reply, "documento 1", "document answer references visible number")
    assert_contains(doc_reply, "Lo que sé", "document answer has grounded section")
    assert_contains(doc_reply, "Lo que falta confirmar", "document answer has confirmation section")

    priority_packet = build_case_qa_packet("Val, cuál documento debería revisar primero?", client_id=KAREN_CLIENT_ID)
    priority_reply = render_case_qa_answer(priority_packet)
    assert_contains(priority_reply, "Documento recomendado", "priority answer recommends a document")
    assert_contains(priority_reply, '"Val, resume el documento 1"', "priority answer gives safe next command")


def test_async_route_and_no_live_mutation() -> None:
    before_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    before_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None

    update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_qa(
            update,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, qué sabes del caso?",
        )
    )
    assert_true(handled, "Q&A route handles overview")
    assert_true(len(update.message.replies) == 1, "Q&A route sends one compact answer")
    _assert_safe_answer(update.message.replies[0], label="async overview")

    non_karen = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_qa(
            non_karen,
            context=None,
            chat_id=123,
            client_id="other-client",
            text="Val, qué sabes del caso?",
        )
    )
    assert_true(not handled, "non-Karen client not handled")
    assert_true(non_karen.message.replies == [], "non-Karen gets no reply")

    after_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    after_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None
    assert_true(before_grocery == after_grocery, "CLIENT_GROCERY.md untouched")
    assert_true(before_folders == after_folders, "CLIENT_FOLDERS.json untouched")
    assert_true(_git_cached_live_files() == "", "live client files are not staged")


def test_bot_route_order() -> None:
    source = (ROOT / "bot.py").read_text(encoding="utf-8")
    folder_idx = source.find("KAREN_GENERIC_FOLDER_GATE")
    qa_idx = source.find("KAREN_CASE_WORKSPACE_QA_GATE")
    workspace_idx = source.find("KAREN_CASE_WORKSPACE_STATUS_GATE")
    old_status_idx = source.find("KAREN_CASE_STATUS_GATE")
    assert_true(folder_idx >= 0, "bot has generic folder gate")
    assert_true(qa_idx >= 0, "bot has Q&A gate")
    assert_true(workspace_idx >= 0, "bot has workspace gate")
    assert_true(folder_idx < qa_idx, "folder gate beats Q&A")
    assert_true(qa_idx < workspace_idx, "Q&A beats workspace fallback for natural questions")
    assert_true(old_status_idx < 0 or qa_idx < old_status_idx, "Q&A beats legacy case status")


def main() -> int:
    test_question_classification_and_renderer()
    test_async_route_and_no_live_mutation()
    test_bot_route_order()
    print("PASS: Caso Finca conversational Q&A smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
