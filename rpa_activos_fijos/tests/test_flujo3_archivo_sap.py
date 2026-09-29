"""
Pruebas de la preparación del archivo para SAP: copia temporal con el nombre
EXACTO que exige SAP ("CREAR (BRP).xlsm" para BRP - Creación).
La carpeta carga_sap/ se redirige a una temporal.
"""

import os

import pytest

from core.exceptions import SapError
from core.models import Solicitud
from flujos import flujo3_sap


@pytest.fixture
def carga_sap(tmp_path, monkeypatch):
    carpeta = tmp_path / "carga_sap"
    carpeta.mkdir()
    monkeypatch.setattr(flujo3_sap, "CARGA_SAP_DIR", str(carpeta))
    return carpeta


def solicitud_con_archivo(tmp_path, case_id, contenido, tipo="brp", accion="creacion"):
    ruta = tmp_path / f"{case_id}_{tipo}_{accion}.xlsm"
    ruta.write_bytes(contenido)
    return Solicitud(case_id=case_id, tipo=tipo, accion=accion, excel_path=str(ruta))


def test_copia_con_el_nombre_exacto_de_sap(tmp_path, carga_sap):
    solicitud = solicitud_con_archivo(tmp_path, "PDA-7889", b"datos 7889")

    ruta = flujo3_sap.preparar_archivo_sap(solicitud)

    assert os.path.basename(ruta) == "CREAR (BRP).xlsm"
    assert open(ruta, "rb").read() == b"datos 7889"
    assert solicitud.archivo_sap == ruta
    # El archivo de la solicitud sigue ahí, intacto y con su nombre.
    assert open(solicitud.excel_path, "rb").read() == b"datos 7889"


def test_cada_solicitud_reemplaza_la_copia_anterior(tmp_path, carga_sap):
    primera = solicitud_con_archivo(tmp_path, "PDA-7889", b"datos 7889")
    segunda = solicitud_con_archivo(tmp_path, "PDA-7890", b"datos 7890")

    flujo3_sap.preparar_archivo_sap(primera)
    ruta = flujo3_sap.preparar_archivo_sap(segunda)

    assert os.listdir(carga_sap) == ["CREAR (BRP).xlsm"]
    assert open(ruta, "rb").read() == b"datos 7890"


def test_si_falla_la_copia_no_queda_el_archivo_de_otra_solicitud(tmp_path, carga_sap):
    primera = solicitud_con_archivo(tmp_path, "PDA-7889", b"datos 7889")
    flujo3_sap.preparar_archivo_sap(primera)

    rota = Solicitud(case_id="PDA-7890", tipo="brp", accion="creacion",
                     excel_path=str(tmp_path / "no_existe.xlsm"))
    with pytest.raises(SapError):
        flujo3_sap.preparar_archivo_sap(rota)

    # Lo importante: el archivo de la PDA-7889 ya no está listo para cargarse.
    assert os.listdir(carga_sap) == []


def test_combinacion_sin_nombre_configurado(tmp_path, carga_sap):
    solicitud = solicitud_con_archivo(tmp_path, "PDA-1", b"x", tipo="prj")
    with pytest.raises(SapError, match="NOMBRE_ARCHIVO_SAP"):
        flujo3_sap.preparar_archivo_sap(solicitud)
    assert os.listdir(carga_sap) == []
