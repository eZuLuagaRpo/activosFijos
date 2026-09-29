"""
Pruebas de SAP etapa 1 (hasta antes de "Ejecutar"), con un NAVEGADOR FALSO.

No hay SAP de pruebas, así que se simula el navegador: pestañas, pantalla de
login, barra de transacción e iframes. Se verifica QUÉ hace el bot y en QUÉ
ORDEN, y sobre todo que NUNCA llegue a ejecutar.
"""

import logging

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import config
import orquestador
from core.exceptions import SapError
from core.models import CasoBandeja, Solicitud
from flujos import flujo3_sap
from sap import sap_webgui
from sap.sap_webgui import SapWebGui

BARRA = config.SAP_XPATH_BARRA_TRANSACCION[0]
USUARIO = config.SAP_XPATH_LOGIN_USUARIO[0]
CLAVE = config.SAP_XPATH_LOGIN_CLAVE[0]
BOTON_LOGIN = config.SAP_XPATH_LOGIN_BOTON[0]
OPCION_CREAR = config.SAP_MASIVA_XPATH_OPCION_ACCION["creacion"][0]
CAMPO_RUTA = config.SAP_MASIVA_XPATH_CAMPO_RUTA[0]
EJECUCION_TEST = config.SAP_MASIVA_XPATH_EJECUCION_TEST[0]


# -- Navegador falso -------------------------------------------------------------

class FakeElement:
    def __init__(self, navegador, nombre, al_clic=None):
        self.navegador = navegador
        self.nombre = nombre
        self.al_clic = al_clic
        self.texto = ""

    def click(self):
        self.navegador.acciones.append(("clic", self.nombre))
        if self.al_clic:
            self.al_clic()

    def send_keys(self, *teclas):
        if teclas[:2] == (Keys.CONTROL, "a"):
            return
        if teclas == (Keys.DELETE,):
            self.texto = ""
            return
        escrito = "".join(t for t in teclas if t not in (Keys.ENTER, Keys.TAB))
        self.texto += escrito
        self.navegador.acciones.append(("escribir", self.nombre, escrito, Keys.ENTER in teclas))


class FakeSwitch:
    def __init__(self, navegador):
        self.n = navegador

    def new_window(self, tipo):
        self.n.pestanas.append("sap")
        self.n.actual = "sap"

    def window(self, nombre):
        self.n.actual = nombre
        self.n.acciones.append(("pestana", nombre))

    def default_content(self):
        self.n.frame = None

    def frame(self, frame):
        self.n.frame = frame


class FakeBrowser:
    """Pestaña 'appian' abierta. `con_sso`: SAP entra sin pedir login.
    `barra_en_iframe`: la pantalla de SAP va dentro de un iframe."""

    def __init__(self, con_sso=False, barra_en_iframe=False):
        self.pestanas = ["appian"]
        self.actual = "appian"
        self.frame = None
        self.acciones = []
        self.con_sso = con_sso
        self.barra_en_iframe = barra_en_iframe
        self.pagina_sap = {}          # xpath -> FakeElement (página principal)
        self.pagina_iframe = {}       # xpath -> FakeElement (dentro del iframe)
        self.switch_to = FakeSwitch(self)

    @property
    def current_window_handle(self):
        return self.actual

    def get(self, url):
        self.acciones.append(("abrir", url))
        if self.con_sso:
            self._mostrar_sap()
        else:
            self.pagina_sap = {
                USUARIO: FakeElement(self, "usuario"),
                CLAVE: FakeElement(self, "clave"),
                BOTON_LOGIN: FakeElement(self, "login", al_clic=self._mostrar_sap),
            }

    def _mostrar_sap(self):
        pantalla = {
            BARRA: FakeElement(self, "barra"),
            OPCION_CREAR: FakeElement(self, "opcion_crear"),
            CAMPO_RUTA: FakeElement(self, "campo_ruta"),
            EJECUCION_TEST: FakeElement(self, "ejecucion_test"),
        }
        if self.barra_en_iframe:
            self.pagina_sap, self.pagina_iframe = {}, pantalla
        else:
            self.pagina_sap = pantalla

    def find_elements(self, por, valor):
        if self.actual != "sap":
            return []
        if por == By.TAG_NAME and valor == "iframe":
            return ["iframe1"] if self.pagina_iframe and self.frame is None else []
        pagina = self.pagina_iframe if self.frame else self.pagina_sap
        return [pagina[valor]] if valor in pagina else []


@pytest.fixture(autouse=True)
def rapido(monkeypatch):
    monkeypatch.setattr(sap_webgui, "TIMEOUT", 1)
    monkeypatch.setattr(flujo3_sap, "SAP_PAUSA_REVISION_SEG", 0)


def sap_con(navegador, logger=None):
    return SapWebGui(navegador, "usuario@bancolombia.com.co", "Secreta123", logger=logger)


def solicitud(tmp_path, monkeypatch, tipo="brp", accion="creacion"):
    carpeta = tmp_path / "carga_sap"
    carpeta.mkdir(exist_ok=True)
    monkeypatch.setattr(flujo3_sap, "CARGA_SAP_DIR", str(carpeta))
    excel = tmp_path / f"PDA-7889_{tipo}_{accion}.xlsm"
    excel.write_bytes(b"plantilla")
    return Solicitud(case_id="PDA-7889", tipo=tipo, accion=accion, excel_path=str(excel))


# -- SapWebGui ---------------------------------------------------------------------

def test_abre_pestana_nueva_e_inicia_sesion(caplog):
    navegador = FakeBrowser()
    with caplog.at_level(logging.INFO):
        sap = sap_con(navegador, logger=logging.getLogger("t"))
        sap.asegurar_sesion()

    assert navegador.pestanas == ["appian", "sap"]
    assert ("abrir", config.SAP_URL) in navegador.acciones
    assert navegador.pagina_sap[BARRA]  # quedó en la pantalla principal de SAP
    assert ("escribir", "usuario", "usuario@bancolombia.com.co", False) in navegador.acciones
    assert ("escribir", "clave", "Secreta123", False) in navegador.acciones
    assert "Secreta123" not in caplog.text   # la contraseña NUNCA va al log


def test_con_sso_no_llena_el_login():
    navegador = FakeBrowser(con_sso=True)
    sap_con(navegador).asegurar_sesion()
    assert not [a for a in navegador.acciones if a[0] == "escribir"]


def test_la_segunda_vez_no_abre_otra_pestana():
    navegador = FakeBrowser(con_sso=True)
    sap = sap_con(navegador)
    sap.asegurar_sesion()
    sap.volver_a_appian()
    sap.asegurar_sesion()
    assert navegador.pestanas == ["appian", "sap"]
    assert navegador.actual == "sap"


def test_transaccion_con_prefijo_n_y_enter():
    navegador = FakeBrowser(con_sso=True)
    sap = sap_con(navegador)
    sap.asegurar_sesion()
    sap.ir_a_transaccion("Z_AM_MASIVA")
    assert ("escribir", "barra", "/nZ_AM_MASIVA", True) in navegador.acciones


def test_encuentra_elementos_dentro_de_un_iframe():
    navegador = FakeBrowser(con_sso=True, barra_en_iframe=True)
    sap = sap_con(navegador)
    sap.asegurar_sesion()
    sap.ir_a_transaccion("Z_AM_MASIVA")
    assert ("escribir", "barra", "/nZ_AM_MASIVA", True) in navegador.acciones


def test_volver_a_appian():
    navegador = FakeBrowser(con_sso=True)
    sap = sap_con(navegador)
    sap.asegurar_sesion()
    sap.volver_a_appian()
    assert navegador.actual == "appian"


def test_selector_que_no_aparece_da_error_claro():
    navegador = FakeBrowser(con_sso=True)
    sap = sap_con(navegador)
    sap.asegurar_sesion()
    with pytest.raises(SapError, match="no apareció"):
        sap.clic(['//*[@id="NO-EXISTE"]'], "un botón inexistente")


# -- Flujo 3 · etapa 1 ---------------------------------------------------------------

def test_etapa1_hace_los_pasos_en_orden_y_se_detiene(tmp_path, monkeypatch):
    navegador = FakeBrowser()
    sol = solicitud(tmp_path, monkeypatch)

    paso = flujo3_sap.cargar_a_sap(sap_con(navegador), sol)

    pasos = [a for a in navegador.acciones if a[0] in ("clic", "escribir")]
    # (antes de escribir en un campo, el bot hace clic en él)
    assert pasos[-6:] == [
        ("clic", "barra"),
        ("escribir", "barra", "/nZ_AM_MASIVA", True),
        ("clic", "opcion_crear"),
        ("clic", "campo_ruta"),
        ("escribir", "campo_ruta", sol.archivo_sap, False),
        ("clic", "ejecucion_test"),
    ]
    assert sol.archivo_sap.endswith("CREAR (BRP).xlsm")
    assert "Detenido antes de Ejecutar" in paso


def test_etapa1_con_ejecutar_real_no_ejecuta_nada(tmp_path, monkeypatch):
    monkeypatch.setattr(flujo3_sap, "SAP_EJECUTAR_REAL", True)
    navegador = FakeBrowser(con_sso=True)
    with pytest.raises(SapError, match="No se ejecutó nada"):
        flujo3_sap.cargar_a_sap(sap_con(navegador), solicitud(tmp_path, monkeypatch))
    # Lo último que tocó fue "Ejecución de test": nunca un botón de ejecutar.
    assert [a for a in navegador.acciones if a[0] == "clic"][-1] == ("clic", "ejecucion_test")


def test_combinacion_sin_transaccion_no_abre_sap(tmp_path, monkeypatch):
    navegador = FakeBrowser(con_sso=True)
    sol = solicitud(tmp_path, monkeypatch, tipo="prj")
    with pytest.raises(SapError, match="SAP_TRANSACCION_POR_CASO"):
        flujo3_sap.cargar_a_sap(sap_con(navegador), sol)
    assert navegador.pestanas == ["appian"]


# -- Orquestador: siempre vuelve a Appian ---------------------------------------------

def test_orquestador_vuelve_a_appian_aunque_sap_falle(monkeypatch):
    class SapFalso:
        vueltas = 0

        def volver_a_appian(self):
            SapFalso.vueltas += 1

    def sap_que_falla(sap, sol, logger=None):
        raise SapError("SAP no respondió")

    monkeypatch.setattr(orquestador.flujo1_appian, "obtener_solicitud",
                        lambda c, caso, logger=None: Solicitud(case_id=caso.case_id))
    monkeypatch.setattr(orquestador.flujo2_validar, "validar_solicitud",
                        lambda s, logger=None: None)
    monkeypatch.setattr(orquestador.flujo3_sap, "cargar_a_sap", sap_que_falla)

    resultado = orquestador._procesar_un_caso(
        None, SapFalso(), CasoBandeja("PDA-1"), logging.getLogger("t"))

    assert not resultado.exito and resultado.paso == "Flujo 3 (SAP)"
    assert SapFalso.vueltas == 1
