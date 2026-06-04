#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.case_workspace import (  # noqa: E402
    DEFAULT_CASO_FINCA_FIXTURE_PATH,
    _split_telegram_text,
    load_caso_finca_workspace_source_labeled,
    maybe_handle_case_workspace_status,
    render_workspace_compact_status,
    render_workspace_status,
)


KAREN_CLIENT_ID = "kar" + "en"
LIVE_FILE = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_GROCERY.md"
STALE_PHRASES = ("bajar de peso", "task_high", "memoria pura")
PRIVATE_BODY_PHRASES = (
    "Copia para propósitos informativos solamente",
    "Copia para propositos informativos solamente",
    "JUZGADO PRIMERO DE CIRCUITO",
    "Prescripción Adquisitiva de Dominio",
)


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


def _git_cached_client_grocery() -> str:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", str(LIVE_FILE.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout.strip()


def test_loader_and_renderer_source_labels() -> None:
    assert_true(DEFAULT_CASO_FINCA_FIXTURE_PATH.exists(), "source-labeled fixture exists")
    case = load_caso_finca_workspace_source_labeled()
    assert_true(case.known_records, "known records loaded")
    assert_true(case.confirmation_records, "confirmation records loaded")
    assert_true(case.timeline_events, "timeline records loaded")
    assert_true(case.documents, "documents loaded")
    assert_contains(case.source_label, "source-labeled", "case source label")

    compact = render_workspace_compact_status(case, client_id=KAREN_CLIENT_ID)
    assert_contains(compact, "📁 Estado rápido", "compact default screen exists")
    assert_contains(compact, '"Val, muéstrame todo el Caso Finca"', "compact offers full view command")
    assert_not_contains(compact, "ID técnico del documento", "compact avoids technical document ids")

    reply = render_workspace_status(case, client_id=KAREN_CLIENT_ID)
    for section in (
        "Lo que sabemos",
        "Qué falta confirmar",
        "Documentos relacionados",
        "Línea de tiempo / eventos",
        "Preguntas para Nora",
        "Pendientes",
        "Próximo paso sugerido",
    ):
        assert_contains(reply, section, f"section present: {section}")

    assert_contains(reply, "Tany", "Tany-facing opening")
    assert_contains(reply, "Nora", "Nora prep preserved")
    assert_contains(reply, "Nora/la abogada confirma efecto legal", "legal boundary")
    assert_contains(reply, "lectura y organizacion; no voy a mover nada", "read-only boundary")
    assert_contains(reply, "Fuente del tablero: datos registrados y auditoría de documentos", "friendly board source")
    assert_contains(reply, "Fuente: auditoría de documentos", "friendly document source")
    assert_contains(reply, "Confianza: alta", "friendly confidence rendered")
    assert_contains(reply, "Estado: requiere revisión legal", "friendly legal-review status rendered")
    assert_contains(reply, "vfms:20260531_000001", "trusted OCR-ready document id")
    assert_contains(reply, "ID técnico del documento: vfms:20260531_000001", "technical document id labeled clearly")
    assert_contains(reply, "12_ESPECIAL_RESUMEN_CASO_FINAL_JUNC", "trusted extracted summary candidate")
    assert_contains(reply, "OCR: disponible", "OCR status rendered in Spanish")
    assert_contains(reply, "Resumen: desconocido", "summary status rendered in Spanish")
    assert_contains(reply, "Relevancia para Caso Finca: alta", "relevance rendered in Spanish")
    assert_contains(reply, "Siguiente paso seguro:", "safe next action rendered in Spanish")
    assert_contains(reply, 'Pedir: "Val, resume con OCR el último documento"', "quoted OCR command example")
    assert_contains(reply, 'Pedir: "Val, prepárame el paquete para Nora"', "quoted Nora command example")
    assert_contains(reply, "candidato pendiente de confirmar", "uncertain candidates softened")
    for label in (
        "fixture/source-labeled v1",
        "source_type=",
        "source_name=",
        "confidence=",
        "status=",
        "observed_at=",
        "document_id:",
        "source/path category:",
        "OCR status:",
        "summary status:",
        "relevance:",
        "safe next action:",
    ):
        assert_not_contains(reply, label, f"raw/internal label absent: {label}")
    for phrase in STALE_PHRASES:
        assert_not_contains(reply, phrase, f"stale phrase absent: {phrase}")
    for phrase in PRIVATE_BODY_PHRASES:
        assert_not_contains(reply, phrase, f"raw body phrase absent: {phrase}")
    chunks = _split_telegram_text(reply, limit=3600)
    assert_true(len(chunks) >= 2, "current workspace reply is split into Telegram-safe chunks")
    assert_true(all(len(chunk) <= 3600 for chunk in chunks), "workspace chunks stay under Telegram-safe limit")


def test_route_uses_source_labeled_workspace_without_mutation() -> None:
    before = LIVE_FILE.read_text(encoding="utf-8") if LIVE_FILE.exists() else None
    update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_status(
            update,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, abre mi Caso Finca",
        )
    )
    after = LIVE_FILE.read_text(encoding="utf-8") if LIVE_FILE.exists() else None
    assert_true(handled, "workspace route handled open phrase")
    assert_true(len(update.message.replies) == 1, "default workspace route replies compactly")
    reply = "\n".join(update.message.replies)
    assert_contains(reply, "📁 Estado rápido", "route reply uses compact first screen")
    assert_contains(reply, '"Val, muéstrame todo el Caso Finca"', "route offers full view command")
    assert_not_contains(reply, "ID técnico del documento", "compact route hides technical ids")
    assert_not_contains(reply, "Fuente: auditoría de documentos", "compact route hides detailed source labels")
    assert_not_contains(reply, "fixture/source-labeled v1", "route hides fixture label")
    assert_not_contains(reply, "source_type=", "route hides raw source labels")

    full_update = FakeUpdate()
    handled = asyncio.run(
        maybe_handle_case_workspace_status(
            full_update,
            context=None,
            chat_id=123,
            client_id=KAREN_CLIENT_ID,
            text="Val, muéstrame todo el Caso Finca",
        )
    )
    full_reply = "\n".join(full_update.message.replies)
    assert_true(handled, "full workspace route handled explicit phrase")
    assert_true(len(full_update.message.replies) >= 2, "explicit full workspace route replies in chunks")
    assert_contains(full_update.message.replies[0], "[1/", "first full chunk has chunk prefix")
    assert_contains(full_reply, "Fuente: auditoría de documentos", "full route reply includes friendly source labels")
    assert_contains(full_reply, "vfms:20260531_000001", "full route reply includes trusted document attachment")
    assert_true(before == after, "CLIENT_GROCERY.md content untouched")
    assert_true(_git_cached_client_grocery() == "", "CLIENT_GROCERY.md is not staged")


def main() -> int:
    test_loader_and_renderer_source_labels()
    test_route_uses_source_labeled_workspace_without_mutation()
    print("PASS: Caso Finca source-labeled workspace smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
