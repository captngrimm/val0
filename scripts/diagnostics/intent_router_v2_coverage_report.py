#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.intent_router_v2 import classify_intent_shadow  # noqa: E402
from scripts.diagnostics.intent_router_v2_sample_harness import SAMPLES  # noqa: E402


BOT = ROOT / "bot.py"
OBSERVATION_REPORTS = (
    ROOT / "docs" / "architecture" / "ROUTER_07_SHADOW_OBSERVATION_REPORT.md",
    ROOT / "docs" / "architecture" / "ROUTER_12_POST_OBSERVATION_COVERAGE_UPDATE.md",
)
OUTPUT_RELATIVE = Path("tmp/router_coverage/intent_router_v2_coverage_report.txt")
OUTPUT_PATH = ROOT / OUTPUT_RELATIVE


KNOWN_CLASSIFIER_INTENTS = (
    "pending_action_reply",
    "destructive_confirmation",
    "agenda_query",
    "gcal_create",
    "gcal_delete",
    "reminder_create",
    "reminder_query",
    "reminder_delete",
    "reminder_update",
    "task_query",
    "task_create",
    "task_delete",
    "task_complete",
    "document_summary",
    "document_ocr",
    "case_status",
    "adaptive_intake_start",
    "adaptive_intake_domain",
    "adaptive_intake_followup",
    "adaptive_intake_recommendation",
    "memory_capture_candidate",
    "llm_fallback",
)

SHADOW_ONLY_INTENTS = {
    "adaptive_intake_start",
    "adaptive_intake_domain",
    "adaptive_intake_followup",
    "adaptive_intake_recommendation",
    "memory_capture_candidate",
    "llm_fallback",
}

STATIC_OBSERVED_BY_REPORT = {
    "ROUTER_07_SHADOW_OBSERVATION_REPORT.md": {
        "task_query",
        "agenda_query",
        "gcal_create",
        "destructive_confirmation",
        "reminder_create",
        "document_ocr",
        "case_status",
    },
    "ROUTER_12_POST_OBSERVATION_COVERAGE_UPDATE.md": {
        "document_summary",
        "gcal_delete",
        "reminder_query",
        "reminder_delete",
        "reminder_create",
    },
}


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _sample_counts() -> Counter[str]:
    counts: Counter[str] = Counter()
    for sample in SAMPLES:
        counts[str(sample.expected)] += 1
    return counts


def _classifier_intents() -> set[str]:
    intents: set[str] = set()
    for intent in KNOWN_CLASSIFIER_INTENTS:
        try:
            if intent == "memory_capture_candidate":
                decision = classify_intent_shadow("guarda nota: revisar borrador", client_id="client-zero")
            elif intent == "llm_fallback":
                decision = classify_intent_shadow("jajaja", client_id="client-zero")
            else:
                decision = None
            if decision and decision.selected_intent == intent:
                intents.add(intent)
        except Exception:
            pass
    source = _read(ROOT / "core" / "intent_router_v2.py")
    for intent in KNOWN_CLASSIFIER_INTENTS:
        if f'"{intent}"' in source:
            intents.add(intent)
    return intents


def _actual_label_intents() -> set[str]:
    bot = _read(BOT)
    intents: set[str] = set()
    for intent in KNOWN_CLASSIFIER_INTENTS:
        if f'"{intent}",' in bot or f"'{intent}'," in bot or f'"{intent}"' in bot or f"'{intent}'" in bot:
            intents.add(intent)
    if "[INTENT_ROUTER_V2_ACTUAL]" not in bot or "record_actual_intent" not in bot:
        return set()
    return intents


def _observed_intents() -> set[str]:
    observed: set[str] = set()
    for path in OBSERVATION_REPORTS:
        text = _read(path)
        if not text or "match=True" not in text:
            continue
        observed.update(STATIC_OBSERVED_BY_REPORT.get(path.name, set()))
    return observed


def _status(intent: str, *, sample_count: int, has_classifier: bool, has_actual_label: bool, observed: bool) -> str:
    if not has_classifier:
        return "SHADOW_ONLY"
    if intent in SHADOW_ONLY_INTENTS:
        return "SHADOW_ONLY"
    if not has_actual_label:
        return "NEEDS_ACTUAL_LABEL"
    if not observed:
        return "NEEDS_LIVE_OBSERVATION"
    return "COVERED"


def build_report() -> list[dict[str, Any]]:
    counts = _sample_counts()
    classifier_intents = _classifier_intents()
    actual_label_intents = _actual_label_intents()
    observed_intents = _observed_intents()
    intents = sorted(set(KNOWN_CLASSIFIER_INTENTS) | set(counts))
    rows: list[dict[str, Any]] = []
    for intent in intents:
        sample_count = int(counts.get(intent, 0))
        has_classifier = intent in classifier_intents
        has_actual_label = intent in actual_label_intents
        observed = intent in observed_intents
        rows.append({
            "intent": intent,
            "sample_count": sample_count,
            "has_shadow_classifier": has_classifier,
            "has_actual_label": has_actual_label,
            "observed_in_report_or_logs": observed,
            "status": _status(
                intent,
                sample_count=sample_count,
                has_classifier=has_classifier,
                has_actual_label=has_actual_label,
                observed=observed,
            ),
        })
    return rows


def render_table(rows: list[dict[str, Any]]) -> str:
    headers = ("intent", "samples", "classifier", "actual_label", "observed", "status")
    widths = {
        "intent": max(len(headers[0]), *(len(row["intent"]) for row in rows)),
        "samples": len(headers[1]),
        "classifier": len(headers[2]),
        "actual_label": len(headers[3]),
        "observed": len(headers[4]),
        "status": max(len(headers[5]), *(len(row["status"]) for row in rows)),
    }
    fmt = (
        f"{{intent:<{widths['intent']}}}  "
        f"{{samples:>{widths['samples']}}}  "
        f"{{classifier:<{widths['classifier']}}}  "
        f"{{actual_label:<{widths['actual_label']}}}  "
        f"{{observed:<{widths['observed']}}}  "
        f"{{status:<{widths['status']}}}"
    )
    lines = [
        "Intent Router v2 coverage report",
        "",
        fmt.format(intent="intent", samples="samples", classifier="classifier", actual_label="actual_label", observed="observed", status="status"),
        "-" * (sum(widths.values()) + 10),
    ]
    for row in rows:
        lines.append(fmt.format(
            intent=row["intent"],
            samples=str(row["sample_count"]),
            classifier="yes" if row["has_shadow_classifier"] else "no",
            actual_label="yes" if row["has_actual_label"] else "no",
            observed="yes" if row["observed_in_report_or_logs"] else "no",
            status=row["status"],
        ))
    status_counts = Counter(row["status"] for row in rows)
    lines.extend([
        "",
        "Summary:",
        *(f"- {status}: {status_counts[status]}" for status in sorted(status_counts)),
    ])
    return "\n".join(lines)


def write_output(text: str) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(text + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Report Intent Router v2 sample/actual-label/observation coverage.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text report.")
    parser.add_argument("--no-write", action="store_true", help="Do not write tmp/router_coverage output.")
    args = parser.parse_args()

    rows = build_report()
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        text = render_table(rows)
        print(text)
        if not args.no_write:
            write_output(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
