# CONFIGURACIÓN MANUAL — RPA "Parametrización de Activos Fijos"

> **Para quién es este documento:** para ti, que estás empezando en RPA. Aquí
> está, paso a paso y sin dar nada por sabido, **todo lo que hay que conseguir o
> configurar a mano** para que el bot funcione con el Appian real. El código ya
> está listo; lo que falta son **datos del entorno** (URL, selectores, labels y
> el mapeo de columnas).
>
> Cada cosa dice **qué es**, **por qué se necesita** y **dónde exactamente se
> pega** en el código.

---

## Índice

1. [Datos básicos de configuración](#1-datos-básicos-de-configuración)
2. [Cómo capturar un selector (XPath) con F12](#2-cómo-capturar-un-selector-xpath-con-f12)
3. [Selectores de la Bandeja de Actividades](#3-selectores-de-la-bandeja-de-actividades)
4. [Labels del detalle del caso (tipo de activo y acción)](#4-labels-del-detalle-del-caso)
5. [¿Llegan solo activos fijos? (pendiente de confirmar)](#5-llegan-solo-activos-fijos-pendiente-de-confirmar)
6. [Mapeo de columnas Appian → macro SAP](#6-mapeo-de-columnas-appian--macro-sap)
7. [Qué pedirle / sacar del PC de la compañera](#7-qué-pedirle--sacar-del-pc-de-la-compañera)
8. [Empaquetado a .exe y el driver de Edge](#8-empaquetado-a-exe-y-el-driver-de-edge)
9. [Checklist final](#9-checklist-final)

---

## 1. Datos básicos de configuración

Todo esto se edita en el archivo **`config.py`** (la raíz del proyecto).

| Dato | Variable en `config.py` | Qué poner |
|---|---|---|
| **URL de Appian** | `APPIAN_URL` | La dirección **exacta** que usa la compañera. Ej: `https://bancolombia.appiancloud.com/suite/` |
| **Navegador** | `BROWSER` | `"edge"` (confirmar que ella usa Edge) |
| **Timeout general** | `TIMEOUT` | Segundos de espera por elemento (por defecto 90) |
| **Timeout de descargas** | `TIMEOUT_FILES` | Segundos máximos por descarga (por defecto 600) |

Ejemplo (así se ve en `config.py`):

```python
APPIAN_URL = "https://CAMBIAR-POR-URL-REAL-DE-APPIAN"   # <-- reemplazar
BROWSER = "edge"
TIMEOUT = 90
TIMEOUT_FILES = 600
```

> ⚠️ **Nunca** escribas usuario ni contraseña en `config.py`. Esas se piden en
> la pantalla de login cada vez que se ejecuta.

---

## 2. Cómo capturar un selector (XPath) con F12

Un **selector** es una "dirección" que le dice a Selenium **dónde está** un
elemento en la página (una fila, un enlace, un botón). Usamos **XPath**. Así se
captura:

1. Abre **Edge** e ingresa a Appian (a la Bandeja de Actividades o al detalle del
   caso, según lo que quieras capturar).
2. Presiona **F12** para abrir las **DevTools** (herramientas de desarrollador).
3. Haz clic en el ícono de la **flechita** ↖ (arriba a la izquierda del panel de
   DevTools) o presiona **Ctrl+Shift+C**. El cursor pasa a "modo inspección".
4. **Haz clic sobre el elemento** que te interesa (por ejemplo, una fila de la
   tabla o el enlace del ID del caso). En el panel de DevTools se resaltará la
   línea de HTML correspondiente.
5. Sobre esa línea resaltada, **clic derecho → Copy → Copy XPath** (Copiar →
   Copiar XPath). También existe "Copy full XPath" (XPath completo); prefiere el
   **XPath normal**, es más robusto.
6. Ya tienes el XPath en el portapapeles. Ahora lo pegas donde corresponda (ver
   secciones siguientes).

> 💡 **Consejo:** un buen XPath es corto y usa atributos estables (como `id`,
> `role`, `aria-label` o clases con nombre). Evita XPath larguísimos llenos de
> `div[3]/div[2]/...` porque se rompen al mínimo cambio de la página.

> 💡 **Probar un XPath:** en DevTools, abre la pestaña **Console** y escribe
> `$x("TU_XPATH_AQUI")`. Si devuelve una lista con elementos, el XPath funciona.

---

## 3. Selectores de la Bandeja de Actividades

La librería **no** sabe leer la bandeja; eso lo hace nuestro
`appian/bandeja_reader.py`, que usa los XPath definidos en `config.py`. Ahora
mismo son **placeholders** (marcados con `# TODO: CAPTURAR SELECTOR REAL`).

Necesitas capturar **tres cosas** (una es opcional):

### 3.1 Filas de la tabla → `BANDEJA_XPATH_FILAS`

Es el XPath que selecciona **cada fila** de la tabla de la bandeja. Captura una
fila cualquiera (paso 2) y generaliza para que tome todas.

```python
# En config.py
BANDEJA_XPATH_FILAS = [
    "//table//tbody/tr",      # <-- reemplaza por el XPath real de las filas
    "//div[@role='row']",     # respaldo (déjalo o ajústalo)
]
```

> Puedes poner **varios**: el bot prueba el primero y, si no encuentra nada,
> pasa al siguiente (selectores de respaldo).

### 3.2 El ID del caso dentro de la fila → `BANDEJA_XPATH_ID_EN_FILA`

Es el XPath del **enlace o celda que contiene el ID** (ej. `PDA-2389`), pero
**relativo a la fila** (por eso empieza con `.//`).

```python
BANDEJA_XPATH_ID_EN_FILA = [
    ".//a",         # <-- reemplaza por el XPath real (relativo, empieza con .//)
    ".//td[1]//a",  # respaldo
    ".//td[1]",     # respaldo
]
```

Además, el bot reconoce el ID dentro del texto con una **expresión regular**:

```python
BANDEJA_REGEX_CASE_ID = r"[A-Z]{2,5}-\d{2,}"   # reconoce cosas como PDA-2389
```

Si el prefijo real no es `PDA` sino otro, igual funciona (acepta 2–5 letras).
Solo ajústala si el formato es muy distinto.

### 3.3 (Opcional) Filtro por tipo → `BANDEJA_XPATH_FILTRO`

Solo si confirmas que a la bandeja llegan casos **mezclados** (ver sección 5).
De momento se deja vacío y **no se usa**.

---

## 4. Labels del detalle del caso

Cuando el bot abre un caso, la librería devuelve una tabla con dos columnas:
`label` (nombre del campo) y `value` (su valor). De ahí sacamos el **tipo de
activo** y la **acción**. Necesitamos el **texto EXACTO** del label tal como
aparece en Appian.

**Cómo obtenerlo:** abre un caso real en Appian y mira cómo se llaman esos dos
campos. Copia el texto tal cual (con mayúsculas y tildes). Luego pégalo en
`config.py`:

```python
LABELS_TIPO_ACTIVO = [
    "Tipo de Activo",   # <-- reemplaza por el texto EXACTO que veas en Appian
    "Tipo Activo",      # puedes dejar variantes por si cambia entre formularios
]

LABELS_ACCION = [
    "Acción",           # <-- reemplaza por el texto EXACTO
    "Tipo de Acción",
]
```

> El bot normaliza el texto (minúsculas, sin tildes), así que no importa si hay
> pequeñas diferencias de mayúsculas/acentos. Pero el nombre base sí debe coincidir.

### 4.1 Alias de negocio (valores)

El **valor** que devuelve Appian (ej. "Diferidos y Renovaciones", "Creación")
se traduce a un nombre interno con las tablas `ALIAS_TIPO_ACTIVO` y
`ALIAS_ACCION` de `config.py`. Si aparece un valor nuevo que el bot no reconoce,
lo verás en el log con un aviso; solo agrégalo a la tabla:

```python
ALIAS_TIPO_ACTIVO = {
    "diferidos y renovaciones": TIPO_DIFERIDOS,   # ejemplo ya incluido
    # "texto nuevo que salga en appian": TIPO_XXX,
}
```

---

## 5. ¿Llegan solo activos fijos? (pendiente de confirmar)

**Supuesto actual del bot:** a la usuaria le llegan en la bandeja **solo**
solicitudes de activos fijos. **Esto hay que confirmarlo con ella.**

- Si es **cierto**: no hay que hacer nada.
- Si llegan **mezcladas** con otros procesos: hay que **filtrar**. Para eso:
  1. En `config.py` pon `BANDEJA_FILTRAR_POR_TIPO = True`.
  2. Captura el selector del control de filtro (sección 3.3).
  3. Implementa el filtrado en `appian/bandeja_reader.py`, método
     `_aplicar_filtro_tipo` (ya está el "hueco" listo con instrucciones).

---

## 6. Mapeo de columnas Appian → macro SAP

Este es el dato de negocio más importante que **falta**. Es la "tabla de
traducción" que dice: *la columna X del Excel de Appian va a la columna Y de la
macro de SAP*, y esto cambia según el **tipo de activo** y la **acción**.

Se configura en **`transformacion/mapping/mapeo.py`**. Ahora está vacío
(placeholder). Cuando tengas el mapeo real, se llena así:

```python
MAPEO = {
    ("mascaras", "creacion"): {
        "columna_macro_1": "columna_appian_A",
        "columna_macro_2": "columna_appian_B",
    },
    # Caso especial de diferidos (creación en 2 pasos):
    ("diferidos", "creacion_as01"): { ... },   # paso 1: creación
    ("diferidos", "creacion_as02"): { ... },   # paso 2: modificación
}
```

> **Formato:** por cada combinación `(tipo, acción)` un diccionario
> `{ "nombre en la macro" : "nombre en el Excel de Appian" }`.

Mientras el mapeo esté vacío, el bot **igual genera** un Excel de salida, pero
con los datos **sin transformar** (y avisa en el log). Así puedes ir probando el
resto del flujo antes de tener el mapeo definitivo.

### 6.1 Plantillas de la macro

Si la macro real de SAP es un `.xlsx` con un formato/encabezados específicos,
coloca esos archivos en `transformacion/mapping/` y regístralos en
`PLANTILLAS_MACRO` (en `mapeo.py`):

```python
PLANTILLAS_MACRO = {
    "creacion": "plantilla_creacion.xlsx",       # <-- nombre del archivo real
    "modificacion": "plantilla_modificacion.xlsx",
    "eliminacion": "plantilla_eliminacion.xlsx",
}
```

---

## 7. Qué pedirle / sacar del PC de la compañera

El bot se probará en el PC de la compañera. Consigue de ahí (o pídeselo):

1. **Las macros/plantillas reales** de creación, modificación y eliminación
   (los `.xlsx` de destino). → Van a `transformacion/mapping/` (sección 6.1).
   *Por qué:* sin el formato real de salida no se puede armar el archivo para SAP.
2. **Ejemplos reales del Excel** que Appian adjunta, **uno por cada tipo de
   activo** (máscaras, BRP, PRJ, diferidos, mejoras).
   *Por qué:* para conocer los nombres de columna reales y construir el mapeo.
3. **La URL exacta de Appian** que ella usa. → `APPIAN_URL` (sección 1).
   *Por qué:* el bot no puede entrar sin la dirección correcta.
4. **IDs de solicitudes reales** de prueba (ej. `PDA-2389`).
   *Por qué:* para probar `search_case` / `get_case_data` con casos que existen.
5. **Confirmar que su navegador es Edge** y que **puede descargar archivos**
   (sin bloqueos de política).
   *Por qué:* la librería descarga los adjuntos con el navegador; si está
   bloqueado, no hay Excel que procesar.
6. **Confirmar el supuesto de la bandeja** (sección 5): ¿solo activos fijos o
   mezclados?

> 🔐 **Nunca** le pidas su contraseña por escrito ni la guardes en ningún
> archivo. Ella la escribe directamente en la pantalla de login del bot.

---

## 8. Empaquetado a .exe y el driver de Edge

La compañera probablemente **no tiene Python**, así que se le entrega un
**ejecutable**. Se genera con `build.bat`.

### Pasos

```powershell
cd rpa_activos_fijos
..\venv\Scripts\activate
build.bat
```

Esto crea `dist\RPA_Activos_Fijos\`. Esa **carpeta completa** (no solo el .exe)
es la que se copia al PC de la compañera.

- **Modo carpeta (`--onedir`, el que usa `build.bat`):** más estable con Selenium
  y con los assets. Recomendado.
- **Modo un archivo (`--onefile`):** hay una variante comentada al final de
  `build.bat`. Genera un único `.exe`, pero **arranca más lento** y **algunos
  antivirus corporativos lo marcan** como sospechoso.

### ⚠️ El driver de Edge (importante)

Selenium 4.36 resuelve el driver de Edge **en tiempo de ejecución** con
"Selenium Manager", y eso **necesita internet la primera vez** para descargarlo.
En un PC corporativo cerrado esto puede fallar. Soluciones:

1. **Recomendado:** descarga el `msedgedriver.exe` que **coincida con la versión
   de Edge** de la compañera (mira la versión en `edge://settings/help`) desde el
   sitio oficial de Microsoft, y déjalo **junto al `.exe`** (dentro de
   `dist\RPA_Activos_Fijos\`). Selenium suele encontrarlo si está en el PATH o en
   la misma carpeta.
2. **Alternativa:** correr el bot una vez en un PC con internet para que descargue
   el driver, y luego moverlo.

> Anota la versión de Edge de la compañera antes de empaquetar.

### ✅ Paso de verificación

**Prueba el `.exe` en un equipo SIN Python** antes de darlo por bueno. Si abre la
ventana, muestra el login y la consola, y no se cae al arrancar, el empaquetado
está bien (independiente de que el login real de Appian requiera la
configuración de las secciones anteriores).

---

## 9. Checklist final

Marca cada punto cuando lo completes:

- [ ] `APPIAN_URL` con la URL real (sección 1)
- [ ] `BROWSER` confirmado como Edge (sección 1)
- [ ] `BANDEJA_XPATH_FILAS` capturado (sección 3.1)
- [ ] `BANDEJA_XPATH_ID_EN_FILA` capturado (sección 3.2)
- [ ] `LABELS_TIPO_ACTIVO` con el texto real (sección 4)
- [ ] `LABELS_ACCION` con el texto real (sección 4)
- [ ] Supuesto de la bandeja confirmado (sección 5)
- [ ] Macros/plantillas reales colocadas en `transformacion/mapping/` (sección 6.1)
- [ ] `MAPEO` de columnas completado (sección 6)
- [ ] Ejemplos de Excel de Appian por cada tipo (sección 7)
- [ ] IDs de prueba reales (sección 7)
- [ ] Descarga de archivos permitida en el PC (sección 7)
- [ ] `.exe` generado con `build.bat` (sección 8)
- [ ] `msedgedriver` resuelto para el PC corporativo (sección 8)
- [ ] `.exe` probado en un PC sin Python (sección 8)

> Cuando termines los puntos de configuración, el bot debería poder ejecutar el
> Flujo 1 y el Flujo 2 de principio a fin. El Flujo 3 (carga a SAP) se
> implementará en una entrega posterior.
