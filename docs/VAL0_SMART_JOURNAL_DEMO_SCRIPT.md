# VAL0 SMART JOURNAL / WOW LOOP DEMO SCRIPT

## Purpose

Show that Val0 is no longer just a reminder bot.

Val0 can take messy life/work input, classify it, store it, and recover a useful next step.

## Positioning

Val0 starts as a smart private journal that becomes your operator over time.

The user can dump messy thoughts into Val.
Val starts sorting them into:
- reflections
- follow-ups
- ideas
- notes
- tasks
- reminders later

## Demo flow

### 1. Smart journal entry

Send:

/journal Today was rough. Carlos still needs the solar quote, supplier didn’t answer, and I’m honestly overwhelmed. Also save the idea that Val should help me track supplier follow-ups.

Expected:
Val acknowledges the pressure, saves the context, and mentions follow-up / supplier tracking.

### 2. Show clean structured memory

Send:

/exosummary

Expected:
Val shows the latest grouped Exocortex capture:
- reflection
- follow_up
- idea

This avoids dumping noisy raw memory rows during a demo.

### 3. Ask what now

Send:

/whatnow

Expected:
Val recovers:
- Carlos needs quote
- supplier did not answer
- user is overwhelmed
- supplier follow-up idea exists

Val recommends one practical next step.

### 4. Draft the follow-up

Send:

/draftfollowup

Expected:
Val drafts a practical supplier follow-up message based on the recent follow_up memory.

This proves the loop can move from memory into action support.

## What this proves

messy input
→ classify
→ store
→ recover
→ recommend next step

## What to say to tester

This is raw, but the concept is:

You can dump your brain into Val, and she starts sorting your life.

Today it is Mark 1.
The goal is that over time Val learns your workflows, your people, your pressure points, and helps you decide what to do next.

## Honest limits

- Still command-based for demo.
- Still raw.
- Not full ChatGPT.
- Not full personal OS.
- No automatic follow-up workflow yet.
- No polished memory search yet.

## Demo close

Ask:

Did this feel like:
1. a normal bot,
2. a useful journal,
3. or the start of a personal operator?

What felt useful?
What felt fake?
What would make you use it tomorrow?
