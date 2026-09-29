"""
flujos/flujo3_sap.py — FLUJO 3: carga a SAP.

Qué se carga: el MISMO Excel que adjuntó el usuario (ya validado en el Flujo
2); no hay transformación a otro formato. Pero SAP exige que el archivo se
llame EXACTAMENTE de una forma según (tipo, acción) — ej. "CREAR (BRP).xlsm"
— ver NOMBRE_ARCHIVO_SAP en config.py.

Etapas (se construye por partes, supervisado — no hay SAP de pruebas):
  ✅ Etapa 1: preparar el archivo -> abrir la transacción -> escoger la
     opción de la acción -> pegar la ruta -> cambiar "Ejecución de test" ->
     DETENERSE (SAP_EJECUTAR_REAL = False) y dejar la pantalla quieta
     SAP_PAUSA_REVISION_SEG segundos para revisarla.
  🔲 Etapa 2: clic en "Ejecutar" (se programa DE ÚLTIMO, cuando el usuario
     lo pida) y lectura del cuadro de resultados.

Hoy solo está configurado BRP – Creación (Z_AM_MASIVA). Lo que no esté en
SAP_TRANSACCION_POR_CASO no se envía a SAP.
"""

import os
import shutil
import time

from config import (
    CARGA_SAP_DIR,
    NOMBRE_ARCHIVO_SAP,
    SAP_EJECUTAR_REAL,
    SAP_MASIVA_XPATH_CAMPO_RUTA,
    SAP_MASIVA_XPATH_EJECUCION_TEST,
    SAP_MASIVA_XPATH_OPCION_ACCION,
    SAP_PAUSA_REVISION_SEG,
    SAP_TRANSACCION_POR_CASO,
    SAP_TX_MASIVA,
    SAP_XPATH_BOTON_EJECUTAR,
)
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


def cargar_a_sap(sap, solicitud, logger=None):
    """
    Lleva la plantilla validada a SAP hasta JUSTO ANTES de "Ejecutar".

    Args:
        sap (SapWebGui): sesión de SAP (se abre aquí la primera vez).
        solicitud (Solicitud): caso con su plantilla ya validada.
        logger: logger opcional.

    Returns:
        str: texto del paso en el que quedó (para el resumen del caso).

    Raises:
        SapError: si la combinación no está configurada o algo falla en SAP.
    """
    case_id = solicitud.case_id
    transaccion = SAP_TRANSACCION_POR_CASO.get((solicitud.tipo, solicitud.accion))
    if transaccion != SAP_TX_MASIVA:
        raise SapError(
            f"Caso {case_id}: (tipo={solicitud.tipo!r}, accion={solicitud.accion!r}) "
            "no tiene transacción de SAP configurada. Revisa "
            "SAP_TRANSACCION_POR_CASO en config.py."
        )

    ruta = preparar_archivo_sap(solicitud, logger=logger)

    sap.asegurar_sesion()
    sap.ir_a_transaccion(transaccion)
    sap.clic(
        SAP_MASIVA_XPATH_OPCION_ACCION[solicitud.accion],
        f"la opción '{solicitud.accion}' masivo de {transaccion}",
    )
    sap.escribir(SAP_MASIVA_XPATH_CAMPO_RUTA, ruta, "ruta del archivo")
    sap.clic(SAP_MASIVA_XPATH_EJECUCION_TEST, "la opción 'Ejecución de test'")

    if not SAP_EJECUTAR_REAL:
        if logger:
            logger.warning(
                "Caso %s: SAP listo para EJECUTAR, pero SAP_EJECUTAR_REAL = False: "
                "el bot se DETIENE aquí (no hace clic en Ejecutar). Pantalla "
                "disponible para revisión por %s s.",
                case_id,
                SAP_PAUSA_REVISION_SEG,
            )
        time.sleep(SAP_PAUSA_REVISION_SEG)
        return "Detenido antes de Ejecutar en SAP (SAP_EJECUTAR_REAL = False)"

    # Etapa 2 (pendiente): solo se llega aquí si alguien activó el interruptor.
    if not SAP_XPATH_BOTON_EJECUTAR:
        raise SapError(
            "SAP_EJECUTAR_REAL = True pero el botón 'Ejecutar' todavía no está "
            "configurado (SAP_XPATH_BOTON_EJECUTAR). No se ejecutó nada."
        )
    raise SapError(
        "La ejecución en SAP y la lectura de resultados aún no están "
        "implementadas. No se ejecutó nada."
    )
