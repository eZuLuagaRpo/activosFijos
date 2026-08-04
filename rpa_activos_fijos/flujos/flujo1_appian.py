"""
flujos/flujo1_appian.py — FLUJO 1: Appian (bandeja + descarga).

Responsabilidad de este flujo:
  1. Leer la Bandeja de Actividades y obtener la lista de casos pendientes.
  2. Por cada caso: abrirlo, leer su detalle (tipo de activo + acción) y
     descargar el Excel adjunto.
  3. Devolver una lista de objetos `Solicitud` lista para el Flujo 2.

Reglas clave:
  - Se valida SIEMPRE el resultado de cada llamada (lo hace AppianClient).
  - Un caso que falla NO tumba el lote: se registra y se sigue con el siguiente.
  - Los reintentos con backoff protegen contra lentitud de red/render.
"""

from appian.bandeja_reader import BandejaReader
from config import (
    ALIAS_ACCION,
    ALIAS_TIPO_ACTIVO,
    LABELS_ACCION,
    LABELS_TIPO_ACTIVO,
)
from core.exceptions import AppianError, SinAdjuntosError
from core.models import Solicitud
from core.retry import ejecutar_con_reintentos
from core.texto import mapear_alias, normalizar


def _buscar_valor_por_labels(info_df, labels_posibles):
    """
    Busca en el DataFrame (columnas label|value) la primera fila cuyo `label`
    coincida (normalizado) con alguno de los `labels_posibles`. Devuelve el
    `value` crudo, o None si no encuentra ninguno.
    """
    if info_df is None or info_df.empty:
        return None

    labels_norm = [normalizar(l) for l in labels_posibles]
    for _, fila in info_df.iterrows():
        if normalizar(fila.get("label")) in labels_norm:
            return fila.get("value")
    return None


def _extraer_tipo_y_accion(info_df, logger, case_id):
    """
    Del DataFrame de detalle saca el tipo de activo y la acción (crudos y
    canónicos). Si algún label no aparece, se registra un aviso y se deja None
    para que el Flujo 2 decida (el router avisará que no hay handler).
    """
    tipo_crudo = _buscar_valor_por_labels(info_df, LABELS_TIPO_ACTIVO)
    accion_cruda = _buscar_valor_por_labels(info_df, LABELS_ACCION)

    if tipo_crudo is None and logger:
        logger.warning(
            "Caso %s: no se encontró el label de 'tipo de activo'. "
            "Revisa LABELS_TIPO_ACTIVO en config.py.",
            case_id,
        )
    if accion_cruda is None and logger:
        logger.warning(
            "Caso %s: no se encontró el label de 'acción'. "
            "Revisa LABELS_ACCION en config.py.",
            case_id,
        )

    tipo = mapear_alias(tipo_crudo, ALIAS_TIPO_ACTIVO) if tipo_crudo else None
    accion = mapear_alias(accion_cruda, ALIAS_ACCION) if accion_cruda else None

    if tipo_crudo and tipo is None and logger:
        logger.warning(
            "Caso %s: tipo de activo '%s' no está en ALIAS_TIPO_ACTIVO (config.py).",
            case_id,
            tipo_crudo,
        )
    if accion_cruda and accion is None and logger:
        logger.warning(
            "Caso %s: acción '%s' no está en ALIAS_ACCION (config.py).",
            case_id,
            accion_cruda,
        )

    return tipo, accion, tipo_crudo, accion_cruda


def _tomar_excel(files, case_id):
    """
    De la lista de adjuntos descargados toma la ruta del primer Excel.
    Cada adjunto es {"file", "path", "full_path"}.

    Raises:
        SinAdjuntosError: si no hay adjuntos o ninguno es un Excel.
    """
    if not files:
        raise SinAdjuntosError(f"El caso {case_id} no trae adjuntos.")

    for adjunto in files:
        nombre = (adjunto.get("file") or "").lower()
        if nombre.endswith((".xlsx", ".xls", ".xlsm")):
            return adjunto.get("full_path")

    # Si no reconocimos extensión, usamos el primero pero avisamos.
    return files[0].get("full_path")


def obtener_solicitud(client, case_id, logger=None):
    """
    Procesa UN caso: search_case -> get_case_data -> construye la Solicitud.

    Las llamadas web van envueltas en reintentos con backoff. Si algo falla de
    forma definitiva, se propaga la excepción para que el llamador (orquestador)
    la registre y continúe con el siguiente caso.
    """
    # 1) Abrir el caso (con reintentos).
    ejecutar_con_reintentos(
        lambda: client.search_case(case_id),
        excepciones=(AppianError,),
        logger=logger,
        descripcion=f"abrir caso {case_id}",
    )

    # 2) Leer detalle + descargar adjuntos (con reintentos).
    data = ejecutar_con_reintentos(
        lambda: client.get_case_data(case_id, download_attachments=True),
        excepciones=(AppianError,),
        logger=logger,
        descripcion=f"leer datos del caso {case_id}",
    )

    info_df = data.get("info")
    files = data.get("files") or []

    tipo, accion, tipo_crudo, accion_cruda = _extraer_tipo_y_accion(
        info_df, logger, case_id
    )
    excel_path = _tomar_excel(files, case_id)

    solicitud = Solicitud(
        case_id=case_id,
        tipo=tipo,
        accion=accion,
        excel_path=excel_path,
        info_df=info_df,
        tipo_crudo=tipo_crudo,
        accion_cruda=accion_cruda,
    )

    if logger:
        logger.info(
            "Caso %s listo -> tipo='%s' accion='%s' excel='%s'",
            case_id,
            tipo or tipo_crudo,
            accion or accion_cruda,
            excel_path,
        )
    return solicitud


def listar_casos_pendientes(client, logger=None):
    """
    Lee la bandeja y devuelve la lista de case_id pendientes.
    Se separa de `obtener_solicitud` para que el orquestador pueda iterar caso a
    caso y aislar los fallos individuales.
    """
    reader = BandejaReader(client, logger=logger)
    return reader.listar_pendientes()
