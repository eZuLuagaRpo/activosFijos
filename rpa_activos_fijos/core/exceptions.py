"""
core/exceptions.py — Excepciones propias del bot.

¿Por qué excepciones propias? La librería de Appian NO lanza excepciones cuando
algo falla: devuelve un diccionario {success, message, data}. Nuestro wrapper
(appian/appian_client.py) revisa ese `success` y, cuando es False, lanza una de
ESTAS excepciones. Así el resto del código puede usar try/except normal y los
mensajes de error quedan claros y clasificados.
"""


class RPAError(Exception):
    """Excepción base de todo el bot. Las demás heredan de esta."""


class AppianError(RPAError):
    """Fallo genérico al hablar con Appian (login, navegación, etc.)."""


class CasoNoEncontradoError(AppianError):
    """El caso buscado no existe o no se pudo abrir."""


class SinAdjuntosError(AppianError):
    """El caso no tiene el Excel adjunto que necesitamos."""


class ActividadTomadaError(AppianError):
    """La actividad ya fue tomada por otro usuario."""


class TimeoutAppianError(AppianError):
    """Una operación de Appian superó el tiempo de espera."""


class BandejaError(AppianError):
    """No se pudo leer la Bandeja de Actividades (selectores, tabla vacía...)."""


class TransformacionError(RPAError):
    """Fallo al transformar el Excel de Appian al formato de la macro SAP."""


class ConfiguracionError(RPAError):
    """Falta un dato de configuración o una plantilla obligatoria."""
