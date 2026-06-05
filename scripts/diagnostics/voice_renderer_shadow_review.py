#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_OBSERVATION_PATH = Path("tmp/voice_renderer_shadow/observations.jsonl")
INTERNAL_PATTERNS = (
    re.compile(r"vfms:[A-Za-z0-9_:-]*", re.IGNORECASE),
    re.compile(r"\bID t[eé]cnico\b", re.IGNORECASE),
    re.compile(r"\b(document_id|source_type|source_name)\b", re.IGNORECASE),
)


def _redact(text: Any, *, limit: int = 280) -> str:
    value = str(text or "")
    for pattern in INTERNAL_PATTERNS:
        value = pattern.sub("[REDACTED_INTERNAL]", value)
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) > limit:
        return value[:limit].rstrip() + "..."
    return value


def _load_observations(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], [f"Observation file not found: {path}"]
    if path.stat().st_size == 0:
        return [], [f"Observation file is empty: {path}"]

    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            warnings.append(f"Skipped invalid JSONL row {line_number}: {exc.msg}")
            continue
        if isinstance(parsed, dict):
            records.append(parsed)
        else:
            warnings.append(f"Skipped non-object JSONL row {line_number}")
    return records, warnings


def _split_reason(reason: Any) -> list[str]:
    if not reason:
        return []
    values: list[str] = []
    for raw in str(reason).split(","):
        item = raw.strip()
        if item:
            values.append(item)
    return values


def _flag_names(record: dict[str, Any]) -> list[str]:
    values = record.get("safety_flags_triggered") or []
    if isinstance(values, str):
        values = [values]
    names: list[str] = []
    for value in values:
        name = str(value or "").strip()
        if name:
            names.append(name)
    return names


def summarize_observations(records: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = Counter(str(record.get("candidate_status") or "unknown") for record in records)
    accepted = statuses.get("accepted_shadow_only", 0)
    rejected = statuses.get("rejected", 0)
    reasons = Counter(reason for record in records for reason in _split_reason(record.get("rejection_reason")))
    flags = Counter(flag for record in records for flag in _flag_names(record))
    ocr_required = sum(1 for record in records if record.get("ocr_caveat_required") is True)
    ocr_present = sum(1 for record in records if record.get("ocr_caveat_required") is True and record.get("ocr_caveat_present") is True)
    legal_present = sum(1 for record in records if record.get("legal_boundary_present") is True)
    legal_missing = sum(1 for record in records if record.get("legal_boundary_present") is False)
    deterministic_facing = sum(1 for record in records if record.get("user_facing_is_deterministic") is True)
    return {
        "total": len(records),
        "statuses": statuses,
        "accepted": accepted,
        "rejected": rejected,
        "reasons": reasons,
        "flags": flags,
        "ocr_required": ocr_required,
        "ocr_present": ocr_present,
        "legal_present": legal_present,
        "legal_missing": legal_missing,
        "deterministic_facing": deterministic_facing,
    }


def recommendation_for_summary(summary: dict[str, Any]) -> str:
    total = int(summary["total"])
    rejected = int(summary["rejected"])
    accepted = int(summary["accepted"])
    legal_missing = int(summary["legal_missing"])
    flags: Counter[str] = summary["flags"]
    if total == 0:
        return "not enough data: no shadow observations found yet"
    if total < 5:
        return "not enough data: continue shadow observation"
    rejection_rate = rejected / total
    if rejection_rate >= 0.4 or legal_missing or flags.get("internal_leak", 0):
        return "stop/adjust prompt/validation before preview"
    if accepted >= 5 and rejected == 0:
        return "candidates look safe enough for operator-gated preview"
    return "continue shadow observation"


def _sample_lines(records: list[dict[str, Any]], *, status: str, limit: int) -> list[str]:
    lines: list[str] = []
    for record in records:
        if str(record.get("candidate_status") or "") != status:
            continue
        question_type = _redact(record.get("question_type"), limit=60) or "unknown"
        excerpt = _redact(record.get("candidate_excerpt"), limit=220) or "(no candidate excerpt)"
        reason = _redact(record.get("rejection_reason"), limit=140)
        if reason:
            lines.append(f"- {question_type}: {excerpt} | reason={reason}")
        else:
            lines.append(f"- {question_type}: {excerpt}")
        if len(lines) >= limit:
            break
    return lines


def render_review(path: Path, records: list[dict[str, Any]], warnings: list[str], *, sample_limit: int = 3) -> str:
    summary = summarize_observations(records)
    recommendation = recommendation_for_summary(summary)
    statuses: Counter[str] = summary["statuses"]
    reasons: Counter[str] = summary["reasons"]
    flags: Counter[str] = summary["flags"]

    lines = [
        "Bounded Voice Renderer Shadow Review",
        f"Observation path: {path}",
        "",
        "Safety note: report uses redacted/truncated excerpts only; no raw OCR body review.",
    ]
    if warnings:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {_redact(warning, limit=220)}" for warning in warnings)

    lines.extend(
        [
            "",
            "Summary",
            f"- Total observations: {summary['total']}",
            f"- Accepted: {summary['accepted']}",
            f"- Rejected: {summary['rejected']}",
            f"- Other statuses: {sum(count for status, count in statuses.items() if status not in {'accepted_shadow_only', 'rejected'})}",
            f"- Deterministic remained user-facing: {summary['deterministic_facing']}/{summary['total']}",
            "",
            "Rejection Reasons",
        ]
    )
    if reasons:
        lines.extend(f"- {_redact(reason, limit=160)}: {count}" for reason, count in reasons.most_common())
    else:
        lines.append("- none")

    lines.append("")
    lines.append("Safety Flags")
    if flags:
        lines.extend(f"- {_redact(flag, limit=80)}: {count}" for flag, count in flags.most_common())
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "OCR Caveat",
            f"- Required: {summary['ocr_required']}",
            f"- Present when required: {summary['ocr_present']}/{summary['ocr_required']}",
            "",
            "Legal Boundary",
            f"- Present: {summary['legal_present']}",
            f"- Missing: {summary['legal_missing']}",
            "",
            "Sample Accepted Excerpts",
        ]
    )
    lines.extend(_sample_lines(records, status="accepted_shadow_only", limit=sample_limit) or ["- none"])
    lines.append("")
    lines.append("Sample Rejected Excerpts")
    lines.extend(_sample_lines(records, status="rejected", limit=sample_limit) or ["- none"])
    lines.extend(["", "Recommendation", f"- {recommendation}"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Review bounded voice renderer shadow observation JSONL logs.")
    parser.add_argument("--path", default=str(DEFAULT_OBSERVATION_PATH), help="Observation JSONL path.")
    parser.add_argument("--sample-limit", type=int, default=3, help="Accepted/rejected excerpt sample count.")
    args = parser.parse_args()

    path = Path(args.path)
    records, warnings = _load_observations(path)
    print(render_review(path, records, warnings, sample_limit=max(0, args.sample_limit)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
