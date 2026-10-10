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
OUTPUT_DIR = os.path.join(BASE_DIR, "salidas")
LOG_DIR = os.path.join(BASE_DIR, "logs")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

for _carpeta in (DOWNLOAD_DIR, DOWNLOAD_TEST_DIR, OUTPUT_DIR, LOG_DIR):
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
#            (.xlsx o .xlsm)
#            - Solicitudes SIN archivo en esa carpeta se OMITEN (ni se abren).
#            - Tu archivo nunca se modifica: el bot trabaja sobre una copia
#              en downloads/ llamada  PDA-7889_brp_creacion_PRUEBA.xlsm
#            - El adjunto real de Appian se descarga igual y NO se borra.
#            - En SAP, GUARDAR queda PROHIBIDO (aunque SAP_GUARDAR_REAL = True).
#
# ⚠️ Déjalo en False en el .exe que se entrega a la usuaria.
MODO_PRUEBAS_REEMPLAZO = False


# ---------------------------------------------------------------------------
# MODO PRUEBAS — SOLO SAP (TEMPORAL)
# ---------------------------------------------------------------------------
# Para probar la validación + la transacción de SAP cuando NO hay
# solicitudes en Appian (2026-10-05).
#
#   False -> normal.
#   True  -> el bot NO entra a Appian. Abre el navegador, toma los Excel de
#            DOWNLOAD_TEST_DIR nombrados  <lo_que_quieras>_<tipo>_<accion>.xlsx
#            (o .xlsm), ej:  downloads_test/prueba1_brp_creacion.xlsx
#            El final del nombre dice qué validación y qué formulario de SAP
#            usar. Archivos con otro nombre se OMITEN.
#            - Valida cada archivo y lo lleva a SAP fila por fila, con la
#              misma supervisión ("Continuar (sin guardar)").
#            - En SAP, GUARDAR queda PROHIBIDO (aunque SAP_GUARDAR_REAL = True).
#            - Tu archivo nunca se modifica.
#
# No se puede encender a la vez que MODO_PRUEBAS_REEMPLAZO (el bot no arranca).
# ⚠️ Déjalo en False en el .exe que se entrega a la usuaria.
MODO_PRUEBAS_SOLO_SAP = False


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

# CASO ESPECIAL "DOS ARCHIVOS" (2026-10-10). Si una solicitud de la clave trae
# 2 Excel, uno es de la acción indicada en el valor y se hace PRIMERO.
#   BRP: Appian dice "Activos BRP -> Crear" pero llegan 2 Excel:
#     PASO 1: el de MODIFICACIÓN (AS02) — actualizar el número de inventario
#             (el usuario ya trae el valor final con el sufijo T1/T2/T3).
#     PASO 2: el de CREACIÓN (AS01) — igual que una creación normal.
# Cuál archivo es cuál se decide por su CONTENIDO (encabezados de la
# plantilla), no por el nombre. Con UN solo Excel, la solicitud es normal.
CASOS_DOS_ARCHIVOS = {
    (TIPO_BRP, ACCION_CREACION): (TIPO_BRP, ACCION_MODIFICACION),
}

# Si en el PASO 1 alguna fila falla, ¿se hace igual el PASO 2?
#   False (por defecto, lo más seguro): NO se crea nada y la solicitud queda
#         fallida para revisión (los activos nuevos usan el número de
#         inventario que libera la modificación). ⚠️ POR CONFIRMAR con negocio.
#   True: se crea igual.
CASO_ESPECIAL_CREAR_SI_FALLA_MODIFICACION = False


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
# SAP — TRANSACCIONES INDIVIDUALES Y SELECTORES
# ---------------------------------------------------------------------------
# CAMBIO DE NEGOCIO (2026-10-04): NO se usa la carga masiva (Z_AM_MASIVA) ni
# la modificación masiva. Los activos se crean / modifican / borran UNO POR
# UNO con las transacciones AS01 / AS02 / AS06, llenando el formulario con los
# valores de cada fila del Excel. SAP NO recibe el archivo: el Excel del
# usuario solo se lee (y al final se le agrega la columna "Código SAP").
#
# SAP se usa en el NAVEGADOR (SAP GUI for HTML): se maneja con Selenium, igual
# que Appian. Cada selector es una LISTA (principal -> respaldos), como en la
# bandeja: si algún día cambia, se agrega una alternativa aquí sin tocar código.

# SAP GUI for HTML (webgui), mandante 900. Se abre en una PESTAÑA NUEVA del
# mismo navegador de Appian. Inicio de sesión con las MISMAS credenciales de
# Appian (confirmado 2026-09-28).
SAP_URL = "https://sap-erp.apps.bancolombia.corp/sap/bc/gui/sap/its/webgui?sap-client=900#"

# Pantalla de inicio de sesión. ⚠️ POR CONFIRMAR: son los IDs ESTÁNDAR de la
# pantalla de login de SAP (no se capturaron en el ambiente real). Si la
# sesión entra sola (SSO), el bot no los necesita: detecta que ya está la
# barra de transacción y sigue.
SAP_XPATH_LOGIN_USUARIO = ['//*[@id="sap-user"]']
SAP_XPATH_LOGIN_CLAVE = ['//*[@id="sap-password"]']
SAP_XPATH_LOGIN_BOTON = ['//*[@id="LOGON_BUTTON"]']

# Barra donde se escribe el código de la transacción.
SAP_XPATH_BARRA_TRANSACCION = [
    '//*[@id="ToolbarOkCode"]',
]

# Códigos de transacción.
SAP_TX_CREAR = "AS01"              # crear activo fijo
SAP_TX_MODIFICAR = "AS02"          # modificar activo fijo
SAP_TX_BORRAR = "AS06"             # borrar activo fijo

# Qué transacción usa cada (tipo, acción).
# BRP - Creación: solo AS01 (AS01 tiene el campo "TXT.NUM.PRAL.AF", así que la
# columna AC se escribe al crear; ya NO hay paso por AS02).
# BRP - Modificación: AS02 (2026-10-09). Plantilla propia:
# plantillas/BRP/Plantilla Modificacion BRP.xlsm.
SAP_TRANSACCION_POR_CASO = {
    (TIPO_BRP, ACCION_CREACION): SAP_TX_CREAR,
    (TIPO_BRP, ACCION_MODIFICACION): SAP_TX_MODIFICAR,
}

# --- Formularios (columna del Excel -> campo de SAP) ---------------------------
# Cada formulario es una LISTA ORDENADA de pasos que el bot ejecuta, fila por
# fila del Excel (capturado en SAP real, 2026-10-05):
#   {"tipo": "campo", "columna": "A", "nombre": ..., "xpath": [...]}
#        -> escribe el valor de esa columna (borra lo que tenga el campo).
#           Si la celda viene VACÍA, el campo NO se toca (queda lo de SAP).
#   {"tipo": "casilla", "columna": "N", ...}
#        -> si la celda trae algo, hace UN clic en la casilla; si viene vacía,
#           se deja quieta.
#   {"tipo": "enter", "nombre": ...}       -> presiona Enter.
#   {"tipo": "pestana", "nombre": ..., "xpath": [...]}
#        -> cambia de pestaña con DOS clics separados por
#           SAP_ESPERA_ENTRE_CLICS_SEG (uno solo no funciona; SAP es lento).
# Agregar / corregir un campo = tocar una línea aquí, sin programar.
# Solo se llenan los campos de la lista: columnas del Excel sin campo se
# ignoran, y campos sin columna no se tocan (decisión del usuario, 2026-10-05).

# --- Catálogo: campos del formulario del ACTIVO (compartido AS01 / AS02) -------
# AS01 (crear) y AS02 (modificar) abren EL MISMO formulario, con los MISMOS
# XPath (confirmado por el usuario, 2026-10-09); solo cambia la pantalla
# inicial. Por eso cada XPath se define UNA sola vez aquí, con un nombre, y los
# formularios de abajo solo dicen qué COLUMNA va en qué campo.
#   clave: (nombre para el log, [XPath principal, respaldos...])
SAP_CAMPOS_ACTIVO = {
    # Pestaña 1 (la que se abre al dar Enter)
    "denominacion": ("Denominación", ['//*[@id="M0:46:3:1:2B256:1::1:22"]']),
    "txt_num_pral_af": ("TXT.NUM.PRAL.AF", ['//*[@id="M0:46:3:1:2B256:1::3:22"]']),
    "numero_serie": ("Número de serie", ['//*[@id="M0:46:3:1:2B256:1::5:22"]']),
    "numero_inventario": ("Número de inventario", ['//*[@id="M0:46:3:1:2B256:1::6:22"]']),
    "cantidad": ("Cantidad", ['//*[@id="M0:46:3:1:2B256:1::7:22"]']),
    "ultimo_inventario_el": ("Último inventario el", ['//*[@id="M0:46:3:1:2B256:2::1:22"]']),
    "nota_inventario": ("Nota de inventario", ['//*[@id="M0:46:3:1:2B256:2::2:22"]']),
    "capitalizado_el": ("Capitalizado el", ['//*[@id="M0:46:3:1:2B256:3::1:22"]']),
    "descapitalizado_el": ("Descapitalización el", ['//*[@id="M0:46:3:1:2B256:3::1:67"]']),
    "pedido_el": ("Pedido el", ['//*[@id="M0:46:3:1:2B256:3::3:67"]']),
    # Pestaña 2
    "centro_coste": ("Centro de coste", ['//*[@id="M0:46:3:1:2B257:1::1:22"]']),
    "ceco_responsable": ("CeCo responsable", ['//*[@id="M0:46:3:1:2B257:1::2:22"]']),
    "orden_costes": ("Orden costes", ['//*[@id="M0:46:3:1:2B257:1::3:22"]']),
    "centro": ("Centro", ['//*[@id="M0:46:3:1:2B257:1::5:22"]']),
    "emplazamiento": ("Emplazamiento", ['//*[@id="M0:46:3:1:2B257:1::6:22"]']),
    "local": ("Local", ['//*[@id="M0:46:3:1:2B257:1::7:22"]']),
    "matricula": ("Matrícula vehículo", ['//*[@id="M0:46:3:1:2B257:1::8:22"]']),
    "numero_personal": ("Número de personal", ['//*[@id="M0:46:3:1:2B257:1::9:22"]']),
    "elem_pep": ("Elem. PEP (costes)", ['//*[@id="M0:46:3:1:2B257:1::10:22"]']),
    "activo_paralizado": ("Activo fijo paralizado", ['//*[@id="M0:46:3:1:2B257:1::12:1-txt"]']),  # casilla
    # Pestaña 3
    "estado": ("Estado", ['//*[@id="M0:46:3:1:2B258:1::1:22"]']),
    "tipo": ("Tipo", ['//*[@id="M0:46:3:1:2B258:1::2:22"]']),
    "procedencia": ("Procedencia", ['//*[@id="M0:46:3:1:2B258:1::3:22"]']),
    "ubicacion": ("Ubicación", ['//*[@id="M0:46:3:1:2B258:1::4:22"]']),
    "total_depreciados": ("Total depreciados", ['//*[@id="M0:46:3:1:2B258:1::5:22"]']),
    # Pestaña 4
    "acreedor": ("Acreedor", ['//*[@id="M0:46:3:1:2B259:1::1:23"]']),
    "fabricante": ("Fabricante", ['//*[@id="M0:46:3:1:2B259:1::2:23"]']),
    "af_comprado_nuevo": ("AF comprado nuevo", ['//*[@id="M0:46:3:1:2B259:1::3:2-txt"]']),  # casilla
    "comprado_segunda_mano": ("Comprado 2a mano", ['//*[@id="M0:46:3:1:2B259:1::4:2-txt"]']),  # casilla
    "sociedad_gl_asociada": ("Sociedad GL asociada", ['//*[@id="M0:46:3:1:2B259:1::5:23"]']),
    "pais_origen": ("País origen", ['//*[@id="M0:46:3:1:2B259:1::6:23"]']),
    "denominacion_tipo": ("Denominación de tipo", ['//*[@id="M0:46:3:1:2B259:1::7:23"]']),
    "activo_fijo_orig": ("Activo fijo orig.", ['//*[@id="M0:46:3:1:2B259:1::9:23"]']),
    "alta_el": ("Alta el", ['//*[@id="M0:46:3:1:2B259:1::9:67"]']),
    "anio_adquis_orig": ("Año adquis. orig.", ['//*[@id="M0:46:3:1:2B259:1::10:23"]']),
    "valor_original": ("Valor original", ['//*[@id="M0:46:3:1:2B259:1::11:23"]']),
    "parte_prod_propia": ("Parte prod. propia", ['//*[@id="M0:46:3:1:2B259:1::12:23"]']),
    # Pestaña 5
    "clave_agrupamiento": ("Clave de agrupamiento", ['//*[@id="M0:46:3:1:2B260:1::1:22"]']),
    "indicador_propiedad": ("Indicador propiedad", ['//*[@id="M0:46:3:1:2B260:1::2:22"]']),
    "val_patrim_man": ("Val. patrim. man.", ['//*[@id="M0:46:3:1:2B260:1::4:22"]']),
    "delegacion_hacienda": ("Delegación Hacienda", ['//*[@id="M0:46:3:1:2B260:2::1:22"]']),
    "nif_valor_unit": ("N.I.F. valor unit.", ['//*[@id="M0:46:3:1:2B260:2::2:22"]']),
    "cartilla_del": ("Cartilla del", ['//*[@id="M0:46:3:1:2B260:2::3:22"]']),
    "municipio": ("Municipio", ['//*[@id="M0:46:3:1:2B260:2::4:22"]']),
    "reg_propiedad_del": ("Reg. propiedad del", ['//*[@id="M0:46:3:1:2B260:2::5:22"]']),
    "inscripcion_del": ("Inscripción del", ['//*[@id="M0:46:3:1:2B260:2::5:57"]']),
    "tomo": ("Tomo", ['//*[@id="M0:46:3:1:2B260:2::6:22"]']),
    "hoja": ("Hoja", ['//*[@id="M0:46:3:1:2B260:2::6:28"]']),
    "numero_actual": ("Nº actual", ['//*[@id="M0:46:3:1:2B260:2::6:34"]']),
    "ces_propiedad": ("Ces. propiedad", ['//*[@id="M0:46:3:1:2B260:2::6:57"]']),
    "cartilla_parcelaria": ("Cartilla parcelaria", ['//*[@id="M0:46:3:1:2B260:2::7:22"]']),
    "cartilla_parcelaria_2": ("Cartilla parcelaria campo 2", ['//*[@id="M0:46:3:1:2B260:2::7:28"]']),
    "superficie": ("Superficie", ['//*[@id="M0:46:3:1:2B260:2::7:57"]']),
    "superficie_2": ("Superficie campo 2", ['//*[@id="M0:46:3:1:2B260:2::7:76"]']),
    # Pestaña 6
    "clase_seguro": ("Clase", ['//*[@id="M0:46:3:1:2B261:1::1:22"]']),
    "numero_poliza": ("Nº de póliza", ['//*[@id="M0:46:3:1:2B261:1::2:22"]']),
    "comentario": ("Comentario", ['//*[@id="M0:46:3:1:2B261:1::3:22"]']),
    "inicio": ("Inicio", ['//*[@id="M0:46:3:1:2B261:1::5:22"]']),
}

# Pestañas del formulario del activo (la 1 es la que se abre al dar Enter).
SAP_PESTANAS_ACTIVO = {
    2: ("pestaña 2 (centro de coste...)", ['//*[@id="M0:46:3:1::0:1-title"]']),
    3: ("pestaña 3 (estado...)", ['//*[@id="M0:46:3:1::0:2-title"]']),
    4: ("pestaña 4 (acreedor...)", ['//*[@id="M0:46:3:1::0:3-title"]']),
    5: ("pestaña 5 (clave de agrupamiento...)", ['//*[@id="M0:46:3:1::0:4-title"]']),
    6: ("pestaña 6 (clase, póliza...)", ['//*[@id="M0:46:3:1::0:5-title"]']),
}


def _campo(columna, clave):
    """Paso 'escribir el valor de la columna en el campo del catálogo'."""
    nombre, xpath = SAP_CAMPOS_ACTIVO[clave]
    return {"tipo": "campo", "columna": columna, "nombre": nombre, "xpath": xpath}


def _casilla(columna, clave):
    """Paso 'un clic en la casilla si la celda trae algo'."""
    nombre, xpath = SAP_CAMPOS_ACTIVO[clave]
    return {"tipo": "casilla", "columna": columna, "nombre": nombre, "xpath": xpath}


def _pestana(numero):
    """Paso 'cambiar a la pestaña N' (doble clic lento)."""
    nombre, xpath = SAP_PESTANAS_ACTIVO[numero]
    return {"tipo": "pestana", "nombre": nombre, "xpath": xpath}


_ENTER_FORMULARIO = {"tipo": "enter", "nombre": "abrir el formulario completo"}

# AS01 (crear activo fijo) para BRP - Creación. Columnas = plantilla del
# usuario (plantillas/BRP/Plantilla Creación Activos BRP usuario.xlsm).
SAP_FORMULARIO_AS01_BRP = [
    # Pantalla inicial de AS01
    {"tipo": "campo", "columna": "A", "nombre": "Clase de activo fijo", "xpath": ['//*[@id="M0:46:::2:29"]']},
    {"tipo": "campo", "columna": "B", "nombre": "Sociedad", "xpath": ['//*[@id="M0:46:::3:29"]']},
    {"tipo": "campo", "columna": "C", "nombre": "Ctd. de activos fijos iguales", "xpath": ['//*[@id="M0:46:::4:29"]']},
    _ENTER_FORMULARIO,
    # Pestaña 1
    _campo("D", "denominacion"),
    _campo("AC", "txt_num_pral_af"),
    _campo("F", "numero_inventario"),
    # (campo "cantidad": no tiene columna en esta plantilla -> no se llena)
    _campo("G", "capitalizado_el"),
    # Pestaña 2
    _pestana(2),
    _campo("H", "centro_coste"),
    _campo("I", "ceco_responsable"),
    _campo("J", "orden_costes"),
    _campo("K", "centro"),
    _campo("L", "emplazamiento"),
    _campo("M", "matricula"),
    _casilla("N", "activo_paralizado"),
    # Pestaña 3
    _pestana(3),
    _campo("O", "estado"),
    _campo("P", "tipo"),
    _campo("Q", "procedencia"),
    _campo("R", "ubicacion"),
    # (campo "total_depreciados": no tiene columna en esta plantilla)
    # Pestaña 4
    _pestana(4),
    _campo("S", "acreedor"),
    _campo("T", "fabricante"),
    _campo("U", "denominacion_tipo"),
    _campo("V", "parte_prod_propia"),
    # Pestaña 5
    _pestana(5),
    _campo("W", "clave_agrupamiento"),
    _campo("X", "indicador_propiedad"),
    # Columnas de la plantilla SIN campo: E Marca, Y Número de contrato,
    # Z Área de valoración, AA Duración, AB Periodo -> se IGNORAN.
]

# AS02 (modificar activo fijo) para BRP - Modificación (2026-10-09). Columnas =
# plantilla plantillas/BRP/Plantilla Modificacion BRP.xlsm. SAP muestra el
# formulario con los valores ACTUALES del activo: celda vacía = ese campo no se
# toca (conserva lo que tiene); celda con valor = se borra y se escribe.
SAP_FORMULARIO_AS02_BRP = [
    # Pantalla inicial de AS02
    {"tipo": "campo", "columna": "A", "nombre": "Activo fijo", "xpath": ['//*[@id="M0:46:::2:21"]']},
    {"tipo": "campo", "columna": "B", "nombre": "Subnúmero", "xpath": ['//*[@id="M0:46:::3:21"]']},
    {"tipo": "campo", "columna": "C", "nombre": "Sociedad", "xpath": ['//*[@id="M0:46:::4:21"]']},
    _ENTER_FORMULARIO,
    # Pestaña 1
    _campo("D", "denominacion"),
    _campo("F", "numero_serie"),
    _campo("G", "numero_inventario"),
    _campo("H", "cantidad"),
    _campo("J", "ultimo_inventario_el"),
    _campo("K", "nota_inventario"),
    _campo("L", "descapitalizado_el"),
    _campo("M", "pedido_el"),
    # Pestaña 2
    _pestana(2),
    _campo("N", "centro_coste"),
    _campo("O", "ceco_responsable"),
    _campo("P", "orden_costes"),
    _campo("Q", "centro"),
    _campo("R", "emplazamiento"),
    _campo("S", "local"),
    _campo("T", "matricula"),
    _campo("U", "numero_personal"),
    _campo("V", "elem_pep"),
    _casilla("W", "activo_paralizado"),
    # Pestaña 3
    _pestana(3),
    _campo("X", "estado"),
    _campo("Y", "tipo"),
    _campo("Z", "procedencia"),
    _campo("AA", "ubicacion"),
    _campo("AB", "total_depreciados"),
    # Pestaña 4
    _pestana(4),
    _campo("AC", "fabricante"),
    _casilla("AD", "af_comprado_nuevo"),
    _casilla("AE", "comprado_segunda_mano"),
    _campo("AF", "sociedad_gl_asociada"),
    _campo("AG", "pais_origen"),
    _campo("AH", "denominacion_tipo"),
    _campo("AI", "activo_fijo_orig"),
    _campo("AK", "alta_el"),
    _campo("AL", "anio_adquis_orig"),
    _campo("AM", "valor_original"),
    _campo("AN", "parte_prod_propia"),
    # Pestaña 5
    _pestana(5),
    _campo("AO", "clave_agrupamiento"),
    _campo("AP", "indicador_propiedad"),
    _campo("AQ", "val_patrim_man"),
    _campo("AR", "delegacion_hacienda"),
    _campo("AS", "nif_valor_unit"),
    _campo("AT", "cartilla_del"),
    _campo("AU", "municipio"),
    _campo("AV", "reg_propiedad_del"),
    _campo("AW", "inscripcion_del"),
    _campo("AX", "tomo"),
    _campo("AY", "hoja"),
    _campo("AZ", "numero_actual"),
    _campo("BA", "ces_propiedad"),
    _campo("BB", "cartilla_parcelaria"),
    _campo("BC", "cartilla_parcelaria_2"),
    _campo("BD", "superficie"),
    _campo("BE", "superficie_2"),
    # Pestaña 6
    _pestana(6),
    _campo("BF", "clase_seguro"),
    _campo("BG", "numero_poliza"),
    _campo("BH", "comentario"),
    _campo("BI", "inicio"),
    # Columnas de la plantilla SIN campo (por confirmar, PENDIENTES.md): E Marca,
    # I Cantidad 2, AJ Subnúmero activo fijo origen, BJ Parte contratante,
    # BK Número de contrato, BL Fecha del contrato, BM Área de valoración,
    # BN Duración, BO Periodo -> se IGNORAN.
]

# Qué formulario usa cada (tipo, acción). Si no hay, el Flujo 3 no entra a SAP.
SAP_FORMULARIOS_POR_CASO = {
    (TIPO_BRP, ACCION_CREACION): SAP_FORMULARIO_AS01_BRP,
    (TIPO_BRP, ACCION_MODIFICACION): SAP_FORMULARIO_AS02_BRP,
}

# SAP es lento al cambiar de pestaña/ventana: segundos entre el 1er y el 2º
# clic de una pestaña, y después de cambiar de pestaña.
SAP_ESPERA_ENTRE_CLICS_SEG = 2

# SAP web redibuja la pantalla con cada acción. Si un campo "se vence"
# (StaleElementReference) entre encontrarlo y usarlo, se vuelve a buscar y se
# reintenta hasta este número de veces. Además, ENTRE FILAS se recarga la
# página (F5) para empezar cada activo con SAP limpio (1ª prueba real,
# 2026-10-05: sin recargar, la 2ª fila fallaba con elementos vencidos).
SAP_REINTENTOS_ELEMENTO_VENCIDO = 3

# Formatos con los que se ESCRIBEN los valores en SAP. ⚠️ POR CONFIRMAR.
SAP_FORMATO_FECHA = "%d.%m.%Y"     # ej. 05.10.2026 (columna G "Capitalizado el")
SAP_SEPARADOR_DECIMAL = ","        # ej. 12,5 (solo para números con decimales)

# Guardar: btn[11] es el botón "Guardar" estándar de SAP (Ctrl+S = respaldo).
SAP_XPATH_BOTON_GUARDAR = ['//*[@id="M0:36::btn[11]"]']

# Mensaje de la barra inferior tras guardar. ⚠️ PENDIENTE el XPath: mientras
# esté vacío, el bot NO guarda (no podría confirmar si el activo se creó).
SAP_XPATH_MENSAJE_ESTADO = []
# Éxito en AS01: "El act.fj. 7129560 0 se ha creado" -> código 7129560 (el
# primer número; el segundo es el subnúmero).
SAP_REGEX_ACTIVO_CREADO = r"act\.?\s*fj\.?\s*(\d+)\s+\d+\s+se ha creado"
# Mensaje de ÉXITO de cada transacción tras Guardar (el grupo 1 es lo que va a
# la columna de resultado). Si una transacción NO está aquí, el bot NUNCA
# guarda en ella (no podría saber si salió bien).
#   AS02: PENDIENTE el texto del mensaje de éxito de la modificación.
SAP_REGEX_EXITO_POR_TRANSACCION = {
    SAP_TX_CREAR: SAP_REGEX_ACTIVO_CREADO,
}

# Salir SIN guardar (supervisión): DOS clics en "Atrás" (separados por
# SAP_ESPERA_ENTRE_CLICS_SEG) y confirmar "salir sin guardar" en la ventana
# que aparece. SAP vuelve al inicio de la transacción.
SAP_XPATH_BOTON_ATRAS = ['//*[@id="M0:36::btn[3]"]']
SAP_XPATH_CONFIRMAR_SALIR_SIN_GUARDAR = ['//*[@id="M1:46:::3:18"]']

# ⚠️ INTERRUPTOR DE SEGURIDAD. No hay SAP de pruebas: "Guardar" en AS01 /
# AS02 / AS06 CREA, MODIFICA o BORRA activos REALES.
#   False -> el bot llena el formulario de cada activo y SE DETIENE antes de
#            Guardar (supervisión: botón "Continuar" en la ventana del bot,
#            que pasa al siguiente activo SIN guardar).
#   True  -> guarda. Solo se cambia a propósito, tras validar el flujo
#            supervisado.
# En CUALQUIER modo pruebas (REEMPLAZO o SOLO_SAP) guardar está PROHIBIDO
# aunque esto sea True (ver flujo3_sap.guardar_permitido()).
SAP_GUARDAR_REAL = False


# ---------------------------------------------------------------------------
# APPIAN — RESPUESTA EN LA SOLICITUD (capturados en Appian real, 2026-09-28)
# ---------------------------------------------------------------------------
# Se vuelve a la URL de la solicitud (CasoBandeja.url) y se responde:
#   Atender -> modal "Atender solicitud" -> formulario (finalización +
#   comentario + adjunto) -> Finalizar.
# La lógica de cuándo es Exitoso / No Exitoso y el texto del comentario se
# definen más adelante, activo por activo.
#
# ⚠️ Varios selectores usan IDs largos generados por Appian
# ("139287c0..._sectionContents", "45306ca7...", "7f54c5d3..."). Ese tipo de
# ID resultó INESTABLE en este proyecto (ver Changelog 2026-08-11: cambió
# entre casos y sesiones). Se dejan como principal, pero hay que agregarles
# un respaldo por TEXTO VISIBLE (etiqueta del campo / texto del botón).

# Botón en la página de la solicitud que abre las acciones.
RESPUESTA_XPATH_BOTON_ATENDER = [
    '//*[@id="sitesBody"]/div/div/div/div/div[1]/div[2]/div/div[1]/div/div[2]/div/div/button',
]
# Botón "Atender solicitud" dentro del modal.
RESPUESTA_XPATH_BOTON_ATENDER_MODAL = [
    '//*[@id="related-action-body"]/div/div[1]/div[1]/div/div/div/div[2]'
    '/div/div/div/div/div[3]/div/div/button',
]
# Lista desplegable "¿Cómo deseas finalizar esta solicitud?".
RESPUESTA_XPATH_DROPDOWN_FINALIZACION = [
    '//*[@id="139287c082d4707c3511cf84c92c6879_sectionContents"]/div/div/div/div',
]
RESPUESTA_OPCION_EXITOSO = "Finalizado Exitoso"
RESPUESTA_OPCION_NO_EXITOSO = "Finalizado No Exitoso"
# Campo de texto del comentario.
RESPUESTA_XPATH_COMENTARIO = [
    '//*[@id="45306ca7cd940b1a7ec4dfd8ab15fe2f"]',
]
# Botón para adjuntar el Excel con los resultados de SAP.
RESPUESTA_XPATH_BOTON_ADJUNTAR = [
    '//*[@id="139287c082d4707c3511cf84c92c6879_sectionContents"]'
    '/div/div/div/div/div[4]/div[2]/div/div/div[2]/button',
]
# Botón "Finalizar" (cierra la solicitud y Appian notifica al usuario).
RESPUESTA_XPATH_BOTON_FINALIZAR = [
    '//*[@id="7f54c5d3d67e507bd6a5d030a08698fa_sectionContents"]'
    '/div/div/div[3]/div[2]/div/div/button',
]
# ⚠️ INTERRUPTOR DE SEGURIDAD. Las solicitudes y los usuarios son REALES
# (también en MODO PRUEBAS). Con False el bot llena el formulario pero NO
# hace clic en Finalizar. Solo se cambia a True a propósito.
APPIAN_RESPONDER_REAL = False


# ---------------------------------------------------------------------------
# NOMBRE DEL EJECUTABLE / APP
# ---------------------------------------------------------------------------
APP_NOMBRE = "RPA Activos Fijos"
APP_VERSION = "0.1.0"
