"""
validacion/plantillas/brp_creacion.py — Plantilla "Creación Activos BRP".

Cada fila de datos (desde la fila 2) es UN activo a crear. Desde el
2026-10-04 se crean uno por uno en SAP con AS01 (ya no hay carga masiva):
el bot lee cada fila y llena el formulario de AS01 con sus valores.
Plantilla que envía el USUARIO: plantillas/BRP/Plantilla Creación Activos
BRP usuario.xlsm (hoja "FORMATO", encabezados en la fila 1, columnas A..AC).
  - AC "TXT.NUM.PRAL.AF (Nombre y NIT del acreedor)" (2026-09-29): se
    escribe en el campo del mismo nombre de AS01. Informativa, máx. 50
    caracteres (si se excede = ERROR). Es obligatorio que la columna EXISTA:
    una plantilla sin AC se rechaza por encabezado faltante (V3).
  - La columna S "ACREEDOR" es OTRO campo.
La macro `Crear_BRP` que trae el archivo es una utilidad del usuario: se ignora.

Reglas (entregadas por negocio, 2026-09-27):
  V1 · Obligatorios A, B, C, D, F, H, O, W (vacío = sin contenido, solo
       espacios o 0).
  V2 · C (cantidad de activos) debe ser exactamente 1: cada fila es UN
       activo para que SAP le asigne un código único.
  V3 · Estructura (encabezados + al menos una fila) -> en BaseValidador.
  V4 · Vehículos: si M (matrícula) viene diligenciada, U (modelo) es
       obligatoria.
  V5 · T máx. 30 y U máx. 15 caracteres -> solo advertencia.
  Final: TODO O NADA. Si una fila es inválida, no se procesa la plantilla.
  Formato: .xlsx o .xlsm (2026-10-04; antes solo .xlsm por la masiva).

FUENTE DE VERDAD de qué es obligatorio / condicional / informativo: el Word
de proceso (plantillas/BRP/Activos BRP Creación.docx), comparado por NOMBRE
DE CAMPO (sus letras de columna tienen errores; manda la letra real de la
plantilla). El texto "OBLIGATORIO" de los encabezados del Excel NO cuenta:
E, I, P, Q, R lo dicen y no son obligatorios. Campos que el Word no menciona
no se validan. (Confirmado por el usuario, 2026-09-28.)
"""

from validacion.base_validador import (
    CONDICIONAL,
    INFORMATIVO,
    NO_SE_VALIDA,
    OBLIGATORIO,
    BaseValidador,
    Columna,
    es_vacia,
)


class ValidadorBrpCreacion(BaseValidador):
    nombre = "BRP - Creación"
    # Formatos aceptados: .xlsx y .xlsm (los de BaseValidador). Desde el
    # 2026-10-04 SAP ya no recibe el archivo, así que no se exige .xlsm.

    columnas = (
        Columna("A", "CLASE ACTIVOS FIJOS. OBLIGATORIA", "Clase de Activo Fijo", OBLIGATORIO),
        Columna("B", "SOCIEDAD. OBLIGATORIA", "Sociedad", OBLIGATORIO),
        Columna("C", "CTD.DE ACTIVOS FIJOS IGUALES. OBLIGATORIA", "Cantidad de Activos", OBLIGATORIO),
        Columna("D", "DENOMINACION.OBLIGATORIA", "Denominación", OBLIGATORIO),
        Columna("E", "MARCA OBLIGATORIA", "Marca", INFORMATIVO),
        Columna("F", "No INVENTARIO OBLIGATORIO", "Número de Inventario", OBLIGATORIO),
        Columna("G", "CAPITALIZADO EL", "Fecha de capitalización", NO_SE_VALIDA),
        Columna("H", "CENTRO DE COSTE. OBLIGATORIO", "Centro de Coste", OBLIGATORIO),
        Columna("I", "CECO RESPOSANBLE. OBLIGATORIO", "CeCo Responsable", NO_SE_VALIDA),
        Columna("J", "ORDEN COSTES", "Orden de costes", NO_SE_VALIDA),
        Columna("K", "CENTRO", "Centro", NO_SE_VALIDA),
        Columna("L", "EMPLAZAMIENTO", "Emplazamiento", NO_SE_VALIDA),
        Columna("M", "MATRICULA VEHICULO", "Matrícula Vehículo", CONDICIONAL),
        Columna("N", "ACTIVO FIJO PARALIZ", "Activo fijo paralizado", NO_SE_VALIDA),
        Columna("O", "ESTADO. OBLIGATORIO", "Estado", OBLIGATORIO),
        Columna("P", "TIPO OBLIGATORIO", "Tipo de Activo", INFORMATIVO),
        Columna("Q", "PROCEDENCIA OBLIGATORIA", "Procedencia", INFORMATIVO),
        Columna("R", "UBICACIÓN OBLIGATORIA", "Ubicación", INFORMATIVO),
        Columna("S", "ACREEDOR", "Acreedor", INFORMATIVO),
        Columna("T", "FABRICANTE (SERIE) 30 caracteres", "Fabricante", INFORMATIVO, max_largo=30),
        Columna("U", "DENOMINACION DE TIPO. MODELO (15 caracteres)", "Modelo", CONDICIONAL, max_largo=15),
        Columna("V", "PARTE PROD.PROPIA", "% Participación", INFORMATIVO),
        Columna("W", "CLAVE AGRUPAMIENTO OBLIGATORIO", "Clave de Agrupamiento", OBLIGATORIO),
        Columna("X", "INDICADOR PROPIEDAD", "Indicador de propiedad", NO_SE_VALIDA),
        Columna("Y", "NUMERO DE CONTRATO", "Número de contrato", NO_SE_VALIDA),
        Columna("Z", "AREA DE VALORACIÓN", "Área de Valoración", INFORMATIVO),
        Columna("AA", "DURACIÓN", "Duración", INFORMATIVO),
        Columna("AB", "PERIODO", "Periodo", NO_SE_VALIDA),
        # Columna EXTRA: va al campo "TXT.NUM.PRAL.AF" de AS01.
        # Informativa, pero > 50 caracteres = ERROR.
        Columna("AC", "TXT.NUM.PRAL.AF (Nombre y NIT del acreedor)",
                "Nombre y NIT del acreedor", INFORMATIVO,
                max_largo=50, largo_es_error=True),
    )

    def reglas_fila(self, fila, resultado_fila):
        # V2 · Cantidad = 1 (si está vacía ya la reportó V1).
        cantidad = fila.get("C")
        if not es_vacia(cantidad) and not _es_uno(cantidad):
            resultado_fila.errores.append(
                f"{self.etiqueta('C')} debe ser 1 y trae '{cantidad}'."
            )

        # V4 · Vehículo (tiene matrícula) -> el modelo es obligatorio.
        if not es_vacia(fila.get("M")) and es_vacia(fila.get("U")):
            resultado_fila.errores.append(
                f"Es un vehículo ({self.etiqueta('M')} diligenciada) y falta "
                f"{self.etiqueta('U')}."
            )


def _es_uno(valor):
    """Acepta 1, 1.0 o el texto "1" (también "1.0"). Nada más."""
    if isinstance(valor, bool):
        return False
    if isinstance(valor, (int, float)):
        return valor == 1
    try:
        return float(str(valor).strip()) == 1
    except ValueError:
        return False
