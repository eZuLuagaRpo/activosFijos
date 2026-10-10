"""
validacion/router.py — Enrutador (tipo de activo, acción) -> validador.

Cada combinación se va habilitando a medida que negocio entrega su plantilla
y sus reglas (se trabaja activo por activo). Si llega una combinación que aún
no tiene validador, el caso NO se procesa: nunca se envía a SAP una plantilla
sin validar.
"""

from config import ACCION_CREACION, ACCION_MODIFICACION, TIPO_BRP
from core.exceptions import ValidacionError
from validacion.plantillas.brp_creacion import ValidadorBrpCreacion
from validacion.plantillas.brp_modificacion import ValidadorBrpModificacion

VALIDADORES = {
    (TIPO_BRP, ACCION_CREACION): ValidadorBrpCreacion,
    (TIPO_BRP, ACCION_MODIFICACION): ValidadorBrpModificacion,
}


def identificar_plantilla(ruta_excel, candidatos):
    """
    Devuelve el (tipo, accion) de `candidatos` cuya plantilla coincide con
    los encabezados del archivo, o None si no coincide con ninguna. Se usa
    cuando una solicitud trae 2 Excel, para saber cuál es cuál por CONTENIDO
    (no por el nombre del archivo).
    """
    for clave in candidatos:
        clase = VALIDADORES.get(clave)
        if clase is not None and clase().reconoce_encabezados(ruta_excel):
            return clave
    return None


def resolver(tipo, accion, logger=None):
    """Devuelve una instancia del validador para (tipo, accion)."""
    clase = VALIDADORES.get((tipo, accion))
    if clase is None:
        raise ValidacionError(
            f"Aún no hay validación implementada para (tipo={tipo!r}, "
            f"accion={accion!r}). El caso no se procesa."
        )
    return clase(logger=logger)
