#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Check:
    label: str
    cmd: list[str]
    required: bool = True
    only_if_exists: Path | None = None


def _checks() -> list[Check]:
    py = sys.executable or "python3"
    return [
        Check("compile bot.py", ["./scripts/val0py", "-m", "py_compile", "bot.py"]),
        Check(
            "compile OCR runtime",
            ["./scripts/val0py", "-m", "py_compile", "core/document_ocr_runtime.py"],
            only_if_exists=REPO_ROOT / "core" / "document_ocr_runtime.py",
        ),
        Check("client isolation audit", [py, "scripts/quality/client_isolation_audit.py"]),
        Check("preferred name memory guard", [py, "scripts/quality/karen_preferred_name_memory_guard_smoke.py"]),
        Check("Tany vocative", [py, "scripts/quality/karen_vocative_tany_smoke.py"]),
        Check("natural name/language guard", [py, "scripts/quality/karen_natural_name_language_guard_smoke.py"]),
        Check("agenda hygiene", [py, "scripts/quality/karen_agenda_hygiene_smoke.py"]),
        Check("Karen Day0 routes", [py, "scripts/quality/karen_day0_route_smoke.py"]),
        Check("GCal event creation", [py, "scripts/quality/karen_gcal_event_creation_smoke.py"]),
        Check("GCal event delete", [py, "scripts/quality/karen_gcal_event_delete_smoke.py"]),
        Check("GCal stale delete guard", [py, "scripts/quality/karen_gcal_delete_stale_context_smoke.py"]),
        Check("Monday reminder/agenda", [py, "scripts/quality/karen_natural_monday_reminder_agenda_smoke.py"]),
        Check("pending reminder context", [py, "scripts/quality/karen_pending_reminder_context_smoke.py"]),
        Check("Karen reminder time parser", ["./scripts/val0py", "scripts/quality/karen_reminder_time_parser_smoke.py"]),
        Check("numbered reminder/task management", [py, "scripts/quality/karen_numbered_reminder_task_management_smoke.py"]),
        Check("vencidos reminder variants", [py, "scripts/quality/karen_reminder_vencidos_action_variants_smoke.py"]),
        Check("tomorrow agenda/task completion", [py, "scripts/quality/karen_tomorrow_agenda_task_completion_smoke.py"]),
        Check("task route priority", [py, "scripts/quality/karen_task_route_priority_smoke.py"]),
        Check("task data hygiene", [py, "scripts/quality/karen_task_data_hygiene_smoke.py"]),
        Check("document MVP RC", [py, "scripts/quality/karen_document_mvp_rc_smoke.py"]),
        Check("no-caption numbered docs", [py, "scripts/quality/karen_no_caption_numbered_docs_smoke.py"]),
        Check("document watermark guard", [py, "scripts/quality/karen_document_watermark_guard_smoke.py"]),
        Check("saved summary watermark guard", [py, "scripts/quality/karen_saved_summary_watermark_guard_smoke.py"]),
        Check("OCR spike script smoke", [py, "scripts/quality/ocr_spike_script_smoke.py"]),
        Check("OCR runtime smoke", [py, "scripts/quality/karen_ocr_runtime_smoke.py"]),
    ]


def _path_exists_for_check(check: Check) -> bool:
    if check.only_if_exists is not None:
        return check.only_if_exists.exists()
    script = check.cmd[-1] if check.cmd and check.cmd[-1].endswith(".py") else ""
    if script.startswith("scripts/quality/"):
        return (REPO_ROOT / script).exists()
    return True


def _run_check(check: Check) -> tuple[str, int]:
    if not _path_exists_for_check(check):
        return ("SKIPPED" if not check.required or check.only_if_exists else "MISSING", 0 if check.only_if_exists else 127)

    result = subprocess.run(
        check.cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    return ("PASS" if result.returncode == 0 else "FAIL", result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Karen RC smoke suite in a stable order.")
    parser.add_argument("--keep-going", action="store_true", help="Run all checks and summarize failures instead of stopping at the first failure.")
    args = parser.parse_args()

    failures: list[tuple[Check, int]] = []
    skipped: list[Check] = []

    print("Karen RC full smoke suite")
    print(f"Repo: {REPO_ROOT}")
    print("")

    for idx, check in enumerate(_checks(), start=1):
        print(f"[{idx:02d}] {check.label}")
        print("$ " + " ".join(check.cmd))
        status, code = _run_check(check)
        print(f"=> {status}")
        print("")

        if status == "SKIPPED":
            skipped.append(check)
            continue
        if status != "PASS":
            failures.append((check, code))
            if not args.keep_going:
                break

    print("Summary")
    if skipped:
        print(f"SKIPPED: {len(skipped)}")
        for check in skipped:
            print(f"- {check.label}")
    if failures:
        print(f"FAIL: {len(failures)}")
        for check, code in failures:
            print(f"- {check.label} (exit {code})")
        return 1

    print("PASS: Karen RC full smoke suite passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
