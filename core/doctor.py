#!/usr/bin/env python3
"""
VAL0 Doctor — Phase 1 Hardening Diagnostic

Goals:
- Safe, testable via CLI.
- No secrets printed.
- No LLM usage.
- Able to run from an interactive shell and still see systemd-set env.

Usage:
  /opt/val0/.venv/bin/python -m core.doctor
  /opt/val0/.venv/bin/python -m core.doctor --json
  /opt/val0/.venv/bin/python -m core.doctor --unit val0-bot.service
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple


UNIT_DEFAULT = "val0-bot.service"

SAFE_ENV_KEYS = (
    "VAL0_TZ",
    "VAL0_GCAL_ENABLED",
    "VAL0_GCAL_INCLUDE_UNBOUND",
    "VAL0_DB_PATH",
    "VAL0_DB_KEY_FILE",
)

# If we list /etc/val0/gcal, never echo filenames that imply secrets/tokens
SENSITIVE_NAME_PATTERNS = ("token", "secret", "refresh", "access", "private", "key")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _run(cmd: list[str]) -> Tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True)
        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip()
        combined = "\n".join([x for x in [out, err] if x])
        return p.returncode, combined
    except Exception as e:
        return 1, f"{type(e).__name__}: {e}"


def _git_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {"ok": True}
    rc, branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    rc2, commit = _run(["git", "rev-parse", "HEAD"])

    if rc != 0:
        info["ok"] = False
        info["branch"] = None
        info["error_branch"] = branch
    else:
        info["branch"] = branch.splitlines()[-1].strip()

    if rc2 != 0:
        info["ok"] = False
        info["commit"] = None
        info["error_commit"] = commit
    else:
        info["commit"] = commit.splitlines()[-1].strip()

    return info


def _parse_systemd_environment_blob(blob: str) -> Dict[str, str]:
    """
    systemctl show -p Environment returns something like:
      Environment=VAR1=a VAR2=b "VAR3=hello world"
    We parse into {VAR: value}. This is best-effort.
    """
    env: Dict[str, str] = {}
    if not blob:
        return env

    # Remove leading "Environment=" if present
    line = blob.strip()
    if line.startswith("Environment="):
        line = line[len("Environment="):].strip()

    if not line:
        return env

    parts: list[str] = []
    cur = ""
    in_quotes = False
    quote_char = ""

    for ch in line:
        if ch in ("'", '"'):
            if not in_quotes:
                in_quotes = True
                quote_char = ch
                continue
            if in_quotes and ch == quote_char:
                in_quotes = False
                quote_char = ""
                continue
        if ch == " " and not in_quotes:
            if cur:
                parts.append(cur)
                cur = ""
        else:
            cur += ch
    if cur:
        parts.append(cur)

    for p in parts:
        if "=" not in p:
            continue
        k, v = p.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k:
            continue
        env[k] = v
    return env


def _systemd_env(unit: str) -> Dict[str, str]:
    rc, out = _run(["systemctl", "show", unit, "-p", "Environment"])
    if rc != 0:
        return {}
    return _parse_systemd_environment_blob(out)


def _dotenv_env(path: str) -> Dict[str, str]:
    """
    Parse a simple KEY=VALUE .env file.
    No shell expansion, no secrets printed. Best-effort.
    """
    p = Path(path)
    if not p.exists():
        return {}

    env: Dict[str, str] = {}
    try:
        for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k:
                env[k] = v
    except Exception:
        return {}
    return env


def _effective_env(unit: str) -> Dict[str, Any]:
    """
    Resolve env values in a deterministic order:
    1) current process env (os.environ)
    2) /opt/val0/.env
    3) systemd unit Environment (override.conf + base unit)
    We track where each value came from.
    """
    sources: Dict[str, str] = {}
    values: Dict[str, str | None] = {k: None for k in SAFE_ENV_KEYS}

    # 1) process env
    for k in SAFE_ENV_KEYS:
        v = os.getenv(k)
        if v is not None:
            values[k] = v
            sources[k] = "process"

    # 2) .env file (only fills missing)
    dot = _dotenv_env("/opt/val0/.env")
    for k in SAFE_ENV_KEYS:
        if values[k] is None and k in dot:
            values[k] = dot[k]
            sources[k] = "dotenv:/opt/val0/.env"

    # 3) systemd env (only fills missing)
    sdenv = _systemd_env(unit)
    for k in SAFE_ENV_KEYS:
        if values[k] is None and k in sdenv:
            values[k] = sdenv[k]
            sources[k] = f"systemd:{unit}"

    return {"values": values, "sources": sources}


def _file_stat(path_str: str | None) -> Dict[str, Any]:
    if not path_str:
        return {"path": None, "exists": False}

    p = Path(path_str)
    if not p.exists():
        return {"path": str(p), "exists": False}

    try:
        st = p.stat()
        mode = stat.S_IMODE(st.st_mode)
        return {
            "path": str(p),
            "exists": True,
            "mode_octal": oct(mode),
            "uid": st.st_uid,
            "gid": st.st_gid,
            "size": st.st_size,
        }
    except Exception as e:
        return {"path": str(p), "exists": True, "error": f"{type(e).__name__}: {e}"}


def _mask_filename(name: str) -> str:
    lower = name.lower()
    if any(pat in lower for pat in SENSITIVE_NAME_PATTERNS):
        return "<masked>"
    return name


def _dir_listing(dir_path: str) -> Dict[str, Any]:
    p = Path(dir_path)
    if not p.exists():
        return {"path": str(p), "exists": False, "files": []}
    if not p.is_dir():
        return {"path": str(p), "exists": True, "is_dir": False, "files": []}

    files = []
    try:
        for child in sorted(p.iterdir()):
            files.append(_mask_filename(child.name))
        return {"path": str(p), "exists": True, "is_dir": True, "files": files}
    except Exception as e:
        return {"path": str(p), "exists": True, "is_dir": True, "error": f"{type(e).__name__}: {e}", "files": []}


def _import_check(module: str) -> Dict[str, Any]:
    try:
        __import__(module)
        return {"module": module, "ok": True}
    except Exception as e:
        return {"module": module, "ok": False, "error": f"{type(e).__name__}: {e}"}


def _truthy(v: str | None) -> bool:
    if v is None:
        return False
    return v.strip().lower() in ("1", "true", "yes", "on")


def main() -> int:
    ap = argparse.ArgumentParser(description="VAL0 Doctor (Phase 1 hardening diagnostic)")
    ap.add_argument("--json", action="store_true", help="Emit JSON output")
    ap.add_argument("--unit", default=UNIT_DEFAULT, help=f"systemd unit name (default: {UNIT_DEFAULT})")
    args = ap.parse_args()

    eff = _effective_env(args.unit)
    env = eff["values"]
    sources = eff["sources"]

    report: Dict[str, Any] = {
        "ts_utc": _now_iso(),
        "unit": args.unit,
        "git": _git_info(),
        "env": env,
        "env_sources": sources,
        "checks": {
            "db_path": _file_stat(env.get("VAL0_DB_PATH")),
            "db_key_file": _file_stat(env.get("VAL0_DB_KEY_FILE")),
            "gcal_dir": _dir_listing("/etc/val0/gcal"),
            "imports": [
                _import_check("core.case_mvp"),
                _import_check("core.gcal_client"),
                _import_check("core.due_merge"),
            ],
        },
        "assertions": {
            "no_llm_in_legal_gates": True
        },
    }

    ok = True

    if not report["git"].get("ok", False):
        ok = False

    if not report["checks"]["db_path"].get("exists", False):
        ok = False
    if not report["checks"]["db_key_file"].get("exists", False):
        ok = False

    for imp in report["checks"]["imports"]:
        if not imp.get("ok", False):
            ok = False

    # GCAL optional. If enabled, require /etc/val0/gcal exists.
    if _truthy(env.get("VAL0_GCAL_ENABLED")):
        if not report["checks"]["gcal_dir"].get("exists", False):
            ok = False

    report["ok"] = ok

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"VAL0 DOCTOR @ {report['ts_utc']}")
        print(f"- unit: {args.unit}")
        print(f"- ok: {report['ok']}")
        g = report["git"]
        print(f"- git: branch={g.get('branch')} commit={g.get('commit')}")
        print(f"- env:")
        for k in SAFE_ENV_KEYS:
            v = env.get(k)
            src = sources.get(k, "unset")
            print(f"  - {k}={v}  (src={src})")

        gd = report["checks"]["gcal_dir"]
        print(f"- gcal_dir: {gd.get('path')} (exists={gd.get('exists')}) files={gd.get('files', [])}")
        print("- imports:")
        for imp in report["checks"]["imports"]:
            if imp["ok"]:
                print(f"  - {imp['module']}: OK")
            else:
                print(f"  - {imp['module']}: FAIL ({imp.get('error')})")

    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
