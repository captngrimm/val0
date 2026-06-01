#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "architecture" / "INTENT_ROUTER_V2_MARCHING_ORDER.md"
INVENTORY = ROOT / "scripts" / "diagnostics" / "route_inventory.py"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def test_doc_exists_and_contains_priority_order() -> None:
    assert_true(DOC.exists(), "architecture doc exists")
    text = DOC.read_text(encoding="utf-8")
    required = [
        "1. Pending actions",
        "2. Destructive confirmations",
        "3. Direct utilities",
        "4. Documents / OCR",
        "5. Case/finca/legal context",
        "6. Memory capture",
        "7. LLM fallback",
        "shadow mode",
        "karen_rc_full_smoke.py",
        "IntentCandidate",
        "IntentDecision",
        "RouterPriorityMap",
    ]
    for needle in required:
        assert_contains(text, needle, "architecture doc content")


def test_route_inventory_script_compiles_and_has_categories() -> None:
    assert_true(INVENTORY.exists(), "route inventory script exists")
    source = INVENTORY.read_text(encoding="utf-8")
    for needle in [
        "maybe_handle_",
        "_looks_like_",
        "MEMORY_TEST_TEXT",
        "pending actions / confirmations",
        "agenda / Google Calendar",
        "documents / OCR",
        "generic/LLM fallback",
        "tmp/route_inventory/route_inventory.txt",
    ]:
        assert_contains(source, needle, "route inventory script content")

    result = subprocess.run(
        ["./scripts/val0py", "-m", "py_compile", "scripts/diagnostics/route_inventory.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"route inventory compiles: {result.stderr}")


def test_runtime_behavior_files_not_modified() -> None:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, "git status succeeded")
    allowed_prefixes = (
        " M clients/karen/CLIENT_GROCERY.md",
        " M bot.py",
        "A  core/intent_router_v2.py",
        "?? core/intent_router_v2.py",
        " M core/intent_router_v2.py",
        "A  core/intent_router_v2_observer.py",
        "?? core/intent_router_v2_observer.py",
        " M core/intent_router_v2_observer.py",
        "A  docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md",
        "?? docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md",
        "A  scripts/diagnostics/intent_router_v2_sample_harness.py",
        "?? scripts/diagnostics/intent_router_v2_sample_harness.py",
        "A  scripts/diagnostics/intent_router_v2_observer_demo.py",
        "?? scripts/diagnostics/intent_router_v2_observer_demo.py",
        " M scripts/diagnostics/intent_router_v2_observer_demo.py",
        "A  scripts/diagnostics/route_inventory.py",
        "?? scripts/diagnostics/route_inventory.py",
        "A  scripts/quality/intent_router_v2_docs_smoke.py",
        "?? scripts/quality/intent_router_v2_docs_smoke.py",
        "A  scripts/quality/intent_router_v2_observer_smoke.py",
        "?? scripts/quality/intent_router_v2_observer_smoke.py",
        " M scripts/quality/intent_router_v2_observer_smoke.py",
        "A  scripts/quality/intent_router_v2_sample_harness_smoke.py",
        "?? scripts/quality/intent_router_v2_sample_harness_smoke.py",
        "A  scripts/quality/intent_router_v2_shadow_smoke.py",
        "?? scripts/quality/intent_router_v2_shadow_smoke.py",
        " M scripts/diagnostics/intent_router_v2_sample_harness.py",
        " M scripts/diagnostics/route_inventory.py",
        " M scripts/quality/intent_router_v2_docs_smoke.py",
        " M scripts/quality/intent_router_v2_sample_harness_smoke.py",
        " M scripts/quality/intent_router_v2_shadow_smoke.py",
        " M docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md",
        "A  docs/ops/ROUTER_05_SHADOW_OBSERVATION_PLAYBOOK.md",
        "?? docs/ops/ROUTER_05_SHADOW_OBSERVATION_PLAYBOOK.md",
        " M docs/ops/ROUTER_05_SHADOW_OBSERVATION_PLAYBOOK.md",
        "A  scripts/ops/router_shadow_mode.sh",
        "?? scripts/ops/router_shadow_mode.sh",
        " M scripts/ops/router_shadow_mode.sh",
        "?? scripts/ops/",
        "A  scripts/quality/router_shadow_playbook_smoke.py",
        "?? scripts/quality/router_shadow_playbook_smoke.py",
        " M scripts/quality/router_shadow_playbook_smoke.py",
        " M scripts/quality/intent_router_v2_observer_smoke.py",
        "A  docs/architecture/ROUTER_07_SHADOW_OBSERVATION_REPORT.md",
        "?? docs/architecture/ROUTER_07_SHADOW_OBSERVATION_REPORT.md",
        "A  scripts/quality/router_shadow_observation_report_smoke.py",
        "?? scripts/quality/router_shadow_observation_report_smoke.py",
        " M docs/architecture/ROUTER_07_SHADOW_OBSERVATION_REPORT.md",
        " M core/intent_router_v2.py",
        " M scripts/diagnostics/intent_router_v2_sample_harness.py",
        " M scripts/quality/intent_router_v2_sample_harness_smoke.py",
        "A  docs/architecture/ROUTER_09_COVERAGE_GAP_REPORT.md",
        "?? docs/architecture/ROUTER_09_COVERAGE_GAP_REPORT.md",
        " M docs/architecture/ROUTER_09_COVERAGE_GAP_REPORT.md",
        "A  scripts/diagnostics/intent_router_v2_coverage_report.py",
        "?? scripts/diagnostics/intent_router_v2_coverage_report.py",
        " M scripts/diagnostics/intent_router_v2_coverage_report.py",
        "A  scripts/quality/intent_router_v2_coverage_report_smoke.py",
        "?? scripts/quality/intent_router_v2_coverage_report_smoke.py",
        " M scripts/quality/intent_router_v2_coverage_report_smoke.py",
        "A  docs/architecture/ROUTER_12_POST_OBSERVATION_COVERAGE_UPDATE.md",
        "?? docs/architecture/ROUTER_12_POST_OBSERVATION_COVERAGE_UPDATE.md",
        "A  scripts/quality/intent_router_v2_post_observation_coverage_smoke.py",
        "?? scripts/quality/intent_router_v2_post_observation_coverage_smoke.py",
        "A  docs/architecture/ROUTER_14_FINAL_SHADOW_COVERAGE_UPDATE.md",
        "?? docs/architecture/ROUTER_14_FINAL_SHADOW_COVERAGE_UPDATE.md",
        "A  scripts/quality/intent_router_v2_router14_coverage_smoke.py",
        "?? scripts/quality/intent_router_v2_router14_coverage_smoke.py",
    )
    for raw in result.stdout.splitlines():
        if not raw.strip():
            continue
        assert_true(
            raw.startswith(allowed_prefixes),
            f"unexpected runtime/non-doc change in status: {raw}",
        )


def main() -> int:
    test_doc_exists_and_contains_priority_order()
    test_route_inventory_script_compiles_and_has_categories()
    test_runtime_behavior_files_not_modified()
    print("PASS: Intent Router v2 docs smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
