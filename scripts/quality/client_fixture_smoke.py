#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.intent_interpreter import interpret_user_intent  # noqa: E402


REQUIRED_CASE_KEYS = {"id", "input"}


def _load_fixture(path: Path) -> list[dict[str, Any]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AssertionError(f"{path}: invalid JSON: {exc}") from exc

    if isinstance(raw, dict) and isinstance(raw.get("cases"), list):
        cases = raw["cases"]
    elif isinstance(raw, list):
        cases = raw
    else:
        raise AssertionError(f"{path}: fixture must be a JSON list or an object with a cases list")

    normalized: list[dict[str, Any]] = []
    for idx, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise AssertionError(f"{path}: case {idx} must be an object")
        missing = REQUIRED_CASE_KEYS - set(case)
        if missing:
            raise AssertionError(f"{path}: case {idx} missing required keys: {sorted(missing)}")
        normalized.append(case)
    return normalized


def _default_fixture_paths(client: str) -> list[Path]:
    fixture_dir = ROOT / "tests" / "fixtures" / client
    if not fixture_dir.exists():
        raise AssertionError(f"missing fixture directory: {fixture_dir}")
    paths = sorted(fixture_dir.glob("*.json"))
    if not paths:
        raise AssertionError(f"no JSON fixtures found under: {fixture_dir}")
    return paths


def _result_fields_blob(result: dict[str, Any]) -> str:
    return json.dumps(result.get("fields") or {}, ensure_ascii=False, sort_keys=True).lower()


def _check_case(case: dict[str, Any], *, client_id: str) -> tuple[str, str]:
    case_id = str(case["id"])
    text = str(case["input"])
    expected_intent = case.get("expected_intent")
    expected_route_hint = case.get("expected_route_hint")
    expected_contains = [str(item).lower() for item in case.get("expected_contains") or []]
    expected_not_contains = [str(item).lower() for item in case.get("expected_not_contains") or []]
    xfail = bool(case.get("xfail"))

    result = interpret_user_intent(text, client_id=client_id, pending_state=case.get("pending_state"))
    fields_blob = _result_fields_blob(result)
    failures: list[str] = []

    if expected_intent and result.get("intent") != expected_intent:
        failures.append(f"intent expected {expected_intent!r}, got {result.get('intent')!r}")
    if expected_route_hint and result.get("route_hint") != expected_route_hint:
        failures.append(f"route_hint expected {expected_route_hint!r}, got {result.get('route_hint')!r}")

    for needle in expected_contains:
        if needle not in fields_blob:
            failures.append(f"fields missing {needle!r}")
    for needle in expected_not_contains:
        if needle in fields_blob:
            failures.append(f"fields unexpectedly contain {needle!r}")

    if failures:
        detail = "; ".join(failures)
        if xfail:
            return "XFAIL", f"{case_id}: {detail}"
        return "FAIL", f"{case_id}: {detail}"

    if xfail:
        return "XPASS", f"{case_id}: expected failure now passes; update fixture TODO"
    return "PASS", f"{case_id}: {result.get('intent')} route={result.get('route_hint')}"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run fixture-based Intent Interpreter client smoke cases.")
    parser.add_argument("--client", default="karen", help="Client fixture name and interpreter client_id. Default: karen")
    parser.add_argument(
        "--fixture",
        action="append",
        default=[],
        help="Specific fixture JSON path. May be passed more than once. Defaults to tests/fixtures/<client>/*.json",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    paths = [Path(item) for item in args.fixture] if args.fixture else _default_fixture_paths(str(args.client))

    case_count = 0
    pass_count = 0
    xfail_count = 0
    xpass_count = 0
    failures: list[str] = []

    print(f"Client fixture smoke: client={args.client}")
    for path in paths:
        resolved = path if path.is_absolute() else ROOT / path
        cases = _load_fixture(resolved)
        print(f"\nFixture: {resolved.relative_to(ROOT) if resolved.is_relative_to(ROOT) else resolved}")
        for case in cases:
            case_count += 1
            status, message = _check_case(case, client_id=str(args.client))
            print(f"{status}: {message}")
            if status == "PASS":
                pass_count += 1
            elif status == "XFAIL":
                xfail_count += 1
            elif status == "XPASS":
                xpass_count += 1
            else:
                failures.append(message)

    print("\nSummary")
    print(f"cases={case_count} pass={pass_count} xfail={xfail_count} xpass={xpass_count} fail={len(failures)}")
    if failures:
        print("FAIL: client fixture smoke found mismatches.")
        return 1
    print("PASS: client fixture smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
