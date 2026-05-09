# VAL0 ONBOARDING CONSULTANT V1 CHECKPOINT

## Date
2026-05-09

## Branch
val0-voice-shakedown-and-tester-pass

## Status
PASS.

Onboarding Consultant v1 is working.

## What works

- /onboard starts first-contact consultant flow.
- Val asks 7 operating-profile questions.
- User answers naturally.
- Answers are stored as durable user_facts.
- /onboardstatus displays the saved operating profile.
- Val recommends a starter workflow.

## Proven test profile

User: Carlos

Saved facts:
- preferred_name: Carlos
- primary_role: instalo paneles solares
- use_case: negocio
- main_goal: cerrar cotizaciones más rápido
- friction_points: proveedores no responden y se me pierden seguimientos
- current_tools: whatsapp y excel
- tracking_buckets: clientes, proveedores, cotizaciones y seguimientos
- starter_workflow: Clientes/proveedores → cotizaciones/seguimientos → /whatnow → /draftfollowup
- onboarding_status: complete_v1

## Product meaning

This gives Val0 a first-contact advisor layer.

Val no longer only waits for tasks.
Val can ask who the user is, what they do, where things break, and what workflow should exist first.

## Why this matters

This supports the $30 founder-beta angle:

Val0 is not just a bot.
Val0 is a guided exocortex setup:
- first contact
- operating profile
- smart journal
- narrative capture
- whatnow recovery
- draft action support

## Known limitations

- onboarding is command-based.
- onboarding state is in-memory only while active.
- questions are fixed Mark 1 sequence.
- Val does not yet adapt questions dynamically.
- /whatnow does not yet fully use operating profile facts.
- no profile deletion/export UI yet.
- no privacy UX yet.

## Next recommended milestone

Profile-aware /whatnow:
- load operating profile facts
- include role, goal, friction, tools, tracking buckets
- make next-step recommendations based on profile + recent memory

Example:
If user is a solar installer and suppliers are the friction, /whatnow should prioritize quote/supplier follow-up over generic advice.


## Profile-aware recovery update

Profile-aware /whatnow is working.

After onboarding, /whatnow now uses operating profile facts:
- preferred_name
- primary_role
- use_case
- main_goal
- friction_points
- current_tools
- tracking_buckets
- starter_workflow
- onboarding_status

Proven behavior:
For a solar installer profile, /whatnow used:
- goal: cerrar cotizaciones más rápido
- tools: WhatsApp y Excel
- friction: proveedores no responden / seguimientos perdidos
- workflow: clientes/proveedores → cotizaciones/seguimientos → /whatnow → /draftfollowup

Result:
Val recommended reviewing pending quotes/follow-ups and using /draftfollowup to prepare a reactivation message.

Product meaning:
Val now connects first-contact onboarding to daily recovery/advice.

This is the first bridge between:
Onboarding Consultant
→ Operating Profile
→ Smart Journal
→ What Now recovery
→ Action support
