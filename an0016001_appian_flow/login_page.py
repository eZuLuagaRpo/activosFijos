"""
Módulo encargado de la autenticación en la aplicación Appian.

Contiene la clase LoginPage, la cual permite:
- Detectar si la página requiere autenticación
- Ejecutar el proceso de login con credenciales
- Manejar errores de autenticación y tiempos de espera

Este componente es la puerta de entrada a la aplicación
dentro del flujo de automatización.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .response import build_response
from .xpath_builder import XPathBuilder


class LoginPage:
    """
    Gestiona el proceso de autenticación en la aplicación.

    Permite:
    - Validar si el login es requerido
    - Ingresar credenciales
    - Ejecutar el acceso al sistema
    """

    def __init__(self, driver, wait):
        """
        Inicializa la página de login.

        Args:
            driver: Instancia del WebDriver.
            wait: WebDriverWait para sincronización.
        """
        self.driver = driver
        self.wait = wait

    def required_login(self):
        """
        Determina si la aplicación requiere autenticación.

        Verifica la presencia del campo de usuario en la interfaz.

        Returns:
            bool: True si se requiere login, False en caso contrario.
        """
        try:
            self.wait.until(
                lambda d: d.find_elements(
                    *XPathBuilder.by_data_text("Bandeja de Actividades")
                )
                or d.find_elements(By.ID, "un")
            )
            return len(self.driver.find_elements(By.ID, "un")) > 0

        except TimeoutException:
            return False

    def login(self, user=None, password=None):
        """
        Ejecuta el proceso de autenticación en la aplicación.

        Flujo:
        - Valida si el campo de usuario está presente
        - Ingresa usuario y contraseña
        - Presiona el botón de login

        Args:
            user (str, opcional): Usuario de acceso.
                Ejemplo: "xx@bancolombia.com.co"
            password (str, opcional): Contraseña.

        Returns:
            dict: Respuesta estructurada indicando éxito o error.

        Errores manejados:
            - Timeout: la aplicación no respondió
            - RuntimeError: errores específicos del entorno
            - Exception: errores generales del proceso
        """
        try:
            # Validación si se requiere ingresar el usuario
            user_field = self.driver.find_elements(By.ID, "un")

            if user_field:
                # Usuario
                self.wait.until(
                    EC.visibility_of_element_located(XPathBuilder.input_by_id("un"))
                ).send_keys(user)

                # Password
                self.wait.until(
                    EC.visibility_of_element_located(XPathBuilder.input_by_id("pw"))
                ).send_keys(password)

                # Botón Login
                self.wait.until(
                    EC.element_to_be_clickable(
                        XPathBuilder.input_by_id("jsLoginButton")
                    )
                ).click()

                # Esperar la pantalla principal validando si fue exitoso o no el login
                self.wait.until(
                    EC.presence_of_element_located(
                        XPathBuilder.by_data_text("Bandeja de Actividades")
                    )
                )

            return build_response(True, "OK")

        except Exception as e:
            return build_response(False, f"No fue posible realizar el login. {e}")
