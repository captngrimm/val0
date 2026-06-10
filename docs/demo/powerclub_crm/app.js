const STATUS_CLASSES = {
  Venta: "venta",
  "Promesa de compra": "promesa-de-compra",
  Seguimiento: "seguimiento",
  Ilocalizable: "ilocalizable",
  "No contacto": "no-contacto",
};

const TODAY = "2026-06-09";
const TOTAL_FAKE_RECORDS = 60;
const PLAN_OPTIONS = ["Mensual $49", "Prepagado 1 mes", "Trimestral", "Semestral", "Anual", "Otro plan"];

const leads = [
  {
    id: "PC-DEMO-001",
    name: "Socio Demo 001",
    phone: "+507 6000-0101",
    email: "socio.demo.001@example.invalid",
    branch: "Costa del Este",
    advisor: "Asesor Demo A",
    shift: "Turno mañana",
    interest: "Nueva membresía",
    lastPlan: "Sin plan anterior",
    offeredPlan: "Mensual $49",
    memberStatus: "Prospecto",
    managementStatus: "Seguimiento",
    priority: "Alta",
    channel: "Celular",
    sourceFile: "Archivo por nombre: Prospectos junio",
    currentTools: "Correo, Google Drive y celular",
    appointmentScheduled: false,
    lastContact: "2026-06-07",
    nextFollowUp: "2026-06-09",
    nextAction: "Llamar hoy para confirmar plan familiar.",
    managementNote: "Pendiente validar horario preferido.",
    notes: "Prospecto ficticio interesado en horario nocturno. El seguimiento centralizado evita depender solo del archivo por nombre.",
    history: [
      "2026-06-05: Solicitó información de planes.",
      "2026-06-07: Se explicó plan familiar y quedó pendiente llamada.",
    ],
  },
  {
    id: "PC-DEMO-002",
    name: "Socio Demo 002",
    phone: "+507 6000-0102",
    email: "socio.demo.002@example.invalid",
    branch: "San Francisco",
    advisor: "Asesor Demo B",
    shift: "Turno tarde",
    interest: "Reactivación",
    lastPlan: "Mensual $49",
    offeredPlan: "Trimestral",
    memberStatus: "Ex socio",
    managementStatus: "Promesa de compra",
    priority: "Media",
    channel: "Llamada de socio",
    sourceFile: "Archivo por nombre: Reactivaciones",
    currentTools: "Correo, Google Drive y celular",
    appointmentScheduled: false,
    lastContact: "2026-06-08",
    nextFollowUp: "2026-06-08",
    nextAction: "Enviar resumen manual de opciones y llamar en dos días.",
    managementNote: "Quiere comparar plan trimestral con mensual.",
    notes: "Socio ficticio llamó para consultar nueva compra. Próximo paso visible para continuidad entre turnos.",
    history: [
      "2026-06-04: Registro importado desde exportación de ejemplo.",
      "2026-06-08: Contactado por llamada manual.",
    ],
  },
  {
    id: "PC-DEMO-003",
    name: "Socio Demo 003",
    phone: "+507 6000-0103",
    email: "socio.demo.003@example.invalid",
    branch: "El Dorado",
    advisor: "Asesor Demo A",
    shift: "Turno mañana",
    interest: "Seguimiento de prueba",
    lastPlan: "Sin plan anterior",
    offeredPlan: "Prepagado 1 mes",
    memberStatus: "Prospecto",
    managementStatus: "Seguimiento",
    priority: "Alta",
    channel: "Venta presencial",
    sourceFile: "Archivo por nombre: Pruebas y visitas",
    currentTools: "Laptop, correo y Google Drive",
    appointmentScheduled: true,
    lastContact: "2026-06-08",
    nextFollowUp: "2026-06-10",
    nextAction: "Confirmar asistencia a cita de evaluación.",
    managementNote: "Visita agendada en sucursal.",
    notes: "Prospecto ficticio atendido en persona; requiere historial de contacto visible para el siguiente operador.",
    history: [
      "2026-06-06: Completó prueba de cortesía ficticia.",
      "2026-06-08: Se agenda cita en sucursal.",
    ],
  },
  {
    id: "PC-DEMO-004",
    name: "Socio Demo 004",
    phone: "+507 6000-0104",
    email: "socio.demo.004@example.invalid",
    branch: "Albrook",
    advisor: "Asesor Demo C",
    shift: "Turno tarde",
    interest: "Renovación",
    lastPlan: "Semestral",
    offeredPlan: "Anual",
    memberStatus: "Socio por vencer",
    managementStatus: "No contacto",
    priority: "Media",
    channel: "Celular",
    sourceFile: "Archivo por nombre: Renovaciones",
    currentTools: "Correo, Google Drive y celular",
    appointmentScheduled: false,
    lastContact: "Sin contacto",
    nextFollowUp: "2026-06-09",
    nextAction: "Primer contacto manual para renovación.",
    managementNote: "No se ha logrado primer contacto.",
    notes: "Socio ficticio con renovación pendiente. Aún no hay contacto registrado para el turno actual.",
    history: ["2026-06-09: Registro ficticio asignado a asesora."],
  },
  {
    id: "PC-DEMO-005",
    name: "Socio Demo 005",
    phone: "+507 6000-0105",
    email: "socio.demo.005@example.invalid",
    branch: "Costa del Este",
    advisor: "Asesor Demo B",
    shift: "Turno mañana",
    interest: "Upgrade",
    lastPlan: "Trimestral",
    offeredPlan: "Semestral",
    memberStatus: "Socio activo",
    managementStatus: "Venta",
    priority: "Baja",
    channel: "Venta presencial",
    sourceFile: "Archivo por nombre: Upgrades",
    currentTools: "Laptop, correo y Google Drive",
    appointmentScheduled: false,
    lastContact: "2026-06-06",
    nextFollowUp: "2026-06-20",
    nextAction: "Seguimiento de satisfacción post-inscripción.",
    managementNote: "Venta demo cerrada en sucursal.",
    notes: "Conversión simulada de venta presencial para mostrar trazabilidad desde asesor y sucursal.",
    history: [
      "2026-06-03: Interés en upgrade ficticio.",
      "2026-06-06: Marcado como inscrito en demo.",
    ],
  },
  {
    id: "PC-DEMO-006",
    name: "Socio Demo 006",
    phone: "+507 6000-0106",
    email: "socio.demo.006@example.invalid",
    branch: "San Francisco",
    advisor: "Asesor Demo C",
    shift: "Turno cierre",
    interest: "Lead corporativo",
    lastPlan: "Otro plan",
    offeredPlan: "Anual",
    memberStatus: "Prospecto",
    managementStatus: "Ilocalizable",
    priority: "Media",
    channel: "Celular",
    sourceFile: "Archivo por nombre: Corporativos",
    currentTools: "Correo, Google Drive y celular",
    appointmentScheduled: false,
    lastContact: "2026-06-02",
    nextFollowUp: "2026-06-06",
    nextAction: "Cerrar con motivo y revisar aprendizaje.",
    managementNote: "No responde celular en intentos demo.",
    notes: "Oportunidad ficticia no localizada por celular; queda historial para continuidad del siguiente turno.",
    history: [
      "2026-06-01: Contacto inicial.",
      "2026-06-02: Indica que no seguirá este mes.",
    ],
  },
];

function createGeneratedRecords(count) {
  const branches = ["Costa del Este", "San Francisco", "El Dorado", "Albrook", "Brisas"];
  const advisors = ["Asesor Demo A", "Asesor Demo B", "Asesor Demo C", "Asesor Demo D", "Asesor Demo E", "Asesor Demo F"];
  const statuses = ["Venta", "Promesa de compra", "Seguimiento", "Ilocalizable", "No contacto"];
  const memberStatuses = ["Prospecto", "Socio activo", "Ex socio", "Socio por vencer", "Excluido"];
  const interests = ["Nueva membresía", "Reactivación", "Renovación", "Upgrade", "Seguimiento de prueba"];
  const channels = ["Celular", "Llamada de socio", "Venta presencial"];
  const priorities = ["Alta", "Media", "Baja"];

  return Array.from({ length: count }, (_, index) => {
    const number = index + 7;
    const status = statuses[index % statuses.length];
    const branch = branches[index % branches.length];
    const advisor = advisors[index % advisors.length];
    const plan = PLAN_OPTIONS[index % PLAN_OPTIONS.length];
    const lastPlan = PLAN_OPTIONS[(index + 2) % PLAN_OPTIONS.length];
    const nextDay = String(9 + (index % 12)).padStart(2, "0");
    const lastDay = String(1 + (index % 8)).padStart(2, "0");
    const padded = String(number).padStart(3, "0");

    return {
      id: `PC-DEMO-${padded}`,
      name: `Socio Demo ${padded}`,
      phone: `+507 6000-${String(100 + number).padStart(4, "0")}`,
      email: `socio.demo.${padded}@example.invalid`,
      branch,
      advisor,
      shift: index % 3 === 0 ? "Turno mañana" : index % 3 === 1 ? "Turno tarde" : "Turno cierre",
      interest: interests[index % interests.length],
      lastPlan,
      offeredPlan: plan,
      memberStatus: memberStatuses[index % memberStatuses.length],
      managementStatus: status,
      priority: priorities[index % priorities.length],
      channel: channels[index % channels.length],
      sourceFile: `Archivo por nombre: Base demo ${branch}`,
      currentTools: index % 2 === 0 ? "Correo, Google Drive y celular" : "Laptop, correo y Google Drive",
      appointmentScheduled: index % 7 === 0,
      lastContact: `2026-06-${lastDay}`,
      nextFollowUp: `2026-06-${nextDay}`,
      nextAction: status === "Venta" ? "Seguimiento de satisfacción." : "Gestionar contacto y actualizar estado.",
      managementNote: "Nota demo para seguimiento del asesor.",
      notes: "Registro ficticio generado para demostrar volumen, scroll y filtros.",
      history: [
        `2026-06-${lastDay}: Registro demo asignado.`,
        `2026-06-${lastDay}: Interacción ficticia registrada.`,
      ],
    };
  });
}

leads.push(...createGeneratedRecords(TOTAL_FAKE_RECORDS - leads.length));

let selectedId = leads[0].id;
let activeFilter = "todos";

const leadList = document.querySelector("#leadList");
const recordCount = document.querySelector("#recordCount");
const operatorView = document.querySelector("#operatorView");
const managerView = document.querySelector("#managerView");
const operatorTab = document.querySelector("#operatorTab");
const managerTab = document.querySelector("#managerTab");
const operatorAdvisorFilter = document.querySelector("#operatorAdvisorFilter");
const branchFilter = document.querySelector("#branchFilter");
const advisorFilter = document.querySelector("#advisorFilter");
const sourceFilter = document.querySelector("#sourceFilter");
const statusFilter = document.querySelector("#statusFilter");
const temperatureFilter = document.querySelector("#temperatureFilter");

const EXECUTIVE_RECORDS = 1800;
const EXECUTIVE_ADVISOR_COUNT = 56;
const EXECUTIVE_BRANCHES = ["Costa del Este", "San Francisco", "El Dorado", "Albrook", "Brisas", "Via Brasil"];
const EXECUTIVE_SOURCES = ["Instagram", "Facebook", "Walk-in", "Referido", "Web", "Corporativo", "Evento", "Reactivacion", "Llamada entrante", "Promocion"];
const EXECUTIVE_STATUSES = ["Nuevo", "Contactado", "Interesado", "Cita agendada", "Visitado", "Venta", "Perdido"];
const TEMPERATURES = ["Hot", "Warm", "Cold"];
const AVERAGE_MEMBERSHIP_VALUE_FAKE = 69;
const WEEK_DAYS = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"];

const executiveAdvisors = Array.from({ length: EXECUTIVE_ADVISOR_COUNT }, (_, index) => {
  const number = index + 1;
  return {
    id: `advisor_demo_${String(number).padStart(3, "0")}`,
    name: `Asesor Demo ${String(number).padStart(2, "0")}`,
    branch: EXECUTIVE_BRANCHES[index % EXECUTIVE_BRANCHES.length],
  };
});

const executiveLeads = Array.from({ length: EXECUTIVE_RECORDS }, (_, index) => {
  const advisor = executiveAdvisors[index % executiveAdvisors.length];
  const branch = advisor.branch;
  const source = EXECUTIVE_SOURCES[(index * 3 + Math.floor(index / 11)) % EXECUTIVE_SOURCES.length];
  const status = EXECUTIVE_STATUSES[(index * 5 + Math.floor(index / 17)) % EXECUTIVE_STATUSES.length];
  const temperature = TEMPERATURES[(index + (status === "Interesado" ? 0 : 1)) % TEMPERATURES.length];
  const day = 1 + (index % 28);
  const followUpOffset = (index % 13) - 6;
  const followUpDay = Math.max(1, Math.min(28, 9 + followUpOffset));
  const isOverdue = followUpDay < 9 && status !== "Venta" && status !== "Perdido";
  const isStuck = status !== "Venta" && status !== "Perdido" && (index % 10 === 0 || (status === "Visitado" && index % 4 === 0));
  const value = AVERAGE_MEMBERSHIP_VALUE_FAKE + (index % 5) * 10;
  const activities = 1 + (index % 6) + (status === "Venta" ? 2 : 0);

  return {
    id: `lead_demo_${String(index + 1).padStart(4, "0")}`,
    name: `Prospecto Demo ${String(index + 1).padStart(4, "0")}`,
    branch,
    advisorId: advisor.id,
    advisor: advisor.name,
    source,
    status,
    temperature,
    createdDay: day,
    nextFollowUpDay: followUpDay,
    overdueHours: isOverdue ? (9 - followUpDay) * 24 + (index % 8) * 3 : 0,
    agingBucket: isOverdue
      ? followUpDay <= 1
        ? "8+ dias"
        : followUpDay <= 5
          ? "4-7 dias"
          : followUpDay <= 7
            ? "2-3 dias"
            : "1 dia"
      : "Hoy",
    isOverdue,
    isStuck,
    isDueToday: followUpDay === 9 && status !== "Venta" && status !== "Perdido",
    estimatedValue: value,
    activities,
    calls: 1 + (index % 4),
    messages: 1 + (index % 5),
    visits: status === "Cita agendada" || status === "Visitado" || status === "Venta" ? 1 : 0,
  };
});

const executiveActivitiesByDay = WEEK_DAYS.map((day, index) => ({
  day,
  count: executiveLeads.reduce((sum, lead) => sum + (lead.createdDay % 7 === index ? lead.activities : 0), 0),
}));

function normalizeClass(value) {
  return value.toLowerCase().replaceAll(" ", "-");
}

function needsFollowUp(lead) {
  return lead.nextFollowUp < TODAY && lead.managementStatus !== "Venta";
}

function isPending(lead) {
  return ["Seguimiento", "No contacto", "Ilocalizable", "Promesa de compra"].includes(lead.managementStatus);
}

function isManaged(lead) {
  return lead.managementStatus !== "No contacto";
}

function countStatus(rows, status) {
  return rows.filter((lead) => lead.managementStatus === status).length;
}

function operatorRows() {
  const advisor = operatorAdvisorFilter.value || leads[0].advisor;
  return leads.filter((lead) => lead.advisor === advisor);
}

function filteredLeads() {
  const assignedRows = operatorRows();
  if (activeFilter === "pendientes") {
    return assignedRows.filter(isPending);
  }
  if (activeFilter === "alta") {
    return assignedRows.filter((lead) => lead.priority === "Alta");
  }
  if (activeFilter === "citas") {
    return assignedRows.filter((lead) => lead.appointmentScheduled);
  }
  return assignedRows;
}

function statusPill(status) {
  return `<span class="status-pill ${STATUS_CLASSES[status]}">${status}</span>`;
}

function renderLeadList() {
  const rows = filteredLeads();
  const assignedRows = operatorRows();
  recordCount.textContent = `${rows.length} registros`;
  document.querySelector("#operatorAssignedMetric").textContent = assignedRows.length;
  document.querySelector("#operatorManagedMetric").textContent = assignedRows.filter(isManaged).length;
  document.querySelector("#operatorPendingMetric").textContent = assignedRows.filter(isPending).length;
  document.querySelector("#operatorSalesMetric").textContent = countStatus(assignedRows, "Venta");
  document.querySelector("#operatorPromisesMetric").textContent = countStatus(assignedRows, "Promesa de compra");
  document.querySelector("#operatorFollowUpsMetric").textContent = countStatus(assignedRows, "Seguimiento");
  document.querySelector("#operatorUnreachableMetric").textContent = countStatus(assignedRows, "Ilocalizable");
  document.querySelector("#operatorNoContactMetric").textContent = countStatus(assignedRows, "No contacto");

  if (!rows.some((lead) => lead.id === selectedId) && rows[0]) {
    selectedId = rows[0].id;
  }

  leadList.innerHTML = rows
    .map(
      (lead) => `
        <button class="lead-card ${lead.id === selectedId ? "active" : ""}" type="button" data-id="${lead.id}">
          <div class="lead-top">
            <strong>${lead.name}</strong>
            ${statusPill(lead.managementStatus)}
          </div>
          <div class="lead-meta">
            <span>${lead.branch}</span>
            <span>${lead.advisor} · ${lead.shift}</span>
          </div>
          <div class="lead-meta">
            <span>Último: ${lead.lastContact}</span>
            <span>Próximo: ${lead.nextFollowUp}</span>
          </div>
          <div class="lead-meta">
            <span>Prioridad ${lead.priority}</span>
            <span>Estado socio: ${lead.memberStatus}</span>
          </div>
          <div class="lead-meta">
            <span>Estado de gestión: ${lead.managementStatus}</span>
            <span>${lead.channel}</span>
          </div>
        </button>
      `
    )
    .join("");
}

function renderDetail() {
  const lead = leads.find((item) => item.id === selectedId) || leads[0];
  const [nextActionDate, nextActionText] = lead.nextAction.includes(" - ")
    ? lead.nextAction.split(" - ")
    : [lead.nextFollowUp, lead.nextAction];
  document.querySelector("#detailName").textContent = lead.name;
  document.querySelector("#detailPhone").textContent = `Celular: ${lead.phone}`;
  document.querySelector("#detailEmail").textContent = `Correo electrónico: ${lead.email}`;
  document.querySelector("#detailBranch").textContent = lead.branch;
  document.querySelector("#detailAdvisor").textContent = lead.advisor;
  document.querySelector("#detailShift").textContent = lead.shift;
  document.querySelector("#detailInterest").textContent = lead.interest;
  document.querySelector("#detailLastPlan").textContent = lead.lastPlan;
  document.querySelector("#detailOfferedPlan").textContent = lead.offeredPlan;
  document.querySelector("#detailMemberStatus").textContent = lead.memberStatus;
  document.querySelector("#detailManagementStatus").textContent = lead.managementStatus;
  document.querySelector("#detailLastContact").textContent = lead.lastContact;
  document.querySelector("#detailNextAction").textContent = `${lead.nextFollowUp} - ${lead.nextAction}`;
  document.querySelector("#detailChannel").textContent = lead.channel;
  document.querySelector("#detailSourceFile").textContent = lead.sourceFile;
  document.querySelector("#detailTools").textContent = lead.currentTools;
  document.querySelector("#detailNotes").textContent = lead.notes;
  document.querySelector("#nextActionInput").value = nextActionText;
  document.querySelector("#nextActionDateInput").value = nextActionDate || lead.nextFollowUp;
  document.querySelector("#managementNoteInput").value = lead.managementNote;
  document.querySelector("#offeredPlanSelect").value = lead.offeredPlan;

  const priority = document.querySelector("#detailPriority");
  priority.textContent = `Prioridad ${lead.priority}`;
  priority.className = `priority-pill ${normalizeClass(lead.priority)}`;

  document.querySelector("#detailHistory").innerHTML = lead.history.map((item) => `<li>${item}</li>`).join("");

  document.querySelectorAll(".status-actions button").forEach((button) => {
    button.classList.toggle("active", button.dataset.managementStatus === lead.managementStatus);
  });
}

function populateFilters() {
  const branches = ["Todas", ...EXECUTIVE_BRANCHES];
  const advisors = ["Todos", ...executiveAdvisors.map((advisor) => advisor.name)];
  const operatorAdvisors = [...new Set(leads.map((lead) => lead.advisor))];
  operatorAdvisorFilter.innerHTML = operatorAdvisors.map((advisor) => `<option value="${advisor}">${advisor}</option>`).join("");
  operatorAdvisorFilter.value = operatorAdvisors[0] || "";
  branchFilter.innerHTML = branches.map((branch) => `<option value="${branch}">${branch}</option>`).join("");
  advisorFilter.innerHTML = advisors.map((advisor) => `<option value="${advisor}">${advisor}</option>`).join("");
  sourceFilter.innerHTML = ["Todos", ...EXECUTIVE_SOURCES].map((source) => `<option value="${source}">${source}</option>`).join("");
  statusFilter.innerHTML = ["Todos", ...EXECUTIVE_STATUSES].map((status) => `<option value="${status}">${status}</option>`).join("");
  temperatureFilter.innerHTML = ["Todas", ...TEMPERATURES].map((temperature) => `<option value="${temperature}">${temperature}</option>`).join("");
  selectedId = operatorRows()[0]?.id || leads[0].id;
}

function managerRows() {
  return executiveLeads.filter((lead) => {
    const branchOk = branchFilter.value === "Todas" || lead.branch === branchFilter.value;
    const advisorOk = advisorFilter.value === "Todos" || lead.advisor === advisorFilter.value;
    const sourceOk = sourceFilter.value === "Todos" || lead.source === sourceFilter.value;
    const statusOk = statusFilter.value === "Todos" || lead.status === statusFilter.value;
    const temperatureOk = temperatureFilter.value === "Todas" || lead.temperature === temperatureFilter.value;
    return branchOk && advisorOk && sourceOk && statusOk && temperatureOk;
  });
}

function branchRowsForBreakdown() {
  return executiveLeads.filter((lead) => branchFilter.value === "Todas" || lead.branch === branchFilter.value);
}

function progressPercent(rows) {
  if (!rows.length) {
    return 0;
  }
  const managed = rows.filter((lead) => lead.status !== "Nuevo").length;
  return Math.round((managed / rows.length) * 100);
}

function formatMoney(value) {
  return `$${Math.round(value).toLocaleString("en-US")}`;
}

function pct(part, total) {
  return total ? Math.round((part / total) * 100) : 0;
}

function statusCount(rows, status) {
  return rows.filter((lead) => lead.status === status).length;
}

function isAtRisk(lead) {
  return lead.isOverdue || lead.isStuck || (lead.temperature === "Hot" && !lead.isDueToday && lead.status !== "Venta" && lead.status !== "Perdido");
}

function recoveryProbability(lead) {
  if (lead.isStuck && lead.status === "Visitado") return 0.3;
  if (lead.temperature === "Hot") return 0.35;
  if (lead.temperature === "Warm") return 0.2;
  return 0.05;
}

function groupBy(rows, key) {
  return rows.reduce((groups, row) => {
    const groupKey = row[key];
    groups[groupKey] = groups[groupKey] || [];
    groups[groupKey].push(row);
    return groups;
  }, {});
}

function advisorStats(rows) {
  const grouped = groupBy(rows, "advisor");
  return Object.entries(grouped).map(([advisor, advisorRows]) => {
    const converted = statusCount(advisorRows, "Venta");
    const open = advisorRows.filter((lead) => lead.status !== "Venta" && lead.status !== "Perdido").length;
    const overdue = advisorRows.filter((lead) => lead.isOverdue).length;
    const activity = advisorRows.reduce((sum, lead) => sum + lead.activities + lead.calls + lead.messages + lead.visits, 0);
    return {
      advisor,
      branch: advisorRows[0].branch,
      assigned: advisorRows.length,
      activity,
      converted,
      open,
      overdue,
      risk: advisorRows.filter(isAtRisk).length,
      conversion: pct(converted, advisorRows.length),
      value: advisorRows.reduce((sum, lead) => sum + (lead.status === "Venta" ? lead.estimatedValue : 0), 0),
    };
  });
}

function renderBars(containerId, rows, labelKey, valueKey, detail) {
  if (!rows.length) {
    document.querySelector(containerId).innerHTML = `<article><div><strong>Sin datos para este filtro</strong><span>Ajuste filtros de demo</span></div><div class="bar-track"><span style="width: 5%"></span></div></article>`;
    return;
  }
  const max = Math.max(...rows.map((row) => row[valueKey]), 1);
  document.querySelector(containerId).innerHTML = rows
    .map((row) => `
      <article>
        <div>
          <strong>${row[labelKey]}</strong>
          <span>${detail(row)}</span>
        </div>
        <div class="bar-track"><span style="width: ${Math.max(5, Math.round((row[valueKey] / max) * 100))}%"></span></div>
      </article>
    `)
    .join("");
}

function renderManager() {
  const rows = managerRows();
  const activeRows = rows.filter((lead) => lead.status !== "Venta" && lead.status !== "Perdido");
  const dueTodayRows = rows.filter((lead) => lead.isDueToday);
  const overdueRows = rows.filter((lead) => lead.isOverdue);
  const riskRows = rows.filter(isAtRisk);
  const recoverable = riskRows.reduce((sum, lead) => sum + lead.estimatedValue * recoveryProbability(lead), 0);
  const atRiskValue = riskRows.reduce((sum, lead) => sum + lead.estimatedValue, 0);

  document.querySelector("#assignedMetric").textContent = activeRows.length.toLocaleString("en-US");
  document.querySelector("#pendingMetric").textContent = dueTodayRows.length.toLocaleString("en-US");
  document.querySelector("#promisesMetric").textContent = statusCount(rows, "Interesado").toLocaleString("en-US");
  document.querySelector("#salesMetric").textContent = statusCount(rows, "Venta").toLocaleString("en-US");
  document.querySelector("#followUpsMetric").textContent = rows.filter((lead) => lead.status === "Contactado" || lead.status === "Cita agendada").length.toLocaleString("en-US");
  document.querySelector("#noContactMetric").textContent = overdueRows.length.toLocaleString("en-US");
  document.querySelector("#unreachableMetric").textContent = riskRows.length.toLocaleString("en-US");
  document.querySelector("#atRiskValueMetric").textContent = formatMoney(atRiskValue);
  document.querySelector("#recoverableValueMetric").textContent = formatMoney(recoverable);
  document.querySelector("#hotRiskMetric").textContent = riskRows.filter((lead) => lead.temperature === "Hot").length.toLocaleString("en-US");
  document.querySelector("#recoveryNarrativeValue").textContent = `Estimacion demo: ${formatMoney(recoverable)} rescatables.`;

  const monthProgress = progressPercent(rows);
  document.querySelector("#monthProgressMetric").textContent = `${monthProgress}%`;
  document.querySelector("#monthProgressLabel").textContent = `${rows.filter((lead) => lead.status !== "Nuevo").length} de ${rows.length} gestionados`;
  document.querySelector("#monthProgressBar").style.width = `${monthProgress}%`;

  const branchNames = [...new Set(rows.map((lead) => lead.branch))];
  document.querySelector("#branchTableBody").innerHTML = branchNames
    .map((branch) => {
      const branchRows = rows.filter((lead) => lead.branch === branch);
      const branchRisk = branchRows.filter(isAtRisk).length;
      return `
        <tr>
          <td>${branch}</td>
          <td>${branchRows.length}</td>
          <td>${statusCount(branchRows, "Venta")}</td>
          <td>${statusCount(branchRows, "Interesado")}</td>
          <td>${statusCount(branchRows, "Contactado") + statusCount(branchRows, "Cita agendada")}</td>
          <td>${branchRows.filter((lead) => lead.isOverdue).length}</td>
          <td>${branchRisk}</td>
          <td>${branchRows.filter((lead) => lead.isDueToday).length}</td>
          <td>${formatMoney(branchRows.reduce((sum, lead) => sum + lead.estimatedValue, 0))}</td>
        </tr>
      `;
    })
    .join("");

  const breakdownRows = rows.length ? rows : branchRowsForBreakdown();
  const advisorRows = advisorStats(breakdownRows);
  document.querySelector("#advisorTableBody").innerHTML = advisorRows
    .sort((a, b) => b.assigned - a.assigned)
    .slice(0, 24)
    .map((row) => {
      const advisorLeadRows = breakdownRows.filter((lead) => lead.advisor === row.advisor);
      const normalizedRow = row || {
        assigned: 0,
        converted: 0,
        overdue: 0,
        risk: 0,
        conversion: 0,
      };
      return `
        <tr>
          <td>${row.advisor}</td>
          <td>${normalizedRow.assigned}</td>
          <td>${normalizedRow.converted}</td>
          <td>${statusCount(advisorLeadRows, "Interesado")}</td>
          <td>${statusCount(advisorLeadRows, "Contactado")}</td>
          <td>${normalizedRow.overdue}</td>
          <td>${normalizedRow.risk}</td>
          <td>${advisorLeadRows.filter((lead) => lead.isDueToday).length}</td>
          <td>${normalizedRow.conversion}%</td>
        </tr>
      `;
    })
    .join("");

  const topBy = (key) => advisorRows.reduce((best, row) => (!best || row[key] > best[key] ? row : best), null);
  const topSales = topBy("converted");
  const topPending = topBy("open");
  const topNoContact = topBy("overdue");
  const topUnreachable = topBy("risk");
  document.querySelector("#coachingSummary").innerHTML = [
    ["Mas ventas", topSales, "converted"],
    ["Mas pendientes", topPending, "open"],
    ["Mas atraso", topNoContact, "overdue"],
    ["Mas riesgo", topUnreachable, "risk"],
  ]
    .map(([label, row, key]) => `<article><span>${label}</span><strong>${row ? row.advisor : "-"}</strong><p>${row ? row[key] : 0} registros</p></article>`)
    .join("");

  document.querySelector("#activityRankingList").innerHTML = [...advisorRows]
    .sort((a, b) => b.activity - a.activity)
    .slice(0, 8)
    .map((row) => `<li><strong>${row.advisor}</strong><span>${row.activity} actividades - ${row.branch}</span></li>`)
    .join("") || "<li>Sin datos para este filtro.</li>";

  document.querySelector("#resultRankingList").innerHTML = [...advisorRows]
    .sort((a, b) => b.converted - a.converted || b.conversion - a.conversion)
    .slice(0, 8)
    .map((row) => `<li><strong>${row.advisor}</strong><span>${row.converted} ventas - ${row.conversion}% conversion</span></li>`)
    .join("") || "<li>Sin datos para este filtro.</li>";

  document.querySelector("#riskList").innerHTML = riskRows
    .slice(0, 8)
    .map((lead) => `<li><strong>${lead.advisor}</strong> - ${lead.branch}. ${lead.name} en ${lead.status}; ${lead.isOverdue ? `${lead.overdueHours}h de atraso` : "sin proximo paso claro"}.</li>`)
    .join("") || "<li>No hay oportunidades en riesgo para este filtro.</li>";

  document.querySelector("#pendingFollowUpsList").innerHTML = dueTodayRows
    .slice(0, 7)
    .map((lead) => `<li><strong>${lead.name}</strong><span>${lead.advisor} - ${lead.branch} - ${lead.temperature}</span></li>`)
    .join("") || "<li>No hay pendientes para hoy con este filtro.</li>";

  document.querySelector("#overdueFollowUpsList").innerHTML = overdueRows
    .sort((a, b) => b.overdueHours - a.overdueHours)
    .slice(0, 7)
    .map((lead) => `<li><strong>${lead.name}</strong><span>${lead.overdueHours}h - ${lead.advisor} - ${formatMoney(lead.estimatedValue)}</span></li>`)
    .join("") || "<li>No hay seguimiento atrasado con este filtro.</li>";

  const agingRows = ["Hoy", "1 dia", "2-3 dias", "4-7 dias", "8+ dias"].map((bucket) => ({
    label: bucket,
    count: rows.filter((lead) => lead.agingBucket === bucket).length,
  }));
  renderBars("#agingChart", agingRows, "label", "count", (row) => `${row.count} seguimientos`);

  const funnelRows = EXECUTIVE_STATUSES.map((status) => ({
    label: status,
    count: statusCount(rows, status),
  }));
  renderBars("#statusFunnel", funnelRows, "label", "count", (row) => `${row.count} registros`);

  const sourceRows = Object.entries(groupBy(rows, "source"))
    .map(([source, sourceRows]) => ({
      source,
      count: sourceRows.length,
      converted: statusCount(sourceRows, "Venta"),
      conversion: pct(statusCount(sourceRows, "Venta"), sourceRows.length),
    }))
    .sort((a, b) => b.conversion - a.conversion || b.count - a.count)
    .slice(0, 8);
  renderBars("#sourcePerformance", sourceRows, "source", "count", (row) => `${row.converted} ventas - ${row.conversion}% conversion`);

  const maxActivity = Math.max(...executiveActivitiesByDay.map((item) => item.count), 1);
  document.querySelector("#activityTrend").innerHTML = executiveActivitiesByDay
    .map((item) => `
      <article>
        <span style="height: ${Math.max(16, Math.round((item.count / maxActivity) * 120))}px"></span>
        <strong>${item.day}</strong>
        <em>${item.count}</em>
      </article>
    `)
    .join("");

  document.querySelector("#stuckOpportunitiesList").innerHTML = rows
    .filter((lead) => lead.isStuck)
    .slice(0, 8)
    .map((lead) => `<li><strong>${lead.name}</strong><span>${lead.status} - ${lead.branch} - rescatar ${formatMoney(lead.estimatedValue * recoveryProbability(lead))}</span></li>`)
    .join("") || "<li>No hay stuck opportunities para este filtro.</li>";

  const weakestBranch = Object.entries(groupBy(rows, "branch"))
    .map(([branch, branchRows]) => ({ branch, overdue: branchRows.filter((lead) => lead.isOverdue).length, total: branchRows.length }))
    .sort((a, b) => pct(b.overdue, b.total) - pct(a.overdue, a.total))[0];
  const noisySource = sourceRows.sort((a, b) => b.count - a.count || a.conversion - b.conversion)[0];
  const topRiskAdvisor = topUnreachable;
  document.querySelector("#managerActionPrompts").innerHTML = [
    ["Rescatar hoy", `${riskRows.filter((lead) => lead.temperature === "Hot").length} hot leads en riesgo. Priorizar llamadas manuales y reasignacion si el asesor no puede actuar.`],
    ["Coaching de asesor", `${topRiskAdvisor ? topRiskAdvisor.advisor : "-"} concentra riesgo. Revisar calidad de contacto y seguimiento atrasado.`],
    ["Inspeccionar sucursal", `${weakestBranch ? weakestBranch.branch : "-"} muestra mayor tasa de atraso. Revisar carga y disciplina de seguimiento.`],
    ["Revisar canal", `${noisySource ? noisySource.source : "-"} genera volumen. Validar si convierte o consume tiempo de asesores.`],
    ["Cerrar ciclo", `${rows.filter((lead) => lead.status === "Visitado" && lead.isStuck).length} visitas sin desenlace. Exigir proxima accion.`],
  ]
    .map(([title, copy]) => `<article><span>${title}</span><strong>${copy}</strong></article>`)
    .join("");
}

function switchView(view) {
  const managerActive = view === "manager";
  operatorView.classList.toggle("active-view", !managerActive);
  operatorView.hidden = managerActive;
  managerView.hidden = !managerActive;
  operatorTab.classList.toggle("active", !managerActive);
  managerTab.classList.toggle("active", managerActive);
  operatorTab.setAttribute("aria-selected", String(!managerActive));
  managerTab.setAttribute("aria-selected", String(managerActive));
  if (managerActive) {
    renderManager();
  }
}

leadList.addEventListener("click", (event) => {
  const card = event.target.closest(".lead-card");
  if (!card) return;
  selectedId = card.dataset.id;
  renderLeadList();
  renderDetail();
});

document.querySelectorAll(".chip").forEach((button) => {
  button.addEventListener("click", () => {
    activeFilter = button.dataset.filter;
    document.querySelectorAll(".chip").forEach((chip) => chip.classList.toggle("active", chip === button));
    renderLeadList();
  });
});

operatorAdvisorFilter.addEventListener("change", () => {
  selectedId = operatorRows()[0]?.id || leads[0].id;
  renderLeadList();
  renderDetail();
});

document.querySelectorAll(".status-actions button").forEach((button) => {
  button.addEventListener("click", () => {
    const lead = leads.find((item) => item.id === selectedId);
    lead.managementStatus = button.dataset.managementStatus;
    lead.history = [`Demo: Estado de gestión marcado como ${lead.managementStatus}.`, ...lead.history];
    renderLeadList();
    renderDetail();
    renderManager();
  });
});

document.querySelector("#offeredPlanSelect").addEventListener("change", (event) => {
  const lead = leads.find((item) => item.id === selectedId);
  lead.offeredPlan = event.target.value;
  renderDetail();
});

document.querySelector("#nextActionInput").addEventListener("input", (event) => {
  const lead = leads.find((item) => item.id === selectedId);
  lead.nextAction = event.target.value;
  renderLeadList();
});

document.querySelector("#nextActionDateInput").addEventListener("change", (event) => {
  const lead = leads.find((item) => item.id === selectedId);
  lead.nextFollowUp = event.target.value;
  renderLeadList();
  renderManager();
});

document.querySelector("#managementNoteInput").addEventListener("input", (event) => {
  const lead = leads.find((item) => item.id === selectedId);
  lead.managementNote = event.target.value;
});

operatorTab.addEventListener("click", () => switchView("operator"));
managerTab.addEventListener("click", () => switchView("manager"));
branchFilter.addEventListener("change", renderManager);
advisorFilter.addEventListener("change", renderManager);
sourceFilter.addEventListener("change", renderManager);
statusFilter.addEventListener("change", renderManager);
temperatureFilter.addEventListener("change", renderManager);

populateFilters();
renderLeadList();
renderDetail();
renderManager();
