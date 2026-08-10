"""
Módulo encargado de la gestión y descarga de reportes en Appian.

Contiene la clase ReportPage, la cual permite:
- Acceder a la vista de reportes
- Aplicar filtros dinámicos (fechas y listas)
- Validar formatos de entrada
- Descargar reportes en Excel
- Controlar la generación y descarga de archivos

Este componente encapsula toda la lógica necesaria para interactuar
con reportes dentro de la aplicación.
"""

import os
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from .response import build_response
from .xpath_builder import XPathBuilder


class ReportPage:
    """
    Gestiona la interacción con la página de reportes.

    Permite:
    - Aplicar filtros dinámicos
    - Validar fechas
    - Ejecutar descargas de reportes
    - Integrarse con el gestor de descargas
    """

    def __init__(self, driver, wait, timeout_files, download_dir, download_manager):
        """
        Inicializa la página de reportes.

        Args:
            driver: Instancia del WebDriver.
            wait: WebDriverWait para sincronización.
            timeout_files (int): Tiempo máximo de espera para descargas.
            download_dir (str): Directorio de descarga.
            download_manager: Gestor de descargas.
        """
        self.driver = driver
        self.wait = wait
        self.timeout_files = timeout_files
        self.download_dir = download_dir
        self.download_manager = download_manager

    # -------------------------------------------------
    # DESCARGAR INFORMES
    # -------------------------------------------------
    def download_report(self, filter_data):
        """
        Ejecuta la descarga de un reporte aplicando filtros dinámicos.

        Flujo:
        - Abre el reporte
        - Aplica los filtros (fechas o listas)
        - Ejecuta la descarga
        - Espera hasta que el archivo esté disponible

        Args:
            filter_data (dict):
                Diccionario con los filtros a aplicar:
                - key: nombre del filtro
                - value:
                    - str → filtro tipo dropdown
                    - list/tuple (2 valores) → filtro de rango de fechas

        Returns:
            dict: Respuesta estructurada con:
                - success (bool)
                - message (str)
                - data (dict):
                    - file
                    - path
                    - full_path
        """
        step = "Abrir reporte"
        try:
            step = "Aplicar filtros"
            for filter_name, filter_value in filter_data.items():
                # ignorar filtros vacíos
                if not filter_value:
                    continue

                # detectar fecha (lista o tupla de 2 valores)
                if isinstance(filter_value, (list, tuple)) and len(filter_value) == 2:
                    # Validar fechas
                    self._validate_date(filter_name, filter_value[0], filter_value[1])

                    # Aplicar filtro fecha
                    self._apply_date_filter(
                        filter_name, filter_value[0], filter_value[1]
                    )

                # si es campo seleccionable
                elif isinstance(filter_value, str):
                    self._apply_dropdown_filter(filter_name, filter_value)

            step = "Click en descargar informe"
            self.wait.until(
                EC.element_to_be_clickable(
                    XPathBuilder.button_by_text("Exportar a Excel")
                )
            ).click()

            step = "Esperando que el informe descargue"
            file = self.download_manager.wait_for_download(self.download_dir)

            return build_response(
                True,
                "OK",
                {
                    "file": file,
                    "path": self.download_dir,
                    "full_path": os.path.join(self.download_dir, file),
                },
            )

        except Exception as e:
            return build_response(False, f"Error en el reporte -> ({step}). {str(e)}")

    def open_process_hq(self, report_data):
        """
        Valida que la pantalla de reportes esté disponible.

        Espera la presencia del botón de exportación.

        Raises:
            Exception: Si no es posible acceder al reporte.
        """
        step = "Esperar a que el reporte cargue"
        try:
            # buscar la url del reporte
            report_link = self.wait.until(
                EC.presence_of_element_located(
                    XPathBuilder.contains_text(
                        "a", report_data["report_name"], equal=True
                    )
                )
            )

            main_window = self.driver.current_window_handle
            old_windows = self.driver.window_handles

            report_link.click()

            # esperar nueva pestaña
            self.wait.until(lambda d: len(d.window_handles) > len(old_windows))

            # cambiar
            new_windows = [
                w for w in self.driver.window_handles if w not in old_windows
            ]
            if not new_windows:
                raise Exception("No se abrió una nueva ventana para el reporte")

            new_window = new_windows[0]

            self.driver.switch_to.window(new_window)

            # esperar que deje de ser about:blank
            self.wait.until(lambda d: d.current_url != "about:blank")

            # URL
            report_url = self.driver.current_url
            if not report_url:
                raise Exception("No se pudo obtener la URL del reporte")

            self.wait.until(
                EC.visibility_of_element_located(
                    XPathBuilder.button_by_text("Exportar a Excel")
                )
            )

            return {"main_window": main_window, "report_window": new_window}

        except Exception as e:
            raise Exception(f"No fue posible abrir el reporte. ({step})") from e

    def close_process_hq(self, process_data):
        """
        Cierra la ventana del proceso de reporte.

        Args:
            process_data (dict): Datos del proceso de reporte.

        Raises:
            Exception: Si no es posible cerrar el reporte.
        """
        step = "Esperar a que el reporte cargue"
        try:
            # CERRAR pestaña del reporte
            self.driver.close()

            # VOLVER a la principal
            self.driver.switch_to.window(process_data["main_window"])

        except Exception as e:
            raise Exception(f"No fue posible cerrar el reporte. ({step})") from e

    def _apply_date_filter(self, filter_name, date_from, date_to):
        """
        Aplica un filtro de rango de fechas.

        Args:
            filter_name (str): Nombre del filtro.
            date_from (str): Fecha inicial (dd/mm/yyyy).
            date_to (str): Fecha final (dd/mm/yyyy).

        Raises:
            Exception: Si ocurre error durante la aplicación del filtro.
        """
        try:
            # abrir filtro
            self._open_filter_process_hq(filter_name)

            # input DESDE
            input_from = self.wait.until(
                EC.element_to_be_clickable(XPathBuilder.input_picker("Desde"))
            )
            input_from.click()
            input_from.clear()
            input_from.send_keys(date_from)

            # input HASTA
            input_to = self.wait.until(
                EC.element_to_be_clickable(XPathBuilder.input_picker("Hasta"))
            )
            input_to.click()
            input_to.clear()
            input_to.send_keys(date_to)
            input_to.send_keys(Keys.ENTER)

        except Exception as e:
            raise Exception(
                f"Error aplicando el filtro: {filter_name}. ({str(e)})"
            ) from e

    def _apply_dropdown_filter(self, filter_name, filter_value):
        """
        Aplica un filtro tipo dropdown.

        Args:
            filter_name (str): Nombre del filtro.
            filter_value (str): Valor a seleccionar.

        Raises:
            Exception: Si ocurre un error durante la selección.
        """
        step = "Abrir filtro"
        try:
            # abrir filtro
            self._open_filter_process_hq(filter_name)

            step = f"Seleccionar opción: {filter_value}"
            option = self.wait.until(
                EC.presence_of_element_located(
                    XPathBuilder.dropdown_option(filter_value)
                )
            )
            option.click()
            option.send_keys(Keys.ESCAPE)

        except Exception as e:
            raise Exception(
                f"Error aplicando el filtro: {filter_name}. {step}. ({str(e)})"
            ) from e

    def _open_filter_process_hq(self, filter_name):
        """
        Abre el panel de un filtro específico dentro del reporte.

        Args:
            filter_name (str): Nombre del filtro.

        Raises:
            Exception: Si no se encuentra el filtro.
        """
        try:
            card = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        f"""
                //strong[normalize-space()='{filter_name}']
                /ancestor::div[contains(@class,'CardLayout')][1]
                """,
                    )
                )
            )

            dropdown = card.find_element(
                By.XPATH,
                ".//div[@data-testid='DateRangeWidget-dropdown' or @role='combobox']",
            )

            self.wait.until(EC.element_to_be_clickable(dropdown))
            dropdown.click()

        except Exception as e:
            raise Exception("No se encontró el filtro") from e

    def _validate_date(self, filter_name, date_from, date_to):
        """
        Valida el formato y coherencia de un rango de fechas.

        Args:
            filter_name (str): Nombre del filtro.
            date_from (str): Fecha inicial.
            date_to (str): Fecha final.

        Raises:
            Exception:
                - Si el formato es inválido
                - Si la fecha inicial es mayor que la final
        """
        try:
            f_desde = datetime.strptime(date_from, "%d/%m/%Y")
            f_hasta = datetime.strptime(date_to, "%d/%m/%Y")

        except ValueError as e:
            raise Exception(f"{filter_name} → formato inválido. Use dd/mm/yyyy") from e

        # validar orden
        if f_desde > f_hasta:
            raise Exception(
                f"{filter_name} → fecha desde ({date_from}) es mayor que hasta ({date_to})"
            )

    def search_report(self, report_data):
        """
        Busca un reporte en la interfaz de Appian utilizando el nombre del flujo
        y el nombre del reporte proporcionados.

        Args:
            report_data (dict): Diccionario con la información necesaria para la búsqueda.
                Debe contener las siguientes claves:
                    - flow_name (str): Nombre del flujo a buscar.
                    - report_name (str): Nombre del reporte asociado al flujo.

        Raises:
            Exception: Si no se proporciona el nombre del flujo.
            Exception: Si no se proporciona el nombre del reporte.
            Exception: Si ocurre algún error durante la búsqueda en la interfaz,
                    incluyendo problemas con el localizador del elemento o interacción
                    con el navegador.

        Returns:
            None: Este método no retorna ningún valor, pero realiza la acción de búsqueda
            en la interfaz.
        """
        try:
            if not report_data["flow_name"]:
                raise Exception("Debe proporcionar el nombre del flujo.")

            if not report_data["report_name"]:
                raise Exception("Debe proporcionar el nombre del reporte.")

            # buscar el reporte por nombre del flujo
            field_category = self.wait.until(
                EC.visibility_of_element_located(
                    XPathBuilder.input_by_placeholder(
                        "Buscar por informe o nombre de consola"
                    )
                )
            )
            field_category.clear()
            field_category.send_keys(report_data["flow_name"])
            field_category.send_keys(Keys.ENTER)

        except Exception as e:
            raise Exception(
                f"No fue posible encontrar el reporte ({report_data['report_name']}) {str(e)}"
            ) from e
