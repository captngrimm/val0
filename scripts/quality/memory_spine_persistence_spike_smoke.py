#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TMP_FIXTURE_DIR = ROOT / "tmp" / "memory_spine_spike" / "smoke"
CLIENT_ZERO_PATH = Path("clients") / "karen"
PROTECTED_FOLDERS = CLIENT_ZERO_PATH / "CLIENT_FOLDERS.json"
PROTECTED_GROCERY = CLIENT_ZERO_PATH / "CLIENT_GROCERY.md"
PROTECTED = (
    PROTECTED_FOLDERS.as_posix(),
    PROTECTED_GROCERY.as_posix(),
)

import sys

sys.path.insert(0, str(ROOT))

from core.memory_spine import (  # noqa: E402
    DEFAULT_FIXTURE_DIR,
    MEMORY_SPINE_ENABLED_DEFAULT,
    MemorySpineError,
    build_memory_index_fixture,
    confirm_memory_candidate,
    create_memory_candidate,
    is_memory_spine_enabled,
    load_confirmed_memory_fixture,
    write_confirmed_memory_fixture,
)


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r}")


def assert_raises(fn, label: str) -> None:
    try:
        fn()
    except MemorySpineError:
        return
    raise AssertionError(label)


def _clean_tmp_fixture() -> None:
    if TMP_FIXTURE_DIR.exists():
        shutil.rmtree(TMP_FIXTURE_DIR)


def test_feature_disabled_by_default() -> None:
    assert_true(MEMORY_SPINE_ENABLED_DEFAULT is False, "feature constant disabled by default")
    assert_true(is_memory_spine_enabled({}) is False, "feature env disabled by default")
    assert_true(is_memory_spine_enabled({"VAL0_MEMORY_SPINE_EXPERIMENTAL": "1"}) is True, "feature can be enabled only explicitly")


def test_confirmed_memory_fixture_flow() -> None:
    _clean_tmp_fixture()
    candidate = create_memory_candidate(
        client_id="fixture_client_001",
        user_id="fixture_user_001",
        title="Daily Operator fixture setup",
        summary="Fixture user confirmed a daily review with agenda, tasks, reminders, and undated pending items.",
        linked_workflow="daily_operator",
        retrieval_tags=["daily_review", "workflow_profile", "fixture_only"],
        privacy_boundary_summary="No messages, reminders, calendar events, or tasks are created without confirmation.",
    )

    assert_true(candidate["memory_type"] == "memory_candidate", "candidate memory_type")
    assert_true(candidate["consent_status"] == "proposed", "candidate starts proposed")
    assert_true(candidate["confirmed_by_user"] is False, "candidate not confirmed")
    assert_true(candidate["privacy_boundary"]["memory_type"] == "privacy_boundary", "candidate includes privacy boundary")
    assert_true(candidate["sensitivity"] == "moderate", "candidate includes sensitivity")
    assert_true("daily_review" in candidate["retrieval_tags"], "candidate includes retrieval tags")

    assert_raises(
        lambda: confirm_memory_candidate(candidate, consent_status="proposed", confirmed_by_user=True),
        "cannot confirm with proposed consent",
    )
    assert_raises(
        lambda: confirm_memory_candidate(candidate, consent_status="confirmed", confirmed_by_user=False),
        "cannot confirm without confirmed_by_user",
    )
    assert_raises(
        lambda: write_confirmed_memory_fixture(candidate, TMP_FIXTURE_DIR),
        "cannot save unconfirmed candidate",
    )

    confirmed = confirm_memory_candidate(candidate, consent_status="confirmed", confirmed_by_user=True)
    assert_true(confirmed["memory_type"] == "workflow_profile", "confirmed memory becomes workflow profile")
    assert_true(confirmed["consent_status"] == "confirmed", "confirmed consent status")
    assert_true(confirmed["confirmed_by_user"] is True, "confirmed by user")
    assert_true("confirmed_memory" in confirmed["retrieval_tags"], "confirmed memory retrieval tag")
    assert_true(confirmed["privacy_boundary"]["consent_status"] == "confirmed", "confirmed privacy boundary")
    assert_true(confirmed["audit_event"]["memory_type"] == "audit_event", "confirmed includes audit event")

    path = write_confirmed_memory_fixture(confirmed, TMP_FIXTURE_DIR)
    assert_true(path.exists(), "confirmed fixture written")
    assert_true(TMP_FIXTURE_DIR in path.parents, "fixture written under tmp memory spine path")
    assert_not_contains(path.as_posix(), "/clients/", "fixture path not under clients")
    assert_not_contains(path.as_posix(), "val0_memory", "fixture path not production db")

    loaded = load_confirmed_memory_fixture(confirmed["id"], TMP_FIXTURE_DIR)
    assert_true(loaded["id"] == confirmed["id"], "loaded fixture matches confirmed id")
    index = build_memory_index_fixture([loaded], TMP_FIXTURE_DIR)
    assert_true(index["entries"], "memory index entries created")
    entry = index["entries"][0]
    assert_true(entry["memory_type"] == "memory_index_entry", "index entry memory type")
    assert_true(entry["client_id"] == "fixture_client_001", "index scoped to fixture client")
    assert_true(entry["user_id"] == "fixture_user_001", "index scoped to fixture user")
    assert_true("daily_review" in entry["retrieval_tags"], "index preserves retrieval tags")
    assert_true((TMP_FIXTURE_DIR / "memory_index.json").exists(), "index fixture file exists")


def test_storage_guards_and_no_raw_secrets() -> None:
    candidate = create_memory_candidate(
        client_id="fixture_client_001",
        user_id="fixture_user_001",
        title="Fixture setup",
        summary="Fixture user wants a daily review.",
    )
    confirmed = confirm_memory_candidate(candidate, consent_status="confirmed", confirmed_by_user=True)
    assert_raises(
        lambda: write_confirmed_memory_fixture(confirmed, ROOT / "clients" / "fixture"),
        "clients path rejected",
    )
    assert_raises(
        lambda: write_confirmed_memory_fixture(confirmed, ROOT / "val0_memory.enc.db"),
        "production db path rejected",
    )
    assert_raises(
        lambda: create_memory_candidate(
            client_id="fixture_client_001",
            user_id="fixture_user_001",
            title="Secret fixture",
            summary="password: never-store-this",
        ),
        "raw secret rejected",
    )


def test_no_runtime_or_client_hardcoding() -> None:
    module_text = (ROOT / "core" / "memory_spine.py").read_text(encoding="utf-8")
    for needle in (
        "bot.py",
        "telegram",
        "Google Calendar",
        "CLIENT_GROCERY.md",
        "CLIENT_FOLDERS.json",
        "/" + "clients" + "/" + "karen",
        "kar" + "en",
        "Ale",
    ):
        assert_not_contains(module_text, needle, f"no runtime/client hardcoding: {needle}")
    assert_true(DEFAULT_FIXTURE_DIR.as_posix().endswith("tmp/memory_spine_spike"), "default fixture path is tmp only")


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
    test_feature_disabled_by_default()
    test_confirmed_memory_fixture_flow()
    test_storage_guards_and_no_raw_secrets()
    test_no_runtime_or_client_hardcoding()
    test_protected_not_staged()
    print("PASS: memory spine persistence spike smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
