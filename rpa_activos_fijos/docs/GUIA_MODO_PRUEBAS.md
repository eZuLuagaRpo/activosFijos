# Guía — Modo pruebas (reemplazo del Excel)

> **Para qué sirve esta guía:** explica, paso a paso, cómo probar el bot con
> **solicitudes reales de Appian** usando un Excel preparado por ti, mientras
> los usuarios sigan adjuntando el formato viejo. También explica **para qué
> sirve cada interruptor** de `config.py`.
>
> **Alcance actual:** solo **Activos BRP – Creación** (carga masiva).
> Última actualización: 2026-09-29 (plantilla nueva con columna AC; la copia
> para SAP se envía sin AC; SAP etapa 1: entra y se detiene antes de Ejecutar).

---

## 1. ¿Qué es y por qué existe?

Hoy los usuarios todavía adjuntan en Appian el **formato viejo** de Excel.
Con ese formato la validación del bot **siempre falla**, así que no se puede
probar el flujo con los archivos reales.

El **modo pruebas** resuelve eso: el bot trabaja con Appian **de verdad**, pero
el Excel que valida y lleva a SAP es **uno que tú preparas** en el formato
nuevo.

| Parte del flujo | Modo normal | Modo pruebas |
|---|---|---|
| Iniciar sesión en Appian | Real | Real |
| Leer la bandeja | Real | Real |
| Elegir qué solicitudes trabajar | Todas las de "Parametrización de Activos" | **Solo las que tienen tu archivo** en `downloads_test/` |
| Abrir la solicitud y leer "Detalles" (activo y acción) | Real | Real |
| Descargar el adjunto del usuario | Real | Real (se guarda, pero **no se usa**) |
| Excel que se valida y va a SAP | El adjunto del usuario | **Tu archivo** (una copia) |

> Es **temporal**. Cuando los usuarios adjunten el formato nuevo, se deja
> apagado.

---

## 2. Qué hace y qué NO hace el bot hoy (importante)

**Sí hace:**
- Lee la bandeja, abre la solicitud, identifica activo y acción.
- Valida tu Excel con las reglas de BRP – Creación (incluida la columna AC).
- Prepara `carga_sap/CREAR (BRP).xlsm`: una copia de tu Excel con el
  **nombre exacto que exige SAP** y **SIN la columna AC** (SAP no la acepta
  en la carga masiva). Tu Excel conserva la columna AC.
- **Entra a SAP** en una pestaña nueva del mismo navegador (mismas
  credenciales de Appian), abre `Z_AM_MASIVA`, escoge "crear masivo", pega
  la ruta de `CREAR (BRP).xlsm` y hace clic en "Ejecución de test".
- **Se DETIENE ahí** y deja la pantalla de SAP quieta
  `SAP_PAUSA_REVISION_SEG` segundos (120 por defecto) para que la revises.
  Luego vuelve a Appian y sigue con la siguiente solicitud.

**NO hace (a propósito o porque aún no está construido):**
- **No hace clic en "Ejecutar" en SAP** (`SAP_EJECUTAR_REAL = False`): no
  se crea ningún activo.
- **No entra a AS02** a escribir la columna AC en cada activo (aún no está
  construido; cuando lo esté, guardar dependerá de `SAP_MODIFICAR_REAL`).
- **No responde ni cierra** solicitudes en Appian
  (`APPIAN_RESPONDER_REAL = False`; además esa parte aún no está construida).

Es decir: **hoy puedes correr el modo pruebas sin riesgo** de crear o
modificar activos ni de notificar a usuarios.

> 👀 **En la pausa de revisión confirma en SAP:** que está en `Z_AM_MASIVA`,
> que quedó marcada la opción de **crear masivo**, que la **ruta** del
> archivo es la de `carga_sap\CREAR (BRP).xlsm`, que SAP **acepta el archivo**
> (sin la columna AC) y cómo quedó **"Ejecución de test"** (según la usuaria
> funcional, un clic la deja deshabilitada).

---

## 3. Los interruptores de `config.py` (para qué sirve cada uno)

Todos están en `rpa_activos_fijos/config.py`. Los de **seguridad** vienen
en `False` y protegen contra cambios en sistemas REALES (no hay SAP de
pruebas y las solicitudes/usuarios de Appian son reales). **Solo se cambian
a propósito**, cuando se decida explícitamente que esa etapa ya está
validada.

| Interruptor | Valor por defecto | Qué controla | Con `False` | Con `True` |
|---|---|---|---|---|
| `MODO_PRUEBAS_REEMPLAZO` | `False` | **De dónde sale el Excel** | Flujo real: se usa el adjunto que el usuario subió a Appian | Se usa **tu** archivo de `downloads_test/`; solicitudes sin archivo se omiten |
| `SAP_EJECUTAR_REAL` 🔒 | `False` | **Crear** los activos en SAP (clic en "Ejecutar" de `Z_AM_MASIVA`) | El bot llega hasta "Ejecución de test" y **se detiene** (+ pausa de revisión). No crea nada | Hace clic en Ejecutar → **crea activos reales**. (Hoy el botón aún no está configurado: si se enciende, el bot se detiene con error sin ejecutar nada) |
| `SAP_MODIFICAR_REAL` 🔒 | `False` | **Guardar** en AS02 el valor de la columna AC en cada activo | (Cuando esté construido) llena AS02 pero **no guarda**. Permite probar con un activo ya existente sin cambiar nada | Guarda → **modifica activos reales**. (Aún no está construido) |
| `APPIAN_RESPONDER_REAL` 🔒 | `False` | **Finalizar** la solicitud en Appian (Appian notifica al usuario) | (Cuando esté construido) llena el formulario de respuesta pero **no** hace clic en Finalizar | Finaliza la solicitud → **el usuario recibe la respuesta**. (Aún no está construido) |

Y un **ajuste** (no es de seguridad):

| Ajuste | Por defecto | Para qué |
|---|---|---|
| `SAP_PAUSA_REVISION_SEG` | `120` | Segundos que el bot deja quieta la pantalla de SAP para que la revises, mientras `SAP_EJECUTAR_REAL = False` |

> 🔒 **Regla:** en una prueba normal **solo** se cambia
> `MODO_PRUEBAS_REEMPLAZO`. Los tres de seguridad se quedan en `False`.
> Cada uno se activará por primera vez en una prueba **supervisada** y
> acordada, de a uno.

---

## 4. Paso a paso

### Paso 1 — Escoge la(s) solicitud(es) a probar en Appian

1. Entra a Appian y abre la **Bandeja de Actividades**.
2. Busca una solicitud con **Nombre del Flujo = "Parametrización de Activos"**.
3. Ábrela y confirma en la sección **"Detalles"** que dice:
   **Activos BRP → Crear**.
   > Si es otro activo o acción (ej. PRJ, Modificar), el bot la va a marcar
   > como fallida con *"Aún no hay validación implementada"*. Por ahora solo
   > BRP – Creación.
4. Anota el **número de la solicitud** (columna "Número De La Solicitud"),
   por ejemplo `PDA-7889`.

### Paso 2 — Prepara el Excel en el formato nuevo

1. Copia la plantilla del **usuario** (la que tiene la columna AC):
   `plantillas/BRP/Plantilla Creación Activos BRP usuario.xlsm`
   > ⚠️ No uses `Plantilla Creación Activos BRP.xlsm` (sin "usuario"): esa
   > es el formato que recibe SAP (A..AB) y el bot la rechaza porque le
   > falta la columna AC.
2. Ábrela y llena **una fila por activo desde la fila 2**. No modifiques la
   fila 1 (encabezados).
3. Asegúrate de cumplir las reglas (si no, el bot la rechazará, lo cual
   también es una prueba válida):

   | Regla | Detalle |
   |---|---|
   | Obligatorios | **A** Clase, **B** Sociedad, **C** Cantidad, **D** Denominación, **F** No. Inventario, **H** Centro de Coste, **O** Estado, **W** Clave de Agrupamiento |
   | Vacío | Celda sin nada, solo espacios o con `0` cuenta como **vacía** |
   | Cantidad (C) | Debe ser exactamente **1** |
   | Vehículos | Si llenas **M** (Matrícula), el **U** (Modelo) es obligatorio |
   | Largos (solo aviso) | **T** Fabricante ≤ 30 caracteres · **U** Modelo ≤ 15 |
   | **AC** "TXT.NUM.PRAL.AF (Nombre y NIT del acreedor)" | Puede ir vacía. Si se llena: **máximo 50 caracteres (si se pasa, es ERROR)** |
   | S "ACREEDOR" | Es **otro** campo (no confundir con AC). Informativo |
   | Todo o nada | Si **una** fila falla, se rechaza el archivo completo |

4. Guárdala como **Libro de Excel habilitado para macros (`.xlsm`)**.
   Un `.xlsx` será rechazado (SAP exige `.xlsm`).

### Paso 3 — Nombra el archivo EXACTAMENTE con el número de la solicitud

El nombre debe ser **solo el número**, sin nada más:

| ✅ Correcto | ❌ Incorrecto | Por qué |
|---|---|---|
| `PDA-7889.xlsm` | `PDA-7889 (1).xlsm` | Tiene texto extra |
| `pda-7889.xlsm` (mayúsculas no importan) | `PDA-7889_brp.xlsm` | Tiene texto extra |
| | `PDA-7889.xlsx` | Lo encuentra, pero la validación lo rechaza por no ser `.xlsm` |
| | `PDA 7889.xlsm` | Falta el guion |

> 💡 **Tip Windows:** activa *Vista → Extensiones de nombre de archivo* en el
> Explorador para ver la extensión real y no terminar con
> `PDA-7889.xlsm.xlsm`.

**Solo un archivo por solicitud.** Si dejas `PDA-7889.xlsm` y `PDA-7889.xlsx`
a la vez, el bot marca error y no adivina cuál usar.

### Paso 4 — Pon el archivo en `downloads_test/`

Copia tu(s) archivo(s) a:

```
rpa_activos_fijos/downloads_test/
```

Puedes dejar varios (uno por cada solicitud que quieras probar). Las
solicitudes de la bandeja que **no** tengan archivo aquí se **omiten**: el bot
ni siquiera las abre.

### Paso 5 — Activa el modo en `config.py`

1. Abre `rpa_activos_fijos/config.py`.
2. Busca la sección **"MODO PRUEBAS — REEMPLAZO DEL EXCEL"**.
3. Cambia:

   ```python
   MODO_PRUEBAS_REEMPLAZO = False
   ```
   por:
   ```python
   MODO_PRUEBAS_REEMPLAZO = True
   ```
4. Guarda el archivo. **No toques** los interruptores de seguridad
   (`SAP_EJECUTAR_REAL`, `SAP_MODIFICAR_REAL`, `APPIAN_RESPONDER_REAL`).

> Si el bot ya estaba abierto, **ciérralo y ábrelo de nuevo**: la
> configuración se lee al arrancar.

### Paso 6 — Ejecuta el bot

```powershell
cd rpa_activos_fijos
..\venv\Scripts\activate
python app.py
```

Ingresa las credenciales de Appian y presiona **Ejecutar**.

> **¿Y el `.exe`?** El `.exe` lleva el `config.py` "congelado" al momento de
> construirlo. Para probar, es mucho más cómodo `python app.py`. Si
> necesitas el `.exe` en modo pruebas, hay que construirlo con el switch en
> `True` (y **nunca entregar ese** a la usuaria).

### Paso 7 — Revisa la consola

Al iniciar verás un aviso grande. Revisa que la lista de archivos sea la que
esperas:

```
WARNING | ######################################################################
WARNING | #  MODO PRUEBAS ACTIVO (MODO_PRUEBAS_REEMPLAZO = True en config.py)
WARNING | #  Se usarán los Excel de downloads_test en vez de los adjuntos de
WARNING | #  Appian. Solicitudes sin archivo allí se OMITEN.
WARNING | #  Archivos de prueba encontrados (1): PDA-7889.xlsm
WARNING | ######################################################################
```

Por cada solicitud con archivo verás algo así:

```
INFO    | Caso PDA-7889: navegación directa OK.
INFO    | Caso PDA-7889: Excel renombrado -> PDA-7889_brp_creacion.xls
WARNING | MODO PRUEBAS | Caso PDA-7889: se REEMPLAZA el adjunto de Appian (PDA-7889_brp_creacion.xls) por el archivo de prueba PDA-7889.xlsm -> copia de trabajo PDA-7889_brp_creacion_PRUEBA.xlsm
INFO    | Validando 'PDA-7889_brp_creacion_PRUEBA.xlsm' (hoja 'FORMATO') contra la plantilla BRP - Creación.
INFO    | Caso PDA-7889 | Flujo 2: Plantilla válida (2 filas)
INFO    | Caso PDA-7889: archivo para SAP preparado -> ...\carga_sap\CREAR (BRP).xlsm (copia de PDA-7889_brp_creacion_PRUEBA.xlsm, SIN la(s) columna(s) ['TXT.NUM.PRAL.AF (Nombre y NIT del acreedor)'])
INFO    | Abriendo SAP en una pestaña nueva: https://sap-erp.apps.bancolombia.corp/...
INFO    | SAP: iniciando sesión con el usuario '...'.        (o "SAP: sesión ya activa.")
INFO    | SAP: sesión iniciada.
INFO    | SAP: abriendo transacción Z_AM_MASIVA.
INFO    | SAP: ruta del archivo -> ...\carga_sap\CREAR (BRP).xlsm
WARNING | Caso PDA-7889: SAP listo para EJECUTAR, pero SAP_EJECUTAR_REAL = False: el bot se DETIENE aquí (no hace clic en Ejecutar). Pantalla disponible para revisión por 120 s.
INFO    | Caso PDA-7889 procesado correctamente (Detenido antes de Ejecutar en SAP (SAP_EJECUTAR_REAL = False)).
```

> SAP se abre **una sola vez** (con la primera solicitud válida); las
> siguientes reutilizan la misma pestaña. Si ninguna solicitud es válida,
> SAP ni se abre.

Y las que no tienen archivo:

```
INFO    | Caso PDA-7900 OMITIDO: MODO PRUEBAS: no hay archivo PDA-7900.xlsx/.xlsm en downloads_test; la solicitud se omite.
```

Al final, el resumen:

```
INFO    | === Resumen de la ejecución ===
WARNING | (Ejecución en MODO PRUEBAS: Excel reemplazados por los de downloads_test)
INFO    | Total de casos:   5
INFO    | Procesados OK:    1
INFO    | Fallidos:         0
INFO    | Omitidos:         4
```

- **Procesados OK:** tu Excel pasó la validación y SAP quedó listo para
  ejecutar (el bot se detuvo antes, a propósito).
- **Fallidos:** algo salió mal (ver "Detalle de casos fallidos" y la
  sección 6 de esta guía).
- **Omitidos:** solicitudes de la bandeja sin archivo tuyo. Es normal.

El mismo contenido queda guardado en `rpa_activos_fijos/logs/ejecucion_AAAAMMDD_HHMMSS.log`.

### Paso 8 — Revisa los archivos que quedaron

| Carpeta | Archivo | Qué es |
|---|---|---|
| `downloads_test/` | `PDA-7889.xlsm` | **Tu archivo. Nunca se modifica.** |
| `downloads/` | `PDA-7889_brp_creacion.xls` (o la extensión que tenga) | El adjunto **real** del usuario, descargado de Appian. Se conserva, no se usa. |
| `downloads/` | `PDA-7889_brp_creacion_PRUEBA.xlsm` | **Copia de trabajo** de tu archivo (A..AC, **con** la columna AC): es la que se valida y la que, más adelante, recibirá la columna "Código SAP" y se devolverá al usuario. |
| `carga_sap/` | `CREAR (BRP).xlsm` | Copia con el **nombre exacto que exige SAP**, **sin la columna AC** y sin nada de lo que haya a la derecha de AC (notas, etc.): queda A..AB, igual a la plantilla de SAP. Queda la de la **última** solicitud válida (cada una reemplaza a la anterior). |

> Puedes abrir `carga_sap/CREAR (BRP).xlsm` para confirmar que es tu archivo
> y que termina en la columna **AB (PERIODO)**. **Ciérralo antes de volver a
> ejecutar el bot**: si está abierto, el bot no puede reemplazarlo y marca el
> caso como fallido.

### Paso 9 — Cuando termines: APAGA el modo

1. En `config.py` vuelve a dejar:
   ```python
   MODO_PRUEBAS_REEMPLAZO = False
   ```
2. (Opcional) Borra tus archivos de `downloads_test/` para que no se usen
   por error en una prueba futura. **No borres el archivo `.gitkeep`.**
3. **Nunca** generes el `.exe` para la usuaria con el modo en `True`.

---

## 5. Checklist rápido

- [ ] La solicitud está en la bandeja y en "Detalles" dice **Activos BRP → Crear**.
- [ ] Excel hecho desde la **plantilla del usuario** (`... BRP usuario.xlsm`, con columna **AC**), llenado desde la fila 2.
- [ ] AC con **máximo 50 caracteres** (o vacía).
- [ ] Guardado como **`.xlsm`**.
- [ ] Nombre = **solo el número**: `PDA-7889.xlsm`.
- [ ] Archivo en **`rpa_activos_fijos/downloads_test/`** (uno por solicitud).
- [ ] `MODO_PRUEBAS_REEMPLAZO = True` en `config.py`, guardado.
- [ ] `SAP_EJECUTAR_REAL`, `SAP_MODIFICAR_REAL` y `APPIAN_RESPONDER_REAL` en **`False`** (no tocar).
- [ ] Bot reiniciado (`python app.py`).
- [ ] `carga_sap/CREAR (BRP).xlsm` **cerrado** en Excel.
- [ ] Al terminar: `MODO_PRUEBAS_REEMPLAZO = False`.

---

## 6. Problemas comunes

| Mensaje en la consola | Qué significa | Qué hacer |
|---|---|---|
| `Archivos de prueba encontrados (0): NINGUNO` | La carpeta está vacía o el archivo quedó en otro lado | Revisa que esté en `rpa_activos_fijos/downloads_test/` |
| `Caso PDA-XXXX OMITIDO: ... no hay archivo` (y tú sí pusiste uno) | El nombre no coincide exacto | Revisa el nombre (Paso 3): sin texto extra, con guion, sin doble extensión |
| `hay 2 archivos de prueba para PDA-XXXX ... Deja solo uno` | Hay `.xlsx` y `.xlsm` (u otro) con el mismo número | Deja solo el `.xlsm` |
| `Formato de archivo no soportado ('.xlsx'); la plantilla BRP - Creación debe ser .xlsm` | Guardaste como `.xlsx` | Guardar como "Libro habilitado para macros" (`.xlsm`) |
| `Faltan encabezados en la fila 1: AC 'TXT.NUM.PRAL.AF (Nombre y NIT del acreedor)'` | Usaste la plantilla de **SAP** (sin AC) en vez de la del **usuario** | Partir de `Plantilla Creación Activos BRP usuario.xlsm` |
| `Faltan encabezados en la fila 1: ...` (otra columna) | Se modificó/borró algún encabezado | Partir de nuevo de la plantilla del usuario |
| `fila N: Faltan campos obligatorios: ...` | Esa fila tiene obligatorios vacíos (o con 0) | Llenar las columnas indicadas |
| `fila N: C (Cantidad de Activos) debe ser 1 ...` | La cantidad no es 1 | Poner 1 (una fila = un activo) |
| `fila N: Es un vehículo ... y falta U (Modelo)` | Hay matrícula pero no modelo | Llenar U, o vaciar M si no es vehículo |
| `fila N: AC (Nombre y NIT del acreedor) tiene N caracteres (máximo 50)` | AC pasa de 50 caracteres (**error**, rechaza) | Acortarlo a 50 o menos |
| `La plantilla no tiene filas de datos` | Solo tiene encabezados | Llenar al menos una fila desde la 2 |
| `Aún no hay validación implementada para (tipo='prj', ...)` | La solicitud real no es BRP – Creación | Usar una solicitud de BRP – Creación |
| `no se pudo borrar la copia anterior 'CREAR (BRP).xlsm' (¿está abierta...?)` | Tienes abierto ese archivo | Cerrarlo en Excel/SAP y ejecutar de nuevo |
| Aviso `el Excel traía N columna(s) después de AC (fuera de la plantilla); se quitaron de la copia para SAP` | Había algo escrito a la derecha de AC | Nada: es solo informativo. SAP recibe A..AB y tu Excel conserva esas columnas |
| `no se pudieron quitar las columnas [...] de 'CREAR (BRP).xlsm'` | No se pudo quitar AC de la copia (no debería pasar si la validación pasó) | Revisar el log; la copia a medias se borra sola |
| `El caso ... no trae adjuntos` / `trae 2 Excel adjuntos` | Problema con el adjunto **real** de Appian | En modo pruebas el adjunto real se descarga igual (a propósito, para no ocultar fallas reales). Usa otra solicitud |
| Advertencia `T (Fabricante) tiene N caracteres (máximo 30)` | Solo aviso, **no** rechaza | Opcional: acortarlo |
| `SAP: no apareció la pantalla inicial de SAP (barra de transacción o login)` | SAP no cargó, o la pantalla de login usa otros IDs | Revisa que la URL abra a mano. Si pide login, captura los XPath de usuario, clave y botón y ponlos en `SAP_XPATH_LOGIN_*` (hoy son los estándar de SAP, **por confirmar**) |
| `SAP: no apareció la barra de transacción después del login (¿credenciales?)` | Usuario/clave rechazados, o SAP pidió algo más (ej. cambio de clave) | Entrar a mano a SAP una vez y revisar |
| `SAP: no apareció la opción 'creacion' masivo de Z_AM_MASIVA ...` (u otro elemento) | La transacción no abrió, o cambió el selector | Revisa en pantalla y actualiza el XPath en `config.py` (sección SAP) |
| Mientras corre, la pestaña de SAP queda "congelada" 2 minutos | Es la **pausa de revisión** a propósito | Puedes bajarla en `SAP_PAUSA_REVISION_SEG` |

---

## 7. Detalles técnicos (para quien mantenga el código)

- Switch: `MODO_PRUEBAS_REEMPLAZO` en `config.py` (por defecto `False`).
  Carpetas: `DOWNLOAD_TEST_DIR` (`downloads_test/`) y `CARGA_SAP_DIR`
  (`carga_sap/`). Nombre SAP: `NOMBRE_ARCHIVO_SAP`. Columnas que se quitan
  de la copia para SAP: `COLUMNAS_QUITAR_ANTES_DE_SAP` (por encabezado) y
  todo lo que esté después de `ULTIMA_COLUMNA_PLANTILLA`.
- Interruptores de seguridad: `SAP_EJECUTAR_REAL`, `SAP_MODIFICAR_REAL`,
  `APPIAN_RESPONDER_REAL` (sección 3).
- Código: `flujos/flujo1_appian.py` → `_buscar_archivo_prueba()` (antes de
  abrir la solicitud) y `_usar_archivo_prueba()` (después de descargar y
  renombrar el adjunto real). `orquestador.py` → `_avisar_modo_pruebas()` y
  conteo de omitidos (`CasoOmitidoError`). `flujos/flujo3_sap.py` →
  `preparar_archivo_sap()` (copia + quitar columnas) y `cargar_a_sap()`
  (etapa 1). `sap/sap_webgui.py` → pestaña, login, transacción,
  clics/escritura (con iframes y respaldos).
- Con el switch en `False` el comportamiento es exactamente el del flujo
  real (hay una prueba automática que lo verifica aunque existan archivos en
  `downloads_test/`).
- Pruebas: `python -m pytest tests -q` desde `rpa_activos_fijos/`.
- Todo lo del modo está marcado con el texto **"MODO PRUEBAS"** en el código,
  para encontrarlo y retirarlo fácil cuando ya no se necesite.
- Lo que falta por construir está en [PENDIENTES.md](PENDIENTES.md).
