#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.intent_router_v2 import classify_intent_shadow  # noqa: E402


@dataclass(frozen=True)
class Sample:
    category: str
    text: str
    expected: str
    note: str = ""
    pending_state: dict[str, Any] | None = None


SAMPLES: tuple[Sample, ...] = (
    Sample("task_query", "Val que tareas tengo activas?", "task_query"),
    Sample("task_query", "Vale. ¿Qué tareas tengo activas?", "task_query"),
    Sample("task_query", "Val, ¿qué tareas tengo activa?", "task_query"),
    Sample("task_query", "Vale qué tareas tengo activas", "task_query", "voice-prefix variant"),
    Sample("task_management", "Val elimina la tarea 1", "task_delete"),
    Sample("task_management", "elimina tarea 2", "task_delete"),
    Sample("task_management", "Eliminarla del listado", "pending_action_reply", "pending task-delete clarification follow-up", {"type": "task_delete_clarification"}),
    Sample("task_management", "marca la tarea 1 como hecha", "task_complete", "task completion is distinct from destructive delete"),

    Sample("reminders", "Recuérdame en 10 minutos llamar a Mabel", "reminder_create"),
    Sample("reminders", "Val recuérdame cumpleaños de Miguel el lunes a las 10", "reminder_create"),
    Sample("reminders", "Val qué recordatorios tengo", "reminder_query"),
    Sample("reminders", "elimina el recordatorio 1", "reminder_delete"),
    Sample("reminders", "cambia el recordatorio 1 para las 11", "reminder_update", "diagnostic label; runtime may still offer edit fallback"),

    Sample("agenda", "Val qué tengo mañana", "agenda_query"),
    Sample("agenda", "Que tengo para el lunes", "agenda_query"),
    Sample("agenda", "va el que tengo mañana", "agenda_query", "voice-prefix variant"),

    Sample("gcal_create", "Val agenda prueba calendario mañana a las 10am", "gcal_create"),
    Sample("gcal_create", "Val agenda para el lunes llamar al Juzgado a las 9", "gcal_create"),
    Sample("gcal_delete", "Val elimina el evento 1", "gcal_delete"),
    Sample("gcal_delete", "elimina evento dos", "gcal_delete"),
    Sample("gcal_delete", "borrar evento dos", "gcal_delete"),
    Sample("gcal_delete", "eliminar el compromiso 1", "gcal_delete", "compromiso maps to visible Google Calendar event action"),

    Sample("confirmations", "sí", "pending_action_reply", "pending state consumes yes", {"type": "gcal_create_confirmation"}),
    Sample("confirmations", "ok", "pending_action_reply", "pending state consumes ok", {"type": "task_delete_confirmation"}),
    Sample("confirmations", "dale", "pending_action_reply", "pending state consumes dale", {"type": "gcal_delete_confirmation"}),
    Sample("confirmations", "cancelar", "destructive_confirmation", "without pending state, this is a destructive confirmation/cancel word"),
    Sample("confirmations", "see", "pending_action_reply", "voice typo should only resolve inside pending context", {"type": "gcal_create_confirmation"}),
    Sample("confirmations", "hoy", "pending_action_reply", "pending reminder date follow-up", {"type": "reminder_missing_date"}),
    Sample("confirmations", "para hoy", "pending_action_reply", "pending reminder date follow-up", {"type": "reminder_missing_date"}),

    Sample("documents", "Val resume documento 2", "document_summary"),
    Sample("documents", "Val resume el documento 3", "document_summary"),
    Sample("documents", "Val resume el último documento", "document_summary"),
    Sample("documents", "Val resume este documento", "document_summary"),
    Sample("documents", "Val haz OCR del documento 1", "document_ocr"),
    Sample("documents", "Val resume con OCR el último documento", "document_ocr"),
    Sample("documents", "Val lee visualmente este documento", "document_ocr"),
    Sample("documents", "Val lee visualmente el último documento", "document_ocr"),
    Sample("documents", "bal resume con OCR el último documento", "document_ocr", "voice-prefix variant"),

    Sample("case_status", "Qué tengo guardado del caso del terreno", "case_status"),
    Sample("case_status", "Val dime datos de la finca", "case_status"),
    Sample("case_status", "datos de finca 10082", "case_status"),
    Sample("case_status", "qué herederos tengo registrados", "case_status"),
    Sample("case_status", "prepara preguntas para Nora", "case_status", "current design treats Nora prep as case/legal context"),

    Sample("llm_fallback", "Que mala eres", "llm_fallback"),
    Sample("llm_fallback", "😭", "llm_fallback"),
    Sample("llm_fallback", "jajaja", "llm_fallback"),
    Sample("llm_fallback", "qué opinas", "llm_fallback"),
)


def _run_samples() -> list[dict[str, Any]]:
    rows = []
    for sample in SAMPLES:
        decision = classify_intent_shadow(
            sample.text,
            client_id="client-zero",
            chat_id=None,
            pending_state=sample.pending_state,
        )
        rows.append({
            "category": sample.category,
            "input": sample.text,
            "expected": sample.expected,
            "predicted": decision.selected_intent,
            "confidence": decision.confidence,
            "reason": decision.reason,
            "note": sample.note,
            "pass": decision.selected_intent == sample.expected,
        })
    return rows


def _print_table(rows: list[dict[str, Any]]) -> None:
    headers = ("category", "input", "expected", "predicted", "confidence", "result")
    widths = {
        "category": max(len(headers[0]), *(len(row["category"]) for row in rows)),
        "input": min(58, max(len(headers[1]), *(len(row["input"]) for row in rows))),
        "expected": max(len(headers[2]), *(len(row["expected"]) for row in rows)),
        "predicted": max(len(headers[3]), *(len(row["predicted"]) for row in rows)),
        "confidence": len(headers[4]),
        "result": len(headers[5]),
    }
    fmt = (
        f"{{category:<{widths['category']}}}  "
        f"{{input:<{widths['input']}}}  "
        f"{{expected:<{widths['expected']}}}  "
        f"{{predicted:<{widths['predicted']}}}  "
        f"{{confidence:>{widths['confidence']}}}  "
        f"{{result:<{widths['result']}}}"
    )
    print(fmt.format(category="category", input="input", expected="expected", predicted="predicted", confidence="confidence", result="result"))
    print("-" * (sum(widths.values()) + 10))
    for row in rows:
        text = row["input"]
        if len(text) > widths["input"]:
            text = text[: widths["input"] - 3].rstrip() + "..."
        print(fmt.format(
            category=row["category"],
            input=text,
            expected=row["expected"],
            predicted=row["predicted"],
            confidence=f"{float(row['confidence']):.2f}",
            result="PASS" if row["pass"] else "FAIL",
        ))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run curated Karen phrase samples against Intent Router v2 shadow classifier.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text table.")
    parser.add_argument("--allow-failures", action="store_true", help="Exit zero even when a sample prediction differs from expected.")
    args = parser.parse_args()

    rows = _run_samples()
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        _print_table(rows)
        total = len(rows)
        passed = sum(1 for row in rows if row["pass"])
        print(f"\nSummary: {passed}/{total} PASS")

    failures = [row for row in rows if not row["pass"]]
    if failures and not args.allow_failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
