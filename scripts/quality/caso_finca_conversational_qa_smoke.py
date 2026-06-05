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
    case_qa_context_active,
    classify_case_qa_question,
    mark_case_qa_context,
    maybe_handle_case_workspace_qa,
    render_case_qa_answer,
)
from core.founder_intro import INTENT_LIMITATIONS, normalize_founder_intro_intent, render_founder_intro_response  # noqa: E402


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


class FakeContext:
    def __init__(self) -> None:
        self.chat_data: dict[str, object] = {}


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
    assert_not_contains(reply, "Val0/VFMS", f"{label} hides internal storage labels")
    assert_not_contains(reply, "JUZGADO PRIMERO DE CIRCUITO", f"{label} avoids raw OCR body")
    for phrase in STALE_PHRASES:
        assert_not_contains(reply, phrase, f"{label} no stale contamination {phrase}")
    for phrase in FORBIDDEN:
        assert_not_contains(reply, phrase, f"{label} avoids forbidden legal certainty {phrase}")
    if expect_ocr:
        assert_contains(reply, "Nota OCR", f"{label} includes OCR caveat")


def test_question_classification_and_renderer() -> None:
    explicit_cases = {
        "Val, qué sabes del caso?": "case_overview",
        "Val, qué le pregunto a Nora?": "nora_questions",
        "Val, explícame lo de la finca en palabras simples.": "plain_language_explanation",
        "Val, ese primer documento, por qué importa?": "document_explanation",
        "Val, qué hago antes de hablar con la abogada?": "next_action",
    }
    contextual_cases = {
        "Val, qué falta revisar?": "needs_review",
        "Val, qué sabemos seguro y qué falta confirmar?": "known_vs_uncertain",
    }
    document_priority_aliases = {
        "Val, cuál documento debería revisar primero?": "document_priority",
        "Val, cuál documento reviso primero?": "document_priority",
    }
    for phrase, expected in explicit_cases.items():
        assert_true(classify_case_qa_question(phrase) == expected, f"classifies {phrase!r} as {expected}")
        packet = build_case_qa_packet(phrase, client_id=KAREN_CLIENT_ID)
        assert_true(packet is not None, f"packet built for {phrase!r}")
        reply = render_case_qa_answer(packet)
        _assert_safe_answer(reply, label=expected, expect_ocr=(expected == "document_explanation"))
    for phrase, expected in contextual_cases.items():
        assert_true(classify_case_qa_question(phrase) is None, f"contextless phrase does not globally route: {phrase!r}")
        assert_true(
            classify_case_qa_question(phrase, case_context=True) == expected,
            f"contextual phrase classifies {phrase!r} as {expected}",
        )
        packet = build_case_qa_packet(phrase, client_id=KAREN_CLIENT_ID, case_context=True)
        assert_true(packet is not None, f"contextual packet built for {phrase!r}")
        reply = render_case_qa_answer(packet)
        _assert_safe_answer(reply, label=expected)
    for phrase, expected in document_priority_aliases.items():
        assert_true(classify_case_qa_question(phrase) == expected, f"document priority alias classifies {phrase!r} as {expected}")
        packet = build_case_qa_packet(phrase, client_id=KAREN_CLIENT_ID)
        assert_true(packet is not None, f"document priority packet built for {phrase!r}")
        reply = render_case_qa_answer(packet)
        _assert_safe_answer(reply, label=expected)
        assert_contains(reply, "Documento recomendado", f"document priority alias answer recommends document: {phrase}")
        assert_not_contains(reply, "Qué hago ahora", f"document priority alias avoids whatnow title: {phrase}")

    doc_packet = build_case_qa_packet("Val, ese primer documento, por qué importa?", client_id=KAREN_CLIENT_ID)
    assert_true(doc_packet is not None and doc_packet.selected_document_number == 1, "first document maps to document 1")
    doc_reply = render_case_qa_answer(doc_packet)
    assert_contains(doc_reply, "documento 1", "document answer references visible number")
    assert_contains(doc_reply, "Hechos en Val", "document answer has grounded section")
    assert_contains(doc_reply, "Falta confirmar", "document answer has confirmation section")

    priority_packet = build_case_qa_packet("Val, cuál documento debería revisar primero?", client_id=KAREN_CLIENT_ID, case_context=True)
    priority_reply = render_case_qa_answer(priority_packet)
    assert_contains(priority_reply, "Documento recomendado", "priority answer recommends a document")
    assert_contains(priority_reply, "Por qué ese primero", "priority answer explains grounded reason")
    assert_contains(priority_reply, '"Val, resume el documento 1"', "priority answer gives safe next command")
    assert_not_contains(priority_reply, "vfms:", "priority answer hides internal IDs")

    natural_priority_packet = build_case_qa_packet("Val, cuál documento reviso primero?", client_id=KAREN_CLIENT_ID)
    assert_true(
        natural_priority_packet is not None and natural_priority_packet.question_type == "document_priority",
        "natural document-priority alias routes to Caso Finca priority",
    )
    natural_priority_reply = render_case_qa_answer(natural_priority_packet)
    assert_contains(natural_priority_reply, "Documento recomendado", "natural priority answer recommends document")
    assert_contains(natural_priority_reply, "Por qué ese primero", "natural priority answer has grounded reason")
    assert_not_contains(natural_priority_reply, "Qué hago ahora", "natural priority avoids generic whatnow block")
    assert_not_contains(natural_priority_reply, "que hago ahora", "natural priority avoids generic whatnow copy")


def test_async_route_and_no_live_mutation() -> None:
    before_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    before_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None

    update = FakeUpdate()
    context = FakeContext()
    mark_case_qa_context(context, source="smoke_case_context")
    assert_true(case_qa_context_active(context), "case context active in smoke")
    handled = asyncio.run(
        maybe_handle_case_workspace_qa(
            update,
            context=context,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, qué falta revisar?",
        )
    )
    assert_true(handled, "Q&A route handles context-only needs-review phrase")
    assert_true(len(update.message.replies) == 1, "Q&A route sends one compact answer")
    _assert_safe_answer(update.message.replies[0], label="async contextual needs-review")

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


def test_live_failure_phrases_are_protected() -> None:
    for phrase, expected, required in (
        ("Val, qué falta revisar?", "needs_review", "Falta confirmar"),
        ("Val, qué sabemos seguro y qué falta confirmar?", "known_vs_uncertain", "Hechos en Val"),
    ):
        assert_true(build_case_qa_packet(phrase, client_id=KAREN_CLIENT_ID) is None, f"general phrase requires case context: {phrase}")
        packet = build_case_qa_packet(phrase, client_id=KAREN_CLIENT_ID, case_context=True)
        assert_true(packet is not None and packet.question_type == expected, f"packet protects live phrase: {phrase}")
        reply = render_case_qa_answer(packet)
        _assert_safe_answer(reply, label=f"live phrase {expected}")
        assert_contains(reply, required, f"live phrase {expected} has expected section")
        assert_contains(reply, "Señales / indicios", f"live phrase {expected} has grounded signal section")
        assert_not_contains(reply, "memoria mágica", f"live phrase {expected} avoids founder limitations")
        assert_not_contains(reply, "no debe prometer", f"live phrase {expected} avoids founder limitations")


def test_founder_limitations_still_available() -> None:
    general = (
        "Val, qué no puedes hacer todavía?",
        "Val, cuáles son tus límites?",
        "Qué falta desarrollar en Val?",
    )
    for phrase in general:
        assert_true(classify_case_qa_question(phrase) is None, f"general limitations phrase not classified as case Q&A: {phrase}")
        assert_true(normalize_founder_intro_intent(phrase) == INTENT_LIMITATIONS, f"founder limitations still recognizes: {phrase}")
    limitations = render_founder_intro_response(INTENT_LIMITATIONS)
    assert_contains(limitations, "no debe prometer", "founder limitations copy remains available")


def test_generic_whatnow_stays_generic() -> None:
    phrase = "Val, qué hago ahora?"
    assert_true(classify_case_qa_question(phrase) is None, "generic whatnow phrase not classified as case Q&A")
    assert_true(
        build_case_qa_packet(phrase, client_id=KAREN_CLIENT_ID, case_context=True) is None,
        "active case context still does not hijack generic whatnow",
    )


def test_bot_route_order() -> None:
    source = (ROOT / "bot.py").read_text(encoding="utf-8")
    folder_idx = source.find("KAREN_GENERIC_FOLDER_GATE")
    founder_idx = source.find("maybe_handle_founder_intro_query(update, text, context)")
    qa_idx = source.find("KAREN_CASE_WORKSPACE_QA_GATE")
    workspace_idx = source.find("KAREN_CASE_WORKSPACE_STATUS_GATE")
    old_status_idx = source.find("KAREN_CASE_STATUS_GATE")
    founder_exclusion_idx = source.find("classify_case_qa_question(text, case_context=case_qa_context_active(context))")
    founder_intent_idx = source.find("intent = normalize_founder_intro_intent(text)")
    assert_true(folder_idx >= 0, "bot has generic folder gate")
    assert_true(founder_idx >= 0, "bot has founder intro gate")
    assert_true(qa_idx >= 0, "bot has Q&A gate")
    assert_true(workspace_idx >= 0, "bot has workspace gate")
    assert_true(founder_exclusion_idx >= 0, "founder intro excludes contextual Caso Finca Q&A")
    assert_true(founder_exclusion_idx < founder_intent_idx, "Q&A exclusion runs before founder intent classifier")
    assert_true(folder_idx < qa_idx, "folder gate beats Q&A")
    assert_true(founder_idx < qa_idx, "founder gate is earlier, so exclusion is required")
    assert_true(qa_idx < workspace_idx, "Q&A beats workspace fallback for natural questions")
    assert_true(old_status_idx < 0 or qa_idx < old_status_idx, "Q&A beats legacy case status")


def main() -> int:
    test_question_classification_and_renderer()
    test_async_route_and_no_live_mutation()
    test_live_failure_phrases_are_protected()
    test_founder_limitations_still_available()
    test_generic_whatnow_stays_generic()
    test_bot_route_order()
    print("PASS: Caso Finca conversational Q&A smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
