# VAL0 EXOCORTEX MARK 1

## Mission

Val0 Mark 1 is not a generic chatbot and not a reminder bot.

Val0 Mark 1 is a conversational exocortex:

User dumps messy life/work input
→ Val classifies what kind of thing it is
→ Val stores or acts on it reliably
→ Val replies conversationally
→ Val can recover it later
→ Val helps decide the next step

## Product sentence

Val0 lets you dump your brain into a private assistant that starts sorting your life.

## Core promise

Talk naturally.
Val sorts.

## Core loop

1. Capture messy input
2. Classify into buckets
3. Store/action reliably
4. Reply with presence
5. Recover context later
6. Suggest next step

## Buckets

- note
- reminder
- task
- idea
- reflection
- care_mode
- decision
- parking_lot
- project
- follow_up
- normal_chat

## Mark 1 wow demo

User:

Val, today was rough. Carlos still needs the solar quote, supplier didn’t answer, and I’m honestly overwhelmed. Also save the idea that Val should help me track supplier follow-ups.

Expected Val:

I’m sorting that.

Saved:
- Reflection: today felt rough and overwhelming.
- Client follow-up: Carlos needs the solar quote.
- Supplier issue: supplier did not answer.
- Idea: supplier follow-up workflow.

My recommendation: don’t solve the whole business right now. First move is Carlos, because that is closest to money. Want me to draft the follow-up?

## Architecture rule

Conversational input.
Deterministic action.
Conversational output.

## Classifier rule

The LLM may classify and summarize.
The LLM may not directly execute actions.
It returns structured intent.
Deterministic code executes storage, reminders, tasks, and retrieval.

## Trust rule

Do not fake capability.
Do not fake memory.
Do not fake certainty.
If stored, say stored.
If not stored, say not stored.
If unsure, ask one clarifying question.

## Care mode rule

If the user is overwhelmed, discouraged, venting, spiraling, or asking Val to take charge:
- do not convert it into a task by default
- store as reflection or care_mode
- respond with grounded presence
- give one small next action
- avoid big life decisions from emotional crisis state

## HUD rule

Every ops/build response should include a small HUD:
- Mission
- Current milestone
- Progress
- Timebox
- Status
- Next action

## Weekend target

By end of weekend, prove:

1. Messy input can be classified.
2. Reflection can be stored.
3. Reminder/idea/action can still route correctly.
4. “What now?” can read recent context and recommend one step.

## Non-goals this weekend

- no dashboard
- no new app
- no local model routing
- no broad ValPrime rebuild
- no gadget lane expansion
- no paid-user blast
- no personal OS claims

## Success condition

A friend/family tester can see the demo and say:

It’s raw, but I understand it. I can dump my brain into it and it starts sorting my life.
