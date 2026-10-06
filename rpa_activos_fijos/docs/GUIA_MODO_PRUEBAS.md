# Guía — Modos de prueba

> **Para qué sirve esta guía:** explica, paso a paso, cómo probar el bot
> mientras los usuarios sigan adjuntando el formato viejo de Excel. Hay **dos
> modos de prueba** (y en ninguno se guarda nada en SAP). También explica
> **para qué sirve cada interruptor** de `config.py`.
>
> **Alcance actual:** solo **Activos BRP – Creación**.
> Última actualización: 2026-10-05 (nuevo **modo solo SAP**; SAP activo por
> activo con AS01: el bot llena el formulario de cada activo, se detiene antes
> de Guardar y espera "Continuar").

---

## 0. ¿Qué modo uso?

| | **Modo REEMPLAZO** | **Modo SOLO SAP** |
|---|---|---|
| Interruptor en `config.py` | `MODO_PRUEBAS_REEMPLAZO = True` | `MODO_PRUEBAS_SOLO_SAP = True` |
| ¿Necesita una solicitud real de BRP en la bandeja de Appian? | **Sí** | **No** |
| ¿Entra a Appian? | Sí (bandeja, solicitud, descarga) | **No** |
| ¿De dónde saca el activo y la acción? | De la sección "Detalles" de la solicitud real | Del **nombre del archivo** |
| Nombre del Excel en `downloads_test/` | `PDA-7889.xlsx` (número de la solicitud) | `prueba1_brp_creacion.xlsx` |
| ¿Valida el Excel? | Sí | Sí |
| ¿Llena AS01 en SAP y pide "Continuar"? | Sí | Sí |
| ¿Guarda en SAP? | **Nunca** | **Nunca** |
| Sirve para | Probar **todo el recorrido** con solicitudes reales | Probar **la validación y SAP** cuando no hay solicitudes |
| Paso a paso | Sección 4 | Sección 5 |

> Los dos modos son **excluyentes**: si se encienden ambos, el bot no arranca
> y lo avisa en la consola.

---

## 1. ¿Por qué existen? (y cómo funciona el modo reemplazo)

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
| Excel que se valida y se usa en SAP | El adjunto del usuario | **Tu archivo** (una copia) |
| Guardar en SAP | Según `SAP_GUARDAR_REAL` | **PROHIBIDO siempre** |

> Es **temporal**. Cuando los usuarios adjunten el formato nuevo, se deja
> apagado.

---

## 2. Qué hace y qué NO hace el bot hoy (importante)

**Sí hace:**
- Lee la bandeja, abre la solicitud, identifica activo y acción.
- Valida tu Excel con las reglas de BRP – Creación (incluida la columna AC).
- **Entra a SAP** en una pestaña nueva del mismo navegador (mismas
  credenciales de Appian) y, **por cada fila** de tu Excel (= un activo):
  1. Abre `AS01` desde cero (`/nAS01`).
  2. Llena la pantalla inicial (Clase A, Sociedad B, Cantidad C) y presiona
     Enter.
  3. Llena el formulario completo, pasando por sus 5 pestañas (cada cambio
     de pestaña son **dos clics separados por 2 segundos**, porque SAP es
     lento). Las celdas **vacías** del Excel no se tocan; la casilla
     "Activo fijo paralizado" (N) solo se marca si la celda trae algo.
  4. **Se DETIENE antes de Guardar.** En la ventana del bot se habilita el
     botón amarillo **"Continuar (sin guardar)"** y el estado cambia a
     *"Esperando revisión en SAP"*. Revisa el formulario en SAP con calma.
  5. Al presionar **Continuar**, el bot sale **sin guardar** (Atrás dos veces
     + "salir sin guardar") y pasa al siguiente activo.
  6. Antes de cada activo (desde el segundo) **recarga la página de SAP**
     (como F5): SAP vuelve a su inicio con la pantalla limpia y el bot entra
     de nuevo a `AS01`. Sin esto, en la 1ª prueba real la segunda fila
     fallaba con *"stale element reference"* (SAP queda redibujando la
     pantalla después de salir de la transacción).
- Si algo falla en una fila (ej. un campo que no aparece), lo anota en el
  log y **sigue con la siguiente fila**.

**NO hace (a propósito):**
- **Nunca presiona Guardar en modo pruebas** — está prohibido por código,
  aunque alguien encienda `SAP_GUARDAR_REAL`. No se crea ningún activo.
- **No responde ni cierra** solicitudes en Appian
  (`APPIAN_RESPONDER_REAL = False`; además esa parte aún no está construida).

> 👀 **Qué revisar en cada pausa (en SAP):** que cada campo tenga el valor
> de la fila correcta (sobre todo la **fecha G**, que se escribe como
> `05.10.2026`, y los números con decimales), que estén las 5 pestañas
> llenas y que no haya avisos de SAP en la barra de abajo. Si algo se ve
> mal, anótalo: se corrige en `config.py` (`SAP_FORMULARIO_AS01_BRP`).

---

## 3. Los interruptores de `config.py` (para qué sirve cada uno)

Todos están en `rpa_activos_fijos/config.py`. Los de **seguridad** vienen
en `False` y protegen contra cambios en sistemas REALES (no hay SAP de
pruebas y las solicitudes/usuarios de Appian son reales). **Solo se cambian
a propósito**, cuando se decida explícitamente que esa etapa ya está
validada.

| Interruptor | Valor por defecto | Qué controla | Con `False` | Con `True` |
|---|---|---|---|---|
| `MODO_PRUEBAS_REEMPLAZO` | `False` | **De dónde sale el Excel** (con Appian) | Flujo real: se usa el adjunto que el usuario subió a Appian | Se usa **tu** archivo `downloads_test/PDA-7889.xlsx`; solicitudes sin archivo se omiten; **guardar en SAP queda prohibido** |
| `MODO_PRUEBAS_SOLO_SAP` | `False` | **Saltarse Appian** | Normal | **No entra a Appian**: toma los `downloads_test/<id>_<tipo>_<accion>.xlsx`, los valida y los lleva a SAP; **guardar en SAP queda prohibido** |
| `SAP_GUARDAR_REAL` 🔒 | `False` | **"Guardar" en SAP** (AS01 crea, AS02 modifica, AS06 borra activos REALES) | El bot llena el formulario de cada activo y **se detiene antes de Guardar**; botón "Continuar (sin guardar)" para seguir | Guarda → **crea/modifica/borra activos reales**. **Igual queda bloqueado si cualquier modo de prueba está encendido**, y también si no está configurado dónde leer el mensaje de SAP (`SAP_XPATH_MENSAJE_ESTADO`) |
| `APPIAN_RESPONDER_REAL` 🔒 | `False` | **Finalizar** la solicitud en Appian (Appian notifica al usuario) | (Cuando esté construido) llena el formulario de respuesta pero **no** hace clic en Finalizar | Finaliza la solicitud → **el usuario recibe la respuesta**. (Aún no está construido) |

Y unos **ajustes** de SAP (no son de seguridad):

| Ajuste | Por defecto | Para qué |
|---|---|---|
| `SAP_FORMULARIO_AS01_BRP` | (campos capturados) | Qué columna del Excel va en qué campo de AS01, en qué orden y en qué pestaña |
| `SAP_ESPERA_ENTRE_CLICS_SEG` | `2` | Segundos entre los dos clics de cada pestaña (y al salir sin guardar). Súbelo si SAP no alcanza a cambiar de pestaña |
| `SAP_REINTENTOS_ELEMENTO_VENCIDO` | `3` | Si SAP redibuja la pantalla justo cuando el bot va a usar un campo, el bot lo vuelve a buscar hasta este número de veces |
| `SAP_FORMATO_FECHA` | `%d.%m.%Y` (05.10.2026) | Cómo se escribe la fecha G "Capitalizado el" — **por confirmar** |
| `SAP_SEPARADOR_DECIMAL` | `,` | Separador de decimales al escribir números — **por confirmar** |

> 🔒 **Regla:** en una prueba **solo** se cambia el interruptor del modo que
> vas a usar (`MODO_PRUEBAS_REEMPLAZO` **o** `MODO_PRUEBAS_SOLO_SAP`). Los de
> seguridad se quedan en `False`. Cada uno se activará por primera vez en una
> prueba **supervisada** y acordada.
>
> 🛡️ **Bloqueo de SAP:** para que el bot presione Guardar hacen falta TODAS
> estas condiciones: `SAP_GUARDAR_REAL = True`, **ningún** modo de prueba
> encendido y `SAP_XPATH_MENSAJE_ESTADO` configurado. En cualquier modo de
> prueba es imposible guardar aunque alguien encienda el interruptor por
> error.

---

## 4. Paso a paso — Modo REEMPLAZO (con solicitudes reales de Appian)

### Paso 1 — Escoge la(s) solicitud(es) a probar en Appian

1. Entra a Appian y abre la **Bandeja de Actividades**.
2. Busca una solicitud con **Nombre del Flujo = "Parametrización de Activos"**.
   > ⚠️ Hoy el bot solo lee la **primera página** de la bandeja (ver
   > PENDIENTES.md, P10). Usa solicitudes que aparezcan en la página 1.
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
   > ⚠️ No uses `Plantilla Creación Activos BRP.xlsm` (sin "usuario"): era el
   > formato de la carga masiva (A..AB) y el bot la rechaza porque le falta
   > la columna AC.
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

4. Guárdala como **`.xlsx`** o **`.xlsm`** (las dos sirven). Un `.xls`
   viejo se rechaza.

### Paso 3 — Nombra el archivo EXACTAMENTE con el número de la solicitud

El nombre debe ser **solo el número**, sin nada más:

| ✅ Correcto | ❌ Incorrecto | Por qué |
|---|---|---|
| `PDA-7889.xlsm` | `PDA-7889 (1).xlsm` | Tiene texto extra |
| `PDA-7889.xlsx` | `PDA-7889_brp.xlsm` | Tiene texto extra |
| `pda-7889.xlsm` (mayúsculas no importan) | `PDA 7889.xlsm` | Falta el guion |
| | `PDA-7889.xls` | Lo encuentra, pero la validación lo rechaza (formato viejo) |

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
   (`SAP_GUARDAR_REAL`, `APPIAN_RESPONDER_REAL`).

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
INFO    | Validando 'PDA-7889_brp_creacion_PRUEBA.xlsm' (hoja 'FORMATO') con la plantilla BRP - Creación.
INFO    | Caso PDA-7889 | Flujo 2: Plantilla válida (2 filas)
INFO    | Leyendo filas de 'PDA-7889_brp_creacion_PRUEBA.xlsm' (hoja 'FORMATO') con la plantilla BRP - Creación.
INFO    | Caso PDA-7889: 2 activo(s) para AS01. Guardar en SAP: NO (se detiene antes de Guardar en cada activo).
INFO    | Abriendo SAP en una pestaña nueva: https://sap-erp.apps.bancolombia.corp/...
INFO    | SAP: sesión iniciada.                              (o "SAP: sesión ya activa.")
INFO    | SAP: abriendo transacción AS01.
INFO    | SAP: fila 2, A (Clase de activo fijo) -> BRP01
...                                                          (un renglón por campo)
WARNING | Caso PDA-7889, fila 2: formulario de AS01 lleno. NO se guarda. Revisa SAP y presiona 'Continuar'.
        <- aquí el bot ESPERA tu clic en "Continuar (sin guardar)"
INFO    | SAP: página recargada.
INFO    | SAP: sesión ya activa.
INFO    | SAP: abriendo transacción AS01.
...                                                          (fila 3)
INFO    | Caso PDA-7889 procesado correctamente (Revisado en SAP SIN guardar (2 fila(s))).
```

> SAP se abre **una sola vez** (con la primera solicitud válida); las
> siguientes reutilizan la misma pestaña.

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

- **Procesados OK:** tu Excel pasó la validación y se revisaron sus activos
  en SAP **sin guardar**.
- **Fallidos:** algo salió mal (ver "Detalle de casos fallidos" y la
  sección 7 de esta guía).
- **Omitidos:** solicitudes de la bandeja sin archivo tuyo. Es normal.

El mismo contenido queda guardado en `rpa_activos_fijos/logs/ejecucion_AAAAMMDD_HHMMSS.log`.

### Paso 8 — Revisa los archivos que quedaron

| Carpeta | Archivo | Qué es |
|---|---|---|
| `downloads_test/` | `PDA-7889.xlsm` | **Tu archivo. Nunca se modifica.** |
| `downloads/` | `PDA-7889_brp_creacion.xls` (o la extensión que tenga) | El adjunto **real** del usuario, descargado de Appian. Se conserva, no se usa. |
| `downloads/` | `PDA-7889_brp_creacion_PRUEBA.xlsm` | **Copia de trabajo** de tu archivo: es la que se valida y de la que el bot lee cada fila para SAP. |

> En modo pruebas **no** se genera el Excel con "Código SAP" (no se guarda
> nada en SAP). Cuando se guarde de verdad, saldrá en `salidas/` como
> `PDA-7889_brp_creacion_RESPUESTA.xlsm`.

### Paso 9 — Cuando termines: APAGA el modo

1. En `config.py` vuelve a dejar:
   ```python
   MODO_PRUEBAS_REEMPLAZO = False
   ```
2. (Opcional) Borra tus archivos de `downloads_test/` para que no se usen
   por error en una prueba futura. **No borres el archivo `.gitkeep`.**
3. **Nunca** generes el `.exe` para la usuaria con el modo en `True`.

---

## 5. Paso a paso — Modo SOLO SAP (sin Appian)

Para cuando **no hay solicitudes de BRP en Appian** y quieres probar la
validación y la transacción de SAP con un Excel tuyo.

### Paso 1 — Prepara el Excel

Igual que en el modo reemplazo (sección 4, Paso 2): parte de
`plantillas/BRP/Plantilla Creación Activos BRP usuario.xlsm`, llena una fila
por activo desde la fila 2 y guárdalo como `.xlsx` o `.xlsm`. Puedes poner
**datos inventados**: no se guarda nada en SAP.

### Paso 2 — Nómbralo con el activo y la acción

Como no hay solicitud de Appian, el bot saca el activo y la acción del
**final del nombre**:

```
<lo_que_quieras>_<activo>_<accion>.xlsx      (o .xlsm)
```

| ✅ Correcto | ❌ Incorrecto | Por qué |
|---|---|---|
| `prueba1_brp_creacion.xlsx` | `prueba1_brp.xlsx` | Falta la acción |
| `activos_octubre_brp_creacion.xlsm` | `_brp_creacion.xlsx` | Falta la primera parte |
| `Prueba_BRP_Creacion.xlsx` (mayúsculas no importan) | `prueba1_brp_creacion.xls` | Formato viejo |
| | `PDA-7889.xlsx` | Ese es el nombre del **otro** modo |

- La **primera parte** es libre (sirve para reconocer la prueba en el log;
  puede tener guiones bajos).
- **Hoy solo funciona `_brp_creacion`**. Cuando se configuren otras
  acciones serán, por ejemplo, `_brp_modificacion` o `_brp_eliminacion`.
- Puedes dejar **varios** archivos: se procesan en orden alfabético.
- Los archivos con otro nombre se **omiten** (aparecen en el log y en
  "Omitidos").

### Paso 3 — Ponlo en `downloads_test/`

```
rpa_activos_fijos/downloads_test/prueba1_brp_creacion.xlsx
```

> Si en esa carpeta quedaron archivos del modo reemplazo (`PDA-7889.xlsx`),
> no pasa nada: este modo los omite. Pero para no confundirte, mejor deja
> solo los de la prueba que vas a hacer.

### Paso 4 — Activa el modo en `config.py`

1. Abre `rpa_activos_fijos/config.py`.
2. Busca la sección **"MODO PRUEBAS — SOLO SAP"** y cambia:
   ```python
   MODO_PRUEBAS_SOLO_SAP = True
   ```
3. Verifica que `MODO_PRUEBAS_REEMPLAZO = False` (no pueden estar los dos en
   `True`) y **no toques** `SAP_GUARDAR_REAL` ni `APPIAN_RESPONDER_REAL`.
4. Guarda. Si el bot estaba abierto, ciérralo y ábrelo de nuevo.

### Paso 5 — Ejecuta y supervisa

```powershell
cd rpa_activos_fijos
..\venv\Scripts\activate
python app.py
```

Ingresa **tus credenciales** (las mismas de Appian: el bot las usa para
SAP) y presiona **Ejecutar**. El bot:

1. **No entra a Appian**: abre el navegador y va directo a SAP en una
   pestaña nueva.
2. Valida tu Excel (si tiene errores, lo verás en la consola y no va a SAP).
3. Por cada fila: llena AS01, **se detiene** y habilita **"Continuar (sin
   guardar)"**. Revisa en SAP (ver "Qué revisar en cada pausa", sección 2) y
   presiona Continuar.

Así se ve la consola:

```
WARNING | ######################################################################
WARNING | #  MODO PRUEBAS SOLO SAP (MODO_PRUEBAS_SOLO_SAP = True en config.py)
WARNING | #  NO se entra a Appian. Se usan los Excel de downloads_test
WARNING | #  nombrados <id>_<tipo>_<accion>.xlsx (ej. prueba1_brp_creacion.xlsx).
WARNING | #  En SAP NO se guarda nada (se detiene antes de Guardar).
WARNING | ######################################################################
INFO    | MODO SOLO SAP: 1 archivo(s) para probar: prueba1_brp_creacion.xlsx
WARNING | MODO SOLO SAP: 'PDA-7889.xlsx' no sigue el formato <id>_<tipo>_<accion>.xlsx (ej. prueba1_brp_creacion.xlsx); se omite.
INFO    | Validando 'prueba1_brp_creacion.xlsx' (hoja 'FORMATO') con la plantilla BRP - Creación.
INFO    | Caso prueba1 | Flujo 2: Plantilla válida (2 filas)
INFO    | Caso prueba1: 2 activo(s) para AS01. Guardar en SAP: NO (se detiene antes de Guardar en cada activo).
INFO    | Abriendo SAP en una pestaña nueva: https://sap-erp.apps.bancolombia.corp/...
...
WARNING | Caso prueba1, fila 2: formulario de AS01 lleno. NO se guarda. Revisa SAP y presiona 'Continuar'.
        <- aquí el bot ESPERA tu clic en "Continuar (sin guardar)"
WARNING | Caso prueba1, fila 3: formulario de AS01 lleno. NO se guarda. Revisa SAP y presiona 'Continuar'.
INFO    | Caso prueba1 procesado correctamente (Revisado en SAP SIN guardar (2 fila(s))).
INFO    | === Resumen de la ejecución ===
WARNING | (Ejecución en MODO PRUEBAS SOLO SAP: sin Appian, sin guardar en SAP)
INFO    | Total de casos:   2
INFO    | Procesados OK:    1
INFO    | Fallidos:         0
INFO    | Omitidos:         1
```

> En este modo el "caso" se llama como la primera parte del nombre del
> archivo (`prueba1`), no con un número de solicitud.

### Paso 6 — Al terminar: APAGA el modo

1. Vuelve a dejar `MODO_PRUEBAS_SOLO_SAP = False` en `config.py`.
2. Tu archivo **nunca se modifica**; bórralo de `downloads_test/` si ya no
   lo necesitas (**no borres `.gitkeep`**).
3. **Nunca** generes el `.exe` para la usuaria con este modo en `True`.

---

## 6. Checklist rápido

**Modo REEMPLAZO:**


- [ ] La solicitud está en la **página 1** de la bandeja y en "Detalles" dice **Activos BRP → Crear**.
- [ ] Excel hecho desde la **plantilla del usuario** (`... BRP usuario.xlsm`, con columna **AC**), llenado desde la fila 2.
- [ ] AC con **máximo 50 caracteres** (o vacía).
- [ ] Guardado como **`.xlsx`** o **`.xlsm`**.
- [ ] Nombre = **solo el número**: `PDA-7889.xlsm` / `PDA-7889.xlsx`.
- [ ] Archivo en **`rpa_activos_fijos/downloads_test/`** (uno por solicitud).
- [ ] `MODO_PRUEBAS_REEMPLAZO = True` en `config.py`, guardado.
- [ ] `SAP_GUARDAR_REAL` y `APPIAN_RESPONDER_REAL` en **`False`** (no tocar).
- [ ] Tener a la vista la ventana del bot **y** la pestaña de SAP: en cada activo hay que presionar **"Continuar (sin guardar)"**.
- [ ] Bot reiniciado (`python app.py`).
- [ ] Al terminar: `MODO_PRUEBAS_REEMPLAZO = False`.

**Modo SOLO SAP:**

- [ ] Excel desde la **plantilla del usuario** (con columna **AC**), filas desde la 2, `.xlsx` o `.xlsm`.
- [ ] Nombre `<lo_que_quieras>_brp_creacion.xlsx` (ej. `prueba1_brp_creacion.xlsx`).
- [ ] Archivo en **`rpa_activos_fijos/downloads_test/`**.
- [ ] `MODO_PRUEBAS_SOLO_SAP = True` y `MODO_PRUEBAS_REEMPLAZO = False`.
- [ ] `SAP_GUARDAR_REAL` y `APPIAN_RESPONDER_REAL` en **`False`** (no tocar).
- [ ] Bot reiniciado (`python app.py`); ventana del bot y pestaña de SAP a la vista.
- [ ] Al terminar: `MODO_PRUEBAS_SOLO_SAP = False`.

---

## 7. Problemas comunes

| Mensaje en la consola | Qué significa | Qué hacer |
|---|---|---|
| `Archivos de prueba encontrados (0): NINGUNO` | La carpeta está vacía o el archivo quedó en otro lado | Revisa que esté en `rpa_activos_fijos/downloads_test/` |
| `Caso PDA-XXXX OMITIDO: ... no hay archivo` (y tú sí pusiste uno) | El nombre no coincide exacto | Revisa el nombre (Paso 3): sin texto extra, con guion, sin doble extensión |
| `hay 2 archivos de prueba para PDA-XXXX ... Deja solo uno` | Hay `.xlsx` y `.xlsm` (u otro) con el mismo número | Deja solo uno |
| `Formato de archivo no soportado ('.xls'); la plantilla BRP - Creación debe ser .xlsx o .xlsm` | Guardaste en formato viejo | Guardar como `.xlsx` o `.xlsm` |
| `Faltan encabezados en la fila 1: AC 'TXT.NUM.PRAL.AF (Nombre y NIT del acreedor)'` | Usaste la plantilla de la masiva (sin AC) | Partir de `Plantilla Creación Activos BRP usuario.xlsm` |
| `Faltan encabezados en la fila 1: ...` (otra columna) | Se modificó/borró algún encabezado | Partir de nuevo de la plantilla del usuario |
| `fila N: Faltan campos obligatorios: ...` | Esa fila tiene obligatorios vacíos (o con 0) | Llenar las columnas indicadas |
| `fila N: C (Cantidad de Activos) debe ser 1 ...` | La cantidad no es 1 | Poner 1 (una fila = un activo) |
| `fila N: Es un vehículo ... y falta U (Modelo)` | Hay matrícula pero no modelo | Llenar U, o vaciar M si no es vehículo |
| `fila N: AC (Nombre y NIT del acreedor) tiene N caracteres (máximo 50)` | AC pasa de 50 caracteres (**error**, rechaza) | Acortarlo a 50 o menos |
| `La plantilla no tiene filas de datos` | Solo tiene encabezados | Llenar al menos una fila desde la 2 |
| `Aún no hay validación implementada para (tipo='prj', ...)` | La solicitud real no es BRP – Creación | Usar una solicitud de BRP – Creación |
| `MODO_PRUEBAS_REEMPLAZO y MODO_PRUEBAS_SOLO_SAP están encendidos a la vez` | Los dos modos están en `True` | Deja solo uno en `True` |
| `MODO SOLO SAP: 0 archivo(s) para probar: NINGUNO` | No hay archivos con el formato `<id>_<tipo>_<accion>.xlsx` | Revisa el nombre (sección 5, Paso 2) y la carpeta |
| `MODO SOLO SAP: '...' no sigue el formato ... se omite` | Ese archivo tiene otro nombre | Renómbralo, o ignóralo si no es de esta prueba |
| El bot no avanza y el estado dice *"Esperando revisión en SAP"* | Es la pausa de supervisión, a propósito | Revisa SAP y presiona **"Continuar (sin guardar)"** |
| Aviso `SAP redibujó la pantalla mientras se usaba ...; se vuelve a buscar (intento N de 3)` | SAP cambió la pantalla justo cuando el bot iba a escribir | Nada: el bot lo reintenta solo. Si pasa mucho, súbelo en `SAP_REINTENTOS_ELEMENTO_VENCIDO` |
| `fila N: ... stale element reference ...` | SAP siguió redibujando después de los reintentos | Avísalo con el log: puede requerir más espera en ese paso |
| `No se pudo recargar la página de SAP` | El navegador no pudo recargar (o un aviso lo impidió) | Revisa la pestaña de SAP; el bot sigue con la siguiente fila |
| `fila N: SAP: no apareció ... tras 120s` | Un campo / pestaña de AS01 no apareció (XPath distinto, o SAP mostró un aviso) | Mira la pantalla de SAP y la barra de abajo; ajusta el XPath en `SAP_FORMULARIO_AS01_BRP`. El bot ya siguió con la siguiente fila |
| `SAP: no apareció la pantalla inicial de SAP (barra de transacción o login)` | SAP no cargó, o la pantalla de login usa otros IDs | Revisa que la URL abra a mano. Si pide login, captura los XPath de usuario, clave y botón y ponlos en `SAP_XPATH_LOGIN_*` (hoy son los estándar, **por confirmar**) |
| `No se pudo salir del formulario sin guardar` | No apareció el botón Atrás o la ventana de confirmación | Revisa `SAP_XPATH_BOTON_ATRAS` / `SAP_XPATH_CONFIRMAR_SALIR_SIN_GUARDAR` |
| `El caso ... no trae adjuntos` / `trae 2 Excel adjuntos` | Problema con el adjunto **real** de Appian | En modo pruebas el adjunto real se descarga igual (a propósito, para no ocultar fallas reales). Usa otra solicitud |
| Advertencia `T (Fabricante) tiene N caracteres (máximo 30)` | Solo aviso, **no** rechaza | Opcional: acortarlo |

---

## 8. Detalles técnicos (para quien mantenga el código)

- Switches: `MODO_PRUEBAS_REEMPLAZO` y `MODO_PRUEBAS_SOLO_SAP` en
  `config.py` (por defecto `False`; excluyentes). Carpeta:
  `DOWNLOAD_TEST_DIR` (`downloads_test/`).
- Modo solo SAP: `flujos/modo_solo_sap.py` (`interpretar_nombre`,
  `listar_archivos`) y `orquestador._ejecutar_solo_sap()`: crea
  `AppianClient` SOLO para abrir el navegador (sin `start()`, sin Appian) y
  pasa cada archivo por `_procesar()` (Flujo 2 → Flujo 3).
- Interruptores de seguridad: `SAP_GUARDAR_REAL`, `APPIAN_RESPONDER_REAL`
  (sección 3). Regla de guardado: `flujos/flujo3_sap.guardar_permitido()`
  (True solo con `SAP_GUARDAR_REAL = True` y ningún modo de prueba).
- Código: `flujos/flujo1_appian.py` → `_buscar_archivo_prueba()` (antes de
  abrir la solicitud) y `_usar_archivo_prueba()` (después de descargar y
  renombrar el adjunto real). `orquestador.py` → `_avisar_modo_pruebas()` y
  conteo de omitidos (`CasoOmitidoError`). `flujos/flujo3_sap.py` →
  `cargar_a_sap()` (fila por fila con el formulario de `config.py`),
  `_supervisar()` / `_salir_sin_guardar()`, `escribir_columna_codigo_sap()`.
  `sap/sap_webgui.py` → pestaña, login, transacción, clic, doble clic lento,
  Enter, escritura (con iframes y respaldos), `recargar()` entre filas y
  `_actuar()` (reintento ante elementos vencidos; errores en una sola línea). Botón "Continuar":
  `ui/views/console_view.py` (`_esperar_continuar`, aviso por la cola).
- Con el switch en `False` el comportamiento es exactamente el del flujo
  real (hay una prueba automática que lo verifica aunque existan archivos en
  `downloads_test/`).
- Pruebas: `python -m pytest tests -q` desde `rpa_activos_fijos/`.
- Todo lo del modo está marcado con el texto **"MODO PRUEBAS"** en el código,
  para encontrarlo y retirarlo fácil cuando ya no se necesite.
- Lo que falta por construir está en [PENDIENTES.md](PENDIENTES.md).
