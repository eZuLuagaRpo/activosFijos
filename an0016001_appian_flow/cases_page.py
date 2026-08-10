"""
Módulo de gestión de casos dentro de la aplicación Appian.

Contiene la clase CasesPage encargada de:
- Buscar y abrir casos
- Consultar información del caso
- Descargar adjuntos
- Avanzar casos en el flujo
- Crear nuevos casos
"""

import os
import time
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from .xpath_builder import XPathBuilder
from .response import build_response


class CasesPage:
    """
    Representa la página de gestión de casos en Appian.

    Esta clase encapsula todas las operaciones relacionadas con:
    - Búsqueda de casos
    - Consulta de información
    - Manejo de formularios
    - Descarga de adjuntos
    - Creación y avance de solicitudes
    """

    def __init__(self, driver, wait, form_handler, download_manager, download_dir):
        """
        Inicializa la página de casos.

        Args:
            driver: Instancia del WebDriver de Selenium.
            wait: Objeto WebDriverWait para sincronización.
            form_handler: Componente encargado de llenar formularios dinámicos.
            download_manager: Gestor de descargas de archivos.
            download_dir (str): Ruta donde se almacenan los archivos descargados.
        """
        self.driver = driver
        self.wait = wait
        self.form_handler = form_handler
        self.download_manager = download_manager
        self.download_dir = download_dir

    # -------------------------------------------------
    # BUSCAR Y ABRIR CASO
    # -------------------------------------------------
    def search_case(self, case_id):
        """
        Busca un caso en la aplicación y lo abre si existe.

        Args:
            case_id (str): Identificador del caso a buscar.

        Returns:
            dict: Respuesta estructurada indicando:
                - success (bool): Resultado de la operación
                - message (str): Descripción del resultado
        """
        step = f"Inicializando búsqueda de caso {case_id}"

        try:
            step = "Click en Seguimiento de Solicitudes"
            menu = self.wait.until(
                EC.presence_of_element_located(
                    XPathBuilder.by_data_text("Seguimiento de Solicitudes")
                )
            )
            self.driver.execute_script("arguments[0].click();", menu)

            step = "Ingresando caso en el campo de Buscar solicitudes"
            search_field = self.wait.until(
                EC.visibility_of_element_located(
                    XPathBuilder.input_by_placeholder("Buscar solicitudes")
                )
            )
            search_field.clear()
            search_field.send_keys(case_id)

            step = "Click en botón Buscar"
            self.wait.until(
                EC.element_to_be_clickable(XPathBuilder.button_by_text("Buscar"))
            ).click()

            step = "Esperando resultado del caso"
            self.wait.until(
                lambda d: (
                    d.find_elements(
                        *XPathBuilder.contains_text("a", case_id, equal=True)
                    )
                    or d.find_elements(By.XPATH, "//*[@data-empty-grid-message='true']")
                )
            )

            # Caso NO encontrado
            if self.driver.find_elements(
                By.XPATH, "//*[@data-empty-grid-message='true']"
            ):
                return build_response(
                    False, f"No se encontró información para el caso {case_id}"
                )

            step = "Abriendo caso"
            self.wait.until(
                EC.element_to_be_clickable(
                    XPathBuilder.contains_text("a", case_id, equal=True)
                )
            ).click()

            return build_response(True, "OK")

        except TimeoutException:
            return build_response(False, f"Timeout buscando el caso {case_id}")

        except Exception as e:
            return build_response(
                False, f"No fue posible buscar el caso {case_id} ({step}). {str(e)}"
            )

    # -------------------------------------------------
    # OBTENER DATOS DEL CASO
    # Devuelve DataFrame con label | value
    # -------------------------------------------------

    def get_case_data(self, case_id, download_attachments=False):
        """
        Obtiene la información detallada de un caso.

        Extrae todos los campos visibles organizados en secciones
        y los retorna como un DataFrame.

        Args:
            case_id (str): Identificador del caso.
            download_attachments (bool, opcional):
                Indica si se deben descargar los adjuntos del caso.

        Returns:
            dict: Respuesta estructurada que contiene:
                - success (bool)
                - message (str)
                - data (dict):
                    - info (DataFrame): Información del caso
                    - files (list): Archivos descargados
        """
        step = f"Inicializando consulta de caso {case_id}"

        try:
            rows = []

            step = "Obteniendo secciones del caso"
            sections = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[@role='region' and .//h2]")
                )
            )

            step = "Extrayendo campos del caso"
            for section in sections:
                fields = section.find_elements(
                    *XPathBuilder.contains_class("div", "FieldLayout---field_layout")
                )

                for field in fields:
                    try:
                        label = field.find_element(
                            *XPathBuilder.contains_class(
                                "span", "FieldLayout---field_label"
                            )
                        ).text.strip()

                        value = field.find_element(
                            *XPathBuilder.contains_class(
                                "p", "ParagraphText---richtext_paragraph"
                            )
                        ).text.strip()

                        if label:
                            rows.append({"label": label, "value": value})

                    except Exception:
                        # Error local del campo, no aborta todo
                        continue

            if not rows:
                return build_response(
                    False, f"No se encontraron datos para el caso {case_id}", None
                )

            df = pd.DataFrame(rows, columns=["label", "value"])

            try:
                attachments = []
                if download_attachments:
                    attachments = self._download_attachments()

            except Exception as e:
                return build_response(False, e, None)

            return build_response(
                True,
                "Consulta de caso ejecutada correctamente",
                data={"info": df, "files": attachments},
            )

        except Exception as e:
            return build_response(
                False, f"No fue posible consultar el caso {case_id} ({step}). {e}", None
            )

    # -------------------------------------------------
    # AVANZAR CASO
    # -------------------------------------------------
    def advance_case(self, case_id, form_data: dict):
        """
        Avanza un caso dentro del flujo operativo.

        Incluye:
        - Validación de carga del caso
        - Toma de tarea (si aplica)
        - Validación de concurrencia
        - Diligenciamiento de formulario
        - Finalización del proceso

        Args:
            case_id (str): Identificador del caso.
            form_data (dict): Datos necesarios para completar el formulario.

        Returns:
            dict: Resultado de la operación.
        """
        step = f"Inicializando atención de solicitud {case_id}"

        try:
            step = "Esperando que la información del caso cargue"
            self.wait.until(
                EC.presence_of_element_located(
                    XPathBuilder.by_data_testid("Heading-headingTag")
                )
            )

            step = "Click en el estado de la solicitud"
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(@class,'Button---primary') "
                        "and .//span[not(contains(@class,'accessibilityhidden'))]]",
                    )
                )
            ).click()

            step = "Esperando pantalla de atención"
            self.wait.until(
                EC.presence_of_element_located(
                    XPathBuilder.contains_text("p", "Complete la Información")
                )
            )

            step = "Validar si la actividad ya fue tomada o asignada por otro usuario"
            if self.driver.find_elements(
                *XPathBuilder.contains_text(
                    "strong", "Esta actividad ya ha sido tomada"
                )
            ):
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                return build_response(
                    False,
                    "La actividad ya fue tomada "
                    f"o asignada por otro usuario. Para el caso {case_id}",
                )

            step = "Tomar tarea (si aplica)"
            button = self.driver.find_elements(
                *XPathBuilder.button_by_text("Tomar tarea")
            )
            if button:
                button[0].click()

            step = "Esperando pantalla de atención"
            self.wait.until(
                EC.presence_of_element_located(
                    XPathBuilder.contains_text("p", "Complete la Información")
                )
            )

            step = "Llenando formulario dinámico"
            self.form_handler.fill_form(form_data)

            # Finalizar el caso
            step = "Finalizar caso"
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[contains(@class,'VirtualButtonLayout2---align_end')]//button",
                    )
                )
            ).click()

            self._change_case_status()

            return build_response(True, "OK")

        except Exception as e:
            return build_response(
                False, f"No fue posible atender solicitud {case_id} ({step}). {e}"
            )

    def _change_case_status(self):
        """
        Gestiona el cambio de estado del caso después de finalizar
        el formulario.

        Valida si existen errores en los campos requeridos y,
        en caso afirmativo, cancela la operación y lanza excepción.

        Raises:
            Exception: Si no es posible guardar la información del caso.
        """
        try:
            time.sleep(1)  # pequeña pausa para que renderice validaciones

            # Validar si hay errores llenando el formulario
            errors = self.driver.find_elements(
                *XPathBuilder.contains_class("div", "FieldLayout---field_error")
            )

            if errors:
                # Cerramos el modal de atención
                self.wait.until(
                    EC.element_to_be_clickable(XPathBuilder.button_by_text("CANCELAR"))
                ).click()
                # Esperar cierre del modal
                self._close_modal()
                raise Exception("Campos requeridos sin diligenciar.")

            # Esperar cierre del modal
            self._close_modal()

        except Exception as e:
            raise Exception(
                f"No fue posible guardar la informacion del caso. {e}"
            ) from e

    def _close_modal(self):
        """
        Espera el cierre completo de un modal en la interfaz.

        Raises:
            Exception: Si falla la validación del cierre.
        """
        try:
            # Esperar cierre del modal
            self.wait.until(
                lambda d: len(
                    d.find_elements(
                        By.XPATH, "//div[@role='dialog' and @aria-modal='true']"
                    )
                )
                == 0
            )
        except Exception as e:
            raise Exception(f"No fue posible cerrar el modal. {e}") from e

    def _download_attachments(self):
        """
        Descarga todos los adjuntos visibles en la sección 'Adjuntos'.

        La descarga es transaccional:
        - Si falla un archivo, se eliminan los previamente descargados.

        Returns:
            list: Lista de archivos descargados con:
                - file: nombre del archivo
                - path: directorio base
                - full_path: ruta completa

        Raises:
            Exception: Si ocurre un error o la descarga es incompleta.
        """
        try:
            download_files = []

            # Buscar enlaces de adjuntos
            paths = self.driver.find_elements(
                By.XPATH,
                "//h2[.//text()='Adjuntos']"
                "/following::a[contains(@href,'/content/latest')]",
            )

            wait_totals = len(paths)
            # Si no hay adjuntos, retornar lista vacía
            if wait_totals == 0:
                return download_files

            for path in paths:
                name = path.text.strip()

                # Ignorar enlaces sin nombre visible
                if not name:
                    continue

                # Disparar descarga
                path.click()

                # Esperar descarga
                file = self.download_manager.wait_for_download(self.download_dir)

                download_files.append(
                    {
                        "file": file,
                        "path": self.download_dir,
                        "full_path": os.path.join(self.download_dir, file),
                    }
                )

            # Validamos que se descarguen todos los archivos
            if len(download_files) != wait_totals:
                raise Exception(
                    f"Descarga incompleta: se esperaban {wait_totals} adjuntos "
                    f"y solo se descargaron {len(download_files)}"
                )

            return download_files

        except Exception as e:
            # eliminar archivos descargados
            for files in download_files:
                try:
                    if os.path.exists(files["full_path"]):
                        os.remove(files["full_path"])
                except Exception:
                    pass

            raise Exception(f"Fallo en la descarga de adjuntos: {str(e)}") from e

    def _search_category(self, category_name, flow_name):
        """
        Busca una categoría y un flujo dentro del módulo de radicación.

        Args:
            category_name (str): Nombre de la categoría.
            flow_name (str): Nombre del flujo.

        Raises:
            Exception: Si ocurre un error durante la búsqueda.
        """
        try:
            field_category = self.wait.until(
                EC.visibility_of_element_located(
                    XPathBuilder.input_by_placeholder("Buscar Categorías")
                )
            )
            field_category.clear()
            field_category.send_keys(category_name)

            self.wait.until(
                EC.element_to_be_clickable(XPathBuilder.button_by_text("Buscar"))
            ).click()

            time.sleep(2)  # Esperar resultados

            # click en la categoría encontrada
            row = self.wait.until(
                EC.presence_of_element_located(
                    XPathBuilder.contains_text("p", category_name, equal=True)
                )
            )
            row.click()

            field_search = self.wait.until(
                EC.visibility_of_element_located(
                    XPathBuilder.input_by_placeholder("Buscar Flujos")
                )
            )
            field_search.clear()
            field_search.send_keys(flow_name)

            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//input[@placeholder='Buscar Flujos']"
                        "/ancestor::div[contains(@class,'SideBySideGroup')]"
                        "//button[.//span[normalize-space()='Buscar']]",
                    )
                )
            ).click()

            time.sleep(2)  # Esperar resultados

            # Realizar solicitud
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[.//span[contains(@class,'accessibilityhidden') "
                        "and normalize-space()='Acción principal']]",
                    )
                )
            ).click()

            # Esperar cabecera con titulo
            self.wait.until(
                EC.presence_of_element_located(
                    XPathBuilder.contains_text("p", "Complete la Información")
                )
            )

        except Exception as e:
            raise Exception(
                f"buscando categoría/flujo ({category_name}/{flow_name}): {e}"
            ) from e

    # -------------------------------------------------
    # CREAR CASO
    # -------------------------------------------------

    def create_case(self, category_name, flow_name, form_data: dict):
        """
        Crea un nuevo caso en la aplicación.

        Flujo:
        - Navega a radicación
        - Busca categoría y flujo
        - Diligencia formulario
        - Finaliza el proceso
        - Retorna número de solicitud

        Args:
            category_name (str): Nombre de la categoría.
            flow_name (str): Nombre del flujo.
            form_data (dict): Datos del formulario.

        Returns:
            dict: Resultado con el número de caso generado.
        """
        step = "Inicializando radicación"

        try:
            step = "Click en el menú Radicación de Solicitudes"
            menu = self.wait.until(
                EC.presence_of_element_located(
                    XPathBuilder.by_data_text("Radicación de Solicitudes")
                )
            )
            self.driver.execute_script("arguments[0].click();", menu)

            step = "Buscando categoría y flujo"
            self._search_category(category_name, flow_name)

            step = "Llenando formulario"
            self.form_handler.fill_form(form_data)

            step = "Presionando botón Crear"
            self.wait.until(
                EC.element_to_be_clickable(
                    XPathBuilder.button_by_text("Crear", equal=True)
                )
            ).click()

            # Finalizar el caso
            step = "Finalizar caso"
            self._change_case_status()

            step = "Obteniendo número de solicitud"
            case_number = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//p//strong[contains(text(),'-')]")
                )
            ).text.strip()

            return build_response(True, "OK", case_number)

        except TimeoutException as e:
            return build_response(False, f"Timeout durante el paso {step}. {str(e)}")

        except Exception as e:
            return build_response(False, f"Error en {step}. {e}")
