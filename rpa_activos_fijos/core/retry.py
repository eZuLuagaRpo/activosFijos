"""
core/retry.py — Utilidad de reintentos con "backoff".

Muchas operaciones web fallan de forma intermitente por lentitud de red o porque
la página tardó en renderizar. En vez de rendirnos al primer intento, reintentamos
varias veces esperando cada vez un poco más (a esto se le llama "backoff
exponencial").

Se ofrece como decorador (`@reintentar()`) y también como función (`ejecutar_con_reintentos`).
"""

import functools
import time

from config import (
    RETRY_ESPERA_INICIAL,
    RETRY_FACTOR_BACKOFF,
    RETRY_INTENTOS,
)


def ejecutar_con_reintentos(
    funcion,
    intentos=RETRY_INTENTOS,
    espera_inicial=RETRY_ESPERA_INICIAL,
    factor=RETRY_FACTOR_BACKOFF,
    excepciones=(Exception,),
    logger=None,
    descripcion="operación",
):
    """
    Ejecuta `funcion` y la reintenta si lanza una de las `excepciones`.

    Args:
        funcion: función SIN argumentos a ejecutar (usa lambda para pasar args).
        intentos: número máximo de intentos.
        espera_inicial: segundos a esperar tras el primer fallo.
        factor: cuánto se multiplica la espera en cada reintento.
        excepciones: tupla de excepciones que disparan un reintento.
        logger: logger opcional para dejar constancia de los reintentos.
        descripcion: texto para los mensajes de log.

    Returns:
        Lo que devuelva `funcion` si tiene éxito.

    Raises:
        La última excepción si se agotan todos los intentos.
    """
    espera = espera_inicial
    ultimo_error = None

    for intento in range(1, intentos + 1):
        try:
            return funcion()
        except excepciones as e:
            ultimo_error = e
            if logger:
                logger.warning(
                    "Fallo en %s (intento %s/%s): %s",
                    descripcion,
                    intento,
                    intentos,
                    e,
                )
            if intento < intentos:
                time.sleep(espera)
                espera *= factor

    # Si llegamos aquí, se agotaron los intentos.
    if logger:
        logger.error("Se agotaron los reintentos de %s.", descripcion)
    raise ultimo_error


def reintentar(
    intentos=RETRY_INTENTOS,
    espera_inicial=RETRY_ESPERA_INICIAL,
    factor=RETRY_FACTOR_BACKOFF,
    excepciones=(Exception,),
    logger=None,
    descripcion=None,
):
    """
    Versión decorador de `ejecutar_con_reintentos`.

    Ejemplo:
        @reintentar(intentos=3)
        def abrir_bandeja():
            ...
    """

    def decorador(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            desc = descripcion or func.__name__
            return ejecutar_con_reintentos(
                lambda: func(*args, **kwargs),
                intentos=intentos,
                espera_inicial=espera_inicial,
                factor=factor,
                excepciones=excepciones,
                logger=logger,
                descripcion=desc,
            )

        return wrapper

    return decorador
