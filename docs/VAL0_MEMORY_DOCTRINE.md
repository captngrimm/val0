# VAL0 MEMORY DOCTRINE

## Purpose

Memory is the spine of Val0.

Val0 should not rely on one giant chat history and pretend that is intelligence.

Memory must be layered, structured, inspectable, and honest.

## Layers

### 1. Raw message log

Stores:
- original user messages
- assistant replies
- timestamps
- chat_id
- source metadata when available

Purpose:
- audit trail
- reconstruction
- context recovery
- "what did I say?"

Limitation:
- raw logs are not enough for intelligence
- raw logs are noisy
- raw logs should not be treated as a clean operating profile

### 2. Structured Exocortex memory

Stores:
- bucket
- summary
- raw_span / raw_input
- timestamp
- confidence later
- source later
- project/topic later

Buckets:
- reflection
- care_mode
- follow_up
- idea
- note
- task
- reminder
- decision
- parking_lot
- project

Purpose:
- whatnow
- pattern detection
- workflow support
- operator behavior

### 3. Operating profile

Stores:
- preferred name
- role/business/work context
- goals
- tools currently used
- friction points
- important people
- workflows
- preferences

Purpose:
- first-contact onboarding
- personalization
- business/life advisory

### 4. Pattern memory

Stores:
- repeated problems
- recurring people/issues
- missed follow-ups
- repeated emotional loops
- workflow bottlenecks

Purpose:
- insights
- suggestions
- proactive improvement
- "I notice this keeps happening"

### 5. Cold document storage

Stores:
- exact document title
- exact body
- version/history later
- source metadata

Purpose:
- exact retrieval
- "give me that document again"
- line-by-line reuse
- provider messages
- contracts
- templates

## Trust rules

- Never claim exact recall unless exact text exists.
- Never confuse summary with source text.
- Preserve raw where possible.
- Store structured items for reasoning.
- Store documents separately when exact retrieval matters.
- Give users memory visibility and deletion/export tools later.

## Product rule

Raw logs preserve truth.
Structured memory creates usefulness.
Cold storage preserves exact documents.
Pattern memory creates insight.
