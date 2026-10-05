"""
flujos/modo_solo_sap.py — MODO PRUEBAS SOLO SAP (temporal).

Reemplaza al Flujo 1 (Appian) cuando MODO_PRUEBAS_SOLO_SAP = True: en vez de
leer la bandeja, toma los Excel de DOWNLOAD_TEST_DIR y arma una `Solicitud`
por cada uno. El activo y la acción salen del NOMBRE del archivo:

    <lo_que_quieras>_<tipo>_<accion>.xlsx   (o .xlsm)
    ej. prueba1_brp_creacion.xlsx -> id "prueba1", tipo "brp", acción "creacion"

Los tipos y acciones válidos son los canónicos de config.py (los mismos que
el bot reconoce en la sección "Detalles" de Appian).
"""

import os

from config import ALIAS_ACCION, DOWNLOAD_TEST_DIR, LABELS_ACTIVOS_DETALLE
from core.models import Solicitud

EXTENSIONES = (".xlsx", ".xlsm")
TIPOS = sorted(set(LABELS_ACTIVOS_DETALLE.values()), key=len, reverse=True)
ACCIONES = sorted(set(ALIAS_ACCION.values()), key=len, reverse=True)


def interpretar_nombre(nombre_archivo):
    """
    Devuelve (identificador, tipo, accion) a partir del nombre del archivo,
    o None si no sigue el formato <id>_<tipo>_<accion>.xlsx/.xlsm.
    """
    base, extension = os.path.splitext(nombre_archivo)
    if extension.lower() not in EXTENSIONES:
        return None
    base_min = base.lower()
    for accion in ACCIONES:
        for tipo in TIPOS:
            sufijo = f"_{tipo}_{accion}"
            if base_min.endswith(sufijo) and len(base) > len(sufijo):
                return base[: -len(sufijo)], tipo, accion
    return None


def listar_archivos(logger=None):
    """
    Revisa DOWNLOAD_TEST_DIR. Devuelve dos listas:
      - solicitudes: [Solicitud] de los archivos con nombre válido (en orden
        alfabético);
      - ignorados: [nombre] de los archivos con otro nombre (se reportan como
        omitidos).
    Se saltan sin reportar: .gitkeep, ocultos y temporales de Excel (~$...).
    """
    solicitudes, ignorados = [], []
    for nombre in sorted(os.listdir(DOWNLOAD_TEST_DIR)):
        if nombre.startswith((".", "~$")):
            continue
        partes = interpretar_nombre(nombre)
        if partes is None:
            ignorados.append(nombre)
            continue
        identificador, tipo, accion = partes
        solicitudes.append(
            Solicitud(
                case_id=identificador,
                tipo=tipo,
                accion=accion,
                excel_path=os.path.join(DOWNLOAD_TEST_DIR, nombre),
                tipo_crudo=tipo,
                accion_cruda=accion,
            )
        )
    if logger:
        logger.info(
            "MODO SOLO SAP: %s archivo(s) para probar: %s",
            len(solicitudes),
            ", ".join(os.path.basename(s.excel_path) for s in solicitudes) or "NINGUNO",
        )
        for nombre in ignorados:
            logger.warning(
                "MODO SOLO SAP: '%s' no sigue el formato <id>_<tipo>_<accion>.xlsx "
                "(ej. prueba1_brp_creacion.xlsx); se omite.", nombre
            )
    return solicitudes, ignorados
