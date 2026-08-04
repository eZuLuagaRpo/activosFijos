"""
config.py — Configuración central del RPA "Parametrización de Activos Fijos".

TODO lo que un día pueda cambiar (URLs, navegador, tiempos de espera, rutas,
número de reintentos, labels de los campos de Appian, etc.) vive AQUÍ y NO
incrustado dentro del código de los flujos. Así, cuando algo cambie en Appian
o en el PC de la usuaria, solo se toca este archivo.

Si eres principiante: piensa en este archivo como el "panel de control" del bot.
Casi todos los valores marcados con  # TODO  deben confirmarse con la usuaria
real o capturándolos en el navegador (ver docs/CONFIGURACION_MANUAL.md).
"""

import os

# ---------------------------------------------------------------------------
# RUTAS DEL PROYECTO
# ---------------------------------------------------------------------------
# BASE_DIR es la carpeta donde vive este archivo (la raíz del proyecto).
# Se calcula sola; no la cambies.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Carpeta donde la librería de Appian dejará los Excel que descargue.
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")

# Carpeta donde el Flujo 2 guardará los Excel ya transformados al formato macro.
OUTPUT_DIR = os.path.join(BASE_DIR, "salidas")

# Carpeta donde se guardan los archivos de log (uno por ejecución, con fecha).
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Carpeta de assets (imágenes/íconos de la UI).
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Carpeta con las plantillas de macro de SAP y la configuración de mapeo.
MAPPING_DIR = os.path.join(BASE_DIR, "transformacion", "mapping")

# Nos aseguramos de que las carpetas de salida existan al arrancar.
for _carpeta in (DOWNLOAD_DIR, OUTPUT_DIR, LOG_DIR):
    os.makedirs(_carpeta, exist_ok=True)


# ---------------------------------------------------------------------------
# APPIAN — CONEXIÓN Y NAVEGADOR
# ---------------------------------------------------------------------------
# TODO: CONFIRMAR con la usuaria la URL EXACTA de Appian que ella usa.
# Debe ser la dirección completa, por ejemplo:
#   "https://bancolombia.appiancloud.com/suite/"
APPIAN_URL = "https://CAMBIAR-POR-URL-REAL-DE-APPIAN"

# Navegador con el que trabaja la librería. Por defecto Edge (confirmar que la
# usuaria use Edge y que pueda descargar archivos).
BROWSER = "edge"

# Tiempo (segundos) máximo que la librería espera a que un elemento aparezca.
TIMEOUT = 90

# Tiempo (segundos) máximo que la librería espera a que termine una descarga.
TIMEOUT_FILES = 600


# ---------------------------------------------------------------------------
# REINTENTOS (resiliencia ante lentitud de red / render)
# ---------------------------------------------------------------------------
# Número de intentos para operaciones web que pueden fallar por lentitud.
RETRY_INTENTOS = 3

# Espera inicial (segundos) entre reintentos. Crece con "backoff" (ver core/retry.py).
RETRY_ESPERA_INICIAL = 2.0

# Factor de crecimiento de la espera: 2.0 => 2s, 4s, 8s...
RETRY_FACTOR_BACKOFF = 2.0


# ---------------------------------------------------------------------------
# BANDEJA DE ACTIVIDADES — SELECTORES (PLACEHOLDERS)
# ---------------------------------------------------------------------------
# La librería NO sabe leer la Bandeja de Actividades: eso lo construimos
# nosotros en appian/bandeja_reader.py. Necesitamos los XPath reales de la
# tabla de la bandeja. Como todavía no los conocemos, quedan como PLACEHOLDER.
#
# CÓMO CAPTURARLOS: abre Appian en Edge, entra a la Bandeja de Actividades,
# presiona F12 (DevTools), usa la flechita de "inspeccionar" y haz clic sobre
# la fila / el enlace del ID. Copia el XPath y pégalo aquí.
# Paso a paso detallado en docs/CONFIGURACION_MANUAL.md.
#
# Se ofrecen listas de selectores: el bandeja_reader prueba el primero y, si
# no encuentra nada, pasa al siguiente (selectores de respaldo).

# TODO: CAPTURAR SELECTOR REAL — filas de la tabla de la bandeja.
BANDEJA_XPATH_FILAS = [
    "//table//tbody/tr",                     # principal (placeholder)
    "//div[@role='row']",                    # respaldo 1 (placeholder)
    "//*[contains(@class,'grid')]//tr",      # respaldo 2 (placeholder)
]

# TODO: CAPTURAR SELECTOR REAL — celda/enlace que contiene el ID del caso
# DENTRO de cada fila (XPath RELATIVO a la fila, por eso empieza con ".//").
BANDEJA_XPATH_ID_EN_FILA = [
    ".//a",                                  # principal (placeholder)
    ".//td[1]//a",                           # respaldo 1 (placeholder)
    ".//td[1]",                              # respaldo 2 (placeholder)
]

# TODO (OPCIONAL): CAPTURAR SELECTOR REAL — control para filtrar la bandeja por
# tipo de proceso (si algún día llegan casos mezclados). De momento no se usa.
BANDEJA_XPATH_FILTRO = [
    # "//input[@aria-label='Filtrar']",      # placeholder
]

# Expresión regular con la que reconocemos un ID de caso válido dentro del texto
# de la celda. Por defecto reconoce cosas como "PDA-2389".
# TODO: CONFIRMAR el prefijo/patrón real de los casos de activos fijos.
BANDEJA_REGEX_CASE_ID = r"[A-Z]{2,5}-\d{2,}"

# SUPUESTO ACTUAL (PENDIENTE de confirmar): a la usuaria de la bandeja le llegan
# SOLO solicitudes de activos fijos. Si un día llegan mezcladas, poner esto en
# True y completar BANDEJA_XPATH_FILTRO / la lógica de filtrado.
BANDEJA_FILTRAR_POR_TIPO = False


# ---------------------------------------------------------------------------
# DETALLE DEL CASO — LABELS DE LOS CAMPOS QUE NECESITAMOS
# ---------------------------------------------------------------------------
# get_case_data() devuelve un DataFrame con columnas  label | value.
# De ahí sacamos el "tipo de activo" y la "acción". Necesitamos saber el TEXTO
# EXACTO del label tal como aparece en Appian (respetando mayúsculas/tildes).
#
# Se aceptan varios posibles labels por si el nombre cambia entre formularios;
# el flujo1 prueba en orden hasta encontrar uno.
#
# TODO: CONFIRMAR los labels exactos abriendo un caso real y mirando el detalle.
LABELS_TIPO_ACTIVO = [
    "Tipo de Activo",        # placeholder
    "Tipo Activo",           # placeholder
    "Tipo de activo",        # placeholder
]

LABELS_ACCION = [
    "Acción",                # placeholder
    "Accion",                # placeholder
    "Tipo de Acción",        # placeholder
]


# ---------------------------------------------------------------------------
# DOMINIO DE NEGOCIO — TIPOS DE ACTIVO Y ACCIONES
# ---------------------------------------------------------------------------
# Nombres "canónicos" (internos) que usa el bot. El texto que venga de Appian se
# normaliza (minúsculas, sin tildes) y se compara contra los alias de abajo.

# Acciones y su código de macro asociado.
ACCION_CREACION = "creacion"        # AS01
ACCION_MODIFICACION = "modificacion"  # AS02
ACCION_ELIMINACION = "eliminacion"

CODIGO_MACRO_POR_ACCION = {
    ACCION_CREACION: "AS01",
    ACCION_MODIFICACION: "AS02",
    ACCION_ELIMINACION: "ELIM",   # TODO: CONFIRMAR el código real de eliminación
}

# Tipos de activo canónicos.
TIPO_MASCARAS = "mascaras"
TIPO_BRP = "brp"
TIPO_PRJ = "prj"
TIPO_DIFERIDOS = "diferidos"
TIPO_MEJORAS = "mejoras"

# Alias: cómo puede venir escrito cada valor desde Appian -> valor canónico.
# TODO: CONFIRMAR/AMPLIAR con los textos reales que aparecen en Appian.
ALIAS_TIPO_ACTIVO = {
    "mascaras": TIPO_MASCARAS,
    "mascara": TIPO_MASCARAS,
    "activo principal": TIPO_MASCARAS,
    "brp": TIPO_BRP,
    "bienes recibidos en pago": TIPO_BRP,
    "prj": TIPO_PRJ,
    "proyecto": TIPO_PRJ,
    "activo de proyecto": TIPO_PRJ,
    "diferidos": TIPO_DIFERIDOS,
    "diferido": TIPO_DIFERIDOS,
    "diferidos y renovaciones": TIPO_DIFERIDOS,
    "licencias": TIPO_DIFERIDOS,
    "mejoras": TIPO_MEJORAS,
    "mejora": TIPO_MEJORAS,
}

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
# NOMBRE DEL EJECUTABLE / APP
# ---------------------------------------------------------------------------
APP_NOMBRE = "RPA Activos Fijos"
APP_VERSION = "0.1.0"
