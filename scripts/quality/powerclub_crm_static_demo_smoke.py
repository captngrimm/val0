#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = ROOT / "docs/demo/powerclub_crm"
HTML = DEMO_DIR / "index.html"
CSS = DEMO_DIR / "styles.css"
JS = DEMO_DIR / "app.js"
DOC = ROOT / "docs/product/POWERCLUB_CRM_01B_STATIC_DUMMY_DEMO.md"
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
    for path in (HTML, CSS, JS, DOC):
        assert_true(path.exists(), f"{path.relative_to(ROOT)} exists")


def test_spanish_labels_and_branding() -> None:
    text = read_demo()
    for needle in (
        "Val AI Ops Discovery",
        "Isthmus Dynamics",
        "Honest AI Ops",
        "Power Club CRM Pilot",
        "CRM Operativo Ligero",
        "Vista asesores",
        "Vista gerencial",
        "Lista de socios y prospectos",
        "Sucursal",
        "Asesor",
        "Último contacto",
        "Próxima acción",
        "Prioridad",
        "Teléfono",
        "Tipo de interés",
        "Estado socio",
        "Estado de gestión",
        "Turno",
        "Canal",
        "Archivo actual",
        "Herramientas actuales",
        "Notas",
        "Historial de interacción",
    ):
        assert_contains(text, needle, "Spanish UI labels and branding")


def test_disclaimer_statuses_and_manager_metrics() -> None:
    text = read_demo()
    for needle in (
        "Demo con datos ficticios. No usa información real de Power Club.",
        "Leads abiertos",
        "Seguimientos vencidos",
        "Citas agendadas",
        "Conversiones simuladas",
        "Filtro por sucursal",
        "Filtro por asesor",
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


def test_no_real_data_or_promise_violations() -> None:
    text = read_demo()
    for needle in (
        "datos reales de Power Club en la demo",
        "informacion real de Power Club incluida",
        "integracion de pagos incluida",
        "automatizacion por WhatsApp incluida",
        "CRM de produccion listo",
        "reemplaza el CRM actual desde hoy",
        "API conectada",
        "backend activo",
        "full SaaS",
        "Karen",
        "chat log",
        "transcript",
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
    test_estado_de_gestion_values_and_interpretation()
    test_static_no_network_or_auth_or_backend()
    test_no_real_data_or_promise_violations()
    test_forbidden_files_not_touched()
    print("PASS: Power Club CRM static demo smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
