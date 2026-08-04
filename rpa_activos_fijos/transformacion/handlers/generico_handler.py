"""
transformacion/handlers/generico_handler.py — Handler genérico (PLACEHOLDER).

Sirve para CUALQUIER combinación (tipo, acción) que siga el patrón base: una
entrada -> una salida. La mayoría de combinaciones usan este handler.

⚠️ El mapeo real de columnas todavía no existe (ver transformacion/mapping/).
Mientras tanto, este handler copia el Excel de Appian "tal cual" a la carpeta de
salidas, marcando claramente que falta aplicar el mapeo. Así el Flujo 2 ya
produce un archivo y el Flujo 3 (futuro) tiene algo con qué trabajar.
"""

from transformacion.base_handler import BaseHandler
from transformacion.mapping.mapeo import obtener_mapeo


class GenericoHandler(BaseHandler):
    """Handler de patrón base: una solicitud -> un archivo macro."""

    def __init__(self, tipo, accion, logger=None):
        super().__init__(logger=logger)
        self.tipo = tipo
        self.accion = accion

    def transformar(self, solicitud):
        df_appian = self._leer_excel_appian(solicitud)

        mapeo = obtener_mapeo(self.tipo, self.accion)
        if mapeo:
            # TODO: cuando exista el mapeo real, transformar columnas aquí.
            df_salida = self._aplicar_mapeo(df_appian, mapeo)
        else:
            if self.logger:
                self.logger.warning(
                    "Caso %s: no hay mapeo definido para (%s, %s). "
                    "Se genera la macro con los datos SIN transformar "
                    "(placeholder). Completa transformacion/mapping/mapeo.py.",
                    solicitud.case_id,
                    self.tipo,
                    self.accion,
                )
            df_salida = df_appian

        archivo = self._guardar_macro(df_salida, solicitud, self.accion)
        return [archivo]

    def _aplicar_mapeo(self, df_appian, mapeo):
        """
        Renombra/selecciona columnas de Appian según el mapeo (dict
        columna_macro -> columna_appian). PLACEHOLDER de la lógica real.
        """
        # Estructura de ejemplo; se afinará cuando llegue el mapeo real.
        columnas = {}
        for columna_macro, columna_appian in mapeo.items():
            if columna_appian in df_appian.columns:
                columnas[columna_macro] = df_appian[columna_appian]
        import pandas as pd

        return pd.DataFrame(columnas) if columnas else df_appian
