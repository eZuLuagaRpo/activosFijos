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
# SAP — TRANSACCIONES Y SELECTORES (capturados en SAP real, 2026-09-28)
# ---------------------------------------------------------------------------
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

# Códigos de transacción. Por ahora SOLO se usa la masiva (BRP va por masiva);
# AS01 / AS02 / AS06 quedan registradas para cuando se configuren.
SAP_TX_MASIVA = "Z_AM_MASIVA"      # crear / modificar / borrar masivo
SAP_TX_CREAR = "AS01"              # pendiente de configurar
SAP_TX_MODIFICAR = "AS02"          # pendiente de configurar
SAP_TX_BORRAR = "AS06"             # pendiente de configurar

# Qué transacción usa cada (tipo, acción). Solo lo que ya está configurado.
SAP_TRANSACCION_POR_CASO = {
    (TIPO_BRP, ACCION_CREACION): SAP_TX_MASIVA,
}

# --- Z_AM_MASIVA -------------------------------------------------------------
# 1) Opción según la acción (crear / modificar / borrar masivo).
SAP_MASIVA_XPATH_OPCION_ACCION = {
    ACCION_CREACION: ['//*[@id="M0:46:::1:2-txt"]'],
    ACCION_MODIFICACION: ['//*[@id="M0:46:::2:2-txt"]'],
    ACCION_ELIMINACION: ['//*[@id="M0:46:::3:2-txt"]'],
}
# 2) Campo donde se PEGA la ruta completa del archivo (la misma para las 3
#    opciones), ej. C:\...\carga_sap\CREAR (BRP).xlsm. Decisión 2026-09-28:
#    se escribe la ruta en vez de usar el botón del explorador
#    ('//*[@id="ls-inputfieldhelpbutton"]'), porque ese botón abre una ventana
#    de WINDOWS que Selenium no puede manejar.
SAP_MASIVA_XPATH_CAMPO_RUTA = [
    '//*[@id="M0:46:::3:59-r"]',
]
# 3) "Ejecución de test": se cambia con UN clic en su texto. Según la usuaria,
#    al entrar a la transacción siempre aparece en el mismo estado, así que un
#    clic basta (confirmado 2026-09-28; verificar en la 1ª prueba supervisada).
SAP_MASIVA_XPATH_EJECUCION_TEST = [
    '//*[@id="M0:46:::5:2-txt"]',
]

# Botón "Ejecutar" y cuadro de resultados: PENDIENTES (se capturan después de
# la primera prueba supervisada).
SAP_XPATH_BOTON_EJECUTAR = []
# ⚠️ INTERRUPTOR DE SEGURIDAD. No hay SAP de pruebas: ejecutar crea activos
# REALES. Con False el bot llega hasta deshabilitar "Ejecución de test" y SE
# DETIENE (no hace clic en Ejecutar). Solo se cambia a True a propósito,
# después de validar el flujo supervisado.
SAP_EJECUTAR_REAL = False

# Mientras SAP_EJECUTAR_REAL = False: segundos que el bot deja la pantalla de
# SAP quieta (lista para revisar) antes de seguir con la siguiente solicitud.
SAP_PAUSA_REVISION_SEG = 120


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
