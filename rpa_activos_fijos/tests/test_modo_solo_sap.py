"""
Pruebas del MODO PRUEBAS SOLO SAP: sin Appian, los Excel de downloads_test
(<id>_<tipo>_<accion>.xlsx) pasan por validación y SAP, sin guardar nunca.
Se usa el SAP falso de test_sap_as01.py.
"""

import logging
import shutil

import pytest
from openpyxl import load_workbook

import orquestador
from flujos import flujo3_sap, modo_solo_sap
from test_sap_as01 import FILA, GUARDAR, PLANTILLA, FakeSap


class ClienteFalso:
    """Imita AppianClient: abre 'el navegador' pero NUNCA debe iniciar sesión."""

    creados = 0

    def __init__(self, logger=None):
        ClienteFalso.creados += 1
        self.driver = object()
        self.cerrado = False
        self.inicio_sesion = False
        ClienteFalso.ultimo = self

    def start(self, user, password):
        self.inicio_sesion = True

    def cerrar(self):
        self.cerrado = True


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    carpeta = tmp_path / "downloads_test"
    carpeta.mkdir()
    (carpeta / ".gitkeep").write_text("")
    monkeypatch.setattr(modo_solo_sap, "DOWNLOAD_TEST_DIR", str(carpeta))
    monkeypatch.setattr(orquestador, "MODO_PRUEBAS_SOLO_SAP", True)
    monkeypatch.setattr(orquestador, "MODO_PRUEBAS_REEMPLAZO", False)
    monkeypatch.setattr(flujo3_sap, "MODO_PRUEBAS_SOLO_SAP", True)
    monkeypatch.setattr(flujo3_sap, "MODO_PRUEBAS_REEMPLAZO", False)
    monkeypatch.setattr(orquestador, "AppianClient", ClienteFalso)
    ClienteFalso.creados = 0
    sap = FakeSap()
    sap.volver_a_appian = lambda: None
    monkeypatch.setattr(orquestador, "SapWebGui", lambda *a, **k: sap)
    return carpeta, sap


def excel(carpeta, nombre, filas):
    ruta = carpeta / nombre
    shutil.copy(PLANTILLA, ruta.with_suffix(".xlsm"))
    libro = load_workbook(ruta.with_suffix(".xlsm"), keep_vba=True)
    for numero, fila in enumerate(filas, start=2):
        for letra, valor in fila.items():
            libro.worksheets[0][f"{letra}{numero}"] = valor
    libro.save(ruta)
    if ruta.suffix != ".xlsm":
        ruta.with_suffix(".xlsm").unlink()
    return ruta


# -- Nombre del archivo ---------------------------------------------------------------

@pytest.mark.parametrize("nombre, esperado", [
    ("prueba1_brp_creacion.xlsx", ("prueba1", "brp", "creacion")),
    ("Activos_Oct_BRP_Creacion.xlsm", ("Activos_Oct", "brp", "creacion")),
    ("x_segunda_informacion_modificacion.xlsx", ("x", "segunda_informacion", "modificacion")),
    ("prueba1_brp.xlsx", None),            # falta la acción
    ("_brp_creacion.xlsx", None),          # falta el identificador
    ("prueba_brp_creacion.xls", None),     # formato viejo
    ("PDA-7889.xlsx", None),               # nombre del OTRO modo (reemplazo)
])
def test_interpretar_nombre(nombre, esperado):
    assert modo_solo_sap.interpretar_nombre(nombre) == esperado


# -- Seguridad ---------------------------------------------------------------------------

def test_en_modo_solo_sap_nunca_se_permite_guardar(monkeypatch):
    monkeypatch.setattr(flujo3_sap, "SAP_GUARDAR_REAL", True)
    monkeypatch.setattr(flujo3_sap, "MODO_PRUEBAS_REEMPLAZO", False)
    monkeypatch.setattr(flujo3_sap, "MODO_PRUEBAS_SOLO_SAP", True)
    assert flujo3_sap.guardar_permitido() is False


def test_los_dos_modos_a_la_vez_no_arrancan(entorno, monkeypatch):
    monkeypatch.setattr(orquestador, "MODO_PRUEBAS_REEMPLAZO", True)
    resumen = orquestador.ejecutar("u", "p", logger=logging.getLogger("t"))
    assert resumen.total == 0
    assert ClienteFalso.creados == 0          # ni siquiera abrió el navegador


# -- Recorrido completo -----------------------------------------------------------------

def test_recorrido_sin_appian_valida_y_lleva_a_sap_sin_guardar(entorno, monkeypatch):
    carpeta, sap = entorno
    monkeypatch.setattr(flujo3_sap, "SAP_GUARDAR_REAL", True)   # aun así NO debe guardar
    excel(carpeta, "prueba1_brp_creacion.xlsx", [FILA, dict(FILA, F="INV-2")])
    excel(carpeta, "prueba2_brp_creacion.xlsm", [dict(FILA, C=5)])    # inválida
    (carpeta / "notas.txt").write_text("x")                           # nombre sin formato
    original = (carpeta / "prueba1_brp_creacion.xlsx").read_bytes()
    pedidos = []

    resumen = orquestador.ejecutar("u", "p", logger=logging.getLogger("t"),
                                   esperar_continuar=pedidos.append)

    cliente = ClienteFalso.ultimo
    assert not cliente.inicio_sesion           # NO entró a Appian
    assert cliente.cerrado                     # cerró el navegador
    assert (resumen.total, resumen.exitosos, resumen.fallidos, resumen.omitidos) == (3, 1, 1, 1)
    assert len(pedidos) == 2                   # "Continuar" por cada fila de prueba1
    assert ("clic", GUARDAR[0]) not in sap.acciones
    assert sap.acciones.count(("transaccion", "AS01")) == 2
    assert (carpeta / "prueba1_brp_creacion.xlsx").read_bytes() == original   # intacto


def test_sin_archivos_no_abre_el_navegador(entorno):
    resumen = orquestador.ejecutar("u", "p", logger=logging.getLogger("t"))
    assert resumen.total == 0
    assert ClienteFalso.creados == 0
