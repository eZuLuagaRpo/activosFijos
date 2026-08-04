"""
flujos/flujo2_procesar.py — FLUJO 2: Excel de Appian -> formato macro SAP.

Responsabilidad:
  1. Recibir una `Solicitud` (con su Excel, tipo y acción).
  2. Pedir al router el handler adecuado para (tipo, acción).
  3. Ejecutar la transformación, que produce uno o más archivos macro.
     (Recordar el caso especial: Diferido + Creación produce DOS archivos.)
  4. Devolver la lista de `ArchivoMacro` generados.

El mapeo real de columnas es un placeholder (ver transformacion/mapping/).
"""

from core.exceptions import TransformacionError
from transformacion import router


def procesar_solicitud(solicitud, logger=None):
    """
    Transforma la `solicitud` al formato macro. Devuelve una lista de
    `ArchivoMacro` (uno o dos, según el caso).

    Raises:
        TransformacionError: si no hay handler o la transformación falla.
    """
    if logger:
        logger.info(
            "Flujo 2: transformando caso %s (tipo=%s, accion=%s)...",
            solicitud.case_id,
            solicitud.tipo,
            solicitud.accion,
        )

    handler = router.resolver(solicitud.tipo, solicitud.accion, logger=logger)

    try:
        archivos = handler.transformar(solicitud)
    except Exception as e:
        # Envolvemos cualquier fallo de transformación en una excepción propia
        # y clara, para que el orquestador lo registre bien.
        raise TransformacionError(
            f"Error transformando el caso {solicitud.case_id}: {e}"
        ) from e

    if logger:
        for archivo in archivos:
            logger.info(
                "Flujo 2: generado %s (%s) -> %s",
                archivo.codigo_macro,
                archivo.accion,
                archivo.ruta,
            )
    return archivos
