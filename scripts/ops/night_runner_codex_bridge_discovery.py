#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
PROTECTED_LIVE_FILES = (
    "clients/karen/CLIENT_GROCERY.md",
    "clients/karen/CLIENT_FOLDERS.json",
)
NIGHT_RUNNER_FILES = (
    "scripts/ops/night_runner_dry_run.py",
    "docs/ops/NIGHT_RUNNER_BEDTIME_WORKFLOW.md",
    "docs/ops/NIGHT_RUNNER_V0_DRY_RUN_DESIGN.md",
    "docs/ops/night_runner_bedtime_packet.yaml",
)
COMMON_CODEX_LOCATIONS = (
    "/usr/local/bin/codex",
    "/usr/bin/codex",
    "/opt/homebrew/bin/codex",
)


def _run_git(args: list[str]) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except Exception as exc:
        return f"(git unavailable: {exc})"
    return (proc.stdout or proc.stderr or "").strip()


def _safe_bool(value: bool) -> str:
    return "yes" if value else "no"


def _find_codex_binary(*, path_search: str | None, codex_home: Path, include_common_locations: bool = True) -> str:
    found = shutil.which("codex", path=path_search)
    if found:
        return found
    if not include_common_locations:
        return ""
    candidates = [Path(item) for item in COMMON_CODEX_LOCATIONS]
    candidates.append(codex_home.parent / ".local" / "bin" / "codex")
    candidates.append(Path.home() / ".local" / "bin" / "codex")
    for candidate in candidates:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return ""


def _status_for_protected_files(status: str) -> dict[str, str]:
    result = {path: "clean-or-unreported" for path in PROTECTED_LIVE_FILES}
    for line in status.splitlines():
        if line.startswith("##") or len(line) < 4:
            continue
        code = line[:2]
        path = line[3:].strip() if line[2] == " " else line[2:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        if path in result:
            result[path] = f"dirty/staged code={code}"
    return result


def discover(
    *,
    codex_home: str | Path | None = None,
    path_search: str | None = None,
    include_common_locations: bool = True,
) -> dict[str, object]:
    home = Path(codex_home).expanduser() if codex_home else Path.home() / ".codex"
    codex_binary = _find_codex_binary(
        path_search=path_search,
        codex_home=home,
        include_common_locations=include_common_locations,
    )
    codex_dir_exists = home.exists() and home.is_dir()
    auth_present = (home / "auth.json").exists()
    config_present = (home / "config.toml").exists()
    config_enough = codex_dir_exists and (auth_present or config_present)
    branch = _run_git(["branch", "--show-current"]) or "(unknown)"
    head = _run_git(["rev-parse", "--short", "HEAD"]) or "(unknown)"
    status = _run_git(["status", "--short", "--branch"]) or "(no output)"

    if codex_binary and config_enough:
        decision = "CODEX_LOCAL_READY"
        next_path = "Use a future branch-only dry-run lane to test a no-op Codex invocation packet."
    elif config_enough and not codex_binary:
        decision = "CODEX_CONFIG_PRESENT_BUT_BIN_MISSING"
        next_path = "Repair/install Codex CLI locally, or use Codex cloud/manual task bridge while Night Runner stays diagnostics-only."
    elif not codex_dir_exists:
        decision = "CODEX_NOT_CONFIGURED"
        next_path = "Configure Codex auth locally or keep Night Runner in diagnostics-only mode."
    else:
        decision = "NIGHT_RUNNER_DIAGNOSTICS_ONLY"
        next_path = "Keep using Night Runner for diagnostics/reporting until Codex binary and config are both ready."

    return {
        "decision": decision,
        "codex_binary": codex_binary,
        "codex_home": str(home),
        "codex_dir_exists": codex_dir_exists,
        "auth_json_present": auth_present,
        "config_toml_present": config_present,
        "node": shutil.which("node", path=path_search) or "",
        "npm": shutil.which("npm", path=path_search) or "",
        "npx": shutil.which("npx", path=path_search) or "",
        "night_runner_files": {path: (ROOT / path).exists() for path in NIGHT_RUNNER_FILES},
        "branch": branch,
        "head": head,
        "git_status": status,
        "protected_live_files": _status_for_protected_files(status),
        "tmp_night_runner_exists": (ROOT / "tmp" / "night_runner").exists(),
        "tmp_night_runner_writable": os.access(ROOT / "tmp" / "night_runner", os.W_OK),
        "next_path": next_path,
    }


def render_report(data: dict[str, object]) -> str:
    night_runner_files = data["night_runner_files"]
    protected = data["protected_live_files"]
    assert isinstance(night_runner_files, dict)
    assert isinstance(protected, dict)
    lines = [
        "Night Runner Codex Bridge Discovery",
        "===================================",
        "",
        f"Decision: {data['decision']}",
        "",
        "Codex local invocation:",
        f"- codex binary available: {_safe_bool(bool(data['codex_binary']))}",
        f"- codex binary path: {data['codex_binary'] or '(not found)'}",
        f"- ~/.codex directory present: {_safe_bool(bool(data['codex_dir_exists']))}",
        f"- auth.json present: {_safe_bool(bool(data['auth_json_present']))}",
        f"- config.toml present: {_safe_bool(bool(data['config_toml_present']))}",
        "- secret contents printed: no",
        "",
        "Node tooling:",
        f"- node: {data['node'] or '(not found)'}",
        f"- npm: {data['npm'] or '(not found)'}",
        f"- npx: {data['npx'] or '(not found)'}",
        "",
        "Night Runner files:",
    ]
    for path, exists in night_runner_files.items():
        lines.append(f"- {path}: {'present' if exists else 'missing'}")

    lines.extend(
        [
            "",
            "Repo:",
            f"- branch: {data['branch']}",
            f"- head: {data['head']}",
            "- git status:",
        ]
    )
    lines.extend(f"  {line}" for line in str(data["git_status"]).splitlines())
    lines.extend(["", "Protected live files:"])
    for path, status in protected.items():
        lines.append(f"- {path}: {status} (reported only; not modified)")
    lines.extend(
        [
            "",
            "Workspace report area:",
            f"- tmp/night_runner exists: {_safe_bool(bool(data['tmp_night_runner_exists']))}",
            f"- tmp/night_runner writable: {_safe_bool(bool(data['tmp_night_runner_writable']))}",
            "",
            "Next recommended safe path:",
            f"- {data['next_path']}",
            "",
            "Safety:",
            "- This script did not run Codex on a task.",
            "- This script did not read or print auth.json/config.toml contents.",
            "- This script did not write reports unless a future explicit flag adds that behavior.",
            "- This script did not touch protected live client data.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely discover whether Night Runner can bridge to local Codex.")
    parser.add_argument("--codex-home", help="Override Codex config directory for tests. Contents are never printed.")
    parser.add_argument("--path-search", help="Override PATH search string for tests.")
    parser.add_argument(
        "--ignore-common-locations",
        action="store_true",
        help="Test hook: only use PATH search, not common Codex install locations.",
    )
    args = parser.parse_args(argv)
    print(
        render_report(
            discover(
                codex_home=args.codex_home,
                path_search=args.path_search,
                include_common_locations=not args.ignore_common_locations,
            )
        ),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
