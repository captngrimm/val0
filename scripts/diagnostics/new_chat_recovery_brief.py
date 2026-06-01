#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

KEY_DOCS = (
    "docs/product/VAL0_MASTER_MILESTONE_MAP.md",
    "docs/product/VAL0_SOURCE_OF_TRUTH_INDEX.md",
    "docs/ops/VAL0_SESSION_STARTUP_CHECKLIST.md",
    "docs/product/VAL0_DOCS_VALUE_MAP.md",
    "docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md",
    "docs/product/ROADMAP_02_VALPRIME_SIGNAL_PROTOCOL.md",
    "docs/product/ROADMAP_03_SIGNAL_REGISTRY_STORAGE_DESIGN.md",
    "docs/architecture/OBSIDIAN_01_VAULT_ROLE_CLARIFICATION.md",
    "docs/ops/NEWCHAT_01_RECOVERY_PROTOCOL.md",
    "docs/ops/NEWCHAT_BRIDGE_PROMPT.md",
)


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def _one_line(args: list[str]) -> str:
    result = _run(args)
    text = (result.stdout or result.stderr or "").strip()
    return text.splitlines()[0] if text else f"exit {result.returncode}"


def _extract_active_milestone() -> str:
    path = ROOT / "docs/product/VAL0_MASTER_MILESTONE_MAP.md"
    if not path.exists():
        return "unknown: master milestone map missing"
    text = path.read_text(encoding="utf-8")
    match = re.search(r"The active lane is\s+([^.\n]+)", text)
    if match:
        return match.group(1).strip()
    for line in text.splitlines():
        if "| M45 " in line and "ACTIVE" in line:
            return "M45 Router Coverage / Observation"
    return "unknown: active lane not found"


def _coverage_summary() -> str:
    result = _run(["python3", "scripts/diagnostics/intent_router_v2_coverage_report.py"])
    if result.returncode != 0:
        return f"coverage report failed: {(result.stderr or '').strip()}"
    lines = []
    keep = False
    for line in result.stdout.splitlines():
        if line.strip() == "Summary:":
            keep = True
            continue
        if keep and line.strip():
            lines.append(line.strip())
    return "; ".join(lines) if lines else "coverage summary unavailable"


def _full_smoke() -> int:
    result = _run(["python3", "scripts/quality/karen_rc_full_smoke.py", "--keep-going"])
    print("\n## Karen RC full smoke")
    print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    print(f"=> exit {result.returncode}")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a compact Val0 new-chat recovery brief.")
    parser.add_argument("--full", action="store_true", help="Also run Karen RC full smoke.")
    args = parser.parse_args()

    branch = _one_line(["git", "branch", "--show-current"])
    head = _one_line(["git", "rev-parse", "--short", "HEAD"])
    status = _run(["git", "status", "-sb"]).stdout.strip()

    print("Val0 new chat recovery brief")
    print(f"Repo: {ROOT}")
    print(f"Branch: {branch}")
    print(f"Head: {head}")
    print("Status:")
    print(status)
    print(f"Active milestone: {_extract_active_milestone()}")
    print(f"Router coverage: {_coverage_summary()}")

    print("\nKey docs:")
    missing = 0
    for rel in KEY_DOCS:
        exists = (ROOT / rel).exists()
        missing += 0 if exists else 1
        print(f"- {'OK' if exists else 'MISSING'}: {rel}")

    print("\nContinuity:")
    print("- Ask for ValPrime /continuity or natural new chat bundle when available.")
    print("- Desk / Side Table / Library Index / Vault model is the human continuity layer.")
    print("- This helper verifies repo source-of-truth; it does not replace ValPrime.")

    print("\nNext suggested command:")
    if args.full:
        rc = _full_smoke()
    else:
        rc = 0
        print("python3 scripts/diagnostics/val0_source_of_truth_check.py")
        print("Use --full here only if runtime work is in scope.")

    print("\nStop conditions:")
    print("- unexpected dirty runtime/client files")
    print("- ValPrime continuity conflicts with repo source-of-truth")
    print("- shadow mode ON unexpectedly")
    print("- Karen RC full smoke fails before runtime work")

    return 0 if missing == 0 and rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
