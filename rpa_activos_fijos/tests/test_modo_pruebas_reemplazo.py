"""
Pruebas del MODO PRUEBAS (reemplazo del Excel de Appian por uno de downloads_test).

Se usa un Appian FALSO (sin navegador): la sección "Detalles" dice
"Activos BRP -> Crear" y get_case_data "descarga" un adjunto viejo.
Las carpetas downloads/ y downloads_test/ se redirigen a carpetas temporales.
"""

import logging
import os

import pytest

import orquestador
from core.exceptions import AppianError, CasoOmitidoError
from core.models import CasoBandeja
from flujos import flujo1_appian

DETALLES = (
    "Detalles\nMáscara\n–\nActivos BRP\nCrear\nActivos PRJ\n–\n"
    "Activos Diferidos y Renovaciones\n–\nMejoras\n–\nSegunda Información\n–"
)
CONTENIDO_APPIAN = b"adjunto viejo de appian"
CONTENIDO_PRUEBA = b"mi excel de prueba"


class FakeDriver:
    def __init__(self):
        self.visitadas = []

    def get(self, url):
        self.visitadas.append(url)

    def find_element(self, by, xpath):
        return type("Seccion", (), {"text": DETALLES})()


class FakeClient:
    def __init__(self, carpeta_descargas, logger=None):
        self.driver = FakeDriver()
        self.carpeta = carpeta_descargas

    def get_case_data(self, case_id, download_attachments=True):
        ruta = os.path.join(self.carpeta, "adjunto_usuario.xls")
        with open(ruta, "wb") as f:
            f.write(CONTENIDO_APPIAN)
        return {"info": None, "files": [{"file": "adjunto_usuario.xls", "full_path": ruta}]}


@pytest.fixture
def carpetas(tmp_path, monkeypatch):
    descargas = tmp_path / "downloads"
    pruebas = tmp_path / "downloads_test"
    descargas.mkdir()
    pruebas.mkdir()
    monkeypatch.setattr(flujo1_appian, "DOWNLOAD_DIR", str(descargas))
    monkeypatch.setattr(flujo1_appian, "DOWNLOAD_TEST_DIR", str(pruebas))
    monkeypatch.setattr(orquestador, "DOWNLOAD_TEST_DIR", str(pruebas))
    return descargas, pruebas


def activar(monkeypatch, valor=True):
    monkeypatch.setattr(flujo1_appian, "MODO_PRUEBAS_REEMPLAZO", valor)
    monkeypatch.setattr(orquestador, "MODO_PRUEBAS_REEMPLAZO", valor)


def caso(case_id="PDA-7889"):
    return CasoBandeja(case_id=case_id, fecha_vencimiento="06/10/2026 12:00",
                       url=f"https://appian/fake/{case_id}")


# -- Modo APAGADO: flujo real intacto -----------------------------------------

def test_apagado_usa_el_adjunto_de_appian_aunque_haya_archivo_de_prueba(carpetas, monkeypatch):
    descargas, pruebas = carpetas
    activar(monkeypatch, False)
    (pruebas / "PDA-7889.xlsx").write_bytes(CONTENIDO_PRUEBA)

    solicitud = flujo1_appian.obtener_solicitud(FakeClient(str(descargas)), caso())

    assert os.path.basename(solicitud.excel_path) == "PDA-7889_brp_creacion.xls"
    assert open(solicitud.excel_path, "rb").read() == CONTENIDO_APPIAN
    assert (solicitud.tipo, solicitud.accion) == ("brp", "creacion")


# -- Modo ENCENDIDO -------------------------------------------------------------

def test_encendido_reemplaza_por_copia_del_archivo_de_prueba(carpetas, monkeypatch):
    descargas, pruebas = carpetas
    activar(monkeypatch)
    original = pruebas / "PDA-7889.xlsx"
    original.write_bytes(CONTENIDO_PRUEBA)

    solicitud = flujo1_appian.obtener_solicitud(FakeClient(str(descargas)), caso())

    # Se trabaja sobre una COPIA en downloads/ con el tipo y la acción REALES de Appian.
    assert solicitud.excel_path == str(descargas / "PDA-7889_brp_creacion_PRUEBA.xlsx")
    assert open(solicitud.excel_path, "rb").read() == CONTENIDO_PRUEBA
    # El archivo de prueba original sigue intacto.
    assert original.read_bytes() == CONTENIDO_PRUEBA
    # El adjunto real de Appian se descargó y NO se borró.
    assert (descargas / "PDA-7889_brp_creacion.xls").read_bytes() == CONTENIDO_APPIAN


def test_encendido_sin_archivo_se_omite_y_ni_siquiera_abre_la_solicitud(carpetas, monkeypatch):
    descargas, _ = carpetas
    activar(monkeypatch)
    client = FakeClient(str(descargas))

    with pytest.raises(CasoOmitidoError):
        flujo1_appian.obtener_solicitud(client, caso())
    assert client.driver.visitadas == []


def test_nombre_no_distingue_mayusculas_e_ignora_temporales_de_excel(carpetas, monkeypatch):
    _, pruebas = carpetas
    (pruebas / "~$PDA-7889.xlsx").write_bytes(b"lock")
    (pruebas / "pda-7889.xlsm").write_bytes(CONTENIDO_PRUEBA)
    assert flujo1_appian._buscar_archivo_prueba("PDA-7889").endswith("pda-7889.xlsm")


def test_nombres_parecidos_no_se_confunden(carpetas):
    _, pruebas = carpetas
    (pruebas / "PDA-78890.xlsx").write_bytes(CONTENIDO_PRUEBA)
    (pruebas / "PDA-7889_viejo.xlsx").write_bytes(CONTENIDO_PRUEBA)
    assert flujo1_appian._buscar_archivo_prueba("PDA-7889") is None


def test_dos_archivos_para_la_misma_solicitud_es_error(carpetas):
    _, pruebas = carpetas
    (pruebas / "PDA-7889.xlsx").write_bytes(CONTENIDO_PRUEBA)
    (pruebas / "PDA-7889.xlsm").write_bytes(CONTENIDO_PRUEBA)
    with pytest.raises(AppianError, match="Deja solo uno"):
        flujo1_appian._buscar_archivo_prueba("PDA-7889")


# -- Orquestador: omitidos no cuentan como fallidos -----------------------------

def test_orquestador_cuenta_omitidos_aparte(carpetas, monkeypatch):
    descargas, pruebas = carpetas
    activar(monkeypatch)
    (pruebas / "PDA-1.xlsx").write_bytes(CONTENIDO_PRUEBA)  # no es Excel real -> falla validación

    class Client(FakeClient):
        def __init__(self, logger=None):
            super().__init__(str(descargas))

        def start(self, user, password):
            pass

        def cerrar(self):
            pass

    monkeypatch.setattr(orquestador, "AppianClient", Client)
    monkeypatch.setattr(
        orquestador.flujo1_appian, "listar_casos_pendientes",
        lambda client, logger=None: [caso("PDA-1"), caso("PDA-2"), caso("PDA-3")],
    )

    resumen = orquestador.ejecutar("u", "p", logger=logging.getLogger("prueba"))

    assert (resumen.total, resumen.omitidos, resumen.fallidos, resumen.exitosos) == (3, 2, 1, 0)
    assert [r.case_id for r in resumen.resultados if r.omitido] == ["PDA-2", "PDA-3"]
