"""
Pruebas del CASO ESPECIAL BRP "dos archivos" (2026-10-10): Appian dice
"Activos BRP -> Crear" pero llegan 2 Excel. PASO 1: modificación (AS02,
actualizar número de inventario). PASO 2: creación (AS01), igual que siempre.

Se verifica:
  - Flujo 1: cuál Excel es cuál se decide por CONTENIDO; 2 Excel en otro caso
    sigue siendo revisión manual; renombres; modo pruebas reemplazo.
  - Flujo 2: se validan los DOS (todo o nada).
  - Flujo 3: primero todas las filas de AS02 y luego las de AS01, recargando
    entre activos; si falla la modificación, no se crea (por defecto).
  - Modo solo SAP: <id>_brp_modificacion + <id>_brp_creacion = 1 solicitud.
"""

import logging
import os
import shutil

import pytest
from openpyxl import load_workbook

import orquestador
from core.exceptions import MultiplesAdjuntosError, PlantillaInvalidaError, SapError
from core.models import CasoBandeja, Solicitud
from flujos import flujo1_appian, flujo2_validar, flujo3_sap, modo_solo_sap
from test_modo_pruebas_reemplazo import FakeDriver
from test_sap_as01 import FILA, GUARDAR, MENSAJE, PLANTILLA, FakeSap
from test_validacion_brp_modificacion import excel_modificacion

FILA_MOD = {"A": "7087147", "B": "0", "C": 1000, "G": "71101696T1"}
XPATH_INICIAL_AS02 = '//*[@id="M0:46:::2:21"]'


def excel_creacion(carpeta, nombre, filas):
    ruta = os.path.join(str(carpeta), nombre)
    shutil.copy(PLANTILLA, ruta)
    libro = load_workbook(ruta, keep_vba=True)
    for numero, fila in enumerate(filas, start=2):
        for letra, valor in fila.items():
            libro.worksheets[0][f"{letra}{numero}"] = valor
    libro.save(ruta)
    return ruta


@pytest.fixture
def archivos(tmp_path):
    """Un Excel de creación y uno de modificación, con nombres que NO dicen cuál es cuál."""
    crea = excel_creacion(tmp_path, "adjunto_A.xlsm", [FILA, dict(FILA, F="INV-2")])
    modi = excel_modificacion(tmp_path, [FILA_MOD, dict(FILA_MOD, A="7087188", G="71101697T1")],
                              nombre="adjunto_B.xlsm")
    return crea, modi


@pytest.fixture(autouse=True)
def sin_guardar(tmp_path, monkeypatch):
    monkeypatch.setattr(flujo3_sap, "SAP_GUARDAR_REAL", False)
    monkeypatch.setattr(flujo3_sap, "MODO_PRUEBAS_REEMPLAZO", False)
    monkeypatch.setattr(flujo3_sap, "MODO_PRUEBAS_SOLO_SAP", False)
    monkeypatch.setattr(flujo3_sap, "SAP_XPATH_MENSAJE_ESTADO", [])
    monkeypatch.setattr(flujo3_sap, "OUTPUT_DIR", str(tmp_path / "salidas"))


# -- Flujo 1: cuál Excel es cuál --------------------------------------------------------

def test_un_solo_excel_sigue_siendo_normal(archivos):
    crea, _ = archivos
    assert flujo1_appian._asignar_excels([crea], "PDA-1", "brp", "creacion") == (crea, None)


@pytest.mark.parametrize("orden", [0, 1])
def test_dos_excel_se_identifican_por_contenido(archivos, orden):
    crea, modi = archivos
    rutas = [crea, modi] if orden == 0 else [modi, crea]
    assert flujo1_appian._asignar_excels(rutas, "PDA-1", "brp", "creacion") == (crea, modi)


def test_dos_excel_del_mismo_tipo_van_a_revision_manual(tmp_path, archivos):
    crea, _ = archivos
    otra = excel_creacion(tmp_path, "otra.xlsm", [FILA])
    with pytest.raises(MultiplesAdjuntosError, match="no se pudo identificar"):
        flujo1_appian._asignar_excels([crea, otra], "PDA-1", "brp", "creacion")


def test_dos_excel_fuera_del_caso_especial_siguen_en_revision_manual(archivos):
    with pytest.raises(MultiplesAdjuntosError, match="No se sabe cuál usar"):
        flujo1_appian._asignar_excels(list(archivos), "PDA-1", "brp", "modificacion")


def test_tres_excel_van_a_revision_manual(tmp_path, archivos):
    tercero = excel_creacion(tmp_path, "c.xlsm", [FILA])
    with pytest.raises(MultiplesAdjuntosError, match="trae 3 Excel"):
        flujo1_appian._asignar_excels(list(archivos) + [tercero], "PDA-1", "brp", "creacion")


DETALLES_CREAR = (
    "Detalles\nMáscara\n–\nActivos BRP\nCrear\nActivos PRJ\n–\n"
    "Activos Diferidos y Renovaciones\n–\nMejoras\n–\nSegunda Información\n–"
)


class ClienteDosAdjuntos:
    def __init__(self, rutas, carpeta):
        self.driver = FakeDriver()
        self.rutas, self.carpeta = rutas, carpeta

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
    return descargas, pruebas


def test_flujo1_con_dos_adjuntos_reales(archivos, carpetas, monkeypatch):
    descargas, _ = carpetas
    monkeypatch.setattr(flujo1_appian, "MODO_PRUEBAS_REEMPLAZO", False)
    cliente = ClienteDosAdjuntos(list(archivos), str(descargas))

    sol = flujo1_appian.obtener_solicitud(cliente, CasoBandeja("PDA-7889", url="https://x/PDA-7889"))

    assert (sol.tipo, sol.accion) == ("brp", "creacion")
    assert os.path.basename(sol.excel_path) == "PDA-7889_brp_creacion.xlsm"
    assert os.path.basename(sol.excel_modificacion) == "PDA-7889_brp_modificacion.xlsm"


def test_flujo1_modo_reemplazo_con_dos_archivos_de_prueba(archivos, carpetas, monkeypatch):
    descargas, pruebas = carpetas
    monkeypatch.setattr(flujo1_appian, "MODO_PRUEBAS_REEMPLAZO", True)
    crea, modi = archivos
    shutil.copy(crea, pruebas / "PDA-7889.xlsm")
    shutil.copy(modi, pruebas / "PDA-7889_modificacion.xlsm")
    # El adjunto real (viejo) es uno solo: se conserva y se renombra como siempre.
    viejo = os.path.join(os.path.dirname(crea), "viejo.xls")
    open(viejo, "wb").write(b"formato viejo")
    cliente = ClienteDosAdjuntos([viejo], str(descargas))

    sol = flujo1_appian.obtener_solicitud(cliente, CasoBandeja("PDA-7889", url="https://x/PDA-7889"))

    assert os.path.basename(sol.excel_path) == "PDA-7889_brp_creacion_PRUEBA.xlsm"
    assert os.path.basename(sol.excel_modificacion) == "PDA-7889_brp_modificacion_PRUEBA.xlsm"
    assert (descargas / "PDA-7889_brp_creacion.xls").exists()
    assert (pruebas / "PDA-7889_modificacion.xlsm").exists()       # el original intacto


# -- Flujo 2: se validan los DOS ----------------------------------------------------------

def _especial(crea, modi):
    return Solicitud(case_id="PDA-1", tipo="brp", accion="creacion",
                     excel_path=crea, excel_modificacion=modi)


def test_flujo2_valida_los_dos(archivos):
    r = flujo2_validar.validar_solicitud(_especial(*archivos))
    assert r.valida and r.plantilla == "BRP - Creación"


def test_flujo2_modificacion_invalida_detiene_todo(tmp_path, archivos):
    crea, _ = archivos
    modi_mala = excel_modificacion(tmp_path, [dict(FILA_MOD, C=None)], nombre="mala.xlsm")
    with pytest.raises(PlantillaInvalidaError, match="PASO 1 \\(modificación\\)"):
        flujo2_validar.validar_solicitud(_especial(crea, modi_mala))


def test_flujo2_creacion_invalida_detiene_todo(tmp_path, archivos):
    _, modi = archivos
    crea_mala = excel_creacion(tmp_path, "mala.xlsm", [dict(FILA, C=3)])
    with pytest.raises(PlantillaInvalidaError, match="PASO 2 \\(creación\\)"):
        flujo2_validar.validar_solicitud(_especial(crea_mala, modi))


# -- Flujo 3: primero AS02, después AS01 ------------------------------------------------------

def test_flujo3_modifica_y_luego_crea_sin_guardar(archivos):
    sap = FakeSap()
    pedidos = []

    paso = flujo3_sap.cargar_a_sap(sap, _especial(*archivos), esperar_continuar=pedidos.append)

    transacciones = [a[1] for a in sap.acciones if a[0] == "transaccion"]
    assert transacciones == ["AS02", "AS02", "AS01", "AS01"]
    assert sap.acciones.count(("recargar",)) == 3          # entre TODOS los activos
    i = sap.acciones.index(("transaccion", "AS01"))
    assert sap.acciones[i - 1] == ("recargar",)             # también al pasar de AS02 a AS01
    # El nuevo número de inventario (columna G, ya con T1) se escribe en AS02.
    assert ("escribir", '//*[@id="M0:46:3:1:2B256:1::6:22"]', "71101696T1") in sap.acciones
    assert ("clic", GUARDAR[0]) not in sap.acciones
    assert ["AS02" in p for p in pedidos] == [True, True, False, False]
    assert paso == ("PASO 1 (modificación) AS02: Revisado en SAP SIN guardar (2 fila(s)) | "
                    "PASO 2 (creación) AS01: Revisado en SAP SIN guardar (2 fila(s))")


def test_flujo3_si_falla_la_modificacion_no_se_crea(archivos):
    sap = FakeSap(fallar_en=[XPATH_INICIAL_AS02])
    sol = _especial(*archivos)
    with pytest.raises(SapError, match="NO se hizo el PASO 2"):
        flujo3_sap.cargar_a_sap(sap, sol)
    assert ("transaccion", "AS01") not in sap.acciones
    assert all(t.startswith("ERROR") for t in sol.resultados_sap_modificacion.values())


def test_flujo3_con_el_interruptor_se_crea_aunque_falle_la_modificacion(archivos, monkeypatch):
    monkeypatch.setattr(flujo3_sap, "CASO_ESPECIAL_CREAR_SI_FALLA_MODIFICACION", True)
    sap = FakeSap(fallar_en=[XPATH_INICIAL_AS02])
    flujo3_sap.cargar_a_sap(sap, _especial(*archivos))
    assert [a[1] for a in sap.acciones if a[0] == "transaccion"].count("AS01") == 2


def test_flujo3_nunca_guarda_mientras_as02_no_tenga_mensaje_de_exito(archivos, monkeypatch):
    monkeypatch.setattr(flujo3_sap, "SAP_GUARDAR_REAL", True)
    monkeypatch.setattr(flujo3_sap, "SAP_XPATH_MENSAJE_ESTADO", MENSAJE)
    sap = FakeSap()
    with pytest.raises(SapError, match="AS02"):
        flujo3_sap.cargar_a_sap(sap, _especial(*archivos))
    assert sap.acciones == []       # ni AS02 ni AS01: no entró a SAP


# -- Modo solo SAP: une los dos archivos ----------------------------------------------------

def test_modo_solo_sap_une_los_dos_archivos_del_mismo_identificador(tmp_path, monkeypatch, archivos):
    carpeta = tmp_path / "downloads_test"
    carpeta.mkdir()
    crea, modi = archivos
    shutil.copy(crea, carpeta / "p1_brp_creacion.xlsm")
    shutil.copy(modi, carpeta / "P1_brp_modificacion.xlsm")
    shutil.copy(modi, carpeta / "p2_brp_modificacion.xlsm")      # sin pareja: normal
    monkeypatch.setattr(modo_solo_sap, "DOWNLOAD_TEST_DIR", str(carpeta))

    solicitudes, _ = modo_solo_sap.listar_archivos()

    resumen = {(s.case_id, s.accion, bool(s.excel_modificacion)) for s in solicitudes}
    assert resumen == {("p1", "creacion", True), ("p2", "modificacion", False)}


def test_orquestador_solo_sap_caso_especial(tmp_path, monkeypatch, archivos):
    carpeta = tmp_path / "downloads_test"
    carpeta.mkdir()
    crea, modi = archivos
    shutil.copy(crea, carpeta / "p1_brp_creacion.xlsm")
    shutil.copy(modi, carpeta / "p1_brp_modificacion.xlsm")
    monkeypatch.setattr(modo_solo_sap, "DOWNLOAD_TEST_DIR", str(carpeta))
    monkeypatch.setattr(orquestador, "MODO_PRUEBAS_SOLO_SAP", True)
    monkeypatch.setattr(orquestador, "MODO_PRUEBAS_REEMPLAZO", False)
    monkeypatch.setattr(flujo3_sap, "MODO_PRUEBAS_SOLO_SAP", True)

    class Cliente:
        def __init__(self, logger=None):
            self.driver = object()

        def start(self, u, p):
            raise AssertionError("no debe entrar a Appian")

        def cerrar(self):
            pass

    sap = FakeSap()
    sap.volver_a_appian = lambda: None
    monkeypatch.setattr(orquestador, "AppianClient", Cliente)
    monkeypatch.setattr(orquestador, "SapWebGui", lambda *a, **k: sap)

    resumen = orquestador.ejecutar("u", "p", logger=logging.getLogger("t"))

    assert (resumen.total, resumen.exitosos, resumen.fallidos) == (1, 1, 0)
    assert [a[1] for a in sap.acciones if a[0] == "transaccion"] == ["AS02", "AS02", "AS01", "AS01"]
    assert ("clic", GUARDAR[0]) not in sap.acciones
