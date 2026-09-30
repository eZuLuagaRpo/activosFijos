"""
flujos/flujo3_sap.py — FLUJO 3: carga a SAP.

Qué se carga: una COPIA del Excel que adjuntó el usuario (ya validado en el
Flujo 2), con dos ajustes:
  - el nombre EXACTO que exige SAP según (tipo, acción), ej.
    "CREAR (BRP).xlsm" (NOMBRE_ARCHIVO_SAP en config.py), y
  - SIN las columnas extra que SAP no acepta, ej. la AC de BRP - Creación
    (COLUMNAS_QUITAR_ANTES_DE_SAP), ni nada a la derecha de la última
    columna de la plantilla (ULTIMA_COLUMNA_PLANTILLA). El Excel del usuario
    conserva todo.

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

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string

from config import (
    CARGA_SAP_DIR,
    COLUMNAS_QUITAR_ANTES_DE_SAP,
    ULTIMA_COLUMNA_PLANTILLA,
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
from validacion.base_validador import normalizar_encabezado


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

    # Ajustes SOLO de la copia (el Excel del usuario no se toca):
    #   1) quitar todo lo que esté a la derecha de la última columna de la
    #      plantilla (ej. notas del usuario en AD, AE...), y
    #   2) quitar las columnas que SAP no acepta (ej. AC en BRP - Creación).
    # Si falla, se borra la copia (nunca queda un archivo a medias listo
    # para cargar).
    a_quitar = COLUMNAS_QUITAR_ANTES_DE_SAP.get(clave, [])
    ultima = ULTIMA_COLUMNA_PLANTILLA.get(clave)
    sobrantes = 0
    if a_quitar or ultima:
        try:
            sobrantes = _ajustar_columnas(destino, a_quitar, ultima)
        except Exception as e:
            try:
                os.remove(destino)
            except OSError:
                pass
            raise SapError(
                f"Caso {solicitud.case_id}: no se pudieron quitar las columnas "
                f"{a_quitar} de '{nombre_sap}': {e}"
            )

    solicitud.archivo_sap = destino
    if logger:
        logger.info(
            "Caso %s: archivo para SAP preparado -> %s (copia de %s%s)",
            solicitud.case_id,
            destino,
            os.path.basename(solicitud.excel_path),
            f", SIN la(s) columna(s) {a_quitar}" if a_quitar else "",
        )
        if sobrantes:
            logger.warning(
                "Caso %s: el Excel traía %s columna(s) después de %s (fuera de "
                "la plantilla); se quitaron de la copia para SAP.",
                solicitud.case_id,
                sobrantes,
                ultima,
            )
    return destino


def _ajustar_columnas(ruta, encabezados, ultima_letra=None):
    """
    En la PRIMERA hoja de `ruta`:
      1) si hay `ultima_letra`, borra todas las columnas a su derecha, y
      2) borra las columnas cuyo encabezado (fila 1) coincide con alguno de
         `encabezados` (comparación normalizada, igual que en la validación).
    Conserva las macros (.xlsm). Devuelve cuántas columnas se quitaron en 1).

    Raises:
        ValueError: si alguno de los encabezados no está en el archivo.
    """
    libro = load_workbook(ruta, keep_vba=ruta.lower().endswith(".xlsm"))
    hoja = libro.worksheets[0]

    sobrantes = 0
    if ultima_letra:
        limite = column_index_from_string(ultima_letra)
        sobrantes = max(hoja.max_column - limite, 0)
        if sobrantes:
            hoja.delete_cols(limite + 1, sobrantes)

    fila1 = [normalizar_encabezado(c.value) for c in hoja[1]]
    indices = []
    for encabezado in encabezados:
        buscado = normalizar_encabezado(encabezado)
        if buscado not in fila1:
            raise ValueError(f"no se encontró la columna '{encabezado}' en la fila 1")
        indices.append(fila1.index(buscado) + 1)

    # De derecha a izquierda, para que borrar una no corra a las demás.
    for indice in sorted(indices, reverse=True):
        hoja.delete_cols(indice)
    libro.save(ruta)
    return sobrantes


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
