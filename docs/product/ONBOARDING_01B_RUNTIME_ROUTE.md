# ONBOARDING-01B Guided Workflow Discovery Runtime Route

Purpose: document the narrow Telegram route for guided discovery of the first user flow.

## Runtime Behavior Added

When a user asks discovery-style prompts such as:

- "Val, ¿cómo me puedes ayudar?"
- "Val, ¿qué puedes hacer?"
- "Val, ayúdame a empezar"
- "Val, no sé qué necesito"

Val replies with a Spanish-first guided discovery answer:

- short explanation
- concrete examples
- one-flow-first framing
- founder-beta boundary
- question: "Para empezar bien, escogemos un solo flujo primero. ¿Por dónde empezamos: organizar tu día, pendientes, documentos, clientes, ideas o algo diferente?"

## Scope

This lane is intentionally narrow:

- no client data writes
- no onboarding state
- no feature enablement
- no broad router refactor
- no changes to agenda/task/calendar/Caso Finca behavior

## Safety Boundaries

The reply must not mention:

- internal docs
- smoke tests
- implementation details
- Karen private data
- client files
- AGI or IA mágica claims

Val frames itself as founder beta and asks the user to start with "un solo flujo" before expanding the setup.
