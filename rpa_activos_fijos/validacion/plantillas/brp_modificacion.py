"""
validacion/plantillas/brp_modificacion.py — Plantilla "Modificación BRP".

Cada fila de datos (desde la fila 2) es UN activo a modificar en SAP con AS02.
Plantilla oficial: plantillas/BRP/Plantilla Modificacion BRP.xlsm (primera
hoja, encabezados en la fila 1, columnas A..BO; 2026-10-09).

Reglas (entregadas por el usuario, 2026-10-09):
  - Obligatorios: A (código SAP del activo) y C (sociedad). Son los datos de
    la pantalla inicial de AS02 (junto con B).
  - B (subnúmero): OPCIONAL, aunque el encabezado diga "Obligatorio".
  - El resto: informativo. En AS02 el formulario ya trae los valores actuales
    del activo: celda vacía = ese campo no se toca; celda con valor = se
    reemplaza.
  - Columnas sin campo en AS02 (ver SAP_FORMULARIO_AS02_BRP en config.py) no
    se validan ni se usan.
  - TODO O NADA y formatos .xlsx / .xlsm, igual que todas las plantillas.

Como en creación, manda la clasificación de este archivo y no el texto
"Obligatorio" de los encabezados del Excel.
"""

from validacion.base_validador import (
    INFORMATIVO,
    NO_SE_VALIDA,
    OBLIGATORIO,
    BaseValidador,
    Columna,
)


class ValidadorBrpModificacion(BaseValidador):
    nombre = "BRP - Modificación"

    columnas = (
        # Pantalla inicial de AS02
        Columna("A", "Código SAP del activo\nObligatorio", "Código SAP del activo", OBLIGATORIO),
        Columna("B", "Subnúmero\nObligatorio\n", "Subnúmero", INFORMATIVO),
        Columna("C", "Sociedad\nObligatorio", "Sociedad", OBLIGATORIO),
        # Formulario del activo
        Columna("D", "Denominación", "Denominación", INFORMATIVO),
        Columna("E", "Marca", "Marca", NO_SE_VALIDA),
        Columna("F", "Número de serie", "Número de serie", INFORMATIVO),
        Columna("G", "Número de inventario ", "Número de inventario", INFORMATIVO),
        Columna("H", "Cantidad ", "Cantidad", INFORMATIVO),
        Columna("I", "Cantidad 2", "Cantidad 2", NO_SE_VALIDA),
        Columna("J", "Último inventario el", "Último inventario el", INFORMATIVO),
        Columna("K", "Nota de inventario", "Nota de inventario", INFORMATIVO),
        Columna("L", "Descapitalizado", "Descapitalización el", INFORMATIVO),
        Columna("M", "Pedido el", "Pedido el", INFORMATIVO),
        Columna("N", "Centro de coste\n", "Centro de coste", INFORMATIVO),
        Columna("O", "CeCo responsable", "CeCo responsable", INFORMATIVO),
        Columna("P", "Ord.costes", "Orden costes", INFORMATIVO),
        Columna("Q", "Centro Obligatorio", "Centro", INFORMATIVO),
        Columna("R", "Emplazamiento", "Emplazamiento", INFORMATIVO),
        Columna("S", "Local", "Local", INFORMATIVO),
        Columna("T", "Matrícula vehículo", "Matrícula vehículo", INFORMATIVO),
        Columna("U", "Número de personal", "Número de personal", INFORMATIVO),
        Columna("V", "Elem.PEP (costes)", "Elem. PEP (costes)", INFORMATIVO),
        Columna("W", "Activo fijo paraliz.", "Activo fijo paralizado", INFORMATIVO),
        Columna("X", "Estado", "Estado", INFORMATIVO),
        Columna("Y", "Tipo", "Tipo", INFORMATIVO),
        Columna("Z", "Procedencia", "Procedencia", INFORMATIVO),
        Columna("AA", "Ubicación/ \n4 caracteres", "Ubicación", INFORMATIVO),
        Columna("AB", "Total Depreciados", "Total depreciados", INFORMATIVO),
        Columna("AC", "Fabricante/Serie\n30 caracteres", "Fabricante", INFORMATIVO),
        Columna("AD", "AF. Comprado nuevo", "AF comprado nuevo", INFORMATIVO),
        Columna("AE", "Comprado segunda mano", "Comprado 2a mano", INFORMATIVO),
        Columna("AF", "Sociedad GL asociada", "Sociedad GL asociada", INFORMATIVO),
        Columna("AG", "País origen", "País origen", INFORMATIVO),
        Columna("AH", "Denominación de tipo/Modelo\n15 caracteres", "Denominación de tipo", INFORMATIVO),
        Columna("AI", "Activo fijo orig.", "Activo fijo orig.", INFORMATIVO),
        Columna("AJ", "Subnumero activo fijo origen ", "Subnúmero activo fijo origen", NO_SE_VALIDA),
        Columna("AK", "Alta el", "Alta el", INFORMATIVO),
        Columna("AL", "Año adquis.orig.", "Año adquis. orig.", INFORMATIVO),
        Columna("AM", "Valor original", "Valor original", INFORMATIVO),
        Columna("AN", "Parte prod.propia", "Parte prod. propia", INFORMATIVO),
        Columna("AO", "Clave agrupamiento", "Clave de agrupamiento", INFORMATIVO),
        Columna("AP", "Indicador propiedad", "Indicador propiedad", INFORMATIVO),
        Columna("AQ", "Val.patrim.man.", "Val. patrim. man.", INFORMATIVO),
        Columna("AR", "Delegación Hacienda", "Delegación Hacienda", INFORMATIVO),
        Columna("AS", "N.I.F. valor unit.", "N.I.F. valor unit.", INFORMATIVO),
        Columna("AT", "Cartilla del", "Cartilla del", INFORMATIVO),
        Columna("AU", "Municipio", "Municipio", INFORMATIVO),
        Columna("AV", "Reg.propiedad del", "Reg. propiedad del", INFORMATIVO),
        Columna("AW", "INSCRIPCIÓN DEL", "Inscripción del", INFORMATIVO),
        Columna("AX", "Tomo", "Tomo", INFORMATIVO),
        Columna("AY", "Hoja", "Hoja", INFORMATIVO),
        Columna("AZ", "Nº actual", "Nº actual", INFORMATIVO),
        Columna("BA", "Ces.propiedad", "Ces. propiedad", INFORMATIVO),
        Columna("BB", "Cartilla parcelaria", "Cartilla parcelaria", INFORMATIVO),
        Columna("BC", "Cartilla Parcelaria Campo 2", "Cartilla parcelaria campo 2", INFORMATIVO),
        Columna("BD", "Superficie", "Superficie", INFORMATIVO),
        Columna("BE", "Superficie campo 2", "Superficie campo 2", INFORMATIVO),
        Columna("BF", "Clase", "Clase", INFORMATIVO),
        Columna("BG", "Nº de póliza", "Nº de póliza", INFORMATIVO),
        Columna("BH", "Comentario", "Comentario", INFORMATIVO),
        Columna("BI", "Inicio", "Inicio", INFORMATIVO),
        Columna("BJ", "Parte contratante", "Parte contratante", NO_SE_VALIDA),
        Columna("BK", "Número de contrato", "Número de contrato", NO_SE_VALIDA),
        Columna("BL", "Fecha del contrato", "Fecha del contrato", NO_SE_VALIDA),
        Columna("BM", "AREA DE VALORACIÓN", "Área de valoración", NO_SE_VALIDA),
        Columna("BN", "DURACIÓN", "Duración", NO_SE_VALIDA),
        Columna("BO", "PERIODO", "Periodo", NO_SE_VALIDA),
    )
