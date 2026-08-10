"""
appian/bandeja_reader.py — Lector de la Bandeja de Actividades.

La librería `an0016001_appian_flow` trabaja a partir de un `case_id` YA
conocido (sabe abrir un caso, leer sus datos y descargar adjuntos). Pero NO
sabe recorrer la Bandeja de Actividades para AVERIGUAR qué casos hay
pendientes. Eso lo hacemos aquí, usando directamente el WebDriver de Selenium
que la librería expone.

La bandeja llega con solicitudes de VARIOS procesos mezclados (confirmado con
la usuaria), por eso se filtra por la columna "Nombre Del Flujo". Además se
procesa por PRIORIDAD: se ordena por "Fecha De Vencimiento" (la que vence
antes, primero).
"""

import re
from datetime import datetime

from selenium.webdriver.common.by import By

from config import (
    BANDEJA_FORMATO_FECHA,
    BANDEJA_NOMBRE_FLUJO_ESPERADO,
    BANDEJA_REGEX_CASE_ID,
    BANDEJA_XPATH_FECHA_VENCIMIENTO,
    BANDEJA_XPATH_FILAS,
    BANDEJA_XPATH_ID_EN_FILA,
    BANDEJA_XPATH_NOMBRE_FLUJO,
)
from core.exceptions import BandejaError
from core.models import CasoBandeja
from core.texto import normalizar


class BandejaReader:
    """
    Recorre la Bandeja de Actividades y devuelve la lista de solicitudes de
    Parametrización de Activos pendientes, ya ordenadas por prioridad.
    """

    def __init__(self, appian_client, logger=None):
        # Reutilizamos el driver de la librería a través del wrapper.
        self.client = appian_client
        self.driver = appian_client.driver
        self.logger = logger
        self._regex_id = re.compile(BANDEJA_REGEX_CASE_ID)

    # -- Utilidad: probar una lista de selectores hasta que uno funcione -------
    def _buscar_con_respaldo(self, contexto, lista_xpath, descripcion):
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

    def _texto_de(self, fila, lista_xpath, descripcion):
        """Texto (strip) del primer elemento no vacío que encuentre, o None."""
        for elemento in self._buscar_con_respaldo(fila, lista_xpath, descripcion):
            texto = (elemento.text or "").strip()
            if texto:
                return texto
        return None

    def _texto_y_url_de(self, fila, lista_xpath, descripcion):
        """
        Como `_texto_de`, pero además devuelve el `href` del elemento (para
        poder navegar directo a la solicitud más adelante, sin depender de
        client.search_case()). Devuelve (texto, url); url puede ser None si
        el elemento no es un enlace.
        """
        for elemento in self._buscar_con_respaldo(fila, lista_xpath, descripcion):
            texto = (elemento.text or "").strip()
            if texto:
                return texto, elemento.get_attribute("href")
        return None, None

    def _extraer_case_id(self, texto):
        if not texto:
            return None
        coincidencia = self._regex_id.search(texto)
        return coincidencia.group(0) if coincidencia else None

    def _parsear_fecha(self, texto):
        """Convierte el texto de la fecha a datetime, o None si no se puede."""
        if not texto:
            return None
        try:
            return datetime.strptime(texto, BANDEJA_FORMATO_FECHA)
        except ValueError:
            if self.logger:
                self.logger.warning(
                    "No se pudo interpretar la fecha de vencimiento '%s' "
                    "(se esperaba el formato '%s'). Ese caso quedará al final "
                    "del orden de prioridad.",
                    texto,
                    BANDEJA_FORMATO_FECHA,
                )
            return None

    def listar_pendientes(self):
        """
        Devuelve la lista de `CasoBandeja` (case_id + fecha_vencimiento) de
        Parametrización de Activos pendientes, ordenada por fecha de
        vencimiento ascendente (más urgente primero).

        Raises:
            BandejaError: si no se encuentra la tabla o ninguna solicitud
                legible de Parametrización de Activos.
        """
        if self.logger:
            self.logger.info("Leyendo la Bandeja de Actividades...")

        filas = self._buscar_con_respaldo(
            self.driver, BANDEJA_XPATH_FILAS, "filas de la bandeja"
        )
        if not filas:
            raise BandejaError(
                "No se encontraron filas en la Bandeja de Actividades. "
                "Revisa BANDEJA_XPATH_FILAS en config.py."
            )

        nombre_esperado_norm = normalizar(BANDEJA_NOMBRE_FLUJO_ESPERADO)
        vistos = set()
        pendientes = []

        for fila in filas:
            texto_id, url_caso = self._texto_y_url_de(
                fila, BANDEJA_XPATH_ID_EN_FILA, "ID del caso en la fila"
            )
            case_id = self._extraer_case_id(texto_id)
            if not case_id or case_id in vistos:
                continue

            nombre_flujo = self._texto_de(
                fila, BANDEJA_XPATH_NOMBRE_FLUJO, "nombre del flujo en la fila"
            )
            if normalizar(nombre_flujo) != nombre_esperado_norm:
                continue  # Es de otro proceso, no de Parametrización de Activos.

            fecha_texto = self._texto_de(
                fila, BANDEJA_XPATH_FECHA_VENCIMIENTO, "fecha de vencimiento en la fila"
            )

            if not url_caso and self.logger:
                self.logger.warning(
                    "Caso %s: la celda del ID no tiene un enlace (href). No se "
                    "va a poder abrir directamente; revisa BANDEJA_XPATH_ID_EN_FILA.",
                    case_id,
                )

            vistos.add(case_id)
            pendientes.append(
                CasoBandeja(case_id=case_id, fecha_vencimiento=fecha_texto, url=url_caso)
            )

        if not pendientes:
            raise BandejaError(
                "Se encontraron filas pero ninguna solicitud de "
                f"'{BANDEJA_NOMBRE_FLUJO_ESPERADO}' con un ID legible. "
                "Revisa los selectores BANDEJA_XPATH_* en config.py."
            )

        # Prioridad: vence antes, primero. Fechas no interpretables van al final.
        pendientes.sort(
            key=lambda c: self._parsear_fecha(c.fecha_vencimiento) or datetime.max
        )

        if self.logger:
            self.logger.info(
                "Bandeja leída: %s solicitud(es) de '%s' pendiente(s), en "
                "orden de prioridad:",
                len(pendientes),
                BANDEJA_NOMBRE_FLUJO_ESPERADO,
            )
            for caso in pendientes:
                self.logger.info(
                    "  - %s | vence: %s", caso.case_id, caso.fecha_vencimiento
                )

        return pendientes
