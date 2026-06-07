# ONBOARDING-01D Discovery Recommendation

Purpose: document the narrow first-workflow recommendation step for the daily-operator onboarding path.

## Runtime Behavior Added

After the guided discovery menu and the "Organizar mi día" follow-up, Val asks:

> ¿Dónde tienes tus pendientes ahora: calendario, WhatsApp, notas, papel o en la cabeza?

If the user answers with a source such as calendario, WhatsApp, notas, papel, cabeza, todo regado, WhatsApp y notas, or en todos lados, Val summarizes the source and recommends the first pilot workflow:

> Mi recomendación: empezamos con el flujo Organizar mi día.

## Recommendation Shape

The reply stays concise and operator-like:

- summarizes where the user's pending items live
- recommends "Organizar mi día" as the first workflow
- gives a simple week 1 plan
- says nothing has been saved or configured yet
- says no tasks, reminders, or calendar events were created
- keeps founder-beta and one-flow-first framing
- asks whether the user wants to use this as the first pilot flow

## Week 1 Plan

The week 1 plan is intentionally small:

1. identify where pending items enter
2. separate agenda, tasks, and reminders
3. build a short daily review
4. test reminders or tasks only after confirmation
5. review what helped before expanding

## Guardrails

- no client data writes
- no persistent client profile updates
- no reminders, tasks, or calendar events are created
- no broad router refactor
- no unrelated agenda/task/calendar/Caso Finca behavior changes
- no Karen private data, client file names, AGI claims, or magic-AI claims
- contextless phrases such as "WhatsApp" do not trigger the recommendation

## Scope

This lane is a one-step recommendation only. It does not implement confirmation, setup persistence, workflow scoring storage, or client onboarding profiles.
