"""
Módulo encargado de la gestión y diligenciamiento dinámico de formularios en Appian.

Contiene la clase FormHandler, la cual permite:
- Identificar campos en pantalla a partir de sus labels
- Detectar automáticamente el tipo de cada campo
- Completar formularios dinámicos con diferentes tipos de inputs
- Manejar carga de archivos y controles complejos

Este componente abstrae la complejidad de interacción con formularios
en Appian, permitiendo un llenado flexible basado en configuración.
"""

import re
import time
import unicodedata
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys


class FormHandler:
    """
    Gestiona el diligenciamiento automático de formularios dinámicos.

    Permite identificar y completar distintos tipos de campos como:
    - Inputs de texto
    - Textareas
    - Dropdowns
    - Radio buttons
    - Checkboxes
    - Selectores de usuario (user picker)
    - Carga de archivos

    La lógica está basada en la detección del tipo de campo en tiempo de ejecución.
    """

    def __init__(self, driver, wait, timeout_files):
        """
        Inicializa el manejador de formularios.

        Args:
            driver: Instancia del WebDriver.
            wait: WebDriverWait para sincronización.
            timeout_files (int): Tiempo máximo de espera para carga de archivos.
        """
        self.driver = driver
        self.wait = wait
        self.timeout_files = timeout_files

    def fill_form(self, data: dict):
        """
        Llena un formulario dinámicamente a partir de un diccionario.

        Recorre cada campo identificado por su label y determina el tipo
        de control para aplicar la lógica de llenado correspondiente.

        Args:
            data (dict): Diccionario con:
                - key: nombre del campo (label visible)
                - value: valor a ingresar

        Raises:
            Exception: Si ocurre error en el llenado de algún campo.
        """
        for field_name, value in data.items():
            if value is None or str(value).strip() == "":
                continue

            try:
                time.sleep(0.5)  # Pequeña pausa para evitar problemas de renderizado

                # Obtener el contenedor del campo a partir del label
                fields = self._find_field_by_label(field_name)
                field_layout = fields[0]

                # Detectar tipo de campo
                field_type = self._detect_field_type(field_layout)

                if field_type == "user_picker":
                    for u in value:
                        self._fill_combobox(field_layout, u)
                    continue

                if field_type == "file_upload":
                    self._fill_files(field_layout, value)
                    continue

                if field_type == "textarea":
                    self._fill_textarea(field_layout, value)
                    continue

                if field_type == "dropdown":
                    self._fill_dropdown(field_layout, value)
                    continue

                if field_type == "radio":
                    self._fill_radio(field_layout, value)
                    continue

                if field_type == "checkbox":
                    self._fill_checkbox(field_layout, value)
                    continue

                if field_type == "input":
                    self._fill_text_input(field_layout, value)
                    continue

                raise Exception(f"Tipo de campo '{field_name}' no reconocido")

            except Exception as e:
                raise Exception(f"Error llenando el campo '{field_name}'. {e}") from e

    def _detect_field_type(self, field_layout):
        """
        Detecta el tipo de control de un campo en función de su estructura HTML.

        Args:
            field_layout: Elemento contenedor del campo.

        Returns:
            str: Tipo de campo identificado.

        Raises:
            Exception: Si ocurre error en la detección.
        """
        try:
            field_type = None
            if field_layout.find_elements(
                By.XPATH, ".//input[contains(@class,'PickerWidget---picker_input')]"
            ):
                field_type = "user_picker"

            if field_layout.find_elements(By.XPATH, ".//input[@type='file']"):
                field_type = "file_upload"

            if field_layout.find_elements(By.XPATH, ".//textarea"):
                field_type = "textarea"

            if field_layout.find_elements(By.XPATH, ".//input[@type='checkbox']"):
                field_type = "checkbox"

            if field_layout.find_elements(By.XPATH, ".//input[@type='radio']"):
                field_type = "radio"

            if field_layout.find_elements(By.XPATH, ".//div[@role='combobox']"):
                field_type = "dropdown"

            if field_layout.find_elements(By.XPATH, ".//input[@type='text']"):
                field_type = "input"

            return field_type

        except Exception as e:
            raise Exception(
                f"No fue posible detectar el tipo de campo ({str(e)})"
            ) from e

    # -------------------------------------------------
    # BUSCAR FIELD POR LABEL
    # -------------------------------------------------

    def _normalize(self, text: str) -> str:
        """
        Normaliza texto para comparación flexible.

        Realiza:
        - Conversión a minúsculas
        - Eliminación de tildes
        - Eliminación de caracteres especiales
        - Normalización de espacios

        Args:
            text (str): Texto original.

        Returns:
            str: Texto normalizado.
        """
        if not text:
            return ""

        text = text.lower()
        text = unicodedata.normalize("NFD", text)

        text = "".join(c for c in text if unicodedata.category(c) != "Mn")

        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _find_field_by_label(self, label_text):
        """
        Busca un campo en la interfaz a partir del texto de su label.

        La búsqueda es tolerante a tildes, espacios y variaciones de texto.

        Args:
            label_text (str): Texto visible del label.

        Returns:
            list: Lista de elementos que contienen el campo.

        Raises:
            Exception: Si no se encuentra el campo.
        """
        try:
            search_text = self._normalize(label_text)
            labels = self.wait.until(
                EC.presence_of_all_elements_located(
                    (
                        By.XPATH,
                        "//span[contains(@class,'FieldLayout---field_label')] | "
                        "//label[contains(@class,'FieldLayout---field_label')]",
                    )
                )
            )

            found_fields = []

            for lbl in labels:
                dom_text = self._normalize(lbl.text)

                if search_text in dom_text:
                    fields = lbl.find_elements(
                        By.XPATH,
                        ".//ancestor::div["
                        "contains(@class,'FieldLayout---field_layout') "
                        "and ("
                        ".//input "
                        "or .//textarea "
                        "or .//div[@role='combobox'] "
                        "or .//input[@type='file'] "
                        "or .//div[@role='radiogroup'] "
                        "or .//input[@type='radio'] "
                        "or .//input[@type='checkbox'] "
                        "or .//input[@role='textbox']"
                        ")]",
                    )

                    if fields:
                        found_fields.append(fields[0])
                        break

            if not found_fields:
                raise Exception(f"No se encontró el label '{label_text}'")

            return found_fields

        except Exception as e:
            raise Exception(f"No se encontró el label '{label_text}'") from e

    # -------- TIPOS DE CAMPOS --------

    def _fill_text_input(self, field, value):
        """
        Llena un campo de texto simple.

        Args:
            field: Elemento del campo.
            value: Valor a ingresar.
        """
        try:
            inputs = field.find_elements(By.XPATH, ".//input[@type='text']")
            if inputs:
                inputs[0].clear()
                inputs[0].send_keys(value)
                inputs[0].send_keys(Keys.ENTER)

        except Exception as e:
            raise Exception(f"No se encontró el campo de texto '{field}'") from e

    def _fill_textarea(self, field, value):
        """
        Llena un campo tipo textarea.

        Args:
            field: Elemento del campo.
            value: Valor a ingresar.
        """
        try:
            areas = field.find_elements(By.XPATH, ".//textarea")
            if areas:
                areas[0].clear()
                areas[0].send_keys(value)

        except Exception as e:
            raise Exception(f"No se encontró el campo textarea '{field}'") from e

    def _fill_date(self, field, value):
        """
        Llena un campo de fecha.

        Args:
            field: Elemento del campo.
            value: Fecha en formato texto.
        """
        try:
            dates = field.find_elements(
                By.XPATH, ".//input[@type='text' and @role='textbox']"
            )

            if dates:
                dates[0].clear()
                dates[0].send_keys(value)
                dates[0].send_keys(Keys.TAB)

        except Exception as e:
            raise Exception(f"No se encontró el campo de fecha '{field}'") from e

    def _fill_dropdown(self, field, value):
        """
        Selecciona un valor en un campo tipo dropdown.

        Args:
            field: Elemento del campo.
            value (str): Opción a seleccionar.
        """
        try:
            combos = field.find_elements(
                By.XPATH,
                ".//div[@role='combobox' and contains(@class,'DropdownWidget---dropdown_value')]",
            )

            if not combos:
                raise Exception(f"No se encontró el campo de dropdown {field}")

            dropdown = combos[0]

            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", dropdown
            )

            self.driver.execute_script("arguments[0].click();", dropdown)

            option = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//li[@role='option' and normalize-space()='{value}']")
                )
            )

            option.click()

        except Exception as e:
            raise Exception(f"No se encontró el campo de dropdown '{field}'") from e

    def _fill_radio(self, field, value):
        """
        Selecciona un valor en un grupo de radio buttons.

        Args:
            field: Elemento del campo.
            value (str): Opción a seleccionar.
        """
        try:
            radios = field.find_elements(
                By.XPATH, f".//label[normalize-space()='{value}']"
            )

            if radios:
                radios[0].click()

        except Exception as e:
            raise Exception(f"No se encontró el campo radio '{field}'") from e

    def _fill_checkbox(self, field, value):
        """
        Marca o desmarca un checkbox según el valor.

        Args:
            field: Elemento del campo.
            value (str): "si" o "no".
        """
        try:
            checks = field.find_elements(By.XPATH, ".//input[@type='checkbox']")

            if checks:

                if (value.lower() == "si" and not checks[0].is_selected()) or (
                    value.lower() == "no" and checks[0].is_selected()
                ):

                    field.find_element(By.XPATH, ".//label").click()

        except Exception as e:
            raise Exception(f"No se encontró el campo de checkbox '{field}'") from e

    def _fill_files(self, field, file_paths):
        """
        Carga archivos en un campo tipo adjuntos y espera a que finalice la subida.

        Args:
            field: Elemento del campo.
            file_paths (list | str): Ruta(s) de los archivos.

        Raises:
            Exception: Si falla la carga o si los archivos no existen.
        """
        try:
            if isinstance(file_paths, str):
                file_paths = [file_paths]

            absolute_paths = []

            for path in file_paths:
                path_abs = os.path.abspath(path)

                if not os.path.isfile(path_abs):
                    raise FileNotFoundError(f"Archivo no existe: {path_abs}")

                absolute_paths.append(path_abs)

            file_input = self.wait.until(
                lambda d: field.find_element(By.XPATH, ".//input[@type='file']")
            )

            file_input.send_keys("\n".join(absolute_paths))

            wait_upload = WebDriverWait(self.driver, self.timeout_files)

            wait_upload.until(lambda d: self._files_uploaded(len(absolute_paths)))

        except TimeoutException as e:
            raise Exception(
                "los archivos no terminaron de cargar (archivo muy pesado)"
            ) from e

        except Exception as e:
            raise Exception(f"No se encontró el campo de archivos '{field}'") from e

    def _fill_combobox(self, field_layout, value):
        """
        Selecciona un valor en un campo tipo user picker.

        Args:
            field_layout: Elemento del campo.
            value (str): Valor a seleccionar.
        """
        try:
            input_field = self.wait.until(
                lambda d: field_layout.find_element(
                    By.XPATH, ".//input[contains(@class,'PickerWidget---picker_input')]"
                )
            )

            input_field.clear()
            input_field.send_keys(value)

            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//li[contains(normalize-space(.), '{value}')]")
                )
            )

            input_field.send_keys(Keys.ENTER)

        except Exception as e:
            raise Exception(f"Valor '{value}' no encontrado") from e

    def _files_uploaded(self, expected_count):
        """
        Verifica si todos los archivos han sido cargados completamente.

        Condiciones:
        - Existe tamaño de archivo
        - No hay progreso parcial (texto con "/")
        - No existe icono de carga
        - No está en estado 'uploading'

        Args:
            expected_count (int): Número esperado de archivos.

        Returns:
            bool: True si todos los archivos están completamente cargados.
        """
        try:
            items = self.driver.find_elements(
                By.XPATH, ".//div[@data-testid='FileInfoView-uploadItem']"
            )

            if len(items) < expected_count:
                return False

            for item in items:
                size_elem = item.find_element(
                    By.XPATH, ".//span[@data-testid='FileInfoView-fileSize']"
                )

                text = size_elem.text.strip().lower()

                if "/" in text or text == "":
                    return False

                progress = item.find_elements(
                    By.XPATH, ".//svg[contains(@class,'progress_circle')]"
                )

                if progress:
                    return False

                uploading_icon = item.find_elements(
                    By.XPATH, ".//svg[contains(@class,'uploading')]"
                )

                if uploading_icon:
                    return False

            return True

        except Exception:
            return False
