#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

KEY_DOCS = (
    "docs/product/VAL0_MASTER_MILESTONE_MAP.md",
    "docs/product/VAL0_SOURCE_OF_TRUTH_INDEX.md",
    "docs/product/KAREN_RC_STATUS_MAP.md",
    "docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md",
    "docs/architecture/OBSIDIAN_01_VAULT_ROLE_CLARIFICATION.md",
    "docs/ops/VAL0_SESSION_STARTUP_CHECKLIST.md",
)


def _run(args: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)


def _print_command(title: str, args: list[str]) -> int:
    print(f"\n## {title}")
    print("$ " + " ".join(args))
    result = _run(args)
    output = (result.stdout or "").strip()
    error = (result.stderr or "").strip()
    if output:
        print(output)
    if error:
        print(error)
    print(f"=> exit {result.returncode}")
    return int(result.returncode)


def _print_git_state() -> None:
    _print_command("Branch / status", ["git", "status", "-sb"])
    _print_command("Recent commits", ["git", "log", "--oneline", "-12"])


def _print_docs() -> None:
    print("\n## Source-of-truth docs")
    for rel in KEY_DOCS:
        path = ROOT / rel
        state = "OK" if path.exists() else "MISSING"
        print(f"- {state}: {rel}")


def _print_shadow_guidance() -> None:
    print("\n## Shadow mode guidance")
    print("Intent Router v2 shadow mode should be OFF unless a short observation window is active.")
    print("Inspect without changing state:")
    print("$ bash scripts/ops/router_shadow_mode.sh status")
    print("Do not enable or disable shadow from this diagnostic helper.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Print Val0 source-of-truth and recovery-pack status.")
    parser.add_argument("--full", action="store_true", help="Also run the Karen RC full smoke suite.")
    args = parser.parse_args()

    print("Val0 source-of-truth check")
    print(f"Repo: {ROOT}")
    _print_git_state()
    _print_docs()

    coverage_rc = _print_command(
        "Intent Router v2 coverage report",
        ["python3", "scripts/diagnostics/intent_router_v2_coverage_report.py"],
    )
    _print_shadow_guidance()

    full_rc = 0
    if args.full:
        full_rc = _print_command(
            "Karen RC full smoke",
            ["python3", "scripts/quality/karen_rc_full_smoke.py", "--keep-going"],
        )
    else:
        print("\n## Karen RC full smoke")
        print("SKIPPED by default. Run with --full to execute:")
        print("$ python3 scripts/diagnostics/val0_source_of_truth_check.py --full")

    return 0 if coverage_rc == 0 and full_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
