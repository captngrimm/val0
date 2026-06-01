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
        "A  docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md",
        "?? docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md",
        "A  scripts/diagnostics/route_inventory.py",
        "?? scripts/diagnostics/route_inventory.py",
        "A  scripts/quality/intent_router_v2_docs_smoke.py",
        "?? scripts/quality/intent_router_v2_docs_smoke.py",
        "A  scripts/quality/intent_router_v2_shadow_smoke.py",
        "?? scripts/quality/intent_router_v2_shadow_smoke.py",
        " M scripts/diagnostics/route_inventory.py",
        " M scripts/quality/intent_router_v2_docs_smoke.py",
        " M scripts/quality/intent_router_v2_shadow_smoke.py",
        " M docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md",
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
