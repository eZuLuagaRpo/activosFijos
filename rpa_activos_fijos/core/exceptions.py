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


class MultiplesActivosError(RPAError):
    """Más de un renglón de la sección 'Detalles' trae una acción a la vez
    (se esperaba que solo uno aplicara). No es un error de comunicación con
    Appian, así que NO se reintenta."""


class MultiplesAdjuntosError(RPAError):
    """El caso trae más de un Excel adjunto y no se sabe cuál usar (pendiente
    de confirmar con la dueña de la automatización si es error del usuario o
    un caso legítimo). Por ahora no se adivina: se deja para revisión manual.
    A propósito NO hereda de SinAdjuntosError: el problema no es "no hay
    adjuntos" (eso dispara el respaldo de descarga manual), es que hay
    ambigüedad sobre cuál de los que sí llegaron usar."""
