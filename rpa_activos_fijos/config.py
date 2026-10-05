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
SAP_TRANSACCION_POR_CASO = {
    (TIPO_BRP, ACCION_CREACION): SAP_TX_CREAR,
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

# AS01 (crear activo fijo) para BRP - Creación. Columnas = plantilla del
# usuario (plantillas/BRP/Plantilla Creación Activos BRP usuario.xlsm).
SAP_FORMULARIO_AS01_BRP = [
    # Pantalla inicial de AS01
    {"tipo": "campo", "columna": "A", "nombre": "Clase de activo fijo", "xpath": ['//*[@id="M0:46:::2:29"]']},
    {"tipo": "campo", "columna": "B", "nombre": "Sociedad", "xpath": ['//*[@id="M0:46:::3:29"]']},
    {"tipo": "campo", "columna": "C", "nombre": "Ctd. de activos fijos iguales", "xpath": ['//*[@id="M0:46:::4:29"]']},
    {"tipo": "enter", "nombre": "abrir el formulario completo"},
    # Formulario completo (primera pestaña)
    {"tipo": "campo", "columna": "D", "nombre": "Denominación", "xpath": ['//*[@id="M0:46:3:1:2B256:1::1:22"]']},
    {"tipo": "campo", "columna": "AC", "nombre": "TXT.NUM.PRAL.AF", "xpath": ['//*[@id="M0:46:3:1:2B256:1::3:22"]']},
    {"tipo": "campo", "columna": "F", "nombre": "Número de inventario", "xpath": ['//*[@id="M0:46:3:1:2B256:1::6:22"]']},
    # Campo "Cantidad" '//*[@id="M0:46:3:1:2B256:1::7:22"]': no tiene columna en
    #   la plantilla -> no se llena (decisión del usuario, 2026-10-05).
    {"tipo": "campo", "columna": "G", "nombre": "Capitalizado el", "xpath": ['//*[@id="M0:46:3:1:2B256:3::1:22"]']},
    # Pestaña 2
    {"tipo": "pestana", "nombre": "pestaña 2 (centro de coste...)", "xpath": ['//*[@id="M0:46:3:1::0:1-title"]']},
    {"tipo": "campo", "columna": "H", "nombre": "Centro de coste", "xpath": ['//*[@id="M0:46:3:1:2B257:1::1:22"]']},
    {"tipo": "campo", "columna": "I", "nombre": "CeCo responsable", "xpath": ['//*[@id="M0:46:3:1:2B257:1::2:22"]']},
    {"tipo": "campo", "columna": "J", "nombre": "Orden costes", "xpath": ['//*[@id="M0:46:3:1:2B257:1::3:22"]']},
    {"tipo": "campo", "columna": "K", "nombre": "Centro", "xpath": ['//*[@id="M0:46:3:1:2B257:1::5:22"]']},
    {"tipo": "campo", "columna": "L", "nombre": "Emplazamiento", "xpath": ['//*[@id="M0:46:3:1:2B257:1::6:22"]']},
    {"tipo": "campo", "columna": "M", "nombre": "Matrícula vehículo", "xpath": ['//*[@id="M0:46:3:1:2B257:1::8:22"]']},
    {"tipo": "casilla", "columna": "N", "nombre": "Activo fijo paralizado", "xpath": ['//*[@id="M0:46:3:1:2B257:1::12:1-txt"]']},
    # Pestaña 3
    {"tipo": "pestana", "nombre": "pestaña 3 (estado...)", "xpath": ['//*[@id="M0:46:3:1::0:2-title"]']},
    {"tipo": "campo", "columna": "O", "nombre": "Estado", "xpath": ['//*[@id="M0:46:3:1:2B258:1::1:22"]']},
    {"tipo": "campo", "columna": "P", "nombre": "Tipo", "xpath": ['//*[@id="M0:46:3:1:2B258:1::2:22"]']},
    {"tipo": "campo", "columna": "Q", "nombre": "Procedencia", "xpath": ['//*[@id="M0:46:3:1:2B258:1::3:22"]']},
    {"tipo": "campo", "columna": "R", "nombre": "Ubicación", "xpath": ['//*[@id="M0:46:3:1:2B258:1::4:22"]']},
    # Campo "Total depreciados" '//*[@id="M0:46:3:1:2B258:1::5:22"]': no tiene
    #   columna en la plantilla -> no se llena (decisión del usuario, 2026-10-05).
    # Pestaña 4
    {"tipo": "pestana", "nombre": "pestaña 4 (acreedor...)", "xpath": ['//*[@id="M0:46:3:1::0:3-title"]']},
    {"tipo": "campo", "columna": "S", "nombre": "Acreedor", "xpath": ['//*[@id="M0:46:3:1:2B259:1::1:23"]']},
    {"tipo": "campo", "columna": "T", "nombre": "Fabricante", "xpath": ['//*[@id="M0:46:3:1:2B259:1::2:23"]']},
    {"tipo": "campo", "columna": "U", "nombre": "Denominación de tipo", "xpath": ['//*[@id="M0:46:3:1:2B259:1::7:23"]']},
    {"tipo": "campo", "columna": "V", "nombre": "Parte prod. propia", "xpath": ['//*[@id="M0:46:3:1:2B259:1::12:23"]']},
    # Pestaña 5
    {"tipo": "pestana", "nombre": "pestaña 5 (clave de agrupamiento...)", "xpath": ['//*[@id="M0:46:3:1::0:4-title"]']},
    {"tipo": "campo", "columna": "W", "nombre": "Clave de agrupamiento", "xpath": ['//*[@id="M0:46:3:1:2B260:1::1:22"]']},
    {"tipo": "campo", "columna": "X", "nombre": "Indicador propiedad", "xpath": ['//*[@id="M0:46:3:1:2B260:1::2:22"]']},
    # Columnas de la plantilla SIN campo en este formulario: E Marca, Y Número
    # de contrato, Z Área de valoración, AA Duración, AB Periodo -> se IGNORAN
    # (solo se llenan los campos de esta lista; decisión del usuario, 2026-10-05).
]

# Qué formulario usa cada (tipo, acción). Si no hay, el Flujo 3 no entra a SAP.
SAP_FORMULARIOS_POR_CASO = {
    (TIPO_BRP, ACCION_CREACION): SAP_FORMULARIO_AS01_BRP,
}

# SAP es lento al cambiar de pestaña/ventana: segundos entre el 1er y el 2º
# clic de una pestaña, y después de cambiar de pestaña.
SAP_ESPERA_ENTRE_CLICS_SEG = 2

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

# --- AS02 (REFERENCIA para la acción MODIFICAR) -------------------------------
# Capturados el 2026-09-29, cuando la creación BRP pasaba por AS02 después de
# la masiva (ese paso ya NO existe). Se conservan como referencia para la
# acción MODIFICAR, que tendrá su propia plantilla y se configura después.
SAP_AS02_XPATH_ACTIVO_FIJO = ['//*[@id="M0:46:::2:21-r"]']   # código del activo
SAP_AS02_XPATH_SOCIEDAD = ['//*[@id="M0:46:::4:21"]']        # sociedad
# (luego Enter) Pantalla del activo: campo "TXT.NUM.PRAL.AF". Puede traer
# texto: se BORRA antes de escribir.
SAP_AS02_XPATH_TXT_ACREEDOR = ['//*[@id="M0:46:3:1:2B256:1::3:22"]']


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
