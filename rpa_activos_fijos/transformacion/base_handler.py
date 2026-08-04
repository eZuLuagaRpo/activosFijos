"""
transformacion/base_handler.py — Interfaz común de un handler de transformación.

Un "handler" es la pieza que sabe convertir el Excel que viene de Appian al
formato de la macro de SAP para una combinación concreta (tipo de activo, acción).
Todos los handlers heredan de BaseHandler e implementan `transformar`.

El objetivo de esta entrega es dejar la ESTRUCTURA lista. El mapeo real de
columnas (qué campo de Appian va a qué campo de la macro) lo entregará después
el desarrollador y vivirá en transformacion/mapping/ (no se inventa aquí).
"""

import os
from datetime import datetime

import pandas as pd

from config import CODIGO_MACRO_POR_ACCION, OUTPUT_DIR
from core.models import ArchivoMacro


class BaseHandler:
    """
    Clase base de todos los handlers.

    Subclases deben definir:
      - tipo:   tipo de activo canónico que atienden (str)
      - accion: acción canónica que atienden (str)
    y sobreescribir `transformar()`.
    """

    tipo = None
    accion = None

    def __init__(self, logger=None):
        self.logger = logger

    # -- API pública que usa el Flujo 2 --------------------------------------
    def transformar(self, solicitud):
        """
        Convierte la `solicitud` (con su Excel de Appian) en uno o más
        `ArchivoMacro`. Debe devolver SIEMPRE una lista (aunque sea de 1).

        Esta implementación base es un PLACEHOLDER: lee el Excel de Appian y
        genera un Excel de salida con los datos "tal cual", dejando marcado
        dónde se aplicará el mapeo real. Cada handler concreto la especializa.
        """
        raise NotImplementedError(
            "Cada handler debe implementar transformar()."
        )

    # -- Utilidades compartidas por los handlers ------------------------------
    def _leer_excel_appian(self, solicitud):
        """Lee el Excel descargado de Appian y devuelve un DataFrame de pandas."""
        if not solicitud.excel_path or not os.path.exists(solicitud.excel_path):
            raise FileNotFoundError(
                f"No se encontró el Excel del caso {solicitud.case_id}: "
                f"{solicitud.excel_path}"
            )
        if self.logger:
            self.logger.info(
                "Leyendo Excel de Appian del caso %s: %s",
                solicitud.case_id,
                solicitud.excel_path,
            )
        return pd.read_excel(solicitud.excel_path)

    def _guardar_macro(self, df, solicitud, accion, sufijo=""):
        """
        Guarda un DataFrame como Excel en la carpeta de salidas y devuelve un
        ArchivoMacro describiéndolo.

        El nombre incluye el caso, la acción y una marca de tiempo para no
        pisar archivos de ejecuciones anteriores.
        """
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        codigo = CODIGO_MACRO_POR_ACCION.get(accion, accion.upper())
        marca = datetime.now().strftime("%Y%m%d_%H%M%S")
        parte_sufijo = f"_{sufijo}" if sufijo else ""
        nombre = f"{solicitud.case_id}_{codigo}{parte_sufijo}_{marca}.xlsx"
        ruta = os.path.join(OUTPUT_DIR, nombre)

        df.to_excel(ruta, index=False)

        if self.logger:
            self.logger.info(
                "Macro generada (%s) para el caso %s: %s",
                codigo,
                solicitud.case_id,
                ruta,
            )
        return ArchivoMacro(ruta=ruta, accion=accion, codigo_macro=codigo)
