"""
appian/bandeja_reader.py — Lector de la Bandeja de Actividades (MÓDULO NUEVO).

La librería `an0016001_appian_flow` trabaja a partir de un `case_id` YA conocido
(sabe abrir un caso, leer sus datos y descargar adjuntos). Pero NO sabe recorrer
la Bandeja de Actividades para AVERIGUAR qué casos hay pendientes. Eso lo hacemos
aquí, usando directamente el WebDriver de Selenium que la librería expone.

⚠️ SELECTORES PLACEHOLDER ⚠️
Todavía no conocemos los XPath reales de la tabla de la bandeja. Están en
config.py (BANDEJA_XPATH_*) marcados con  # TODO: CAPTURAR SELECTOR REAL.
Este módulo prueba varios selectores "de respaldo" en orden: si el principal no
encuentra nada, pasa al siguiente antes de rendirse.

Cómo capturar los selectores reales: ver docs/CONFIGURACION_MANUAL.md.
"""

import re

from selenium.webdriver.common.by import By

from config import (
    BANDEJA_FILTRAR_POR_TIPO,
    BANDEJA_REGEX_CASE_ID,
    BANDEJA_XPATH_FILAS,
    BANDEJA_XPATH_ID_EN_FILA,
)
from core.exceptions import BandejaError


class BandejaReader:
    """
    Recorre la Bandeja de Actividades y devuelve la lista de IDs de casos
    pendientes.
    """

    def __init__(self, appian_client, logger=None):
        # Reutilizamos el driver/wait de la librería a través del wrapper.
        self.client = appian_client
        self.driver = appian_client.driver
        self.logger = logger
        self._regex_id = re.compile(BANDEJA_REGEX_CASE_ID)

    # -- Utilidad: probar una lista de selectores hasta que uno funcione -------
    def _buscar_con_respaldo(self, contexto, lista_xpath, descripcion):
        """
        Prueba cada XPath de `lista_xpath` sobre `contexto` (el driver o una
        fila). Devuelve la lista de elementos del primer selector que encuentre
        algo. Si ninguno funciona, devuelve lista vacía.
        """
        for indice, xpath in enumerate(lista_xpath):
            try:
                elementos = contexto.find_elements(By.XPATH, xpath)
                if elementos:
                    if self.logger and indice > 0:
                        self.logger.warning(
                            "Se usó selector de respaldo #%s para %s: %s",
                            indice,
                            descripcion,
                            xpath,
                        )
                    return elementos
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        "Selector inválido para %s (%s): %s", descripcion, xpath, e
                    )
        return []

    def _extraer_case_id(self, fila):
        """
        Dada una fila de la tabla, intenta sacar el ID del caso (ej. PDA-2389).
        Prueba los selectores de ID y, dentro del texto encontrado, aplica la
        expresión regular de config.py para quedarse solo con el ID.
        """
        celdas = self._buscar_con_respaldo(
            fila, BANDEJA_XPATH_ID_EN_FILA, "ID del caso en la fila"
        )
        for celda in celdas:
            texto = (celda.text or "").strip()
            coincidencia = self._regex_id.search(texto)
            if coincidencia:
                return coincidencia.group(0)
        return None

    def listar_pendientes(self):
        """
        Devuelve la lista de `case_id` pendientes en la bandeja (sin duplicados,
        conservando el orden en que aparecen).

        Raises:
            BandejaError: si no se encuentra la tabla o no hay ningún ID legible.
        """
        if self.logger:
            self.logger.info("Leyendo la Bandeja de Actividades...")

        # La librería ya deja abierta la URL base tras el login. Si en el futuro
        # la bandeja está en otra URL, se navega aquí (self.driver.get(...)).

        # PENDIENTE (ver CONFIGURACION_MANUAL.md): se asume que a la usuaria le
        # llegan SOLO solicitudes de activos fijos. Si algún día llegan mezcladas,
        # activar BANDEJA_FILTRAR_POR_TIPO y aplicar el filtro aquí.
        if BANDEJA_FILTRAR_POR_TIPO:
            self._aplicar_filtro_tipo()

        filas = self._buscar_con_respaldo(
            self.driver, BANDEJA_XPATH_FILAS, "filas de la bandeja"
        )

        if not filas:
            raise BandejaError(
                "No se encontraron filas en la Bandeja de Actividades. "
                "Revisa los selectores BANDEJA_XPATH_FILAS en config.py "
                "(ver docs/CONFIGURACION_MANUAL.md)."
            )

        pendientes = []
        for fila in filas:
            case_id = self._extraer_case_id(fila)
            if case_id and case_id not in pendientes:
                pendientes.append(case_id)

        if not pendientes:
            raise BandejaError(
                "Se encontraron filas pero ningún ID de caso legible. "
                "Revisa BANDEJA_XPATH_ID_EN_FILA y BANDEJA_REGEX_CASE_ID en config.py."
            )

        if self.logger:
            self.logger.info(
                "Bandeja leída: %s solicitud(es) pendiente(s): %s",
                len(pendientes),
                ", ".join(pendientes),
            )
        return pendientes

    def _aplicar_filtro_tipo(self):
        """
        Punto preparado para filtrar la bandeja por tipo de proceso (activos
        fijos) cuando se confirme que llegan casos mezclados.

        # TODO: CAPTURAR SELECTOR REAL del filtro (BANDEJA_XPATH_FILTRO) e
        # implementar el clic/escritura necesarios. De momento no hace nada.
        """
        if self.logger:
            self.logger.warning(
                "Filtrado por tipo activado pero NO implementado todavía "
                "(pendiente de confirmar y capturar el selector del filtro)."
            )
