"""
flujos/flujo2_validar.py — FLUJO 2: validación de la plantilla Excel.

Cambio de negocio (2026-09-27): el Excel que adjunta el usuario en Appian YA
ES el formato que se carga a SAP. Ya no se transforma a otro formato: este
flujo es el FILTRO DE CALIDAD antes de SAP.

Responsabilidad:
  1. Recibir una `Solicitud` (con su Excel, tipo y acción).
  2. Pedir al router el validador de (tipo, acción).
  3. Validar la plantilla fila por fila y dejar el detalle en el log.
  4. Regla "todo o nada": si la estructura falla o UNA fila es inválida, se
     lanza PlantillaInvalidaError y el caso no sigue a SAP.
"""

from core.exceptions import PlantillaInvalidaError, ValidacionError
from validacion import router


def validar_solicitud(solicitud, logger=None):
    """
    Valida la plantilla de la `solicitud`. Devuelve el `ResultadoValidacion`
    si es válida.

    Raises:
        ValidacionError: si no hay validador para (tipo, acción) o el Excel
            no se puede abrir.
        PlantillaInvalidaError: si la plantilla no cumple las reglas (lleva
            el resultado completo en `.resultado`).
    """
    if not solicitud.tipo or not solicitud.accion:
        raise ValidacionError(
            f"Caso {solicitud.case_id}: no se identificó el tipo de activo o "
            f"la acción (tipo={solicitud.tipo!r}, accion={solicitud.accion!r})."
        )

    validador = router.resolver(solicitud.tipo, solicitud.accion, logger=logger)
    resultado = validador.validar(solicitud.excel_path)
    _registrar_detalle(solicitud.case_id, resultado, logger)

    if not resultado.valida:
        raise PlantillaInvalidaError(
            f"Caso {solicitud.case_id}: {resultado.resumen()}", resultado
        )
    return resultado


def _registrar_detalle(case_id, resultado, logger):
    """Deja en el log el veredicto y el detalle de cada fila con novedades."""
    if not logger:
        return
    for mensaje in resultado.errores_plantilla:
        logger.error("Caso %s | plantilla: %s", case_id, mensaje)
    for mensaje in resultado.advertencias_plantilla:
        logger.warning("Caso %s | plantilla: %s", case_id, mensaje)
    for fila in resultado.filas:
        for mensaje in fila.errores:
            logger.error("Caso %s | fila %s: %s", case_id, fila.fila, mensaje)
        for mensaje in fila.advertencias:
            logger.warning("Caso %s | fila %s: %s", case_id, fila.fila, mensaje)

    if resultado.valida:
        logger.info("Caso %s | Flujo 2: %s", case_id, resultado.resumen())
    else:
        logger.error("Caso %s | Flujo 2: %s", case_id, resultado.resumen())
