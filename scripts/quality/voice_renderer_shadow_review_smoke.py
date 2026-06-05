#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.diagnostics.voice_renderer_shadow_review import (  # noqa: E402
    _load_observations,
    recommendation_for_summary,
    render_review,
    summarize_observations,
)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_contains(text: str, needle: str, message: str) -> None:
    if needle not in text:
        raise AssertionError(f"{message}: missing {needle!r}")


def assert_not_contains(text: str, needle: str, message: str) -> None:
    if needle in text:
        raise AssertionError(f"{message}: unexpected {needle!r}")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def test_missing_and_empty_files() -> None:
    with tempfile.TemporaryDirectory(prefix="voice_review_missing_") as tmp:
        missing = Path(tmp) / "missing.jsonl"
        rows, warnings = _load_observations(missing)
        report = render_review(missing, rows, warnings)
        assert_contains(report, "Observation file not found", "missing file warning")
        assert_contains(report, "not enough data", "missing file recommendation")

        empty = Path(tmp) / "empty.jsonl"
        empty.write_text("", encoding="utf-8")
        rows, warnings = _load_observations(empty)
        report = render_review(empty, rows, warnings)
        assert_contains(report, "Observation file is empty", "empty file warning")
        assert_contains(report, "Total observations: 0", "empty total")


def test_mixed_report_summaries_and_redaction() -> None:
    with tempfile.TemporaryDirectory(prefix="voice_review_mixed_") as tmp:
        path = Path(tmp) / "observations.jsonl"
        _write_jsonl(
            path,
            [
                {
                    "candidate_status": "accepted_shadow_only",
                    "question_type": "case_overview",
                    "candidate_excerpt": "Tany, va en limpio. Val organiza y resume; Nora/la abogada confirma efecto legal.",
                    "legal_boundary_present": True,
                    "ocr_caveat_required": False,
                    "ocr_caveat_present": None,
                    "user_facing_is_deterministic": True,
                },
                {
                    "candidate_status": "rejected",
                    "question_type": "document_reason",
                    "candidate_excerpt": "Documento vfms:20260531_000001 prueba definitivamente el caso.",
                    "rejection_reason": "internal_leak:vfms:, forbidden_claim:prueba definitivamente",
                    "safety_flags_triggered": ["internal_leak", "forbidden_claim"],
                    "legal_boundary_present": True,
                    "ocr_caveat_required": True,
                    "ocr_caveat_present": False,
                    "user_facing_is_deterministic": True,
                },
            ],
        )
        rows, warnings = _load_observations(path)
        report = render_review(path, rows, warnings)
        assert_contains(report, "Total observations: 2", "mixed total")
        assert_contains(report, "Accepted: 1", "mixed accepted")
        assert_contains(report, "Rejected: 1", "mixed rejected")
        assert_contains(report, "internal_leak", "rejection reason summary")
        assert_contains(report, "forbidden_claim", "safety flag summary")
        assert_contains(report, "Required: 1", "OCR required summary")
        assert_contains(report, "Present when required: 0/1", "OCR present summary")
        assert_not_contains(report.lower(), "vfms:", "raw vfms redacted")
        assert_not_contains(report, "20260531_000001", "raw internal ID tail redacted")
        assert_contains(report, "[REDACTED_INTERNAL]", "redaction marker present")


def test_recommendations() -> None:
    low_sample = summarize_observations(
        [
            {
                "candidate_status": "accepted_shadow_only",
                "legal_boundary_present": True,
                "user_facing_is_deterministic": True,
            }
        ]
    )
    assert_contains(recommendation_for_summary(low_sample), "not enough data", "low sample recommendation")

    high_reject = summarize_observations(
        [
            {
                "candidate_status": "rejected",
                "rejection_reason": "missing_required_boundary",
                "safety_flags_triggered": ["missing_required_boundary"],
                "legal_boundary_present": False,
                "user_facing_is_deterministic": True,
            }
            for _ in range(5)
        ]
    )
    assert_contains(recommendation_for_summary(high_reject), "stop/adjust", "high rejection recommendation")

    preview = summarize_observations(
        [
            {
                "candidate_status": "accepted_shadow_only",
                "legal_boundary_present": True,
                "user_facing_is_deterministic": True,
            }
            for _ in range(5)
        ]
    )
    assert_contains(recommendation_for_summary(preview), "operator-gated preview", "safe preview recommendation")


def test_no_runtime_telegram_integration() -> None:
    bot_source = (ROOT / "bot.py").read_text(encoding="utf-8")
    assert_true("voice_renderer_shadow_review" not in bot_source, "review diagnostic is not wired into bot.py")


def main() -> int:
    test_missing_and_empty_files()
    test_mixed_report_summaries_and_redaction()
    test_recommendations()
    test_no_runtime_telegram_integration()
    print("PASS: voice renderer shadow review smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
