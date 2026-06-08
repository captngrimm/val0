#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "docs/architecture/LLM_ROUTER_01A_EXISTING_SHADOW_ROUTER_ASSIMILATION_PLAN.md"
PRODUCT = ROOT / "docs/product/LLM_ROUTER_01A_PERSONAL_OS_CONVERSATIONALITY_PATH.md"
CLIENT_ZERO_PATH = Path("clients") / "karen"
PROTECTED = (
    (CLIENT_ZERO_PATH / "CLIENT_FOLDERS.json").as_posix(),
    (CLIENT_ZERO_PATH / "CLIENT_GROCERY.md").as_posix(),
)


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r}")


def read_docs() -> str:
    assert_true(ARCH.exists(), "LLM router assimilation architecture doc exists")
    assert_true(PRODUCT.exists(), "LLM router product conversationality doc exists")
    return ARCH.read_text(encoding="utf-8") + "\n\n" + PRODUCT.read_text(encoding="utf-8")


def test_required_concepts() -> None:
    text = read_docs()
    required = (
        "intent_router_v2",
        "conversation_router",
        "intent_interpreter",
        "shadow mode",
        "sample harness",
        "adaptive intake",
        "memory spine",
        "LLM cannot execute",
        "deterministic handlers execute",
        "pending confirmations beat new intent",
        "LLM fallback last",
        "feature flag default OFF",
        "no DB writes",
        "no client data writes",
        "client isolation",
        "sample expansion",
        "response composer",
        "Personal OS",
    )
    for needle in required:
        assert_contains(text, needle, f"required LLM router concept {needle}")


def test_architecture_inventory() -> None:
    text = ARCH.read_text(encoding="utf-8")
    for needle in (
        "core/intent_router_v2.py",
        "core/intent_router_v2_observer.py",
        "core/conversation_router.py",
        "core/intent_interpreter.py",
        "scripts/ops/router_shadow_mode.sh",
        "scripts/diagnostics/intent_router_v2_sample_harness.py",
        "scripts/diagnostics/intent_router_v2_coverage_report.py",
        "LLM-ROUTER-01B",
        "LLM-CLASSIFIER-01",
        "OPERATOR-RESPONSE-01",
        "MEMORY-SPINE-01C",
        "route hijack",
        "stale context",
        "cross-client contamination",
    ):
        assert_contains(text, needle, f"architecture detail {needle}")


def test_product_path_examples() -> None:
    text = PRODUCT.read_text(encoding="utf-8")
    for needle in (
        "soy cajera en una tienda",
        "atiendo caja",
        "trabajo en retail",
        "tengo clientes que perseguir",
        "tengo papeles regados",
        "This is not AGI",
        "This is not autonomous execution",
        "one workflow first",
    ):
        assert_contains(text, needle, f"product path detail {needle}")


def test_protected_not_staged() -> None:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", *PROTECTED],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert_true(proc.stdout.strip() == "", "protected live data files are not staged")


def main() -> int:
    test_required_concepts()
    test_architecture_inventory()
    test_product_path_examples()
    test_protected_not_staged()
    print("PASS: LLM router assimilation plan smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
