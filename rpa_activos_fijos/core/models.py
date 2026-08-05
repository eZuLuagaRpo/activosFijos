"""
core/models.py — Estructuras de datos del bot (dataclasses).

Una "dataclass" es simplemente una clase pensada para guardar datos de forma
ordenada y con nombres claros. Las usamos para mover información entre flujos
sin depender de diccionarios sueltos.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class CasoBandeja:
    """
    Una fila de la Bandeja de Actividades ya filtrada (solo Parametrización de
    Activos). Es lo que produce `BandejaReader.listar_pendientes()`.
    """

    case_id: str                              # ej. "PDA-7133"
    fecha_vencimiento: Optional[str] = None   # texto crudo, ej. "06/10/2026 12:00"


@dataclass
class Solicitud:
    """
    Representa UNA solicitud de activo fijo detectada en la bandeja y ya
    consultada en Appian. Es lo que produce el Flujo 1 y consume el Flujo 2.
    """

    case_id: str                      # ej. "PDA-2389"
    tipo: Optional[str] = None        # tipo de activo canónico (ver config.py)
    accion: Optional[str] = None      # acción canónica (creacion/modificacion/...)
    excel_path: Optional[str] = None  # ruta completa del Excel descargado de Appian
    info_df: Any = None               # DataFrame label|value con todo el detalle
    fecha_vencimiento: Optional[str] = None  # heredada de la bandeja (prioridad)

    # Textos crudos tal como venían en Appian (útil para diagnóstico/logs).
    tipo_crudo: Optional[str] = None
    accion_cruda: Optional[str] = None


@dataclass
class ArchivoMacro:
    """Un archivo Excel de salida ya en formato macro, listo para SAP (Flujo 3)."""

    ruta: str                         # ruta completa del Excel generado
    accion: str                       # creacion / modificacion / eliminacion
    codigo_macro: str                 # AS01 / AS02 / ELIM


@dataclass
class ResultadoCaso:
    """
    Resultado del procesamiento de UN caso a lo largo de los 3 flujos.
    El orquestador acumula una lista de estos para armar el resumen final.
    """

    case_id: str
    exito: bool = False
    motivo: str = ""                              # por qué falló (si falló)
    paso: str = ""                                # en qué paso quedó
    archivos_generados: List[ArchivoMacro] = field(default_factory=list)


@dataclass
class ResumenLote:
    """Resumen final de toda la ejecución."""

    total: int = 0
    exitosos: int = 0
    fallidos: int = 0
    resultados: List[ResultadoCaso] = field(default_factory=list)
