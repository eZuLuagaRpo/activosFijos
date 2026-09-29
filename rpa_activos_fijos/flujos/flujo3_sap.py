"""
flujos/flujo3_sap.py — FLUJO 3: carga a SAP (EN CONSTRUCCIÓN).

Qué se carga: el MISMO Excel que adjuntó el usuario (ya validado en el Flujo
2); no hay transformación a otro formato. Pero SAP exige que el archivo se
llame EXACTAMENTE de una forma según (tipo, acción) — ej. "CREAR (BRP).xlsm"
— ver NOMBRE_ARCHIVO_SAP en config.py.

Hecho:
  - preparar_archivo_sap(): copia temporal con el nombre exacto de SAP.
Pendiente (activo por activo, cuando negocio entregue las etiquetas):
  - Abrir SAP, transacción, cargar el archivo preparado, leer el resultado.
  - El clic en "Ejecutar" se programa DE ÚLTIMO y detrás de un interruptor
    apagado (no hay SAP de pruebas: ejecutar crea activos reales).
"""

import os
import shutil

from config import CARGA_SAP_DIR, NOMBRE_ARCHIVO_SAP
from core.exceptions import SapError


def preparar_archivo_sap(solicitud, logger=None):
    """
    Deja en CARGA_SAP_DIR una COPIA del Excel de la solicitud con el nombre
    exacto que exige SAP y devuelve su ruta.

    Por qué una copia: los Excel se descargan como CASE_ID_tipo_accion.xlsm
    para saber a qué solicitud pertenece cada uno. SAP procesa una solicitud
    a la vez, así que la copia se reemplaza en cada caso, y los resultados
    se anotan después en el archivo de la solicitud (no en la copia).

    Seguridad: ANTES de copiar se borra la copia anterior. Si algo falla,
    nunca queda en la carpeta el archivo de OTRA solicitud listo para cargar.

    Raises:
        SapError: si (tipo, acción) no tiene nombre configurado, o si no se
            pudo borrar/crear la copia (ej. el archivo está abierto en Excel
            o en SAP).
    """
    clave = (solicitud.tipo, solicitud.accion)
    nombre_sap = NOMBRE_ARCHIVO_SAP.get(clave)
    if not nombre_sap:
        raise SapError(
            f"Caso {solicitud.case_id}: no hay nombre de archivo SAP configurado "
            f"para (tipo={solicitud.tipo!r}, accion={solicitud.accion!r}). "
            "Revisa NOMBRE_ARCHIVO_SAP en config.py."
        )

    destino = os.path.join(CARGA_SAP_DIR, nombre_sap)
    try:
        if os.path.exists(destino):
            os.remove(destino)
    except OSError as e:
        raise SapError(
            f"Caso {solicitud.case_id}: no se pudo borrar la copia anterior "
            f"'{nombre_sap}' (¿está abierta en Excel o en SAP?): {e}"
        )

    try:
        shutil.copy2(solicitud.excel_path, destino)
    except OSError as e:
        raise SapError(
            f"Caso {solicitud.case_id}: no se pudo preparar '{nombre_sap}' "
            f"desde {solicitud.excel_path}: {e}"
        )

    solicitud.archivo_sap = destino
    if logger:
        logger.info(
            "Caso %s: archivo para SAP preparado -> %s (copia de %s)",
            solicitud.case_id,
            destino,
            os.path.basename(solicitud.excel_path),
        )
    return destino


def cargar_a_sap(solicitud, logger=None):
    """
    Prepara el archivo con el nombre exacto de SAP. La carga en SAP en sí
    sigue PENDIENTE (stub): solo se registra en el log.

    Args:
        solicitud (Solicitud): caso con su plantilla ya validada.
        logger: logger opcional.
    """
    ruta = preparar_archivo_sap(solicitud, logger=logger)

    mensaje = (
        f"PENDIENTE: carga a SAP no implementada. Archivo listo para cargar: "
        f"{ruta}"
    )
    if logger:
        logger.warning(mensaje)
    else:
        print(mensaje)
    return None
