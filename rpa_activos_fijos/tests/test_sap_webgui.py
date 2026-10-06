"""
Pruebas de SAP con un NAVEGADOR FALSO.

No hay SAP de pruebas, así que se simula el navegador: pestañas, pantalla de
login, barra de transacción e iframes. Se verifica la base de SAP
(sap/sap_webgui.py), las reglas de seguridad de "Guardar" y que el Flujo 3
no entre a SAP mientras el formulario de AS01 no esté configurado.
"""

import logging

import pytest
from selenium.common.exceptions import (
    NoAlertPresentException,
    StaleElementReferenceException,
    UnexpectedAlertPresentException,
)
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
CAMPO = '//*[@id="CAMPO-DE-PRUEBA"]'


# -- Navegador falso -------------------------------------------------------------

class FakeElement:
    def __init__(self, navegador, nombre, al_clic=None):
        self.navegador = navegador
        self.nombre = nombre
        self.al_clic = al_clic
        self.texto = ""
        self.vencerse = 0     # cuántos clics fallan con "elemento vencido"

    def click(self):
        if self.vencerse:
            self.vencerse -= 1
            # Igual al error real de la 1ª prueba (Selenium antepone "Message:").
            raise StaleElementReferenceException(
                "stale element reference: stale element not found\n"
                "  (Session info: MicrosoftEdge=154.0.4258.53)",
                stacktrace=["msedgedriver!GetHandleVerifier [0x7ff77a8620a5+4c15]"])
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

    @property
    def active_element(self):
        return FakeElement(self.n, "foco")

    @property
    def alert(self):
        if not self.n.aviso_abierto:
            raise NoAlertPresentException()
        navegador = self.n

        class Aviso:
            def accept(self):
                navegador.aviso_abierto = False
                navegador.acciones.append(("aviso_aceptado",))

        return Aviso()

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
        self.aviso_abierto = False
        self.aviso_al_recargar = False   # la 1ª recarga choca con "¿Salir del sitio?"

    def refresh(self):
        if self.aviso_al_recargar:
            self.aviso_al_recargar = False
            self.aviso_abierto = True
            raise UnexpectedAlertPresentException("¿Salir del sitio?")
        self.acciones.append(("recargar",))
        self._mostrar_sap()       # la sesión sigue activa: vuelve al inicio de SAP

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
            CAMPO: FakeElement(self, "campo"),
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


def sap_con(navegador, logger=None):
    return SapWebGui(navegador, "usuario@bancolombia.com.co", "Secreta123", logger=logger)


# -- SapWebGui (base de SAP) -------------------------------------------------------

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
    sap.ir_a_transaccion("AS01")
    assert ("escribir", "barra", "/nAS01", True) in navegador.acciones


def test_escribir_borra_y_escribe_en_el_campo():
    navegador = FakeBrowser(con_sso=True)
    sap = sap_con(navegador)
    sap.asegurar_sesion()
    sap.escribir([CAMPO], "valor", "un campo")
    assert navegador.acciones[-2:] == [("clic", "campo"), ("escribir", "campo", "valor", False)]


def test_encuentra_elementos_dentro_de_un_iframe():
    navegador = FakeBrowser(con_sso=True, barra_en_iframe=True)
    sap = sap_con(navegador)
    sap.asegurar_sesion()
    sap.ir_a_transaccion("AS01")
    assert ("escribir", "barra", "/nAS01", True) in navegador.acciones


def test_volver_a_appian():
    navegador = FakeBrowser(con_sso=True)
    sap = sap_con(navegador)
    sap.asegurar_sesion()
    sap.volver_a_appian()
    assert navegador.actual == "appian"


def test_enter_se_presiona_en_el_elemento_con_foco():
    navegador = FakeBrowser(con_sso=True)
    sap = sap_con(navegador)
    sap.asegurar_sesion()
    sap.enter()
    assert navegador.acciones[-1] == ("escribir", "foco", "", True)


def test_doble_clic_lento_espera_entre_clics(monkeypatch):
    esperas = []
    monkeypatch.setattr(sap_webgui.time, "sleep", esperas.append)
    navegador = FakeBrowser(con_sso=True)
    sap = sap_con(navegador)
    sap.asegurar_sesion()
    sap.doble_clic_lento([CAMPO], "una pestaña", 2)
    assert navegador.acciones[-2:] == [("clic", "campo"), ("clic", "campo")]
    assert esperas == [2, 2]


def test_existe_devuelve_none_si_no_aparece():
    navegador = FakeBrowser(con_sso=True)
    sap = sap_con(navegador)
    sap.asegurar_sesion()
    assert sap.existe(['//*[@id="NO-EXISTE"]'], 0) is None
    assert sap.existe([CAMPO], 0) is not None


def test_recargar_deja_sap_en_el_inicio_con_pantalla_nueva():
    navegador = FakeBrowser(con_sso=True)
    sap = sap_con(navegador)
    sap.asegurar_sesion()
    barra_vieja = navegador.pagina_sap[BARRA]
    sap.volver_a_appian()          # aunque esté en la pestaña de Appian...
    sap.recargar()
    assert ("recargar",) in navegador.acciones
    assert navegador.actual == "sap"                       # ...recarga la de SAP
    assert navegador.pagina_sap[BARRA] is not barra_vieja  # pantalla nueva
    sap.ir_a_transaccion("AS01")
    assert navegador.acciones[-1] == ("escribir", "barra", "/nAS01", True)


def test_recargar_acepta_el_aviso_del_navegador_y_reintenta():
    navegador = FakeBrowser(con_sso=True)
    navegador.aviso_al_recargar = True
    sap = sap_con(navegador)
    sap.asegurar_sesion()
    sap.recargar()
    assert ("aviso_aceptado",) in navegador.acciones
    assert ("recargar",) in navegador.acciones


def test_elemento_vencido_se_vuelve_a_buscar_y_funciona():
    navegador = FakeBrowser(con_sso=True)
    sap = sap_con(navegador)
    sap.asegurar_sesion()
    navegador.pagina_sap[BARRA].vencerse = 1     # SAP redibujó justo al usarla
    sap.ir_a_transaccion("AS01")
    assert navegador.acciones[-1] == ("escribir", "barra", "/nAS01", True)


def test_elemento_que_siempre_se_vence_da_error_corto_sin_stacktrace(monkeypatch):
    monkeypatch.setattr(sap_webgui.time, "sleep", lambda s: None)
    navegador = FakeBrowser(con_sso=True)
    sap = sap_con(navegador)
    sap.asegurar_sesion()
    navegador.pagina_sap[BARRA].vencerse = 99
    with pytest.raises(SapError) as error:
        sap.ir_a_transaccion("AS01")
    assert str(error.value) == (
        "No se pudo escribir la transacción AS01: stale element reference: "
        "stale element not found"
    )


def test_selector_que_no_aparece_da_error_claro():
    navegador = FakeBrowser(con_sso=True)
    sap = sap_con(navegador)
    sap.asegurar_sesion()
    with pytest.raises(SapError, match="no apareció"):
        sap.clic(['//*[@id="NO-EXISTE"]'], "un botón inexistente")


# -- Seguridad: cuándo se permite "Guardar" ----------------------------------------

@pytest.mark.parametrize(
    "guardar_real, modo_pruebas, permitido",
    [
        (False, False, False),   # interruptor apagado
        (False, True, False),
        (True, True, False),     # MODO PRUEBAS: prohibido aunque el interruptor esté encendido
        (True, False, True),     # único caso en que se guarda
    ],
)
def test_guardar_permitido(monkeypatch, guardar_real, modo_pruebas, permitido):
    monkeypatch.setattr(flujo3_sap, "SAP_GUARDAR_REAL", guardar_real)
    monkeypatch.setattr(flujo3_sap, "MODO_PRUEBAS_REEMPLAZO", modo_pruebas)
    assert flujo3_sap.guardar_permitido() is permitido


def test_por_defecto_guardar_esta_apagado():
    assert config.SAP_GUARDAR_REAL is False
    assert flujo3_sap.guardar_permitido() is False


# -- Flujo 3 sin formulario configurado ----------------------------------------

def test_flujo3_queda_pendiente_sin_entrar_a_sap(monkeypatch):
    # Si una combinación no tiene formulario configurado, no se entra a SAP.
    monkeypatch.setattr(flujo3_sap, "SAP_FORMULARIOS_POR_CASO", {})
    navegador = FakeBrowser(con_sso=True)
    sol = Solicitud(case_id="PDA-7889", tipo="brp", accion="creacion", excel_path="x.xlsm")

    paso = flujo3_sap.cargar_a_sap(sap_con(navegador), sol)

    assert "Pendiente de SAP (AS01" in paso
    assert navegador.pestanas == ["appian"]      # no abrió SAP
    assert navegador.acciones == []


def test_combinacion_sin_transaccion_da_error_y_no_abre_sap():
    navegador = FakeBrowser(con_sso=True)
    sol = Solicitud(case_id="PDA-1", tipo="prj", accion="creacion", excel_path="x.xlsm")
    with pytest.raises(SapError, match="SAP_TRANSACCION_POR_CASO"):
        flujo3_sap.cargar_a_sap(sap_con(navegador), sol)
    assert navegador.pestanas == ["appian"]


# -- Orquestador: siempre vuelve a Appian ---------------------------------------------

def test_orquestador_vuelve_a_appian_aunque_sap_falle(monkeypatch):
    class SapFalso:
        vueltas = 0

        def volver_a_appian(self):
            SapFalso.vueltas += 1

    def sap_que_falla(sap, sol, logger=None, esperar_continuar=None):
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
