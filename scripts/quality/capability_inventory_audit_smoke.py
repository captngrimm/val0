#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs/architecture/CAPABILITY_INVENTORY_01_FORGOTTEN_ASSETS_AUDIT.md"
DESK = ROOT / "docs/architecture/CAPABILITY_INVENTORY_01_DESK_SOURCE_OF_TRUTH.md"
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
    assert_true(AUDIT.exists(), "capability inventory audit doc exists")
    assert_true(DESK.exists(), "capability inventory Desk doc exists")
    return AUDIT.read_text(encoding="utf-8") + "\n\n" + DESK.read_text(encoding="utf-8")


def test_required_categories() -> None:
    text = read_docs()
    required = (
        "Router / shadow / intent infrastructure",
        "LLM / fallback / response composition",
        "Memory / library / vault / persistence",
        "Adaptive intake / onboarding / founder-beta flows",
        "Calendar / reminders / pending confirmations",
        "Documents / OCR / Caso Finca / legal-admin workflows",
        "Voice / transcription / voice renderer",
        "n8n / Nathan / external automation",
        "Ops / Launchpad / Night Runner / OPEL / ValPrime continuity",
        "Product / sales / founder-beta / Ale/Karen setup kits",
        "Quality gates / smokes / diagnostics",
        "Deprecated, stale, duplicated, risky systems",
    )
    for needle in required:
        assert_contains(text, needle, f"inventory category {needle}")


def test_status_and_assimilation_concepts() -> None:
    text = read_docs()
    required = (
        "Runtime-active",
        "Shadow-only",
        "Diagnostic",
        "Docs-only",
        "Stale / historical / unknown",
        "Borg-Assimilation Candidates",
        "Do-Not-Rebuild Warnings",
        "Recommended Next 5 Lanes",
        "Source-of-Truth Desk Files",
        "Guardrails At Risk Of Being Forgotten",
        "Immediate Risks Found",
        "Recurring Audit Command",
    )
    for needle in required:
        assert_contains(text, needle, f"status/assimilation concept {needle}")


def test_key_assets_present() -> None:
    text = read_docs()
    required = (
        "core/intent_router_v2.py",
        "core/intent_router_v2_observer.py",
        "core/conversation_router.py",
        "core/intent_interpreter.py",
        "core/adaptive_intake.py",
        "core/onboarding_discovery.py",
        "core/memory_spine.py",
        "core/bounded_voice_renderer.py",
        "scripts/diagnostics/markdown_docs_inventory.py",
        "scripts/diagnostics/new_chat_recovery_brief.py",
        "scripts/quality/karen_rc_full_smoke.py",
        "scripts/quality/client_isolation_audit.py",
        "TOOL_ASSIMILATION_MAP",
        "OBSIDIAN_01_VAULT_ROLE_CLARIFICATION",
    )
    for needle in required:
        assert_contains(text, needle, f"key asset {needle}")


def test_guardrails_present() -> None:
    text = read_docs()
    for needle in (
        "Client isolation first",
        "Shadow mode default OFF",
        "Pending confirmations beat new intent",
        "Deterministic handlers execute",
        "LLM fallback last",
        "consent before saving",
        "No DB writes",
        "no client data edits",
        "no production restart",
        "no commits",
    ):
        assert_contains(text, needle, f"guardrail {needle}")


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
    test_required_categories()
    test_status_and_assimilation_concepts()
    test_key_assets_present()
    test_guardrails_present()
    test_protected_not_staged()
    print("PASS: capability inventory audit smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
