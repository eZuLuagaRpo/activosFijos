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
DOWNLOAD_TEST_DIR = os.path.join(BASE_DIR, "downloads_test")  # ver MODO PRUEBAS abajo
CARGA_SAP_DIR = os.path.join(BASE_DIR, "carga_sap")  # ver NOMBRE_ARCHIVO_SAP abajo
OUTPUT_DIR = os.path.join(BASE_DIR, "salidas")
LOG_DIR = os.path.join(BASE_DIR, "logs")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

for _carpeta in (DOWNLOAD_DIR, DOWNLOAD_TEST_DIR, CARGA_SAP_DIR, OUTPUT_DIR, LOG_DIR):
    os.makedirs(_carpeta, exist_ok=True)


# ---------------------------------------------------------------------------
# MODO PRUEBAS — REEMPLAZO DEL EXCEL (TEMPORAL)
# ---------------------------------------------------------------------------
# Existe SOLO mientras los usuarios siguen adjuntando el formato VIEJO de
# Excel en Appian (con el cual la validación siempre falla).
#
#   False -> FLUJO REAL: se usa el Excel tal cual viene adjunto en Appian.
#   True  -> Todo lo de Appian es real (bandeja, solicitud, tipo/acción,
#            descarga), pero el Excel que se valida y se lleva a SAP es el
#            que TÚ dejaste en DOWNLOAD_TEST_DIR con el nombre EXACTO del
#            número de la solicitud, ej:  downloads_test/PDA-7889.xlsm
#            (BRP - Creación solo acepta .xlsm)
#            - Solicitudes SIN archivo en esa carpeta se OMITEN (ni se abren).
#            - Tu archivo nunca se modifica: el bot trabaja sobre una copia
#              en downloads/ llamada  PDA-7889_brp_creacion_PRUEBA.xlsm
#            - El adjunto real de Appian se descarga igual y NO se borra.
#
# ⚠️ Déjalo en False en el .exe que se entrega a la usuaria.
MODO_PRUEBAS_REEMPLAZO = False


# ---------------------------------------------------------------------------
# APPIAN — CONEXIÓN Y NAVEGADOR
# ---------------------------------------------------------------------------
# TODO: CONFIRMAR con la usuaria la URL EXACTA de Appian que ella usa.
APPIAN_URL = "https://CAMBIAR-POR-URL-REAL-DE-APPIAN"

BROWSER = "edge"
TIMEOUT = 120  # subido de 90s: con internet lento algunas cargas tardaban más.
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
# NOTA: el primer selector capturado (".../div/p/span") dejó de encontrarse
# (confirmado 2026-08-18: la espera agotó los 120s completos sin resultado,
# no fue un tema de lentitud). El de abajo se volvió a capturar y quedó sin
# el "/span" final.
BANDEJA_XPATH_FECHA_VENCIMIENTO = [
    './/td[13]/div/p',
]
# Formato en el que Appian muestra la fecha, ej. "06/10/2026 12:00".
BANDEJA_FORMATO_FECHA = "%d/%m/%Y %H:%M"

# Expresión regular con la que reconocemos un ID de caso válido dentro del
# texto de la celda (ej. "PDA-2389").
BANDEJA_REGEX_CASE_ID = r"[A-Z]{2,5}-\d{2,}"


# ---------------------------------------------------------------------------
# DOMINIO DE NEGOCIO — TIPOS DE ACTIVO Y ACCIONES
# ---------------------------------------------------------------------------
# Acciones canónicas.
ACCION_CREACION = "creacion"
ACCION_MODIFICACION = "modificacion"
ACCION_ELIMINACION = "eliminacion"

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

# XPath del contenedor de esa sección completa. NO se usa un ID de Appian
# (aunque lo hayamos capturado alguna vez): esos IDs son generados
# dinámicamente en cada render y NO son estables entre casos ni sesiones —
# confirmado el 2026-08-11, cuando el ID capturado dejó de encontrarse en
# TODOS los casos de una corrida nueva. En su lugar, se busca por el texto
# visible del encabezado ("Detalles"), igual que hace la librería
# internamente para leer sus propias secciones (rol='region' + <h2>).
DETALLE_XPATH_SECCION_ACTIVOS = (
    "//div[@role='region' and .//h2[normalize-space(.)='Detalles']]"
)

# Textos que indican "este tipo no aplica" en el renglón. Appian renderiza
# un GUION MEDIO ("–", en dash, Unicode U+2013) y NO el guion normal ("-"),
# confirmado el 2026-08-18 (todos los renglones se leían como "con acción"
# porque "–" != "-"). Se aceptan varias variantes para no depender de cuál
# use Appian en cada pantalla.
DETALLE_VALORES_VACIOS = ("-", "–", "—")

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
# Excel solo. CONFIRMADO (2026-08-11) que la descarga automática de la
# librería SÍ funciona, así que este respaldo no se ha necesitado todavía.
# ⚠️ Usa el mismo patrón de ID hasheado que resultó inestable en
# DETALLE_XPATH_SECCION_ACTIVOS (ver nota arriba) — si algún día SÍ hace
# falta este respaldo y falla, probablemente haya que rehacerlo con un
# selector por texto en vez de por ID.
DETALLE_XPATH_BOTON_ADJUNTO_RESPALDO = (
    '//*[@id="459088681f2b464483d3c469e4838095_sectionContents"]'
    '/div/div/div/div/div[3]/div[2]/div/div/div/div/button/span/span[2]'
)


# ---------------------------------------------------------------------------
# SAP — NOMBRE EXACTO DEL ARCHIVO QUE SE CARGA
# ---------------------------------------------------------------------------
# En la carga masiva, SAP exige que la plantilla se llame EXACTAMENTE así
# (confirmado con la usuaria funcional, 2026-09-28; mayúsculas tal cual).
# Los Excel se descargan como CASE_ID_tipo_accion.xlsm (para saber de qué
# solicitud es cada uno) y, JUSTO ANTES de cargar a SAP, el bot hace una
# COPIA temporal con este nombre en CARGA_SAP_DIR. Como SAP procesa una
# solicitud a la vez, esa copia se reemplaza en cada caso. En SAP se busca
# el archivo con el explorador, así que la carpeta no tiene que ser una fija.
NOMBRE_ARCHIVO_SAP = {
    (TIPO_BRP, ACCION_CREACION): "CREAR (BRP).xlsm",
}


# ---------------------------------------------------------------------------
# NOMBRE DEL EJECUTABLE / APP
# ---------------------------------------------------------------------------
APP_NOMBRE = "RPA Activos Fijos"
APP_VERSION = "0.1.0"
