"""
core/logger.py — Sistema de logs del bot.

Los logs van a DOS destinos a la vez:
  1. Un ARCHIVO en disco (carpeta logs/), uno por ejecución, con fecha y hora.
     Ahí van TODOS los detalles, incluidas las trazas técnicas.
  2. La CONSOLA de la interfaz gráfica, en vivo, para que la usuaria vea el
     avance. Esto se hace a través de una cola thread-safe (queue.Queue): el bot
     corre en un hilo aparte y "deposita" mensajes en la cola; la UI los recoge.

IMPORTANTE (seguridad): NUNCA se escriben contraseñas. La función `enmascarar`
ayuda a ocultar datos sensibles antes de registrarlos.
"""

import logging
import os
import queue
import re
from datetime import datetime

from config import LOG_DIR


class ColaLogHandler(logging.Handler):
    """
    Handler de logging que, en lugar de imprimir en pantalla, mete cada mensaje
    ya formateado en una cola (queue.Queue). La UI consume esa cola con `after()`
    y así la consola nunca congela la ventana.
    """

    def __init__(self, cola):
        super().__init__()
        self.cola = cola

    def emit(self, record):
        try:
            mensaje = self.format(record)
            self.cola.put((record.levelname, mensaje))
        except Exception:
            # Nunca dejamos que un fallo de logging tumbe el bot.
            self.handleError(record)


def enmascarar(texto):
    """
    Oculta datos sensibles dentro de un texto antes de registrarlo.
    Por ahora enmascara lo que parezca una contraseña en formato clave=valor.
    Amplía esta función si aparecen otros datos sensibles.
    """
    if texto is None:
        return texto
    texto = str(texto)
    # password=..., pass: ..., contraseña ...
    texto = re.sub(
        r"(?i)(password|pass|contrase[nñ]a|pwd)\s*[:=]\s*\S+",
        r"\1=****",
        texto,
    )
    return texto


class _FiltroEnmascarar(logging.Filter):
    """Aplica `enmascarar` a cada mensaje antes de que llegue a los handlers."""

    def filter(self, record):
        record.msg = enmascarar(record.getMessage())
        record.args = ()
        return True


def crear_logger(cola=None, nombre="rpa_activos_fijos"):
    """
    Crea (o reutiliza) el logger principal del bot.

    Args:
        cola (queue.Queue, opcional): cola thread-safe hacia la consola de la UI.
            Si es None, solo se registra en archivo (útil para pruebas).
        nombre (str): nombre del logger.

    Returns:
        logging.Logger listo para usar: logger.info(...), logger.warning(...),
        logger.error(...).
    """
    logger = logging.getLogger(nombre)
    logger.setLevel(logging.INFO)

    # Evitamos duplicar handlers si se llama más de una vez.
    logger.handlers.clear()
    logger.addFilter(_FiltroEnmascarar())

    formato = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # --- Destino 1: archivo con timestamp ---
    os.makedirs(LOG_DIR, exist_ok=True)
    nombre_archivo = datetime.now().strftime("ejecucion_%Y%m%d_%H%M%S.log")
    ruta_log = os.path.join(LOG_DIR, nombre_archivo)
    file_handler = logging.FileHandler(ruta_log, encoding="utf-8")
    file_handler.setFormatter(formato)
    logger.addHandler(file_handler)

    # --- Destino 2: consola de la UI (si nos dieron una cola) ---
    if cola is not None:
        cola_handler = ColaLogHandler(cola)
        cola_handler.setFormatter(formato)
        logger.addHandler(cola_handler)

    logger.info("Log de esta ejecución: %s", ruta_log)
    return logger
