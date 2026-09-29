"""
sap/sap_webgui.py — Manejo de SAP GUI for HTML (SAP en el navegador).

SAP se abre en una PESTAÑA NUEVA del mismo navegador que ya usa Appian (el
driver de la librería), y se entra con las MISMAS credenciales. Este módulo
solo sabe "mover" SAP (abrir, iniciar sesión, ir a una transacción, hacer
clic, escribir); el QUÉ se hace en cada transacción vive en flujos/flujo3_sap.py.

Reglas aplicadas (las mismas que en el resto del bot):
  - Selectores en config.py, como LISTAS (principal -> respaldos).
  - Esperas ACTIVAS con tope (TIMEOUT): se sigue apenas aparece el elemento.
  - SAP web a veces dibuja la pantalla dentro de un <iframe>: se busca en la
    página principal y, si no está, dentro de cada iframe.
  - La contraseña NUNCA se escribe en el log.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from config import (
    SAP_URL,
    SAP_XPATH_BARRA_TRANSACCION,
    SAP_XPATH_LOGIN_BOTON,
    SAP_XPATH_LOGIN_CLAVE,
    SAP_XPATH_LOGIN_USUARIO,
    TIMEOUT,
)
from core.exceptions import SapError


class SapWebGui:
    """Sesión de SAP en una pestaña del navegador de Appian."""

    def __init__(self, driver, user, password, logger=None):
        self.driver = driver
        self._user = user
        self._password = password   # solo en memoria; nunca se registra
        self.logger = logger
        self._pestana_appian = None
        self._pestana_sap = None

    # -- Sesión y pestañas -----------------------------------------------------
    @property
    def abierta(self):
        return self._pestana_sap is not None

    def asegurar_sesion(self):
        """Abre SAP (pestaña nueva + login) la primera vez; después solo
        cambia a su pestaña."""
        if self.abierta:
            self.ir_a_sap()
            return

        self._pestana_appian = self.driver.current_window_handle
        try:
            self.driver.switch_to.new_window("tab")
            self._pestana_sap = self.driver.current_window_handle
            if self.logger:
                self.logger.info("Abriendo SAP en una pestaña nueva: %s", SAP_URL)
            self.driver.get(SAP_URL)
        except Exception as e:
            raise SapError(f"No se pudo abrir SAP ({SAP_URL}): {e}")

        self._iniciar_sesion_si_hace_falta()

    def _iniciar_sesion_si_hace_falta(self):
        """
        Espera a que aparezca la barra de transacción (sesión ya activa, ej.
        SSO) o la pantalla de login. Si es el login, lo llena y espera la
        barra.
        """
        visible = self._esperar_alguno(
            {"barra": SAP_XPATH_BARRA_TRANSACCION, "login": SAP_XPATH_LOGIN_USUARIO},
            "la pantalla inicial de SAP (barra de transacción o login)",
        )
        if visible == "barra":
            if self.logger:
                self.logger.info("SAP: sesión ya activa.")
            return

        if self.logger:
            self.logger.info("SAP: iniciando sesión con el usuario '%s'.", self._user)
        self.escribir(SAP_XPATH_LOGIN_USUARIO, self._user, "usuario de SAP")
        self.escribir(SAP_XPATH_LOGIN_CLAVE, self._password, "contraseña de SAP",
                      registrar_valor=False)
        self.clic(SAP_XPATH_LOGIN_BOTON, "botón de inicio de sesión de SAP")
        self.esperar(SAP_XPATH_BARRA_TRANSACCION,
                     "la barra de transacción después del login (¿credenciales?)")
        if self.logger:
            self.logger.info("SAP: sesión iniciada.")

    def ir_a_sap(self):
        if self._pestana_sap:
            self.driver.switch_to.window(self._pestana_sap)

    def volver_a_appian(self):
        """Deja el navegador en la pestaña de Appian (la necesita el Flujo 1).
        Nunca lanza: si falla, solo lo registra."""
        if not self._pestana_appian:
            return
        try:
            self.driver.switch_to.default_content()
            self.driver.switch_to.window(self._pestana_appian)
        except Exception as e:
            if self.logger:
                self.logger.warning("No se pudo volver a la pestaña de Appian: %s", e)

    # -- Acciones --------------------------------------------------------------
    def ir_a_transaccion(self, codigo):
        """
        Escribe la transacción en la barra y presiona Enter. Se antepone
        "/n" (estándar de SAP): abre la transacción desde cero aunque haya
        otra abierta, así cada solicitud empieza con la pantalla limpia.
        """
        if self.logger:
            self.logger.info("SAP: abriendo transacción %s.", codigo)
        barra = self.esperar(SAP_XPATH_BARRA_TRANSACCION, "la barra de transacción")
        try:
            barra.click()
            barra.send_keys(Keys.CONTROL, "a")
            barra.send_keys(Keys.DELETE)
            barra.send_keys(f"/n{codigo}", Keys.ENTER)
        except Exception as e:
            raise SapError(f"No se pudo escribir la transacción {codigo}: {e}")

    def clic(self, lista_xpath, descripcion):
        elemento = self.esperar(lista_xpath, descripcion)
        try:
            elemento.click()
        except Exception as e:
            raise SapError(f"No se pudo hacer clic en {descripcion}: {e}")

    def escribir(self, lista_xpath, texto, descripcion, registrar_valor=True):
        """Borra lo que tenga el campo, escribe `texto` y sale del campo (Tab)
        para que SAP registre el valor."""
        elemento = self.esperar(lista_xpath, descripcion)
        try:
            elemento.click()
            elemento.send_keys(Keys.CONTROL, "a")
            elemento.send_keys(Keys.DELETE)
            elemento.send_keys(texto, Keys.TAB)
        except Exception as e:
            raise SapError(f"No se pudo escribir en {descripcion}: {e}")
        if self.logger and registrar_valor:
            self.logger.info("SAP: %s -> %s", descripcion, texto)

    # -- Búsqueda de elementos (con iframes y respaldos) ------------------------
    def esperar(self, lista_xpath, descripcion):
        """Espera (tope TIMEOUT) a que aparezca el elemento y lo devuelve."""
        clave = self._esperar_alguno({"x": lista_xpath}, descripcion)
        return self._encontrado[clave]

    def _esperar_alguno(self, opciones, descripcion):
        """
        Espera a que aparezca CUALQUIERA de las `opciones` ({clave: lista de
        XPath}) y devuelve la clave de la que apareció. El elemento queda en
        self._encontrado[clave] y el driver queda dentro del frame donde está.
        """
        self._encontrado = {}

        def buscar(_driver):
            for clave, lista_xpath in opciones.items():
                elemento = self._localizar(lista_xpath)
                if elemento is not None:
                    self._encontrado[clave] = elemento
                    return clave
            return False

        try:
            return WebDriverWait(self.driver, TIMEOUT).until(buscar)
        except Exception:
            raise SapError(
                f"SAP: no apareció {descripcion} tras {TIMEOUT}s. Revisa los "
                f"selectores en config.py: {list(opciones.values())}"
            )

    def _localizar(self, lista_xpath):
        """Busca en la página principal y luego dentro de cada iframe (un
        nivel). Devuelve el primer elemento encontrado o None."""
        self.driver.switch_to.default_content()
        elemento = self._primero(lista_xpath)
        if elemento is not None:
            return elemento
        for frame in self.driver.find_elements(By.TAG_NAME, "iframe"):
            try:
                self.driver.switch_to.frame(frame)
            except Exception:
                continue
            elemento = self._primero(lista_xpath)
            if elemento is not None:
                return elemento
            self.driver.switch_to.default_content()
        return None

    def _primero(self, lista_xpath):
        for indice, xpath in enumerate(lista_xpath):
            try:
                elementos = self.driver.find_elements(By.XPATH, xpath)
            except Exception:
                continue
            if elementos:
                if self.logger and indice > 0:
                    self.logger.warning("SAP: se usó el selector de respaldo #%s: %s",
                                        indice, xpath)
                return elementos[0]
        return None
