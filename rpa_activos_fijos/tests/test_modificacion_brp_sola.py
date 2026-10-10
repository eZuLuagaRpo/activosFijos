"""
Pruebas del flujo de MODIFICACIÓN BRP "sola" (2026-10-10): en Appian la
sección "Detalles" dice "Activos BRP -> Modificar" y la solicitud trae UN
Excel (la plantilla de modificación). El bot entra a AS02 y llena, fila por
fila, igual que la creación (recarga entre activos, supervisión sin guardar).

Se recorre con un Appian y un SAP FALSOS (sin navegador).
"""

import logging
import os
import shutil
import types

import pytest

import orquestador
from core.exceptions import MultiplesAdjuntosError, PlantillaInvalidaError
from core.models import CasoBandeja, Solicitud
from flujos import flujo1_appian, flujo2_validar, flujo3_sap
from test_sap_as01 import FILA, GUARDAR, PLANTILLA, FakeSap
from test_validacion_brp_modificacion import excel_modificacion

DETALLES_MODIFICAR = (
    "Detalles\nMáscara\n–\nActivos BRP\nModificar\nActivos PRJ\n–\n"
    "Activos Diferidos y Renovaciones\n–\nMejoras\n–\nSegunda Información\n–"
)
FILAS_MOD = [
    {"A": "7087147", "B": "0", "C": 1000, "G": "71101696T1", "X": "RO"},
    {"A": "7087188", "C": 1000, "S": "LOCAL-9"},
]


class DriverModificar:
    def __init__(self):
        self.visitadas = []

    def get(self, url):
        self.visitadas.append(url)

    def find_element(self, by, xpath):
        return types.SimpleNamespace(text=DETALLES_MODIFICAR)


class ClienteModificar:
    """Imita AppianClient: "Detalles" dice BRP -> Modificar; adjunta `rutas`."""

    def __init__(self, rutas, carpeta, logger=None):
        self.driver = DriverModificar()
        self.rutas, self.carpeta = rutas, carpeta

    def start(self, user, password):
        pass

    def cerrar(self):
        pass

    def get_case_data(self, case_id, download_attachments=True):
        archivos = []
        for ruta in self.rutas:
            destino = os.path.join(self.carpeta, os.path.basename(ruta))
            shutil.copy(ruta, destino)
            archivos.append({"file": os.path.basename(destino), "full_path": destino})
        return {"info": None, "files": archivos}


@pytest.fixture
def carpetas(tmp_path, monkeypatch):
    descargas, pruebas = tmp_path / "downloads", tmp_path / "downloads_test"
    descargas.mkdir()
    pruebas.mkdir()
    monkeypatch.setattr(flujo1_appian, "DOWNLOAD_DIR", str(descargas))
    monkeypatch.setattr(flujo1_appian, "DOWNLOAD_TEST_DIR", str(pruebas))
    monkeypatch.setattr(flujo1_appian, "MODO_PRUEBAS_REEMPLAZO", False)
    monkeypatch.setattr(orquestador, "MODO_PRUEBAS_REEMPLAZO", False)
    monkeypatch.setattr(orquestador, "MODO_PRUEBAS_SOLO_SAP", False)
    for nombre, valor in (("SAP_GUARDAR_REAL", False), ("MODO_PRUEBAS_REEMPLAZO", False),
                          ("MODO_PRUEBAS_SOLO_SAP", False), ("SAP_XPATH_MENSAJE_ESTADO", [])):
        monkeypatch.setattr(flujo3_sap, nombre, valor)
    monkeypatch.setattr(flujo3_sap, "OUTPUT_DIR", str(tmp_path / "salidas"))
    return descargas, pruebas


def caso(case_id="PDA-9100"):
    return CasoBandeja(case_id, "06/10/2026 12:00", f"https://appian/fake/{case_id}")


# -- Flujo 1 ------------------------------------------------------------------------------

def test_flujo1_detecta_modificar_y_toma_el_unico_excel(tmp_path, carpetas):
    descargas, _ = carpetas
    adjunto = excel_modificacion(tmp_path, FILAS_MOD, nombre="adjunto_usuario.xlsm")
    cliente = ClienteModificar([adjunto], str(descargas))

    sol = flujo1_appian.obtener_solicitud(cliente, caso())

    assert (sol.tipo, sol.accion, sol.accion_cruda) == ("brp", "modificacion", "Modificar")
    assert os.path.basename(sol.excel_path) == "PDA-9100_brp_modificacion.xlsm"
    assert sol.excel_modificacion is None          # NO es el caso especial


def test_flujo1_modificar_con_dos_excel_va_a_revision_manual(tmp_path, carpetas):
    descargas, _ = carpetas
    a = excel_modificacion(tmp_path, FILAS_MOD, nombre="a.xlsm")
    b = excel_modificacion(tmp_path, FILAS_MOD, nombre="b.xlsm")
    with pytest.raises(MultiplesAdjuntosError):
        flujo1_appian.obtener_solicitud(ClienteModificar([a, b], str(descargas)), caso())


def test_flujo1_modo_reemplazo_con_plantilla_de_modificacion(tmp_path, carpetas, monkeypatch):
    descargas, pruebas = carpetas
    monkeypatch.setattr(flujo1_appian, "MODO_PRUEBAS_REEMPLAZO", True)
    shutil.copy(excel_modificacion(tmp_path, FILAS_MOD, nombre="mia.xlsm"), pruebas / "PDA-9100.xlsm")
    viejo = tmp_path / "viejo.xls"
    viejo.write_bytes(b"formato viejo")

    sol = flujo1_appian.obtener_solicitud(ClienteModificar([str(viejo)], str(descargas)), caso())

    assert os.path.basename(sol.excel_path) == "PDA-9100_brp_modificacion_PRUEBA.xlsm"
    assert sol.excel_modificacion is None


# -- Flujo 2 ------------------------------------------------------------------------------

def test_flujo2_rechaza_la_plantilla_de_creacion_en_una_solicitud_de_modificar(tmp_path):
    ruta = tmp_path / "crea.xlsm"
    shutil.copy(PLANTILLA, ruta)
    sol = Solicitud(case_id="PDA-9100", tipo="brp", accion="modificacion", excel_path=str(ruta))
    with pytest.raises(PlantillaInvalidaError, match="Faltan encabezados"):
        flujo2_validar.validar_solicitud(sol)


# -- De punta a punta por el orquestador ----------------------------------------------------

def test_orquestador_modificar_sola_llena_as02_fila_por_fila(tmp_path, carpetas, monkeypatch):
    descargas, _ = carpetas
    adjunto = excel_modificacion(tmp_path, FILAS_MOD, nombre="adjunto_usuario.xlsm")
    sap = FakeSap()
    sap.volver_a_appian = lambda: None
    monkeypatch.setattr(orquestador, "AppianClient",
                        lambda logger=None: ClienteModificar([adjunto], str(descargas)))
    monkeypatch.setattr(orquestador, "SapWebGui", lambda *a, **k: sap)
    monkeypatch.setattr(orquestador.flujo1_appian, "listar_casos_pendientes",
                        lambda client, logger=None: [caso()])
    pedidos = []

    resumen = orquestador.ejecutar("u", "p", logger=logging.getLogger("t"),
                                   esperar_continuar=pedidos.append)

    assert (resumen.total, resumen.exitosos, resumen.fallidos) == (1, 1, 0)
    assert [a[1] for a in sap.acciones if a[0] == "transaccion"] == ["AS02", "AS02"]
    assert sap.acciones.count(("recargar",)) == 1
    assert len(pedidos) == 2 and all("AS02" in p for p in pedidos)
    assert ("clic", GUARDAR[0]) not in sap.acciones
    escritos = [a[2] for a in sap.acciones if a[0] == "escribir"]
    assert "71101696T1" in escritos and "LOCAL-9" in escritos     # G y S llenados
    assert resumen.resultados[0].paso == "Revisado en SAP SIN guardar (2 fila(s))"


def test_la_creacion_sola_no_cambia(tmp_path, carpetas):
    # Regresión: una solicitud "BRP -> Crear" con UN Excel sigue usando AS01.
    ruta = tmp_path / "crea.xlsm"
    shutil.copy(PLANTILLA, ruta)
    from openpyxl import load_workbook
    libro = load_workbook(ruta, keep_vba=True)
    for letra, valor in FILA.items():
        libro.worksheets[0][f"{letra}2"] = valor
    libro.save(ruta)
    sap = FakeSap()
    sol = Solicitud(case_id="PDA-1", tipo="brp", accion="creacion", excel_path=str(ruta))

    flujo3_sap.cargar_a_sap(sap, sol)

    assert [a[1] for a in sap.acciones if a[0] == "transaccion"] == ["AS01"]
