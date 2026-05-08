# VAL BUTTON / WEARGRAM V0

## Status
PASS — first wearable access path confirmed.

## Date
2026-05-08

## Hardware / app path
- OnePlus Watch
- Weargram on Wear OS
- Telegram / Valeria chat
- Val0 Telegram bot

## Confirmed flow
Double-press watch crown → Weargram opens → tap Valeria chat → tap microphone → talk → send → Val0 receives → Val0 replies

## PASS
- Watch hardware shortcut can launch Weargram.
- Weargram opens access to Valeria chat.
- Watch voice notes reach Val0.
- Val0 responds.
- /voice on works from this flow.

## POLISH
- Still requires multiple taps after Weargram opens.
- Need confirm whether Val0 audio replies play cleanly on watch.
- Need latency/reliability testing across:
  - phone locked/unlocked
  - Shokz connected/not connected
  - walking
  - parked car

## BLOCKER
None.

## Next test
Send from watch:
"Val, modo reloj. Dame solo el próximo paso."

Expected:
Short, direct next step only.

## Roadmap rule
This is a micro-UX lane only.
Do not expand into native watch app, wake word, Bluetooth automation, or dashboard before founder-beta launch.
