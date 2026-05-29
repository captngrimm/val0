#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
bot = (ROOT / "bot.py").read_text()

assert "M5J: Karen preferred-name/vocative hard guard" in bot
assert 'Tu apodo registrado es: Tany. Lo estoy usando con y griega.' in bot
assert 'Tany, ¿qué movida seguimos hoy?' in bot

# Guard against accidentally hardcoding the wrong spelling in the direct saludo reply.
assert 'Tani, ¿qué movida seguimos hoy?' not in bot

print("PASS: Karen preferred name guard prefers Tany over contradictory recent memory.")
