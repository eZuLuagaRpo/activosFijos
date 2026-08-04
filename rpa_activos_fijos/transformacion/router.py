"""
transformacion/router.py — Enrutador (tipo de activo, acción) -> handler.

Dado un tipo de activo y una acción (ya canónicos), decide QUÉ handler debe
transformar el Excel. Es el único lugar donde se conecta el negocio con el
handler concreto, así que agregar un nuevo caso especial en el futuro es fácil:
solo se añade una regla aquí.
"""

from config import TIPO_DIFERIDOS
from core.exceptions import TransformacionError
from transformacion.handlers.diferidos_handler import DiferidosHandler
from transformacion.handlers.generico_handler import GenericoHandler


def resolver(tipo, accion, logger=None):
    """
    Devuelve la instancia de handler adecuada para (tipo, accion).

    Args:
        tipo (str): tipo de activo canónico (ver config.py).
        accion (str): acción canónica (creacion/modificacion/eliminacion).
        logger: logger opcional.

    Returns:
        Una instancia de handler lista para llamar .transformar(solicitud).

    Raises:
        TransformacionError: si falta el tipo o la acción (no se pudieron
            reconocer en el Flujo 1).
    """
    if not tipo or not accion:
        raise TransformacionError(
            "No se puede resolver el handler: falta el tipo de activo o la acción "
            f"(tipo={tipo!r}, accion={accion!r}). Revisa los labels/alias en config.py."
        )

    # Caso especial conocido: Diferidos tiene su propio handler (creación en 2 pasos).
    if tipo == TIPO_DIFERIDOS:
        return DiferidosHandler(accion=accion, logger=logger)

    # Resto de combinaciones: patrón base (una entrada -> una salida).
    return GenericoHandler(tipo=tipo, accion=accion, logger=logger)
