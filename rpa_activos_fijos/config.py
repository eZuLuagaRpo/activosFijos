"""
config.py — Configuración central del RPA "Parametrización de Activos Fijos".

TODO lo que un día pueda cambiar (URLs, navegador, tiempos de espera, rutas,
número de reintentos, selectores/labels de Appian, etc.) vive AQUÍ y NO
incrustado dentro del código de los flujos. Así, cuando algo cambie en Appian
o en el PC de la usuaria, solo se toca este archivo.
"""

import os

# ---------------------------------------------------------------------------
# RUTAS DEL PROYECTO
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
OUTPUT_DIR = os.path.join(BASE_DIR, "salidas")
LOG_DIR = os.path.join(BASE_DIR, "logs")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MAPPING_DIR = os.path.join(BASE_DIR, "transformacion", "mapping")

for _carpeta in (DOWNLOAD_DIR, OUTPUT_DIR, LOG_DIR):
    os.makedirs(_carpeta, exist_ok=True)


# ---------------------------------------------------------------------------
# APPIAN — CONEXIÓN Y NAVEGADOR
# ---------------------------------------------------------------------------
# TODO: CONFIRMAR con la usuaria la URL EXACTA de Appian que ella usa.
APPIAN_URL = "https://CAMBIAR-POR-URL-REAL-DE-APPIAN"

BROWSER = "edge"
TIMEOUT = 90
TIMEOUT_FILES = 600


# ---------------------------------------------------------------------------
# REINTENTOS (resiliencia ante lentitud de red / render)
# ---------------------------------------------------------------------------
RETRY_INTENTOS = 3
RETRY_ESPERA_INICIAL = 2.0
RETRY_FACTOR_BACKOFF = 2.0


# ---------------------------------------------------------------------------
# BANDEJA DE ACTIVIDADES — SELECTORES (capturados en Appian real, 2026-08-04)
# ---------------------------------------------------------------------------
# La librería NO sabe leer la Bandeja de Actividades: eso lo construimos
# nosotros en appian/bandeja_reader.py.
#
# Se ofrecen listas de selectores: el bandeja_reader prueba el primero y, si
# no encuentra nada, pasa al siguiente (selectores de respaldo). Por ahora
# solo hay uno por columna (el capturado); si algún día falla, se le agregan
# alternativas aquí sin tocar el código.

# Filas de la tabla de la bandeja.
BANDEJA_XPATH_FILAS = [
    '//*[@id="sitesBody"]/div/div/div[6]/div[2]/div/div[1]/table/tbody/tr',
]

# Celda/enlace con el ID de la solicitud (columna "Número De La Solicitud"),
# XPath RELATIVO a la fila.
BANDEJA_XPATH_ID_EN_FILA = [
    './/td[4]/div/p/strong/a',
]

# Celda con el nombre del flujo (columna "Nombre Del Flujo"), relativo a la
# fila. La bandeja llega con OTROS procesos mezclados (confirmado), por eso
# se filtra por esta columna.
BANDEJA_XPATH_NOMBRE_FLUJO = [
    './/td[6]/p',
]
BANDEJA_NOMBRE_FLUJO_ESPERADO = "Parametrización de Activos"

# Celda con la fecha de vencimiento (columna "Fecha De Vencimiento
# (Solicitud)"), relativo a la fila. Se usa para procesar por PRIORIDAD (la
# que vence antes, primero).
BANDEJA_XPATH_FECHA_VENCIMIENTO = [
    './/td[13]/div/p/span',
]
# Formato en el que Appian muestra la fecha, ej. "06/10/2026 12:00".
BANDEJA_FORMATO_FECHA = "%d/%m/%Y %H:%M"

# Expresión regular con la que reconocemos un ID de caso válido dentro del
# texto de la celda (ej. "PDA-2389").
BANDEJA_REGEX_CASE_ID = r"[A-Z]{2,5}-\d{2,}"


# ---------------------------------------------------------------------------
# DOMINIO DE NEGOCIO — TIPOS DE ACTIVO Y ACCIONES
# ---------------------------------------------------------------------------
# Acciones y su código de macro asociado.
ACCION_CREACION = "creacion"          # AS01
ACCION_MODIFICACION = "modificacion"  # AS02
ACCION_ELIMINACION = "eliminacion"

CODIGO_MACRO_POR_ACCION = {
    ACCION_CREACION: "AS01",
    ACCION_MODIFICACION: "AS02",
    ACCION_ELIMINACION: "ELIM",   # TODO: CONFIRMAR el código real de eliminación
}

# Tipos de activo canónicos (los 6 renglones fijos de la sección "Detalles").
TIPO_MASCARAS = "mascaras"
TIPO_BRP = "brp"
TIPO_PRJ = "prj"
TIPO_DIFERIDOS = "diferidos"
TIPO_MEJORAS = "mejoras"
TIPO_SEGUNDA_INFO = "segunda_informacion"

# Cómo puede venir escrito el VALOR de la acción desde Appian -> valor canónico.
ALIAS_ACCION = {
    "creacion": ACCION_CREACION,
    "crear": ACCION_CREACION,
    "as01": ACCION_CREACION,
    "modificacion": ACCION_MODIFICACION,
    "modificar": ACCION_MODIFICACION,
    "as02": ACCION_MODIFICACION,
    "eliminacion": ACCION_ELIMINACION,
    "eliminar": ACCION_ELIMINACION,
    "baja": ACCION_ELIMINACION,
}


# ---------------------------------------------------------------------------
# DETALLE DEL CASO — SECCIÓN "Detalles" (tipo de activo + acción)
# ---------------------------------------------------------------------------
# Dentro del caso hay una sección "Detalles" con un renglón FIJO por cada tipo
# de activo posible. Debajo de cada nombre aparece la acción a realizar
# (Crear/Modificar/Eliminar) o un guion "-" si ese tipo NO aplica a esta
# solicitud. Se confirmó con la usuaria que SOLO UNO de los renglones trae una
# acción real; si el bot encuentra más de uno, no adivina: marca el caso como
# fallido para revisión manual (ver flujos/flujo1_appian.py).

# XPath del contenedor de esa sección completa (capturado en Appian real).
DETALLE_XPATH_SECCION_ACTIVOS = (
    '//*[@id="f868ae114fc7b69e3840a9e5db2ddaee_sectionContents"]/div/div/div/div'
)

# Texto que indica "este tipo no aplica" en el renglón.
DETALLE_VALOR_VACIO = "-"

# Texto EXACTO de cada renglón tal como aparece en Appian -> tipo canónico.
LABELS_ACTIVOS_DETALLE = {
    "Máscara": TIPO_MASCARAS,
    "Activos BRP": TIPO_BRP,
    "Activos PRJ": TIPO_PRJ,
    "Activos Diferidos y Renovaciones": TIPO_DIFERIDOS,
    "Mejoras": TIPO_MEJORAS,
    "Segunda Información": TIPO_SEGUNDA_INFO,
}

# Botón de descarga de adjuntos, SOLO como respaldo manual por si
# get_case_data(download_attachments=True) de la librería no descarga el
# Excel solo (todavía sin confirmar).
DETALLE_XPATH_BOTON_ADJUNTO_RESPALDO = (
    '//*[@id="459088681f2b464483d3c469e4838095_sectionContents"]'
    '/div/div/div/div/div[3]/div[2]/div/div/div/div/button/span/span[2]'
)


# ---------------------------------------------------------------------------
# NOMBRE DEL EJECUTABLE / APP
# ---------------------------------------------------------------------------
APP_NOMBRE = "RPA Activos Fijos"
APP_VERSION = "0.1.0"
