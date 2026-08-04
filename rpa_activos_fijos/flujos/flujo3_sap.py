"""
flujos/flujo3_sap.py — FLUJO 3: carga a SAP (STUB / PENDIENTE).

⚠️ ESTE FLUJO NO ESTÁ IMPLEMENTADO A PROPÓSITO. ⚠️
En esta entrega solo se deja el esqueleto. La automatización real de SAP se
construirá más adelante.

Cómo se implementará (guía para el futuro):
  - Abrir SAP (probablemente con la librería de scripting de SAP GUI o con una
    librería específica de RPA para SAP, NO con Selenium).
  - Ejecutar la transacción correspondiente (AS01 crear, AS02 modificar, etc.).
  - Cargar el archivo macro generado por el Flujo 2.
  - Validar el resultado y registrar el número de activo creado/modificado.
  - Reutilizar las MISMAS credenciales que Appian (se recogen una sola vez en la UI).
"""


def cargar_a_sap(archivo_macro, logger=None):
    """
    STUB: registra que la carga a SAP está pendiente y retorna sin hacer nada.

    Args:
        archivo_macro (ArchivoMacro): archivo generado por el Flujo 2.
        logger: logger opcional.

    Returns:
        None
    """
    mensaje = (
        f"PENDIENTE: carga a SAP no implementada. Archivo listo para el futuro "
        f"Flujo 3: {getattr(archivo_macro, 'ruta', archivo_macro)}"
    )
    if logger:
        logger.warning(mensaje)
    else:
        print(mensaje)

    # TODO: implementar aquí la automatización real de SAP (ver docstring del módulo).
    return None
