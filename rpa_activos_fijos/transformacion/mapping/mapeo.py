"""
transformacion/mapping/mapeo.py — Configuración de mapeo Appian -> macro SAP.

⚠️ PLACEHOLDER ⚠️
Aquí vivirá el "diccionario de traducción" que dice qué columna del Excel de
Appian corresponde a qué columna de la macro de SAP, POR CADA combinación de
(tipo de activo, acción). El desarrollador lo entregará después; de momento
están vacíos y bien marcados.

Estructura propuesta (cuando llegue el mapeo real, rellenar así):

    MAPEO = {
        ("mascaras", "creacion"): {
            "columna_macro_1": "columna_appian_A",
            "columna_macro_2": "columna_appian_B",
            ...
        },
        ("diferidos", "creacion_paso1"): { ... },   # AS01
        ("diferidos", "creacion_paso2"): { ... },   # AS02
        ...
    }

La clave puede ser (tipo, accion) o, para el caso especial de diferidos, una
sub-acción con sufijo de paso.
"""

# TODO: PEGAR AQUÍ EL MAPEO REAL entregado por el desarrollador (ver
# docs/CONFIGURACION_MANUAL.md, sección "Mapeo Appian -> macro SAP").
MAPEO = {
    # ("mascaras", "creacion"): {},        # placeholder
    # ("mascaras", "modificacion"): {},    # placeholder
    # ("brp", "creacion"): {},             # placeholder
    # ("prj", "creacion"): {},             # placeholder
    # ("diferidos", "creacion_as01"): {},  # placeholder (paso 1)
    # ("diferidos", "creacion_as02"): {},  # placeholder (paso 2)
    # ("mejoras", "creacion"): {},         # placeholder
}

# Ruta (opcional) a una plantilla .xlsx real de la macro de SAP por acción.
# Cuando el desarrollador consiga las macros reales, las coloca en esta carpeta
# y referencia el nombre del archivo aquí.
# TODO: COLOCAR LAS PLANTILLAS REALES en transformacion/mapping/ y nombrarlas aquí.
PLANTILLAS_MACRO = {
    "creacion": None,       # ej. "plantilla_creacion.xlsx"
    "modificacion": None,   # ej. "plantilla_modificacion.xlsx"
    "eliminacion": None,    # ej. "plantilla_eliminacion.xlsx"
}


def obtener_mapeo(tipo, accion):
    """
    Devuelve el diccionario de mapeo para (tipo, accion), o None si aún no está
    definido (placeholder). Los handlers usan esto para transformar columnas.
    """
    return MAPEO.get((tipo, accion))
