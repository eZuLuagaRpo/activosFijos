"""
Módulo de orquestación principal para la automatización de Appian.

Contiene la clase AppianFlow y funciones que se usan en los flujos de Appian.
"""

from functools import wraps
from .driver_manager import create_driver
from .login_page import LoginPage
from .app_state import AppState
from .download_manager import DownloadManager
from .cases_page import CasesPage
from .report_page import ReportPage
from .form_handler import FormHandler
from .response import build_response


# -------------------------------------------------
# DECORADORES
# -------------------------------------------------
# Validar que la app esté lista
def _require_app_ready(context="default"):
    """
    Decorador que valida que la aplicación esté lista antes
    de ejecutar un método.

    Este decorador utiliza el estado de la aplicación (AppState)
    para asegurar que la interfaz haya cargado completamente
    según el contexto indicado.

    Args:
        context (str, opcional): Contexto de validación.
            Valores posibles:
                - "default": vistas normales de la app
                - "report": vistas de reportes

    Returns:
        function: Función decorada que ejecuta validación previa.

    En caso de error:
        Retorna una respuesta estándar con el mensaje de excepción.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                self.app_state.wait_until_ready(context)
                return func(self, *args, **kwargs)
            except Exception as e:
                return build_response(False, str(e))

        return wrapper

    return decorator


class AppianFlow:
    """
    Clase orquestadora principal de la automatización sobre Appian.

    Centraliza la inicialización y coordinación de los distintos componentes:
    - Navegador (WebDriver)
    - Estado de la aplicación
    - Login
    - Gestión de casos
    - Manejo de formularios
    - Descarga de archivos
    - Reportes

    Esta clase actúa como punto de entrada para ejecutar flujos
    de negocio de forma estructurada.
    """

    def __init__(
        self, url, download_dir=None, browser="edge", timeout=90, timeout_files=600
    ):
        """
        Inicializa los parámetros de configuración para la automatización.

        Args:
            - url (str): URL base de la aplicación.
            - download_dir (str, opcional): Ruta donde se guardarán las descargas.
            - browser (str, opcional): Navegador a utilizar (por defecto "edge").
            - timeout (int, opcional): Tiempo de espera para carga de elementos.
            - timeout_files (int, opcional): Tiempo máximo de espera para descargas.
        """

        # --- Infraestructura ---
        self.driver, self.wait = create_driver(browser, timeout, download_dir)
        self.download_dir = self.driver.download_dir
        self.url = url.rstrip("/")
        self.timeout_files = timeout_files

        # --- Estado de la aplicación ---
        self.app_state = AppState(self.driver, self.wait)

        # --- Dependencias ---
        self.download_manager = DownloadManager(self.driver, self.timeout_files)
        self.form_handler = FormHandler(self.driver, self.wait, self.timeout_files)
        self.login_page = LoginPage(self.driver, self.wait)
        self.cases_page = CasesPage(
            self.driver,
            self.wait,
            self.form_handler,
            self.download_manager,
            self.download_dir,
        )
        self.report_page = ReportPage(
            self.driver,
            self.wait,
            self.timeout_files,
            self.download_dir,
            self.download_manager,
        )

    def start(self, user=None, password=None):
        """
        Inicia la aplicación y realiza el proceso de autenticación si es requerido.

        Si el login no es requerido, no se debe enviar usuario ni contraseña.

        Flujo:
        - Inicializa el navegador y abre la URL de la aplicación
        - Verifica si se requiere autenticación.
        - Ejecuta autenticación si aplica.
        - Despues de iniciar la aplicación, se pueden llamar los métodos de negocio
            (buscar caso, avanzar caso, crear caso, descargar reporte).

        Args:
            user (str, opcional): Usuario de acceso.
                Ejemplo: "xx@bancolombia.com.co"
            password (str, opcional): Contraseña del usuario.

        Returns:
            dict: Respuesta estructurada indicando éxito o fallo.
        """
        try:
            # abrir app
            self.app_state.open(self.url)

            # login
            requiered_login = self.login_page.required_login()
            if requiered_login:
                if not user or not password:
                    raise Exception(
                        "Usuario y contraseña son requeridos para este ambiente."
                    )

                return self.login_page.login(user, password)

            return build_response(True, "Aplicación iniciada correctamente")

        except Exception as e:
            return build_response(False, f"Error al iniciar la aplicación. {str(e)}")

    def search_case(self, case_id):
        """
        Busca un número de caso y abre su detalle.

        Args:
            case_id (str): Número del caso.

        Returns:
            dict: Resultado de la operación.
        """
        try:
            self.app_state.open(self.url)
            response = self.app_state.wait_until_ready()
            if not response:
                return build_response(
                    False,
                    "La aplicación no cargó correctamente.",
                )

            return self.cases_page.search_case(case_id)
        except Exception as e:
            return build_response(
                False, f"Error en flujo de búsqueda de caso. {str(e)}"
            )

    @_require_app_ready()
    def get_case_data(self, case_id, download_attachments=False):
        """
        Obtiene la información de un caso.

        Para ejecutar este método, debe haberse ejecutado previamente el método 
        search_case para abrir el detalle del caso.

        Args:
            case_id (str): Número del caso.
            download_attachments (bool, opcional): Indica si se deben descargar adjuntos.

        Returns:
            dict: Resultado con la información del caso.
        """
        return self.cases_page.get_case_data(case_id, download_attachments)

    @_require_app_ready()
    def advance_case(self, case_id, form_data):
        """
        Avanza un caso en el flujo operativo.

        Args:
            case_id (str): Número del caso.
            form_data (dict): Datos para completar el formulario.
                    - nombre_del_campo: Nombre del campo en el formulario
                    - valor: Valor a ingresar o seleccionar en el campo
                    - Ejemplo:
                        form_data = {
                            "Fecha Registro": "04/05/2026",
                            "Cómo Deseas Atender Esta Solicitud": "Complementar Información",
                            "Seleccione la Actividad": "Realizar Solicitud",
                            "Desea Enviar Notificación Personalizada": "Si",
                            "Seleccione el Usuario o los Usuarios": ['abechav'],
                            "Comentario a Enviar en la Notificación": "Se requiere",
                            "Observaciones": "Se requiere complementar la información",
                            "Adjuntos": [
                                r"C:\\Users\\abechav\\Downloads\\id_eucs.xlsx"
                            ]
                        }

        Returns:
            dict: Resultado de la operación.
        """
        return self.cases_page.advance_case(case_id, form_data)

    def create_case(self, category_name, flow_name, form_data):
        """
        Crea un nuevo caso en el flujo.

        Args:
            category_name (str): Nombre de la categoría.
            flow_name (str): Nombre del flujo.
            form_data (dict): Datos del formulario.
                    - nombre_del_campo: Nombre del campo en el formulario
                    - valor: Valor a ingresar o seleccionar en el campo
                    - Ejemplo:
                        form_data = {
                            "Fecha Registro": "04/05/2026",
                            "Cuenta Contable": "1111111111111",
                            "Valor del Registro": 2000.34,
                            "Observaciones": "Radicación automática",
                            "Asignar a": ["abechav"],
                            "Adjuntos": [
                                    r"C:\\Users\\abechav\\Downloads\\FCO_EUC_06_04.xlsx"
                            ]
                        }

        Returns:
            dict: Resultado con el número de caso generado.
        """
        try:
            self.app_state.open(self.url)
            response = self.app_state.wait_until_ready()
            if not response:
                return build_response(
                    False,
                    "La aplicación no cargó correctamente.",
                )

            return self.cases_page.create_case(category_name, flow_name, form_data)
        except Exception as e:
            return build_response(
                False, f"Error en flujo de creación de caso. {str(e)}"
            )

    def download_report(self, report_data, filter_data):
        """
        Descarga un reporte en process-hq basado en filtros.

        Args:
            report_data (dict): Datos del reporte.
                    - flow_name: Nombre del flujo asociado al reporte
                    - report_name: Nombre del reporte a descargar
                    - Ejemplo:
                        report_data = {
                            "flow_name": "Solicitud investigación de bienes",
                            "report_name": "Informe detallado Solicitud investigación de bienes"
                        }
            filter_data (dict): Filtros a aplicar en el reporte.
                    - nombre_del_campo: Nombre del campo a filtrar
                    - valor: Valor para el filtro
                    - Ejemplo:
                        filter_data={
                            "Solicitud fecha de creación": ["01/03/2026", "29/04/2026"],
                            "Estado de la solicitud": "Finalizado exitoso"
                        }

        Returns:
            dict: Resultado de la descarga del reporte.
        """
        try:
            response = self.app_state.wait_until_ready()
            if not response:
                return build_response(
                    False,
                    "La aplicación no cargó correctamente.",
                )

            self.app_state.open(self.app_state.get_report_url(self.url))

            # buscar y abrir reporte
            self.report_page.search_report(report_data)

            # abrimos la pagina de reporte
            process_data = self.report_page.open_process_hq(report_data)

            # descargar
            response = self.report_page.download_report(filter_data)

            # cerramos la pagina de reporte
            self.report_page.close_process_hq(process_data)

            return response

        except Exception as e:
            return build_response(
                False, f"Error en flujo de descarga de reporte. {str(e)}"
            )

    def cerrar(self):
        """
        Cierra el navegador y finaliza la sesión.

        Este método debe ejecutarse al finalizar cualquier flujo
        para liberar recursos.
        """
        self.driver.quit()
