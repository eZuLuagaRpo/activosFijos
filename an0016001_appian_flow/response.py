"""
Módulo de construcción de respuestas estándar del sistema.

Define una estructura uniforme para todas las respuestas
generadas en los flujos de automatización.
"""


def build_response(success: bool, message: str, data=None):
    """
    Crea una respuesta estándar para el sistema.

    Args:
        success (bool): Indica si la operación fue exitosa.
        message (str): Mensaje descriptivo del resultado.
        data (any, opcional): Información adicional.

    Returns:
        dict: Estructura con:
            - success
            - message
            - data
    """
    return {"success": success, "message": message, "data": data}
