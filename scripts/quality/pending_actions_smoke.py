#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.pending_actions import (
    ConfirmationDecision,
    PendingAction,
    classify_confirmation_reply,
    clear_pending_action,
    create_pending_action,
    expire_pending_actions,
    get_pending_action,
    safe_audit_payload,
)


def make_action(
    action_id: str = "act-1",
    chat_id: int = 123,
    client_id: str = "client-a",
    action_type: str = "test_action",
    expires_at: datetime | None = None,
) -> PendingAction:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return PendingAction(
        action_id=action_id,
        chat_id=chat_id,
        client_id=client_id,
        action_type=action_type,
        display_summary="Test action",
        confirm_words=("sí", "si", "dale", "ok"),
        cancel_words=("cancelar", "no"),
        expires_at=expires_at or (now + timedelta(minutes=5)),
        payload={"title": "Safe title", "secret": "do-not-log"},
        audit_metadata={"source": "smoke"},
        created_at=now,
        sensitive_payload_keys=("secret",),
    )


def assert_equal(got, expected, label: str) -> None:
    if got != expected:
        raise AssertionError(f"{label}: expected={expected!r} got={got!r}")


def main() -> int:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    action = make_action()

    for word in ("sí", "si", "dale", "ok"):
        assert_equal(
            classify_confirmation_reply(word, action, now=now),
            ConfirmationDecision.CONFIRM,
            f"confirm word {word}",
        )

    for word in ("cancelar", "no"):
        assert_equal(
            classify_confirmation_reply(word, action, now=now),
            ConfirmationDecision.CANCEL,
            f"cancel word {word}",
        )

    assert_equal(
        classify_confirmation_reply("maybe later", action, now=now),
        ConfirmationDecision.UNKNOWN,
        "unknown text",
    )

    expired = make_action(action_id="expired", expires_at=now - timedelta(seconds=1))
    assert_equal(
        classify_confirmation_reply("sí", expired, now=now),
        ConfirmationDecision.EXPIRED,
        "expired action",
    )

    create_pending_action(action)
    found = get_pending_action(123, action_type="test_action", client_id="client-a", now=now)
    assert_equal(found, action, "lookup by chat/client/action")
    assert_equal(get_pending_action(123, client_id="other", now=now), None, "wrong client lookup")

    audit = safe_audit_payload(action)
    assert_equal(audit["payload"]["secret"], "[redacted]", "sensitive redaction")
    assert_equal(audit["payload"]["title"], "Safe title", "safe payload retained")

    clear_pending_action(action.action_id)
    assert_equal(get_pending_action(123, now=now), None, "clear action")

    create_pending_action(expired)
    assert_equal(expire_pending_actions(now=now), 1, "expire count")
    assert_equal(get_pending_action(expired.chat_id, now=now), None, "expired removed")

    print("PASS: pending actions smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
