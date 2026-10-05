"""
core/models.py — Estructuras de datos del bot (dataclasses).

Una "dataclass" es simplemente una clase pensada para guardar datos de forma
ordenada y con nombres claros. Las usamos para mover información entre flujos
sin depender de diccionarios sueltos.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CasoBandeja:
    """
    Una fila de la Bandeja de Actividades ya filtrada (solo Parametrización de
    Activos). Es lo que produce `BandejaReader.listar_pendientes()`.
    """

    case_id: str                              # ej. "PDA-7133"
    fecha_vencimiento: Optional[str] = None   # texto crudo, ej. "06/10/2026 12:00"
    url: Optional[str] = None                 # href de la fila; se navega directo ahí
    # en vez de usar client.search_case(), que busca en "Seguimiento de
    # Solicitudes" (un módulo distinto de Appian donde estas tareas no aparecen).


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

    # Resultado de SAP por fila del Excel (Flujo 3): {numero_fila: texto}. El
    # texto es el código del activo creado o el mensaje de error; va a la
    # columna "Código SAP" que se le devuelve al usuario.
    resultados_sap: Dict[int, str] = field(default_factory=dict)


@dataclass
class ResultadoFila:
    """Resultado de validar UNA fila de datos de la plantilla (= un activo)."""

    fila: int                                            # número de fila en Excel (2, 3, ...)
    errores: List[str] = field(default_factory=list)     # invalidan la fila
    advertencias: List[str] = field(default_factory=list)  # solo informan

    @property
    def valida(self):
        return not self.errores


@dataclass
class ResultadoValidacion:
    """
    Resultado de validar la plantilla Excel de una solicitud (Flujo 2).

    Regla de negocio "todo o nada": la plantilla solo es válida si la
    estructura está bien Y TODAS sus filas son válidas. Si una sola fila
    falla, no se carga nada a SAP.
    """

    archivo: str                                                 # ruta del Excel validado
    plantilla: str                                               # ej. "BRP - Creación"
    errores_plantilla: List[str] = field(default_factory=list)   # V3: estructura
    advertencias_plantilla: List[str] = field(default_factory=list)
    filas: List[ResultadoFila] = field(default_factory=list)

    @property
    def valida(self):
        return not self.errores_plantilla and all(f.valida for f in self.filas)

    @property
    def filas_invalidas(self):
        return [f for f in self.filas if not f.valida]

    def resumen(self):
        """Una línea legible con el veredicto (para logs y el resumen final)."""
        if self.errores_plantilla:
            return "Plantilla inválida: " + "; ".join(self.errores_plantilla)
        invalidas = self.filas_invalidas
        if invalidas:
            return (
                f"{len(invalidas)} de {len(self.filas)} filas inválidas "
                f"(filas {', '.join(str(f.fila) for f in invalidas)})"
            )
        total = len(self.filas)
        return f"Plantilla válida ({total} {'fila' if total == 1 else 'filas'})"


@dataclass
class ResultadoCaso:
    """
    Resultado del procesamiento de UN caso a lo largo de los 3 flujos.
    El orquestador acumula una lista de estos para armar el resumen final.
    """

    case_id: str
    exito: bool = False
    omitido: bool = False                         # saltado a propósito (no es fallo)
    motivo: str = ""                              # por qué falló (si falló)
    paso: str = ""                                # en qué paso quedó
    validacion: Optional[ResultadoValidacion] = None


@dataclass
class ResumenLote:
    """Resumen final de toda la ejecución."""

    total: int = 0
    exitosos: int = 0
    fallidos: int = 0
    omitidos: int = 0
    resultados: List[ResultadoCaso] = field(default_factory=list)
