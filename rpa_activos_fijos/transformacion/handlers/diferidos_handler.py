"""
transformacion/handlers/diferidos_handler.py — Handler ESPECIAL de Diferidos.

CASO ESPECIAL DE NEGOCIO: la creación de un activo Diferido NO se hace en un solo
paso. Primero se CREA (AS01) y luego se MODIFICA (AS02). Por eso este handler,
cuando la acción es "creación", produce DOS archivos macro:
    1) el de creación (AS01)
    2) el de modificación (AS02)

Para el resto de acciones de Diferidos (modificación, eliminación) se comporta
como el patrón base: una entrada -> una salida.

⚠️ El mapeo real de columnas por paso todavía no existe (placeholder).
"""

from config import ACCION_CREACION, ACCION_MODIFICACION
from transformacion.base_handler import BaseHandler
from transformacion.mapping.mapeo import obtener_mapeo


class DiferidosHandler(BaseHandler):
    """Handler para el tipo de activo 'diferidos', con el caso especial de creación."""

    def __init__(self, accion, logger=None):
        super().__init__(logger=logger)
        self.tipo = "diferidos"
        self.accion = accion

    def transformar(self, solicitud):
        df_appian = self._leer_excel_appian(solicitud)

        # Caso especial: creación de Diferido = AS01 (creación) + AS02 (modificación).
        if self.accion == ACCION_CREACION:
            if self.logger:
                self.logger.info(
                    "Caso %s: Diferido + Creación -> se generarán DOS macros "
                    "(AS01 creación y AS02 modificación).",
                    solicitud.case_id,
                )

            df_as01 = self._transformar_paso(df_appian, solicitud, "creacion_as01")
            archivo_as01 = self._guardar_macro(
                df_as01, solicitud, ACCION_CREACION, sufijo="paso1"
            )

            df_as02 = self._transformar_paso(df_appian, solicitud, "creacion_as02")
            archivo_as02 = self._guardar_macro(
                df_as02, solicitud, ACCION_MODIFICACION, sufijo="paso2"
            )

            # El orden importa: primero creación, luego modificación.
            return [archivo_as01, archivo_as02]

        # Resto de acciones: patrón base (una salida).
        df_salida = self._transformar_paso(df_appian, solicitud, self.accion)
        archivo = self._guardar_macro(df_salida, solicitud, self.accion)
        return [archivo]

    def _transformar_paso(self, df_appian, solicitud, clave_mapeo):
        """
        Aplica el mapeo del paso indicado (clave_mapeo puede ser
        'creacion_as01', 'creacion_as02', 'modificacion', ...). PLACEHOLDER
        mientras no exista el mapeo real: devuelve los datos sin transformar.
        """
        mapeo = obtener_mapeo(self.tipo, clave_mapeo)
        if not mapeo:
            if self.logger:
                self.logger.warning(
                    "Caso %s: sin mapeo para (diferidos, %s). Se usa el Excel "
                    "SIN transformar (placeholder).",
                    solicitud.case_id,
                    clave_mapeo,
                )
            return df_appian

        import pandas as pd

        columnas = {}
        for columna_macro, columna_appian in mapeo.items():
            if columna_appian in df_appian.columns:
                columnas[columna_macro] = df_appian[columna_appian]
        return pd.DataFrame(columnas) if columnas else df_appian
