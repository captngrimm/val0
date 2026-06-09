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
  const branches = ["Todas", ...new Set(leads.map((lead) => lead.branch))];
  const advisors = ["Todos", ...new Set(leads.map((lead) => lead.advisor))];
  const operatorAdvisors = [...new Set(leads.map((lead) => lead.advisor))];
  operatorAdvisorFilter.innerHTML = operatorAdvisors.map((advisor) => `<option value="${advisor}">${advisor}</option>`).join("");
  operatorAdvisorFilter.value = operatorAdvisors[0] || "";
  branchFilter.innerHTML = branches.map((branch) => `<option value="${branch}">${branch}</option>`).join("");
  advisorFilter.innerHTML = advisors.map((advisor) => `<option value="${advisor}">${advisor}</option>`).join("");
  selectedId = operatorRows()[0]?.id || leads[0].id;
}

function managerRows() {
  return leads.filter((lead) => {
    const branchOk = branchFilter.value === "Todas" || lead.branch === branchFilter.value;
    const advisorOk = advisorFilter.value === "Todos" || lead.advisor === advisorFilter.value;
    return branchOk && advisorOk;
  });
}

function branchRowsForBreakdown() {
  return leads.filter((lead) => branchFilter.value === "Todas" || lead.branch === branchFilter.value);
}

function progressPercent(rows) {
  if (!rows.length) {
    return 0;
  }
  const managed = rows.filter(isManaged).length;
  return Math.round((managed / rows.length) * 100);
}

function renderManager() {
  const rows = managerRows();
  document.querySelector("#assignedMetric").textContent = rows.length;
  document.querySelector("#pendingMetric").textContent = rows.filter(isPending).length;
  document.querySelector("#promisesMetric").textContent = countStatus(rows, "Promesa de compra");
  document.querySelector("#salesMetric").textContent = countStatus(rows, "Venta");
  document.querySelector("#followUpsMetric").textContent = countStatus(rows, "Seguimiento");
  document.querySelector("#noContactMetric").textContent = countStatus(rows, "No contacto");
  document.querySelector("#unreachableMetric").textContent = countStatus(rows, "Ilocalizable");

  const monthProgress = progressPercent(rows);
  document.querySelector("#monthProgressMetric").textContent = `${monthProgress}%`;
  document.querySelector("#monthProgressLabel").textContent = `${rows.filter(isManaged).length} de ${rows.length} gestionados`;
  document.querySelector("#monthProgressBar").style.width = `${monthProgress}%`;

  const branchNames = [...new Set(rows.map((lead) => lead.branch))];
  document.querySelector("#branchTableBody").innerHTML = branchNames
    .map((branch) => {
      const branchRows = rows.filter((lead) => lead.branch === branch);
      return `
        <tr>
          <td>${branch}</td>
          <td>${branchRows.length}</td>
          <td>${countStatus(branchRows, "Venta")}</td>
          <td>${countStatus(branchRows, "Promesa de compra")}</td>
          <td>${countStatus(branchRows, "Seguimiento")}</td>
          <td>${countStatus(branchRows, "No contacto")}</td>
          <td>${countStatus(branchRows, "Ilocalizable")}</td>
          <td>${branchRows.filter(isPending).length}</td>
        </tr>
      `;
    })
    .join("");

  const breakdownRows = branchRowsForBreakdown();
  const advisorNames = [...new Set(breakdownRows.map((lead) => lead.advisor))];
  document.querySelector("#advisorTableBody").innerHTML = advisorNames
    .map((advisor) => {
      const advisorRows = breakdownRows.filter((lead) => lead.advisor === advisor);
      return `
        <tr>
          <td>${advisor}</td>
          <td>${advisorRows.length}</td>
          <td>${countStatus(advisorRows, "Venta")}</td>
          <td>${countStatus(advisorRows, "Promesa de compra")}</td>
          <td>${countStatus(advisorRows, "Seguimiento")}</td>
          <td>${countStatus(advisorRows, "No contacto")}</td>
          <td>${countStatus(advisorRows, "Ilocalizable")}</td>
          <td>${advisorRows.filter(isPending).length}</td>
        </tr>
      `;
    })
    .join("");

  const advisorStats = advisorNames.map((advisor) => {
    const advisorRows = breakdownRows.filter((lead) => lead.advisor === advisor);
    return {
      advisor,
      sales: countStatus(advisorRows, "Venta"),
      pending: advisorRows.filter(isPending).length,
      noContact: countStatus(advisorRows, "No contacto"),
      unreachable: countStatus(advisorRows, "Ilocalizable"),
    };
  });
  const topBy = (key) => advisorStats.reduce((best, row) => (!best || row[key] > best[key] ? row : best), null);
  const topSales = topBy("sales");
  const topPending = topBy("pending");
  const topNoContact = topBy("noContact");
  const topUnreachable = topBy("unreachable");
  document.querySelector("#coachingSummary").innerHTML = [
    ["Más ventas", topSales, "sales"],
    ["Más pendientes", topPending, "pending"],
    ["Más no contacto", topNoContact, "noContact"],
    ["Más ilocalizables", topUnreachable, "unreachable"],
  ]
    .map(([label, row, key]) => `<article><span>${label}</span><strong>${row ? row.advisor : "-"}</strong><p>${row ? row[key] : 0} registros</p></article>`)
    .join("");

  const risks = rows
    .filter((lead) => lead.managementStatus === "No contacto" || lead.managementStatus === "Ilocalizable" || (lead.managementStatus === "Promesa de compra" && needsFollowUp(lead)))
    .reduce((groups, lead) => {
      const key = `${lead.branch}|${lead.advisor}|${lead.managementStatus}`;
      groups[key] = groups[key] || { branch: lead.branch, advisor: lead.advisor, status: lead.managementStatus, count: 0 };
      groups[key].count += 1;
      return groups;
    }, {});
  document.querySelector("#riskList").innerHTML = Object.values(risks)
    .slice(0, 8)
    .map((group) => `<li><strong>${group.advisor}</strong> - ${group.branch}. ${group.count} registros en ${group.status}.</li>`)
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

populateFilters();
renderLeadList();
renderDetail();
renderManager();
