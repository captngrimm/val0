# POWERCLUB-CRM-01B - Demo Estática Dummy de CRM

Propósito:
Crear una demo web estática y client-facing para mostrar cómo podría sentirse un CRM operativo ligero para Power Club durante un piloto operativo.

Ubicación:

```text
docs/demo/powerclub_crm/index.html
```

No requiere servidor. Se puede abrir directamente en el navegador.

---

## Qué Muestra

La demo presenta dos vistas principales:

- Vista asesores: lista diaria de socios, prospectos y oportunidades comerciales con sucursal, asesor, turno, canal, estado, prioridad, último contacto y próximo seguimiento.
- Vista gerencial: filtros por sucursal y asesor, métricas de seguimiento y una tabla simple para ver riesgo operativo por sucursal, asesor y canal.

La demo usa branding de reunión:

- Val AI Ops Discovery.
- Isthmus Dynamics / Honest AI Ops.
- Power Club CRM Pilot / CRM Operativo Ligero.

---

## Datos

Todos los datos son ficticios y anónimos.

La demo incluye una nota visible:

```text
Demo con datos ficticios. No usa información real de Power Club.
```

Los nombres, teléfonos, sucursales, asesores, estados, notas e historial de interacción son muestras inventadas para explicar el flujo. No representan socios reales, prospectos reales ni operaciones reales de Power Club.

---

## Flujo de Asesores

Insight operativo usado:
Los operadores trabajan por turnos. El punto de partida actual es abrir laptop, correo, Google Drive y archivos establecidos por nombre; luego se gestiona contacto por celular, llamadas de socios o ventas presenciales. La demo no copia conversaciones ni datos reales: solo usa este patrón operativo de forma paraphraseada.

La vista de asesores permite mostrar:

- Lista de socios/prospectos.
- Estado socio.
- Estado de gestión.
- Sucursal.
- Asesor asignado.
- Turno del operador.
- Herramientas actuales: correo, Google Drive y celular.
- Archivo actual por nombre como dolor de estado actual.
- Canal: celular, llamada de socio o venta presencial.
- Último contacto.
- Fecha de próximo seguimiento.
- Prioridad.
- Ficha de detalle.
- Notas.
- Historial de interacción.
- Próxima acción.

Clarificación comercial:
Estado socio describe la relación de membresía o cliente. Estado de gestión describe el proceso de venta, seguimiento o contacto que maneja el asesor. No son el mismo campo.

Valores visibles de Estado de gestión:

- Venta.
- Promesa de compra.
- Seguimiento.
- Ilocalizable.
- No contacto.

Los botones de Estado de gestión son interactivos dentro del navegador, pero solo modifican el arreglo local de demo mientras la página está abierta. No guardan datos, no llaman APIs y no escriben archivos.

El valor del piloto es centralizar seguimiento, historial de contacto y próximo paso visible para que exista continuidad entre turnos, incluso si el proceso actual inicia desde correo, Google Drive y archivos por nombre.

---

## Flujo Gerencial

La vista gerencial permite mostrar:

- Filtro por sucursal.
- Filtro por asesor.
- Leads abiertos.
- Seguimientos vencidos.
- Citas agendadas.
- Conversiones simuladas.
- Conteo de Venta.
- Conteo de Promesa de compra.
- Conteo de No contacto.
- Conteo de ventas presenciales.
- Tabla por sucursal.
- Lista de oportunidades que requieren atención.

El objetivo es explicar visibilidad gerencial: qué está vencido, quién tiene carga, qué sucursal necesita atención, qué Estado de gestión domina, qué canal genera actividad y qué oportunidades deben revisarse.

---

## Límites

Esta demo no incluye:

- Datos reales de Power Club.
- Datos vivos de clientes.
- Backend.
- APIs.
- Autenticación.
- Integración de pagos.
- Automatización por WhatsApp.
- Promesa de CRM de producción.
- Migración de históricos.
- Integraciones en tiempo real.
- Cambios a bot.py, core/** o clients/**.

La demo es una herramienta de conversación para una reunión. Sirve para alinear lenguaje, flujo y alcance del piloto antes de cualquier implementación.

---

## Cómo Usarla en Reunión

Secuencia sugerida:

1. Abrir `docs/demo/powerclub_crm/index.html`.
2. Señalar la nota de datos ficticios.
3. Mostrar la vista de asesores y explicar la lista diaria.
4. Abrir una ficha de socio/prospecto.
5. Cambiar un estado para mostrar el flujo operativo.
6. Pasar a vista gerencial.
7. Filtrar por sucursal o asesor.
8. Cerrar con la pregunta: qué flujo real conviene pilotear primero.

Frase de posicionamiento:

```text
Esto no reemplaza el CRM actual hoy. Es una demo para visualizar un piloto operativo: seguimiento más claro para asesores y visibilidad gerencial para reducir oportunidades perdidas.
```
