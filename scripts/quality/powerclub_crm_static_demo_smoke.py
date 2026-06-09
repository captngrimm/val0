#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = ROOT / "docs/demo/powerclub_crm"
ASSET_DIR = DEMO_DIR / "assets"
HTML = DEMO_DIR / "index.html"
CSS = DEMO_DIR / "styles.css"
JS = DEMO_DIR / "app.js"
DOC = ROOT / "docs/product/POWERCLUB_CRM_01B_STATIC_DUMMY_DEMO.md"
LOGO_HORIZONTAL = ASSET_DIR / "powerclub-logo-horizontal.png"
LOGO_SQUARE = ASSET_DIR / "powerclub-logo-square.png"
PROTECTED = (
    "bot.py",
    "core",
    "clients",
)


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r}")


def read(path: Path) -> str:
    assert_true(path.exists(), f"{path.relative_to(ROOT)} exists")
    return path.read_text(encoding="utf-8")


def read_demo() -> str:
    return "\n\n".join(read(path) for path in (HTML, CSS, JS, DOC))


def test_required_files_exist() -> None:
    for path in (HTML, CSS, JS, DOC, LOGO_HORIZONTAL, LOGO_SQUARE):
        assert_true(path.exists(), f"{path.relative_to(ROOT)} exists")


def test_spanish_labels_and_branding() -> None:
    text = read_demo()
    for needle in (
        "Val AI Ops Discovery",
        "Isthmus Dynamics",
        "Honest AI Ops",
        "Power Club CRM Pilot",
        "CRM Operativo Ligero",
        "./assets/powerclub-logo-horizontal.png",
        "./assets/powerclub-logo-square.png",
        "powerclub-wordmark",
        "powerclub-mark",
        "Vista asesores",
        "Vista gerencial",
        "Mis socios y prospectos asignados",
        "Sucursal",
        "Asesor",
        "Último contacto",
        "Próxima acción",
        "Prioridad",
        "Teléfono",
        "Celular",
        "Correo electrónico",
        "Tipo de interés",
        "Último plan adquirido",
        "Plan ofrecido",
        "Estado socio",
        "Estado de gestión",
        "Turno",
        "Canal",
        "Archivo actual",
        "Herramientas actuales",
        "Mini-dashboard acumulado del asesor",
        "Total asignados",
        "Total gestionados",
        "Notas",
        "Historial de interacción",
        "Ficha del socio",
    ):
        assert_contains(text, needle, "Spanish UI labels and branding")


def test_disclaimer_statuses_and_manager_metrics() -> None:
    text = read_demo()
    for needle in (
        "Demo con datos ficticios. No usa información real de Power Club.",
        "Socios asignados",
        "Socios por gestionar",
        "Pendientes por gestionar",
        "Total asignados",
        "Total gestionados",
        "Ventas",
        "Promesas de compra",
        "Seguimientos",
        "No contacto",
        "Ilocalizables",
        "Avance del mes",
        "Corte medio mes",
        "Distribución por sucursal",
        "Breakdown por asesor",
        "No contacto / Ilocalizables / Promesas de compra",
        "Filtro de sucursal",
        "Filtro de asesor",
        "TOTAL_FAKE_RECORDS = 60",
        "createGeneratedRecords(TOTAL_FAKE_RECORDS - leads.length)",
    ):
        assert_contains(text, needle, "demo disclaimer/statuses/metrics")


def test_operator_workflow_alignment() -> None:
    text = read_demo()
    for needle in (
        "turnos",
        "Inicio de turno",
        "Continuidad",
        "continuidad entre turnos",
        "correo",
        "Google Drive",
        "celular",
        "archivos por nombre",
        "Archivo por nombre",
        "seguimiento centralizado",
        "historial de contacto",
        "Próximo paso visible",
        "visibilidad gerencial",
        "asesor",
        "sucursal",
        "Venta presencial",
        "ventas presenciales",
        "Llamada de socio",
        "llamadas de socios",
        "Laptop",
    ):
        assert_contains(text, needle, "operator workflow alignment")


def test_manager_realignment_labels_and_logic() -> None:
    text = read_demo()
    for needle in (
        "Vista asesor/operador",
        "Gerente general",
        "Gerente de sucursal",
        "macro totales",
        "comparación por sucursal",
        "coaching",
        "staffing",
        "salidas",
        "bonos",
        "operatorAdvisorFilter",
        "operatorAssignedMetric",
        "operatorManagedMetric",
        "operatorSalesMetric",
        "operatorPromisesMetric",
        "operatorFollowUpsMetric",
        "operatorUnreachableMetric",
        "operatorNoContactMetric",
        "operatorPendingMetric",
        "assignedMetric",
        "pendingMetric",
        "promisesMetric",
        "salesMetric",
        "followUpsMetric",
        "noContactMetric",
        "unreachableMetric",
        "monthProgressMetric",
        "advisorTableBody",
        "progressPercent",
        "branchRowsForBreakdown",
    ):
        assert_contains(text, needle, "manager dashboard realignment")


def test_operator_forms_plans_and_monthly_cycle() -> None:
    text = read_demo()
    for needle in (
        "Próxima acción",
        "Fecha próxima acción",
        "Nota de gestión",
        "nextActionInput",
        "nextActionDateInput",
        "managementNoteInput",
        "Último plan adquirido",
        "Plan ofrecido",
        "offeredPlanSelect",
        "Mensual $49",
        "Prepagado 1 mes",
        "Trimestral",
        "Semestral",
        "Anual",
        "Otro plan",
        "Excluido",
        "Contexto actual",
        "Carga mensual de base/listado",
        "Gestión durante el mes",
        "Cierre mensual",
        "Reporte final mensual",
        "Historial mensual archivado",
        "Exportar gestión a Excel",
        "Generar reporte mensual",
        "Cerrar mes / guardar cierre mensual",
        "Demo: exportación y cierre mensual representados de forma conceptual.",
        "En piloto real, el cierre mensual podría guardar resultados y permitir descarga Excel.",
    ):
        assert_contains(text, needle, "operator forms/plans/monthly cycle")


def test_role_visibility_language() -> None:
    text = read_demo()
    for needle in (
        "Modelo conceptual de visibilidad por rol",
        "Asesor / operador",
        "Ve solo sus registros asignados",
        "Gerente de sucursal",
        "Ve su sucursal y sus asesores",
        "Gerente general",
        "Ve todas las sucursales y puede entrar a una sucursal",
        "No hay autenticación real ni login en esta demo",
    ):
        assert_contains(text, needle, "role visibility language")


def test_asesor_selector_initializes_and_is_readable() -> None:
    text = read_demo()
    for needle in (
        "Asesor en turno",
        "operatorAdvisorFilter.value = operatorAdvisors[0]",
        "const advisor = operatorAdvisorFilter.value || leads[0].advisor",
        "operatorRows()",
        "operatorAssignedMetric",
        "operatorManagedMetric",
        "operatorPendingMetric",
        "operatorSalesMetric",
        "Asesor Demo A",
        "Asesor Demo B",
        "Asesor Demo C",
        "color-scheme: light",
        "option {",
        "background: #fff",
        "color: var(--ink)",
    ):
        assert_contains(text, needle, "asesor selector initialization/readability")


def test_estado_de_gestion_values_and_interpretation() -> None:
    text = read_demo()
    for needle in (
        "Estado de gestión",
        "Venta",
        "Promesa de compra",
        "Seguimiento",
        "Ilocalizable",
        "No contacto",
        "Estado socio describe",
        "Estado de gestión describe",
        "No son el mismo campo",
        "managementStatus",
        "memberStatus",
    ):
        assert_contains(text, needle, "Estado de gestión model")


def test_static_no_network_or_auth_or_backend() -> None:
    text = read(HTML) + "\n\n" + read(JS)
    for needle in (
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "http://",
        "https://",
        "localStorage",
        "sessionStorage",
        "cookie",
        "login",
        "password",
        "auth",
        "token",
    ):
        assert_not_contains(text, needle, "static demo avoids network/auth/persistence")

    html = read(HTML)
    for needle in (
        'src="http',
        "src='http",
        "url(http",
        "remote image",
    ):
        assert_not_contains(html, needle, "static demo avoids remote images")


def test_no_real_data_or_promise_violations() -> None:
    text = read_demo()
    for needle in (
        "datos reales de Power Club en la demo",
        "informacion real de Power Club incluida",
        "integracion de pagos incluida",
        "automatizacion por WhatsApp incluida",
        "CRM de produccion listo",
        "reemplaza el CRM actual desde hoy",
        "Leads abiertos",
        "Seguimientos vencidos",
        "Conversiones simuladas",
        "Oportunidades que requieren atención",
        "vencido",
        "vencidos",
        "Vencidos",
        "API conectada",
        "backend activo",
        "full SaaS",
        "Karen",
        "Carmen",
        "chat log",
        "transcript",
        "vencido",
        "vencidos",
        "Vencidos",
        "exportación real conectada",
        "descarga Excel implementada",
        "guardar resultados automáticamente",
        "CLIENT_FOLDERS.json",
        "CLIENT_GROCERY.md",
        "/clients/karen",
    ):
        assert_not_contains(text, needle, "demo avoids real data and production promises")


def test_forbidden_files_not_touched() -> None:
    proc = subprocess.run(
        ["git", "status", "--short", "--", *PROTECTED],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert_true(proc.stdout.strip() == "", "forbidden runtime/client files are untouched")


def main() -> int:
    test_required_files_exist()
    test_spanish_labels_and_branding()
    test_disclaimer_statuses_and_manager_metrics()
    test_operator_workflow_alignment()
    test_manager_realignment_labels_and_logic()
    test_operator_forms_plans_and_monthly_cycle()
    test_role_visibility_language()
    test_asesor_selector_initializes_and_is_readable()
    test_estado_de_gestion_values_and_interpretation()
    test_static_no_network_or_auth_or_backend()
    test_no_real_data_or_promise_violations()
    test_forbidden_files_not_touched()
    print("PASS: Power Club CRM static demo smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
