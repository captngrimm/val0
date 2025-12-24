# Memory Contract — v0

## Purpose
This memory exists to preserve human work and context across time.
It is not an AI brain. It does not reason or infer on its own.

## Layers

### 1. Raw Logs (logs_raw/)
- Append-only
- May contain full text, dumps, thoughts, transcripts
- Source of truth
- Never edited or summarized automatically

### 2. Daily Summaries (daily_md/)
- One short Markdown file per day
- Human-written or human-approved
- Used as the default recall surface

### 3. Index (index/)
- Stores references only (dates, filenames, topics)
- Does NOT store content
- Used to answer: “Did we ever talk about X?”

## Rules
- Nothing is deleted
- Nothing is rewritten
- Nothing is inferred without source
- Memory is loaded only on explicit request

## Non-goals
- No background reasoning
- No autonomous learning
- No emotional manipulation
- No omniscience

If it can’t be explained in 30 seconds, it doesn’t belong here.
