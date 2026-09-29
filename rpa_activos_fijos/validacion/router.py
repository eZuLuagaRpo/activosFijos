"""
validacion/router.py — Enrutador (tipo de activo, acción) -> validador.

Cada combinación se va habilitando a medida que negocio entrega su plantilla
y sus reglas (se trabaja activo por activo). Si llega una combinación que aún
no tiene validador, el caso NO se procesa: nunca se envía a SAP una plantilla
sin validar.
"""

from config import ACCION_CREACION, TIPO_BRP
from core.exceptions import ValidacionError
from validacion.plantillas.brp_creacion import ValidadorBrpCreacion

VALIDADORES = {
    (TIPO_BRP, ACCION_CREACION): ValidadorBrpCreacion,
}


def resolver(tipo, accion, logger=None):
    """Devuelve una instancia del validador para (tipo, accion)."""
    clase = VALIDADORES.get((tipo, accion))
    if clase is None:
        raise ValidacionError(
            f"Aún no hay validación implementada para (tipo={tipo!r}, "
            f"accion={accion!r}). El caso no se procesa."
        )
    return clase(logger=logger)
