"""
flujos/flujo1_appian.py — FLUJO 1: Appian (bandeja + detalle + descarga).

Responsabilidad de este flujo:
  1. Leer la Bandeja de Actividades y obtener las solicitudes pendientes de
     Parametrización de Activos, en orden de prioridad (BandejaReader).
  2. Por cada caso: abrirlo NAVEGANDO DIRECTO a la URL capturada en la
     bandeja (NO con client.search_case(), que busca en "Seguimiento de
     Solicitudes" — un módulo distinto donde estas tareas no aparecen), leer
     la sección "Detalles" para identificar QUÉ tipo de activo y QUÉ acción
     aplica, y descargar el Excel adjunto.
  3. Devolver una lista de objetos `Solicitud` lista para el Flujo 2.

Cómo se identifica el tipo de activo y la acción:
  La sección "Detalles" del caso trae un renglón FIJO por cada tipo de activo
  posible (Máscara, Activos BRP, Activos PRJ, Activos Diferidos y
  Renovaciones, Mejoras, Segunda Información). Debajo de cada nombre aparece
  la acción a realizar (Crear/Modificar/Eliminar) o un guion "-" si ese tipo
  no aplica. Se confirmó con la usuaria que SOLO UNO debe traer una acción
  real; si aparece más de uno, no se adivina: se marca el caso como fallido.

Reglas clave:
  - Se valida SIEMPRE el resultado de cada llamada (lo hace AppianClient).
  - Un caso que falla NO tumba el lote: se registra y se sigue con el siguiente.
  - Los reintentos con backoff protegen contra lentitud de red/render.
"""

import os
import time

from selenium.webdriver.common.by import By

from appian.bandeja_reader import BandejaReader
from config import (
    ALIAS_ACCION,
    DETALLE_VALOR_VACIO,
    DETALLE_XPATH_BOTON_ADJUNTO_RESPALDO,
    DETALLE_XPATH_SECCION_ACTIVOS,
    DOWNLOAD_DIR,
    LABELS_ACTIVOS_DETALLE,
    TIMEOUT_FILES,
)
from core.exceptions import AppianError, MultiplesActivosError, SinAdjuntosError
from core.models import Solicitud
from core.retry import ejecutar_con_reintentos
from core.texto import mapear_alias, normalizar


def _leer_lineas_seccion_activos(client, case_id):
    """
    Lee la sección "Detalles" del caso y devuelve su texto línea por línea
    (tal como se ve en pantalla, sin líneas vacías). Se asume que cada nombre
    de activo viene seguido, en la línea siguiente, de su acción (o "-").
    """
    try:
        seccion = client.driver.find_element(By.XPATH, DETALLE_XPATH_SECCION_ACTIVOS)
    except Exception as e:
        raise AppianError(
            f"Caso {case_id}: no se encontró la sección de Detalles "
            f"(revisa DETALLE_XPATH_SECCION_ACTIVOS en config.py): {e}"
        )

    lineas = [linea.strip() for linea in (seccion.text or "").split("\n")]
    return [linea for linea in lineas if linea]


def _extraer_tipo_y_accion_detalle(client, case_id, logger=None):
    """
    Recorre los renglones fijos de la sección "Detalles" y determina cuál
    tiene una acción real (distinto de "-").

    Returns:
        (tipo, accion, tipo_crudo, accion_cruda). Si ningún renglón tiene
        acción, devuelve (None, None, None, None) y deja un warning.

    Raises:
        MultiplesActivosError: si más de un renglón trae una acción a la vez.
    """
    lineas = _leer_lineas_seccion_activos(client, case_id)
    lineas_norm = [normalizar(linea) for linea in lineas]
    vacio_norm = normalizar(DETALLE_VALOR_VACIO)

    encontrados = []
    for label_texto, tipo_canonico in LABELS_ACTIVOS_DETALLE.items():
        label_norm = normalizar(label_texto)
        if label_norm not in lineas_norm:
            continue
        indice = lineas_norm.index(label_norm)
        if indice + 1 >= len(lineas):
            continue
        valor_crudo = lineas[indice + 1]
        if normalizar(valor_crudo) == vacio_norm:
            continue
        encontrados.append((tipo_canonico, label_texto, valor_crudo))

    if not encontrados:
        if logger:
            logger.warning(
                "Caso %s: ningún renglón de la sección Detalles trae una "
                "acción (todos están en '%s'). Revisa "
                "DETALLE_XPATH_SECCION_ACTIVOS y LABELS_ACTIVOS_DETALLE en "
                "config.py.",
                case_id,
                DETALLE_VALOR_VACIO,
            )
        return None, None, None, None

    if len(encontrados) > 1:
        detalle = ", ".join(f"{e[1]}={e[2]}" for e in encontrados)
        raise MultiplesActivosError(
            f"Caso {case_id}: más de un tipo de activo trae acción a la vez "
            f"({detalle}). Se esperaba solo uno; revisar el caso manualmente."
        )

    tipo, tipo_crudo, accion_cruda = encontrados[0]
    accion = mapear_alias(accion_cruda, ALIAS_ACCION)
    if accion is None and logger:
        logger.warning(
            "Caso %s: acción '%s' (en '%s') no está en ALIAS_ACCION (config.py).",
            case_id,
            accion_cruda,
            tipo_crudo,
        )

    return tipo, accion, tipo_crudo, accion_cruda


def _abrir_caso_directo(client, case_id, url, logger=None):
    """
    Navega directo a la URL de la solicitud (capturada en la bandeja) en vez
    de usar client.search_case(). Se descubrió que search_case() busca en el
    módulo "Seguimiento de Solicitudes" de Appian, que es un módulo DISTINTO
    a la Bandeja de Actividades y donde estas tareas no aparecen — por eso
    fallaba con "No se encontró información para el caso X" aunque el caso sí
    existía y era perfectamente accesible desde la bandeja.
    """
    if not url:
        raise AppianError(
            f"Caso {case_id}: no se capturó la URL de la fila en la bandeja "
            "(revisa BANDEJA_XPATH_ID_EN_FILA en config.py, la celda del ID "
            "debe ser un enlace <a> con href)."
        )
    try:
        client.driver.get(url)
    except Exception as e:
        raise AppianError(f"No se pudo navegar al caso {case_id}: {e}")

    if logger:
        logger.info("Caso %s: navegación directa OK.", case_id)


def _tomar_excel(files, case_id):
    """
    De la lista de adjuntos descargados por la librería, toma la ruta del
    primer Excel.

    Raises:
        SinAdjuntosError: si no hay adjuntos o ninguno es un Excel.
    """
    if not files:
        raise SinAdjuntosError(f"El caso {case_id} no trae adjuntos.")

    for adjunto in files:
        nombre = (adjunto.get("file") or "").lower()
        if nombre.endswith((".xlsx", ".xls", ".xlsm")):
            return adjunto.get("full_path")

    raise SinAdjuntosError(
        f"El caso {case_id} trae adjuntos pero ninguno parece un Excel."
    )


def _descargar_adjunto_manual(client, case_id, logger=None):
    """
    Respaldo: si la librería no descargó el Excel sola, se hace clic manual
    en el botón de adjuntos (DETALLE_XPATH_BOTON_ADJUNTO_RESPALDO) y se
    espera a que aparezca un archivo nuevo en DOWNLOAD_DIR.
    """
    if logger:
        logger.warning(
            "Caso %s: no se descargó ningún adjunto automáticamente. "
            "Probando clic manual en el botón de descarga.",
            case_id,
        )

    antes = set(os.listdir(DOWNLOAD_DIR))
    try:
        boton = client.driver.find_element(
            By.XPATH, DETALLE_XPATH_BOTON_ADJUNTO_RESPALDO
        )
        boton.click()
    except Exception as e:
        raise SinAdjuntosError(
            f"Caso {case_id}: no se encontró/pudo hacer clic en el botón de "
            f"descarga manual de adjuntos: {e}"
        )

    espera = 0
    while espera < TIMEOUT_FILES:
        ahora = set(os.listdir(DOWNLOAD_DIR))
        nuevos = [
            f for f in (ahora - antes) if not f.endswith((".crdownload", ".tmp"))
        ]
        if nuevos:
            ruta = os.path.join(DOWNLOAD_DIR, nuevos[0])
            if logger:
                logger.info(
                    "Caso %s: adjunto descargado manualmente -> %s", case_id, ruta
                )
            return ruta
        time.sleep(1)
        espera += 1

    raise SinAdjuntosError(
        f"Caso {case_id}: se hizo clic en el botón de descarga pero no "
        f"apareció ningún archivo nuevo en {DOWNLOAD_DIR} tras {TIMEOUT_FILES}s."
    )


def obtener_solicitud(client, caso, logger=None):
    """
    Procesa UN caso (un `CasoBandeja`, ya con su URL de la bandeja): navega
    directo -> detalle (tipo/acción) -> descarga adjunto -> construye la
    Solicitud.

    Las llamadas web van envueltas en reintentos con backoff. Si algo falla de
    forma definitiva, se propaga la excepción para que el llamador
    (orquestador) la registre y continúe con el siguiente caso.
    """
    case_id = caso.case_id
    fecha_vencimiento = caso.fecha_vencimiento

    # 1) Abrir el caso navegando directo a su URL (con reintentos).
    ejecutar_con_reintentos(
        lambda: _abrir_caso_directo(client, case_id, caso.url, logger=logger),
        excepciones=(AppianError,),
        logger=logger,
        descripcion=f"abrir caso {case_id}",
    )

    # 2) Leer datos generales del caso + descargar adjuntos (con reintentos).
    data = ejecutar_con_reintentos(
        lambda: client.get_case_data(case_id, download_attachments=True),
        excepciones=(AppianError,),
        logger=logger,
        descripcion=f"leer datos del caso {case_id}",
    )
    info_df = data.get("info")
    files = data.get("files") or []

    # 3) Identificar tipo de activo + acción desde la sección "Detalles"
    #    (con reintentos; MultiplesActivosError NO se reintenta, es un
    #    problema de datos, no de lentitud).
    tipo, accion, tipo_crudo, accion_cruda = ejecutar_con_reintentos(
        lambda: _extraer_tipo_y_accion_detalle(client, case_id, logger=logger),
        excepciones=(AppianError,),
        logger=logger,
        descripcion=f"leer tipo/acción del caso {case_id}",
    )

    # 4) Excel adjunto: primero lo que ya descargó la librería; si no hay
    #    nada usable, se intenta el clic manual de respaldo.
    try:
        excel_path = _tomar_excel(files, case_id)
    except SinAdjuntosError:
        excel_path = _descargar_adjunto_manual(client, case_id, logger=logger)

    solicitud = Solicitud(
        case_id=case_id,
        tipo=tipo,
        accion=accion,
        excel_path=excel_path,
        info_df=info_df,
        fecha_vencimiento=fecha_vencimiento,
        tipo_crudo=tipo_crudo,
        accion_cruda=accion_cruda,
    )

    if logger:
        logger.info(
            "Caso %s -> vencimiento=%s | activo=%s | accion=%s | excel=%s",
            case_id,
            fecha_vencimiento or "?",
            tipo_crudo or "?",
            accion_cruda or "?",
            excel_path,
        )
    return solicitud


def listar_casos_pendientes(client, logger=None):
    """
    Lee la bandeja y devuelve la lista de `CasoBandeja` (case_id +
    fecha_vencimiento) de Parametrización de Activos pendientes, en orden de
    prioridad. Se separa de `obtener_solicitud` para que el orquestador pueda
    iterar caso a caso y aislar los fallos individuales.
    """
    reader = BandejaReader(client, logger=logger)
    return reader.listar_pendientes()
