"""
Pruebas del Flujo 3 con el formulario de AS02 (BRP - Modificación), usando el
SAP FALSO de test_sap_as01.py. Se verifica que:
  - entra a AS02 y llena la pantalla inicial (activo, subnúmero, sociedad);
  - solo escribe las celdas con valor (en modificación, vacío = conservar);
  - recorre las 6 pestañas, con las casillas solo si traen valor;
  - NUNCA guarda (supervisión) y, aunque se permita guardar, AS02 se niega
    mientras no esté configurado su mensaje de éxito.
"""

import pytest

import config
from core.exceptions import SapError
from core.models import Solicitud
from flujos import flujo3_sap
from test_sap_as01 import GUARDAR, MENSAJE, FakeSap
from test_validacion_brp_modificacion import excel_modificacion

AS02 = config.SAP_FORMULARIO_AS02_BRP


def xpath_de(columna):
    return next(p["xpath"][0] for p in AS02 if p.get("columna") == columna)


@pytest.fixture(autouse=True)
def entorno(tmp_path, monkeypatch):
    monkeypatch.setattr(flujo3_sap, "SAP_GUARDAR_REAL", False)
    monkeypatch.setattr(flujo3_sap, "MODO_PRUEBAS_REEMPLAZO", False)
    monkeypatch.setattr(flujo3_sap, "MODO_PRUEBAS_SOLO_SAP", False)
    monkeypatch.setattr(flujo3_sap, "SAP_XPATH_MENSAJE_ESTADO", [])
    monkeypatch.setattr(flujo3_sap, "OUTPUT_DIR", str(tmp_path / "salidas"))


def solicitud(tmp_path, filas):
    ruta = excel_modificacion(tmp_path, filas)
    return Solicitud(case_id="prueba", tipo="brp", accion="modificacion", excel_path=ruta)


def test_as02_supervisado_llena_solo_lo_que_trae_valor(tmp_path):
    sap = FakeSap()
    pedidos = []
    sol = solicitud(tmp_path, [
        {"A": "7087147", "B": "1", "C": 1000, "X": "RO", "S": "LOCAL-1", "BI": "INICIO"},
        {"A": "7087188", "C": 1000, "W": "X", "AD": "X"},
    ])

    paso = flujo3_sap.cargar_a_sap(sap, sol, esperar_continuar=pedidos.append)

    # Pantalla inicial de AS02 de la fila 2, en orden, y luego Enter.
    assert sap.acciones[1:6] == [
        ("transaccion", "AS02"),
        ("escribir", xpath_de("A"), "7087147"),
        ("escribir", xpath_de("B"), "1"),
        ("escribir", xpath_de("C"), "1000"),
        ("enter",),
    ]
    escritos = [a for a in sap.acciones if a[0] == "escribir"]
    # Fila 2: además de A/B/C, solo X (estado), S (local) y BI (inicio).
    assert escritos[3:6] == [
        ("escribir", xpath_de("S"), "LOCAL-1"),
        ("escribir", xpath_de("X"), "RO"),
        ("escribir", xpath_de("BI"), "INICIO"),
    ]
    # Fila 3: sin subnúmero (B vacío no se escribe) y casillas W y AD con valor.
    assert ("escribir", xpath_de("A"), "7087188") in escritos
    assert sum(1 for a in escritos if a[1] == xpath_de("B")) == 1
    assert sap.acciones.count(("clic", xpath_de("W"))) == 1
    assert sap.acciones.count(("clic", xpath_de("AD"))) == 1
    assert ("clic", xpath_de("AE")) not in sap.acciones
    # 6 pestañas (5 cambios) por fila, nunca Guardar, "Continuar" por fila.
    assert sum(1 for a in sap.acciones if a[0] == "doble_clic" and "-title" in a[1]) == 10
    assert ("clic", GUARDAR[0]) not in sap.acciones
    assert len(pedidos) == 2 and "AS02" in pedidos[0]
    assert sap.acciones.count(("recargar",)) == 1
    assert paso == "Revisado en SAP SIN guardar (2 fila(s))"


def test_as02_no_guarda_aunque_se_permita_guardar(tmp_path, monkeypatch):
    monkeypatch.setattr(flujo3_sap, "SAP_GUARDAR_REAL", True)
    monkeypatch.setattr(flujo3_sap, "SAP_XPATH_MENSAJE_ESTADO", MENSAJE)
    sap = FakeSap()
    with pytest.raises(SapError, match="AS02.*mensaje de éxito"):
        flujo3_sap.cargar_a_sap(sap, solicitud(tmp_path, [{"A": "7087147", "C": 1000}]))
    assert sap.acciones == []        # ni siquiera entró a SAP
