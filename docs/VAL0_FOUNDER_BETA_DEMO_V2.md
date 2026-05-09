# VAL0 FOUNDER BETA DEMO V2

## Product sentence

Val0 starts as a smart private journal that becomes your operator over time.

It helps the user:
- explain their life/work/business
- build an operating profile
- dump messy stories naturally
- extract structured memory
- recover what matters
- decide the next step
- draft practical follow-up messages
- capture future workflow requests safely

## Demo flow

### 1. First contact / operating profile

Send:

/onboard

Use example answers:
- Carlos
- Instalo paneles solares
- Negocio
- Cerrar cotizaciones más rápido
- Proveedores no responden y se me pierden seguimientos
- WhatsApp y Excel
- Clientes, proveedores, cotizaciones y seguimientos

Then send:

/onboardstatus

Expected:
Val shows the operating profile.

### 2. Natural messy story

Send without slash command:

Val, holy shit today was awful. Carlos called me twice because he still needs the solar quote. The supplier ghosted me again and now I look bad. Also save this idea: Val should track supplier follow-ups and warn me when a provider is becoming unreliable.

Expected:
Val understands the story, stores:
- reflection
- follow_up
- follow_up
- idea

### 3. Structured memory view

Send:

/exosummary

Expected:
Val shows latest capture grouped cleanly:
- idea
- seguimiento
- reflexión
with specific item summaries.

### 4. Recovery

Send:

/whatnow

Expected:
Val uses:
- operating profile
- main goal
- friction points
- recent memory

Then recommends the closest useful next step.

### 5. Action support

Send:

/draftfollowup

Expected:
Val drafts a supplier follow-up message.
It should preserve concrete context like:
- cotización solar
- Carlos
- proveedor no responde

It must not greet the supplier as Carlos.

### 6. Roadmap-safe request capture

Send:

/flowrequest Carpintero quiere monitorear herramientas nuevas de carpintería. Por ahora pegará newsletters o artículos y Val debe resumir qué aplica, si vale la pena, y cómo probarlo.

Expected:
Val stores it as a roadmap/flow request, not as a promise.

## What this proves

First contact
→ operating profile
→ free-form story
→ structured memory
→ recovery
→ action draft
→ roadmap request capture

## Honest limits

- Still Telegram-based.
- Still rough.
- Some commands still visible.
- No autonomous sending.
- No web monitoring yet.
- No cold document vault yet.
- No privacy UX yet.
- No polished onboarding UI yet.

## Current offer framing

This is not "better ChatGPT."

This is:
A guided exocortex setup for your life/work/business.

Raw founder beta:
- I help you set it up.
- You talk to it naturally.
- It starts sorting your chaos.
- It remembers useful structure.
- It helps you decide what to do next.
