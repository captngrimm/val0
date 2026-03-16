# VAL DEBUG PROTOCOL

Purpose:
Provide deterministic transparency into Val's internal
decision process during command handling.

This protocol is used when the operator requests debug mode.


--------------------------------------------------
DEBUG TRIGGER
--------------------------------------------------

Debug mode activates when the operator sends:

val debug
val debug mode
val show reasoning
val explain routing


--------------------------------------------------
DEBUG OUTPUT STRUCTURE
--------------------------------------------------

When debug mode is active Val should reveal:

1. ROUTER MATCH
Which handler matched the request.

Example:

Router matched: try_case_status


2. CLEANED INPUT
Normalized command after preprocessing.

Example:

raw: "cómo va el caso de leticia"
clean: "como va el caso de leticia"


3. RESOLUTION LOGIC
How entities were resolved.

Example:

client_name detected: leticia
resolved expediente: 524242024


4. SQL EXECUTION

Example:

SELECT expediente
FROM cases
WHERE chat_id=...
AND lower(client_name) LIKE '%leticia%'


5. HANDLER RESULT

Example:

generate_case_cockpit executed
result returned to Telegram


--------------------------------------------------
DEBUG RULES
--------------------------------------------------

Debug mode must never:

• hide routing decisions
• hide query execution
• hide handler selection


Debug output should be concise but complete.


--------------------------------------------------
DEBUG EXIT
--------------------------------------------------

Debug mode ends automatically after one response.

Unless operator sends:

val debug persistent

