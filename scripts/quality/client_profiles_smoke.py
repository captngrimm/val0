#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.client_identity import KAREN_CHAT_ID, client_profile as legacy_client_profile
from core.client_profiles import (
    WORKFLOW_CALENDAR,
    WORKFLOW_DAILY_OPERATOR,
    WORKFLOW_DOCUMENTS,
    WORKFLOW_GROCERIES,
    WORKFLOW_LEGAL_CASE,
    WORKFLOW_REMINDERS,
    WORKFLOW_TIMELINE,
    ClientProfile,
    get_client_profile,
    get_client_profile_for_chat,
    is_known_client,
    normalize_client_id,
    normalize_workflow,
    render_unknown_client_onboarding_message,
    render_workflow_not_enabled_message,
    require_workflow_access,
    safe_client_profile_summary,
    workflow_enabled,
)
import core.client_profiles as client_profiles


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(f"{label}: expected truthy value")


def assert_false(value, label: str) -> None:
    if value:
        raise AssertionError(f"{label}: expected falsey value")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def main() -> int:
    karen_id = legacy_client_profile("karen")["client_id"]
    karen_vocative = legacy_client_profile("karen")["vocative"]

    profile = get_client_profile(karen_id)
    assert_true(profile, "Karen profile loads")
    assert_equal(profile.client_id, karen_id, "Karen profile id")
    assert_equal(profile.vocative, karen_vocative, "Karen vocative from legacy profile")

    by_chat = get_client_profile_for_chat(KAREN_CHAT_ID)
    assert_true(by_chat, "Karen chat resolves")
    assert_equal(by_chat.client_id, karen_id, "Karen chat profile id")

    assert_false(is_known_client("missing-client"), "unknown client known false")
    denied_unknown = require_workflow_access("missing-client", WORKFLOW_CALENDAR)
    assert_false(denied_unknown.allowed, "unknown client denied")
    assert_equal(denied_unknown.reason, "unknown_client", "unknown client reason")

    assert_false(get_client_profile_for_chat(123456789), "unknown chat denied")

    allowed = require_workflow_access(karen_id, WORKFLOW_DAILY_OPERATOR)
    assert_true(allowed.allowed, "enabled workflow allowed")
    assert_equal(allowed.reason, "workflow_enabled", "enabled workflow reason")
    assert_true(workflow_enabled(karen_id, WORKFLOW_DOCUMENTS), "workflow_enabled helper")

    protected_workflows = (
        WORKFLOW_DOCUMENTS,
        WORKFLOW_TIMELINE,
        WORKFLOW_DAILY_OPERATOR,
        WORKFLOW_LEGAL_CASE,
        WORKFLOW_GROCERIES,
    )
    for workflow in protected_workflows:
        known_decision = require_workflow_access(karen_id, workflow)
        assert_true(known_decision.allowed, f"Karen allowed for {workflow}")

        unknown_decision = require_workflow_access("unknown-client", workflow)
        assert_false(unknown_decision.allowed, f"unknown client denied for {workflow}")
        assert_equal(unknown_decision.reason, "unknown_client", f"unknown denial reason for {workflow}")

        rendered = render_workflow_not_enabled_message(unknown_decision)
        assert_true("todavía no está habilitado para este chat" in rendered, f"not-enabled copy for {workflow}")
        assert_true("información general" in rendered, f"generic fallback preserved in copy for {workflow}")
        for forbidden in (
            "Karen",
            karen_vocative,
            "CASE:KAREN",
            "KAREN-LAND",
            "VFMS",
            "finca 10082",
            str(KAREN_CHAT_ID),
        ):
            assert_not_contains(rendered, forbidden, f"safe denial copy for {workflow}")

    unknown_onboarding = render_unknown_client_onboarding_message()
    assert_true("operador/admin" in unknown_onboarding, "unknown onboarding invites operator activation")
    assert_true("información general" in unknown_onboarding, "unknown onboarding keeps generic help available")

    denied_workflow = require_workflow_access(karen_id, "future workflow")
    assert_false(denied_workflow.allowed, "unknown workflow denied")
    assert_equal(denied_workflow.reason, "unknown_workflow", "unknown workflow reason")

    fixture = ClientProfile(
        client_id="fixture-client",
        display_name="Fixture",
        vocative="",
        language="es",
        chat_ids=(987654321,),
        enabled_workflows=(WORKFLOW_REMINDERS,),
        active_case_id="",
        calendar_status="not_connected",
        metadata={
            "token_path": "/tmp/not-real-token",
            "private_note": "do not expose",
        },
    )
    client_profiles._CLIENT_PROFILES[fixture.client_id] = fixture
    try:
        disabled = require_workflow_access("fixture-client", WORKFLOW_CALENDAR)
        assert_false(disabled.allowed, "disabled workflow denied")
        assert_equal(disabled.reason, "workflow_disabled", "disabled workflow reason")
        assert_true(workflow_enabled("fixture-client", WORKFLOW_REMINDERS), "fixture enabled workflow")

        summary = safe_client_profile_summary(fixture)
        summary_text = str(summary)
        assert_false("token_path" in summary_text, "safe summary hides metadata key")
        assert_false("not-real-token" in summary_text, "safe summary hides metadata value")
        assert_false("private_note" in summary_text, "safe summary hides private metadata")
    finally:
        client_profiles._CLIENT_PROFILES.pop(fixture.client_id, None)

    assert_equal(normalize_client_id("  Client_One-2!! "), "client_one-2", "client id normalization")
    assert_equal(normalize_workflow("Daily Operator"), WORKFLOW_DAILY_OPERATOR, "workflow normalization")
    assert_equal(normalize_workflow("legal-case"), "legal_case", "workflow dash normalization")

    print("PASS: client profile smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
