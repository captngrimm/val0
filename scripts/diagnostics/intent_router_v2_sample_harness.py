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
    text: str
    expected: str
    pending_state: dict[str, Any] | None = None


SAMPLES: tuple[Sample, ...] = (
    Sample("Val que tareas tengo activas?", "task_query"),
    Sample("Vale. ¿Qué tareas tengo activas?", "task_query"),
    Sample("Val, ¿qué tareas tengo activa?", "task_query"),
    Sample("Recuérdame en 10 minutos llamar a Mabel", "reminder_create"),
    Sample("Val recuérdame cumpleaños de Miguel el lunes a las 10", "reminder_create"),
    Sample("Val qué tengo mañana", "agenda_query"),
    Sample("Que tengo para el lunes", "agenda_query"),
    Sample("Val agenda prueba calendario mañana a las 10am", "gcal_create"),
    Sample("Val agenda para el lunes llamar al Juzgado a las 9", "gcal_create"),
    Sample("Val elimina el evento 1", "gcal_delete"),
    Sample("elimina evento dos", "gcal_delete"),
    Sample("Val resume el último documento", "document_summary"),
    Sample("Val resume este documento", "document_summary"),
    Sample("Val resume con OCR el último documento", "document_ocr"),
    Sample("Val lee visualmente este documento", "document_ocr"),
    Sample("Qué tengo guardado del caso del terreno", "case_status"),
    Sample("Val dime datos de la finca", "case_status"),
    Sample("sí", "pending_action_reply", {"type": "reminder_missing_date"}),
    Sample("ok", "pending_action_reply", {"type": "task_delete_confirmation"}),
    Sample("hoy", "pending_action_reply", {"type": "reminder_missing_date"}),
    Sample("para hoy", "pending_action_reply", {"type": "reminder_missing_date"}),
    Sample("Que mala eres", "llm_fallback"),
    Sample("😭", "llm_fallback"),
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
            "input": sample.text,
            "expected": sample.expected,
            "predicted": decision.selected_intent,
            "confidence": decision.confidence,
            "reason": decision.reason,
            "pass": decision.selected_intent == sample.expected,
        })
    return rows


def _print_table(rows: list[dict[str, Any]]) -> None:
    headers = ("input", "expected", "predicted", "confidence", "result")
    widths = {
        "input": min(58, max(len(headers[0]), *(len(row["input"]) for row in rows))),
        "expected": max(len(headers[1]), *(len(row["expected"]) for row in rows)),
        "predicted": max(len(headers[2]), *(len(row["predicted"]) for row in rows)),
        "confidence": len(headers[3]),
        "result": len(headers[4]),
    }
    fmt = (
        f"{{input:<{widths['input']}}}  "
        f"{{expected:<{widths['expected']}}}  "
        f"{{predicted:<{widths['predicted']}}}  "
        f"{{confidence:>{widths['confidence']}}}  "
        f"{{result:<{widths['result']}}}"
    )
    print(fmt.format(input="input", expected="expected", predicted="predicted", confidence="confidence", result="result"))
    print("-" * (sum(widths.values()) + 8))
    for row in rows:
        text = row["input"]
        if len(text) > widths["input"]:
            text = text[: widths["input"] - 3].rstrip() + "..."
        print(fmt.format(
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

    failures = [row for row in rows if not row["pass"]]
    if failures and not args.allow_failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
