# Val0 Trust Registry

Purpose:
Track operational trust, risk, and allowed autonomy for Val0 commands/capabilities.

This is not “LLM confidence.”
This is evidence-based operational trust.

## Color Legend

| Color | Meaning | Allowed ValPrime / LLM Behavior |
|---|---|---|
| 🟢 Green | Safe, tested, read-only or very low-risk | Recommend freely; auto-run if executor exists |
| 🔵 Blue | Low-risk write or reversible state change | Recommend freely; run with light confirmation if needed |
| 🟡 Yellow | Medium risk, newer, user-data affecting, or quality-sensitive | Explain and ask confirmation |
| 🟠 Orange | Fragile, partial, experimental, easy to misunderstand | Manual guidance only |
| 🔴 Red | Destructive, external send, legal-critical, deletion/reset | Never auto-run; explicit confirmation required |
| ⚫ Black | Parked, deprecated, unknown, or not ready | Do not use unless intentionally revived |

## Autonomy Policy

| Trust Score | Meaning | Behavior |
|---:|---|---|
| 0 | Unknown / untested | Explain only |
| 1 | Known fragile | Manual guidance only |
| 2 | Works sometimes | Show command, ask confirmation |
| 3 | Tested basic path | Recommend sequence |
| 4 | Repeatedly tested, low-risk | Can execute safe/read-only actions if executor exists |
| 5 | Battle-tested core block | Safe default behavior |

## Starter Trust Entries

| Command / Capability | Color | Trust | Risk | Evidence | Allowed Autonomy |
|---|---:|---:|---|---|---|
| /health | 🟢 | 4 | Read-only ops | Known registered command; needs Val0 fresh retest | Recommend freely |
| /status | 🟢 | 3 | Read-only status | Registered; needs fresh-user retest | Recommend freely |
| /start | 🟡 | 2 | Onboarding UX | Registered; alpha behavior needs shakedown | Test manually |
| /note | 🔵 | 3 | Writes note | Registered; note system exists | Suggest with light confirmation |
| /notes | 🟢 | 3 | Read-only notes | Registered | Recommend |
| /search | 🟢 | 3 | Read-only search | Registered | Recommend |
| /memory | 🟡 | 2 | Exposes stored facts | Registered; privacy-sensitive | Ask before showing |
| /remember | 🔵 | 2 | Writes memory | Registered; needs trust test | Confirm before writing |
| /sremember | 🟡 | 2 | Writes semantic memory | Registered; FAISS path needs shakedown | Confirm before writing |
| /ssearch | 🟢 | 2 | Semantic search | Registered; result quality unknown | Recommend cautiously |
| /reminders | 🟢 | 3 | Read-only reminders | Registered | Recommend |
| /rmd | 🟡 | 2 | Writes reminders | Registered; time parsing must be tested | Confirm |
| /voice | 🟡 | 3 | Voice mode / preference | Voice works but quality varies | Test manually |
| Telegram voice note ingestion | 🟡 | 3 | STT + memory/task capture | Known working; trust-killers pending | Test manually |
| Legal/case deadline capture | 🔴 | 1 | Legal-critical | Exists but high consequence | Never auto-run |
| Email send / resend / redirect | 🔴 | 1 | External action | Exists; high trust-risk | Explicit confirmation only |
| /place | 🟡 | 2 | External API lookup | Registered; needs UX test | Recommend cautiously |
| /focus | 🔵 | 3 | Writes PM focus | Registered; useful cockpit state | Recommend |
| /showfocus | 🟢 | 3 | Read-only focus | Registered | Recommend |
| /handoff | 🟢 | 3 | Read-only summary | Registered | Recommend |
| /bug | 🔵 | 2 | Writes bug report | Registered | Recommend when failures happen |
| /feedback | 🔵 | 2 | Writes feedback | Registered | Recommend |
| /idea | 🔵 | 2 | Captures idea | Registered | Recommend |
| Reset current user data | 🔴 | 0 | Destructive DB mutation | Not built; table map exists | Never auto-run |
| Test fresh start mode | 🟡 | 0 | Simulated onboarding | Not built | Design next |

## Rule
Destructive actions require explicit confirmation regardless of trust score.
