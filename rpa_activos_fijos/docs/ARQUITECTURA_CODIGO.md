# Cómo funciona el código — RPA "Parametrización de Activos Fijos"

> **Para quién es:** para cualquier persona que necesite entender, mantener o
> ampliar el bot, aunque esté empezando en Python o en RPA. Explica **qué hace
> cada archivo, cómo se conectan entre sí y dónde tocar** para los cambios más
> comunes.
>
> **Documentos relacionados:**
> [ESTADO_PROYECTO.md](ESTADO_PROYECTO.md) (bitácora y decisiones) ·
> [PENDIENTES.md](PENDIENTES.md) (lo que falta) ·
> [GUIA_MODO_PRUEBAS.md](GUIA_MODO_PRUEBAS.md) (cómo probar).
>
> Última actualización: 2026-10-06.

---

## 1. La idea en una frase

El bot **lee las solicitudes pendientes en Appian, valida el Excel que adjuntó
el usuario y crea cada activo en SAP llenando el formulario de la transacción**
(hoy: BRP – Creación con **AS01**), con frenos de seguridad para no tocar
nada real mientras se prueba.

```
  ┌──────────┐     ┌────────────┐     ┌──────────────┐     ┌──────────────┐
  │ Ventana  │ ──► │  APPIAN    │ ──► │ VALIDACIÓN   │ ──► │     SAP      │
  │ del bot  │     │ (Flujo 1)  │     │  (Flujo 2)   │     │  (Flujo 3)   │
  └──────────┘     └────────────┘     └──────────────┘     └──────────────┘
   credenciales     bandeja, abrir      reglas del Excel     AS01 fila por
   + consola        solicitud, tipo/    fila por fila,       fila, se detiene
                    acción, descargar   todo o nada          antes de Guardar
                    el Excel
```

---

## 2. ¿Qué pasa cuando la usuaria presiona "Iniciar"? (recorrido completo)

Este es el "camino" que sigue el código, en orden. Entre paréntesis, el
archivo y la función donde ocurre.

1. **Arranque.** Se abre la ventana (`app.py` → `AppWindow`). Se muestra la
   pantalla de login.
2. **Credenciales.** La usuaria escribe usuario y clave y presiona Iniciar
   (`ui/views/login_view.py` → `_on_iniciar`). Las credenciales quedan **solo
   en memoria** y se pasa a la consola.
3. **El bot arranca en un hilo aparte** (`ui/views/console_view.py` →
   `iniciar_ejecucion` → `_correr_bot`). Así la ventana nunca se congela.
4. **El orquestador toma el control** (`orquestador.py` → `ejecutar`). Revisa
   los interruptores y decide el recorrido:
   - **Normal / modo reemplazo** → `_ejecutar_con_appian`.
   - **Modo solo SAP** → `_ejecutar_solo_sap` (salta Appian).
5. **Appian: inicio de sesión** (`appian/appian_client.py` → `start`).
6. **Appian: leer la bandeja** (`appian/bandeja_reader.py` →
   `listar_pendientes`): filtra "Parametrización de Activos" y ordena por fecha
   de vencimiento.
7. **Por cada solicitud** (`orquestador.py` → `_procesar`), en su propio
   `try/except` (si una falla, las demás siguen):
   1. **Flujo 1 — Appian** (`flujos/flujo1_appian.py` → `obtener_solicitud`):
      entra a la solicitud, lee "Detalles" (qué activo y qué acción), descarga
      y renombra el Excel.
   2. **Flujo 2 — Validación** (`flujos/flujo2_validar.py` →
      `validar_solicitud`): aplica las reglas de la plantilla. Si una fila
      falla, la solicitud no sigue.
   3. **Flujo 3 — SAP** (`flujos/flujo3_sap.py` → `cargar_a_sap`): por cada
      fila del Excel, abre AS01, llena el formulario y se detiene antes de
      Guardar (o guarda, si está permitido).
   4. Vuelve a la pestaña de Appian para la siguiente solicitud.
8. **Resumen final** (`orquestador.py` → `_emitir_resumen`): total, OK,
   fallidos y omitidos. El navegador se cierra **siempre**.
9. **La ventana** muestra "Terminado" y habilita "Volver".

---

## 3. Mapa de carpetas

```
rpa_activos_fijos/
├── app.py                ← punto de entrada (lo que se empaqueta como .exe)
├── config.py             ← ⚙️ TODA la configuración (URLs, XPath, interruptores…)
├── orquestador.py        ← el "director": encadena los flujos y arma el resumen
│
├── ui/                   ← la ventana (customtkinter)
│   ├── app_window.py         ventana principal, cambia entre login y consola
│   ├── styles/theme.py       colores Bancolombia
│   └── views/
│       ├── login_view.py     pantalla de credenciales
│       └── console_view.py   consola en vivo + botón "Continuar (sin guardar)"
│
├── core/                 ← piezas de apoyo que usa todo el bot
│   ├── logger.py             logs a archivo + consola (oculta contraseñas)
│   ├── exceptions.py         errores propios del bot
│   ├── models.py             "fichas" de datos (Solicitud, ResultadoCaso…)
│   ├── retry.py              reintentos con espera creciente
│   └── texto.py              normalizar textos (sin tildes, minúsculas)
│
├── appian/               ← todo lo que habla con Appian
│   ├── appian_client.py      envoltura de la librería corporativa
│   └── bandeja_reader.py     lee la Bandeja de Actividades
│
├── flujos/               ← los 3 pasos del negocio
│   ├── flujo1_appian.py      abrir solicitud, tipo/acción, descargar Excel
│   ├── flujo2_validar.py     validar el Excel
│   ├── flujo3_sap.py         llenar SAP fila por fila
│   └── modo_solo_sap.py      (pruebas) Excel locales en vez de Appian
│
├── validacion/           ← reglas de cada plantilla
│   ├── router.py             (activo, acción) → qué validador usar
│   ├── base_validador.py     motor común de validación
│   └── plantillas/
│       └── brp_creacion.py   columnas y reglas de BRP – Creación
│
├── sap/
│   └── sap_webgui.py     ← cómo "mover" SAP en el navegador
│
├── tests/                ← pruebas automáticas (pytest)
├── downloads/            ← Excel descargados de Appian (se generan al correr)
├── downloads_test/       ← tus Excel para los modos de prueba
├── salidas/              ← Excel de respuesta con "Código SAP"
├── logs/                 ← un log por ejecución
└── docs/                 ← documentación (este archivo y los demás)
```

> **Regla de oro de la organización:** cada carpeta tiene **una sola
> responsabilidad**. La ventana no sabe nada de SAP; SAP no sabe nada de
> Appian; las reglas del Excel no saben nada de navegadores. Así, un cambio
> en un sistema no rompe los otros.

---

## 4. Los módulos, uno por uno

### 4.1 `app.py` — punto de entrada

Lo más corto del proyecto: crea la ventana (`AppWindow`) y arranca su bucle
(`mainloop`). Es el archivo que `build.bat` convierte en `.exe`.

### 4.2 `config.py` — el panel de control

**Todo lo que puede cambiar vive aquí, no dentro del código**: URLs, navegador,
tiempos de espera, rutas de carpetas, XPath de Appian y SAP, formularios de
SAP e interruptores. Si cambia una pantalla de Appian o SAP, normalmente
**solo se toca este archivo**.

Secciones principales:

| Sección | Qué contiene |
|---|---|
| Rutas | `DOWNLOAD_DIR`, `DOWNLOAD_TEST_DIR`, `OUTPUT_DIR`, `LOG_DIR` |
| Modos de prueba | `MODO_PRUEBAS_REEMPLAZO`, `MODO_PRUEBAS_SOLO_SAP` |
| Appian | `APPIAN_URL`, `BROWSER`, `TIMEOUT`, reintentos |
| Bandeja | `BANDEJA_XPATH_*`, nombre del flujo esperado, formato de fecha |
| Negocio | acciones (`ACCION_*`), tipos de activo (`TIPO_*`), `ALIAS_ACCION` |
| Detalle del caso | XPath de la sección "Detalles" y sus 6 renglones |
| SAP | `SAP_URL`, login, barra de transacción, `SAP_TRANSACCION_POR_CASO` |
| Formularios SAP | `SAP_FORMULARIO_AS01_BRP` (columna → campo), `SAP_FORMULARIOS_POR_CASO` |
| Ajustes SAP | esperas entre clics, reintentos, formato de fecha y decimales |
| Seguridad SAP | `SAP_GUARDAR_REAL`, `SAP_XPATH_MENSAJE_ESTADO` |
| Respuesta Appian | `RESPUESTA_XPATH_*`, `APPIAN_RESPONDER_REAL` |

> **Selectores en lista.** Casi todos los XPath son **listas**
> (`["principal", "respaldo 1", ...]`): el bot prueba el primero y, si no
> encuentra nada, el siguiente. Para agregar un respaldo no hay que programar.

### 4.3 `ui/` — la ventana

- **`app_window.py` (`AppWindow`)**: la ventana raíz. Guarda las credenciales
  en memoria (`set_credenciales` / `get_credenciales`) y alterna entre las dos
  pantallas (`mostrar_login`, `mostrar_consola`).
- **`views/login_view.py` (`LoginView`)**: campos de usuario y clave. Al
  presionar Iniciar (`_on_iniciar`) guarda las credenciales, muestra la
  consola y arranca el bot.
- **`views/console_view.py` (`ConsoleView`)**: la consola en vivo.
  - Lanza el bot en un **hilo aparte** (`iniciar_ejecucion` → `_correr_bot`).
  - Cada 100 ms vacía la **cola** de mensajes y los pinta (`_consumir_cola`).
  - Botón **"Continuar (sin guardar)"**: el bot, cuando se detiene en SAP,
    deja un aviso especial en la cola (`ESPERAR_CONTINUAR`) y se queda
    esperando (`_esperar_continuar`). La ventana habilita el botón; al
    presionarlo (`_on_continuar`) el bot sigue.
- **`styles/theme.py` (`apply_theme`)**: colores de la marca.

> **¿Por qué un hilo y una cola?** Si el bot corriera en el mismo hilo de la
> ventana, la ventana se congelaría mientras espera a Appian o SAP. Además, la
> librería gráfica **no permite** tocar la ventana desde otro hilo: por eso el
> bot nunca toca la ventana directamente, solo deja mensajes en la cola.

### 4.4 `core/` — piezas de apoyo

| Archivo | Qué hace | Lo más importante |
|---|---|---|
| `logger.py` | Logs a **dos** destinos: archivo en `logs/` y consola de la ventana | `crear_logger(cola)`. Enmascara contraseñas (`enmascarar`) |
| `exceptions.py` | Errores **propios** del bot, con nombre claro | Ver tabla abajo |
| `models.py` | "Fichas" de datos que viajan entre flujos | Ver tabla abajo |
| `retry.py` | Repetir algo que falló por lentitud, esperando cada vez más | `ejecutar_con_reintentos(funcion, ...)` |
| `texto.py` | Comparar textos sin importar tildes/mayúsculas | `normalizar("Creación ")` → `"creacion"` |

**Errores propios (`exceptions.py`)** — todos heredan de `RPAError`:

| Error | Cuándo ocurre |
|---|---|
| `AppianError` (y sus hijos `BandejaError`, `SinAdjuntosError`, `CasoNoEncontradoError`, `ActividadTomadaError`, `TimeoutAppianError`) | Algo falló hablando con Appian |
| `MultiplesActivosError` | En "Detalles" hay más de un activo con acción |
| `MultiplesAdjuntosError` | La solicitud trae más de un Excel |
| `CasoOmitidoError` | Caso saltado a propósito (modo pruebas sin archivo) — **no es fallo** |
| `ValidacionError` | No hay validador para ese activo/acción, o no se pudo abrir el Excel |
| `PlantillaInvalidaError` | El Excel no cumple las reglas (lleva el detalle por fila) |
| `SapError` | Algo falló en SAP (campo que no aparece, guardar sin poder leer el resultado…) |

**Fichas de datos (`models.py`):**

| Ficha | Qué guarda | Quién la crea |
|---|---|---|
| `CasoBandeja` | número de solicitud, fecha de vencimiento, URL | `bandeja_reader` |
| `Solicitud` | número, tipo, acción, ruta del Excel, resultados de SAP por fila | Flujo 1 (o `modo_solo_sap`) |
| `ResultadoFila` / `ResultadoValidacion` | errores y avisos por fila; si la plantilla es válida | Flujo 2 |
| `ResultadoCaso` | si el caso salió bien, en qué paso quedó y por qué | orquestador |
| `ResumenLote` | totales de la ejecución | orquestador |

### 4.5 `appian/` — hablar con Appian

- **`appian_client.py` (`AppianClient`)**: una "envoltura" de la librería
  corporativa `an0016001_appian_flow`. Esa librería **no lanza errores**:
  responde `{success, message, data}`. Esta envoltura revisa `success` en
  **cada** llamada (`_validar`) y, si falló, lanza el error propio adecuado
  (`_clasificar_error`). También expone el navegador (`driver`) para que otros
  módulos lo usen.
  - `start(user, password)`: abre Appian e inicia sesión.
  - `get_case_data(...)`: lee la solicitud abierta y descarga sus adjuntos.
  - `cerrar()`: cierra el navegador (nunca lanza error).
- **`bandeja_reader.py` (`BandejaReader`)**: la librería no sabe leer la
  Bandeja de Actividades, así que esto se construyó aparte.
  - `listar_pendientes()`: espera a que carguen las filas (`_esperar_filas`)
    y las fechas (`_esperar_fecha_cargada`), filtra por "Nombre Del Flujo",
    guarda el enlace de cada solicitud y ordena por vencimiento.
  - `_buscar_con_respaldo`: prueba la lista de XPath en orden.
  - ⚠️ Hoy solo lee la **página visible** de la bandeja (ver PENDIENTES, P10).

### 4.6 `flujos/` — los pasos del negocio

#### `flujo1_appian.py` — Flujo 1: de la bandeja al Excel

`obtener_solicitud(client, caso)` hace, en orden:

1. (Modo reemplazo) busca tu archivo en `downloads_test/`; si no hay, **omite**
   el caso (`_buscar_archivo_prueba`).
2. Entra a la solicitud **directo por su URL** (`_abrir_caso_directo`).
3. Lee datos y descarga adjuntos (`client.get_case_data`).
4. Lee la sección **"Detalles"** y saca qué activo trae acción y cuál es
   (`_extraer_tipo_y_accion_detalle`). Los vacíos de Appian son guiones
   ("–", "-", "—").
5. Toma el único Excel adjunto (`_tomar_excel`); si no hay, intenta un clic
   de respaldo (`_descargar_adjunto_manual`).
6. Lo renombra a `PDA-7889_brp_creacion.xlsx` (`_normalizar_nombre_excel`).
7. (Modo reemplazo) usa una copia de tu archivo (`_usar_archivo_prueba`).
8. Devuelve una `Solicitud`.

Los pasos lentos van envueltos en **reintentos** (`core/retry.py`).

#### `flujo2_validar.py` — Flujo 2: validar el Excel

`validar_solicitud(solicitud)` pide al router el validador del activo/acción,
valida, escribe en el log cada error/aviso por fila (`_registrar_detalle`) y,
si la plantilla no es válida, lanza `PlantillaInvalidaError` (**todo o nada**).

#### `flujo3_sap.py` — Flujo 3: SAP fila por fila

`cargar_a_sap(sap, solicitud, esperar_continuar)`:

1. Busca la transacción y el **formulario** de ese activo/acción en
   `config.py`. Si no hay formulario, deja el caso "pendiente" sin entrar a SAP.
2. Lee las filas del Excel con la **misma lógica de la validación**
   (`leer_filas`).
3. Por cada fila:
   - (desde la 2ª) **recarga la página** de SAP para empezar limpio;
   - `/nAS01` y **llena el formulario** (`_llenar_formulario`): recorre los
     pasos de la configuración (campo, casilla, Enter, pestaña). Celdas vacías
     no se tocan;
   - si **se puede guardar** (`guardar_permitido`): Guardar y leer el
     mensaje → código del activo o error (`_guardar_y_leer`);
   - si **no**: se detiene, pide "Continuar" y sale sin guardar
     (`_supervisar` → `_salir_sin_guardar`: Atrás ×2 + confirmar);
   - si algo falla: anota `ERROR: ...` en esa fila y **sigue** con la
     siguiente (`_descartar_tras_error`).
4. Si se guardó de verdad, escribe la columna **"Código SAP"** en una copia
   del Excel en `salidas/` (`escribir_columna_codigo_sap`).

Funciones de apoyo: `valor_para_sap` (fechas a `05.10.2026`, decimales con
coma, enteros sin ".0").

**`guardar_permitido()` — el freno de seguridad:** devuelve `True` **solo** si
`SAP_GUARDAR_REAL = True` y **ningún** modo de prueba está encendido. Además,
`cargar_a_sap` se niega a guardar si no está configurado dónde leer el mensaje
de SAP.

#### `modo_solo_sap.py` — modo de prueba sin Appian

Reemplaza al Flujo 1 cuando `MODO_PRUEBAS_SOLO_SAP = True`:
`listar_archivos()` toma los Excel de `downloads_test/` y saca el activo y la
acción **del nombre** (`interpretar_nombre("prueba1_brp_creacion.xlsx")` →
`("prueba1", "brp", "creacion")`).

### 4.7 `validacion/` — las reglas del Excel

Pensado para que **agregar un activo nuevo sea casi solo describir su
plantilla**.

- **`router.py`**: un diccionario `VALIDADORES` que dice qué validador usa cada
  `(activo, acción)`. `resolver(tipo, accion)` lo entrega; si no existe, el
  caso no se procesa (nunca va a SAP un Excel sin validar).
- **`base_validador.py` (`BaseValidador`)**: el **motor común**:
  - abre la primera hoja (`.xlsx` / `.xlsm`);
  - ubica cada columna **por su encabezado**, no por la letra
    (`_ubicar_columnas`, comparando con `normalizar_encabezado`);
  - salta filas vacías (`_filas_de_datos`);
  - revisa obligatorios y largos máximos (`_validar_fila`);
  - llama a las reglas propias de cada plantilla (`reglas_fila`).
  - `leer_filas()` devuelve las filas tal cual para SAP.
  - Una columna se describe con `Columna(letra, encabezado, campo, tipo,
    max_largo, largo_es_error)`; los tipos son `OBLIGATORIO`, `CONDICIONAL`,
    `INFORMATIVO`, `NO_SE_VALIDA`.
  - "Vacío" = sin contenido, solo espacios o `0` (`es_vacia`).
- **`plantillas/brp_creacion.py` (`ValidadorBrpCreacion`)**: la lista de las
  29 columnas (A..AC) y dos reglas propias: cantidad (C) = 1 y vehículo (si
  hay matrícula M, el modelo U es obligatorio).

### 4.8 `sap/sap_webgui.py` — mover SAP en el navegador

SAP se usa en el navegador (SAP GUI for HTML), en una **pestaña nueva** del
mismo navegador de Appian. `SapWebGui` sabe **cómo** moverse; el **qué**
hacer está en `flujo3_sap.py` y en `config.py`.

| Función | Qué hace |
|---|---|
| `asegurar_sesion()` | La 1ª vez abre la pestaña de SAP e inicia sesión si hace falta; después solo cambia a esa pestaña |
| `recargar()` | Recarga la página (F5) y espera que SAP vuelva al inicio |
| `ir_a_transaccion("AS01")` | Escribe `/nAS01` + Enter en la barra |
| `escribir(xpath, texto)` | Borra el campo, escribe y sale con Tab |
| `clic`, `doble_clic_lento`, `enter` | Clics y teclas (el doble clic espera entre clics: SAP es lento) |
| `existe(xpath, segundos)` | ¿Aparece? (espera corta, no da error) |
| `leer_texto(xpath)` | Lee un texto de la pantalla |
| `volver_a_appian()` | Regresa a la pestaña de Appian |

Cómo se protege contra la "inestabilidad" de SAP:

- **Esperas activas** (`esperar` / `_esperar_alguno`): espera hasta que el
  elemento aparezca (máximo `TIMEOUT`), pero sigue apenas aparece.
- **Iframes** (`_localizar`): busca en la página y dentro de cada iframe.
- **Elementos vencidos** (`_actuar`): SAP redibuja la pantalla todo el tiempo;
  si un campo "se vence" justo al usarlo, lo vuelve a buscar y reintenta.
- **Errores cortos** (`_resumen`): solo la primera línea del error, sin el
  stacktrace del navegador.

### 4.9 `orquestador.py` — el director

- `ejecutar(user, password, cola, esperar_continuar)`: punto de entrada del
  bot. Crea el logger, revisa que no estén los dos modos de prueba a la vez,
  elige el recorrido, y en un `finally` **siempre** cierra el navegador y
  escribe el resumen.
- `_ejecutar_con_appian`: login → bandeja → cada caso.
- `_ejecutar_solo_sap`: archivos locales → cada archivo (sin Appian).
- `_procesar`: corre **un** caso (obtener solicitud → Flujo 2 → Flujo 3)
  dentro de su propio `try/except`, de modo que un caso malo nunca detiene el
  lote. Al final vuelve a la pestaña de Appian.
- `_emitir_resumen`: total, OK, fallidos (con motivo) y omitidos.

### 4.10 `tests/` — pruebas automáticas

Se corren con `python -m pytest tests -q` desde `rpa_activos_fijos/`. No
abren Appian ni SAP de verdad: usan **imitaciones** ("falsos") que anotan qué
hizo el bot.

| Archivo | Qué comprueba |
|---|---|
| `test_validacion_brp_creacion.py` | Todas las reglas de la plantilla BRP (obligatorios, vacíos, cantidad, vehículos, largos, columna AC, formatos, columnas corridas…) |
| `test_modo_pruebas_reemplazo.py` | El modo reemplazo: usa tu archivo, omite lo que no tiene archivo, no daña nada |
| `test_modo_solo_sap.py` | El modo solo SAP: nombres de archivo, no entra a Appian, nunca guarda |
| `test_sap_webgui.py` | La base de SAP con un navegador falso: login, pestañas, iframes, recarga, elementos vencidos, reglas de guardado |
| `test_sap_as01.py` | El llenado de AS01 con un SAP falso: orden de los campos, vacíos, casilla, supervisión, errores por fila, código SAP |
| `conftest.py` | Prepara el entorno (si la librería de Appian no está instalada, pone una de mentira) |

---

## 5. Conceptos clave (por qué está hecho así)

| Concepto | En pocas palabras | Dónde |
|---|---|---|
| **Separación de responsabilidades** | Cada carpeta hace una sola cosa | Toda la estructura |
| **Configuración afuera del código** | Lo que cambia vive en `config.py` | `config.py` |
| **Selectores en lista** | Principal + respaldos, sin programar | `config.py`, `bandeja_reader`, `sap_webgui` |
| **Selectores por texto o estructura en Appian** | Los IDs largos de Appian cambian; los textos no | `config.py` (Detalles) |
| **Esperas activas** | Esperar *hasta que* aparezca algo, no un tiempo fijo | `bandeja_reader`, `sap_webgui` |
| **Reintentos** | Repetir lo que falla por lentitud | `core/retry.py`, `sap_webgui._actuar` |
| **Errores propios** | Mensajes claros y clasificados | `core/exceptions.py` |
| **Aislamiento por caso y por fila** | Un fallo no detiene a los demás | `orquestador._procesar`, `flujo3_sap.cargar_a_sap` |
| **Interruptores de seguridad** | Nada real se guarda sin encenderlo a propósito | `config.py`, `guardar_permitido()` |
| **Hilo + cola** | La ventana nunca se congela ni se toca desde otro hilo | `console_view.py` |
| **Contraseñas solo en memoria** | Nunca van al log ni a un archivo | `logger.enmascarar`, `AppWindow` |

---

## 6. Recetas: cómo hacer los cambios más comunes

### Cambió un XPath de SAP o de Appian
Solo en `config.py`. Si quieres conservar el viejo, déjalo como **respaldo**
en la lista: `["nuevo", "viejo"]`.

### Agregar o corregir un campo del formulario de AS01
En `config.py`, `SAP_FORMULARIO_AS01_BRP`, agrega o edita una línea en el
lugar correcto del orden:
```python
{"tipo": "campo", "columna": "E", "nombre": "Marca", "xpath": ['//*[@id="..."]']},
```
Tipos de paso: `campo`, `casilla`, `enter`, `pestana`.

### SAP es lento y no alcanza a cambiar de pestaña
Sube `SAP_ESPERA_ENTRE_CLICS_SEG` en `config.py`.

### Agregar un activo/acción nuevo (ej. PRJ – Creación)
1. Pon la plantilla oficial y el Word en `plantillas/PRJ/`.
2. Crea `validacion/plantillas/prj_creacion.py` copiando `brp_creacion.py`:
   cambia la lista de columnas y las reglas propias.
3. Regístralo en `validacion/router.py` (`VALIDADORES`).
4. En `config.py`: su transacción en `SAP_TRANSACCION_POR_CASO` y su
   formulario en `SAP_FORMULARIOS_POR_CASO`.
5. Agrega sus pruebas en `tests/` y corre `python -m pytest tests -q`.

### Agregar una regla de validación a una plantilla
En el validador de esa plantilla (ej. `brp_creacion.py`), dentro de
`reglas_fila(fila, resultado_fila)`: lee la celda con `fila.get("X")` y
agrega el mensaje a `resultado_fila.errores` (invalida) o
`resultado_fila.advertencias` (solo avisa).

### Después de cualquier cambio
1. Corre las pruebas: `python -m pytest tests -q`.
2. Deja una línea en el Changelog de [ESTADO_PROYECTO.md](ESTADO_PROYECTO.md).
3. Si algo quedó pendiente, anótalo en [PENDIENTES.md](PENDIENTES.md).

---

## 7. Glosario

| Término | Significado |
|---|---|
| **XPath** | "Dirección" de un elemento en una página web, para que el bot lo encuentre |
| **Selenium** | La herramienta que controla el navegador (clics, escribir, leer) |
| **Driver** | El objeto de Selenium que representa al navegador |
| **SAP GUI for HTML / WebGUI** | SAP usado dentro del navegador |
| **Transacción** | Pantalla de SAP con un código (AS01 crear, AS02 modificar, AS06 borrar) |
| **`/n`** | Prefijo de SAP que abre una transacción desde cero |
| **Iframe** | Una página dentro de otra página; SAP a veces dibuja ahí su pantalla |
| **Elemento vencido** (*stale element*) | Un campo que el bot ya había encontrado pero que SAP volvió a dibujar |
| **Hilo** | Una tarea que corre en paralelo (el bot corre en uno distinto al de la ventana) |
| **Cola** | Un buzón por donde el bot le manda mensajes a la ventana |
| **Validador** | La clase que sabe revisar las reglas de una plantilla |
| **Interruptor** | Una variable `True`/`False` en `config.py` que enciende o apaga algo |
| **Prueba automática** | Código que verifica que otro código hace lo que debe |
