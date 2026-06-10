# POWERCLUB-CRM-BATTLE-01D - Live Meeting Script

## Purpose

Give Frank a meeting-ready talk track for the PowerClub CRM Battle Stage.

This script positions the work as a pilot/demo for operational visibility, not as a final production CRM. All dashboard data shown in the static demo is fake/synthetic.

## 1. Opening

```text
Antes de verlo, una aclaracion importante: esto no es el sistema final, no esta conectado a datos reales de PowerClub y no automatiza WhatsApp, pagos ni operaciones reales. Es una demo de piloto para alinear como se veria una capa de visibilidad gerencial sobre seguimiento comercial.
```

```text
La idea no es vender "un CRM" por tener pantallas. La idea es mostrar donde PowerClub podria estar perdiendo oportunidades por falta de seguimiento visible, y que decisiones podria tomar gerencia si esa informacion estuviera clara.
```

## 2. Pain Framing

```text
El dolor principal no es registrar nombres. El dolor es que un lead interesado se enfria si nadie le da seguimiento, si el siguiente asesor no ve el contexto, o si gerencia no sabe que sucursal, asesor o canal esta acumulando atraso.
```

Key point:

- Lost follow-up can become lost money.
- The dashboard makes invisible sales leakage visible early enough for management action.

## 3. Show Executive Dashboard First

Action:

1. Open `docs/demo/powerclub_crm/index.html`.
2. Start on `Vista gerencial`.
3. Point to the fake-data notice.
4. Show the KPI strip before clicking into advisor workflow.

Talk track:

```text
Empezamos por gerencia porque ahi esta el valor comercial: que puede ver un gerente hoy que ayer estaba escondido en llamadas, archivos, turnos o reportes manuales.
```

What to highlight:

- Oportunidades activas / socios asignados.
- Seguimientos para hoy.
- Seguimientos atrasados.
- Oportunidades en riesgo.
- Avance del mes.

## 4. Explain Advisor Rankings

```text
El ranking no es para castigar asesores. Es para separar dos cosas: actividad y resultado. Un asesor puede estar muy activo pero cerrar poco, y eso pide coaching. Otro puede convertir muy bien, y eso pide aprendizaje para replicar lo que funciona.
```

Explain:

- Activity ranking shows commercial motion.
- Result ranking shows conversion.
- Management decision: coach, support, rebalance, recognize, or inspect process.

Financial link:

```text
Si mejoramos conversion sin comprar mas leads, estamos recuperando valor del mismo flujo comercial.
```

## 5. Explain Overdue And Stuck Opportunities

```text
Esta parte es el corazon del piloto: seguimiento atrasado y oportunidades trabadas. No son solo tareas vencidas; son oportunidades con intencion que podrian enfriarse si nadie interviene.
```

Show:

- Pendientes para hoy.
- Seguimientos atrasados.
- Follow-up aging.
- Stuck opportunities.

Decision supported:

- Call today.
- Reassign owner.
- Escalate hot lead.
- Require next action after visit.

## 6. Explain Branch And Source Visibility

```text
La comparacion por sucursal ayuda a separar si el problema es volumen, seguimiento o conversion. La vista de canales ayuda a ver si una fuente trae oportunidades reales o solo ruido que consume tiempo.
```

Show:

- Branch comparison.
- Source/channel performance.
- Filters: branch, advisor, channel, status, temperature.

Management decision:

- Which branch needs attention.
- Which channel deserves more energy.
- Which source creates too much follow-up waste.

## 7. Explain Protected Opportunity Estimate

```text
Este numero es una estimacion de demo, no ingreso real. Sirve para explicar la logica: si tenemos leads calientes atrasados o trabados, podemos asignarles un valor ficticio y una probabilidad ficticia para mostrar la oportunidad que gerencia podria proteger si actua a tiempo.
```

Important language:

- Say "oportunidad protegible."
- Do not say guaranteed recovered revenue.
- Repeat that assumptions are synthetic.

## 8. Manager Action Prompts

```text
La meta no es que el dashboard sea bonito. La meta es que diga: esto es lo que gerencia deberia mirar hoy.
```

Examples:

- Rescue hot leads.
- Coach advisor with high activity but weak conversion.
- Inspect branch with high delay.
- Review noisy channel.
- Close loop on visits without outcome.

## 9. Manager View Options

```text
En un piloto real, podemos congelar una vista gerencial inicial segun la prioridad de PowerClub. No todos los gerentes necesitan la misma pantalla el dia uno.
```

Options:

- Follow-up Control View.
- Advisor Performance View.
- Branch Comparison View.
- Recovery Opportunities View.

Use this question:

```text
Si solo pudieramos poner una vista gerencial en produccion primero, cual le daria mas control esta semana?
```

## 10. Transition To CRM / Operator Workflow

Action:

1. Click `Vista asesores`.
2. Select an advisor.
3. Open a synthetic record.
4. Show status, next action, notes, plan offered, and history.

Talk track:

```text
Despues de ver la vista gerencial, bajamos al flujo del asesor. La idea es que el asesor no trabaje desde memoria, archivo correcto o turno anterior, sino desde una lista clara con estado, historial y proxima accion.
```

## 11. Val PowerClub Copilot Future Add-On

```text
Mas adelante, esto podria tener una capa tipo Val PowerClub Copilot: un asistente corporativo acotado que ayude a gerentes a preguntar por metricas, entender el dashboard, decidir que cambiar y preparar siguientes preguntas.
```

Boundaries:

- Future/add-on, not core Phase 1 promise.
- Transparent and permissioned.
- Scoped to PowerClub-approved knowledge.
- No full autonomy claim.
- No claim that Val already operates PowerClub.

## 12. Close

```text
El siguiente paso no seria construir todo. Seria una reunion corta de descubrimiento para congelar alcance: que vista gerencial va primero, que datos ficticios se vuelven campos reales, que sucursal o proceso entra al piloto, y que queda fuera. Con eso se arma una propuesta de piloto con setup, implementacion/training y mantenimiento.
```

Close ask:

```text
Agendemos discovery, congelemos alcance y armemos propuesta de piloto.
```

## 13. Do Not Say

- "Esto ya esta conectado a PowerClub."
- "Esto automatiza WhatsApp."
- "Esto reconcilia pagos."
- "Esto reemplaza su CRM desde hoy."
- "Este dinero esta recuperado."
- "Val va a operar autonomamente el negocio."
- "Ya tenemos datos reales de sus asesores o socios."
