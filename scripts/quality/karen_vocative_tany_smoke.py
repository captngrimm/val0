#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.client_identity import client_vocative
from core.client_profiles import legacy_client_profile

profile = legacy_client_profile("karen")
assert profile["vocative"] == "Tany", f"Expected Karen vocative Tany, got {profile['vocative']!r}"
assert client_vocative("karen") == ", Tany", f"Expected ', Tany', got {client_vocative('karen')!r}"
print("PASS: Karen vocative baseline is Tany.")
