"""
Módulo de gestión del estado de la aplicación Appian.

Este módulo contiene la clase AppState, encargada de:
- Abrir la aplicación en el navegador
- Validar que la interfaz haya cargado correctamente
- Controlar los distintos estados de disponibilidad según el contexto

Se utiliza como componente base para garantizar que la aplicación
esté lista antes de ejecutar cualquier acción en los flujos de automatización.
"""

from urllib.parse import urlparse
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .xpath_builder import XPathBuilder


class AppState:
    """
    Gestiona el estado general de la aplicación web (Appian),
    incluyendo la apertura de la URL y la validación de que la
    aplicación esté lista para ser utilizada.

    Esta clase encapsula las esperas necesarias para garantizar
    que la interfaz cargue correctamente antes de ejecutar acciones.
    """

    def __init__(self, driver, wait):
        """
        Inicializa el estado de la aplicación.

        Args:
            driver: Instancia del WebDriver de Selenium.
            wait: Objeto de espera explícita (WebDriverWait).
        """
        self.driver = driver
        self.wait = wait

    def open(self, url=None):
        """
        Abre la URL de la aplicación en el navegador.

        Args:
            url (str, opcional): URL a abrir.
        Raises:
            Exception: Si no es posible acceder a la URL.
        """
        try:
            target_url = url
            if not target_url:
                raise Exception("Debe proporcionar una URL a abrir.")

            self.driver.get(target_url)

        except Exception as e:
            raise Exception(f"No fue posible acceder a la URL: {target_url}") from e

    def get_report_url(self, url):
        """
        Construye la URL para acceder a la sección de reportes.

        Args:
            url (str): URL base de la aplicación.

        Returns:
            str: URL completa para acceder a los reportes.
        """
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        return f"{base}/suite/process-hq"

    def wait_until_ready(self, context: str = "default"):
        """
        Espera hasta que la aplicación esté completamente cargada.

        Dependiendo del contexto, valida diferentes elementos en pantalla.

        Args:
            context (str, opcional): Contexto de la validación.
                - "default": Pantalla principal
                - "report": Pantalla de reportes

        Raises:
            Exception: Si la aplicación no carga correctamente dentro del tiempo esperado.
        """
        try:
            if context == "report":
                return self._wait_report_ready()
            return self._wait_default_ready()
        except TimeoutException:
            raise Exception(
                "No fue posible iniciar sesión. "
                "Verifique las credenciales o el estado de la aplicación."
            ) from None

    def _wait_report_ready(self):
        """
        Espera a que la pantalla de reportes esté disponible,
        validando la presencia del botón 'Exportar a Excel'.
        """
        try:
            self.wait.until(
                EC.visibility_of_element_located(
                    XPathBuilder.button_by_text("Exportar a Excel")
                )
            )

            return True
        except TimeoutException:
            return False

    def _wait_default_ready(self):
        """
        Espera a que la pantalla principal esté lista,
        validando la bandeja de actividades.
        """
        try:
            self.wait.until(
                EC.presence_of_element_located(
                    XPathBuilder.by_data_text("Bandeja de Actividades")
                )
            )
            return True
        except TimeoutException:
            return False
