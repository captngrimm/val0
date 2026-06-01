#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.intent_router_v2 import classify_intent_shadow  # noqa: E402
from core.intent_router_v2_observer import (  # noqa: E402
    clear_observations,
    record_actual_intent,
    record_predicted_intent,
    render_intent_observation,
)


def main() -> int:
    clear_observations()
    rows = [
        ("Val que tareas tengo activas?", "task_query", "maybe_handle_karen_task_query_hard_gate"),
        ("Val elimina el evento 1", "gcal_delete", "maybe_handle_karen_gcal_event_number_delete"),
        ("Val elimina la tarea 1", "gcal_delete", "try_gcal_delete_natural"),
    ]

    print("Intent Router v2 observer demo")
    print("input | predicted | actual | match | confidence | handler")
    print("--- | --- | --- | --- | --- | ---")
    for idx, (text, actual, handler) in enumerate(rows, start=1):
        message_id = f"demo-{idx}"
        decision = classify_intent_shadow(text, client_id="client-zero", chat_id=1)
        record_predicted_intent(1, message_id, decision)
        observation = record_actual_intent(1, message_id, actual, handler, reason="demo")
        print(
            f"{text} | {observation.predicted_intent} | {observation.actual_intent} | "
            f"{observation.match} | {observation.confidence:.2f} | {observation.handler_name}"
        )
        print(f"  {render_intent_observation(observation)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
