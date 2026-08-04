# GUÍA — Cómo extraer los selectores y etiquetas de Appian

> **Para qué sirve este archivo:** paso a paso para que captures, desde Appian
> real, todo lo que el bot necesita para leer la **Bandeja de Actividades** y
> el **detalle del caso**. Al final tienes una **plantilla** para pegar lo que
> encuentres y pasármelo. Con eso yo lo dejo listo en `config.py`.
>
> Esta guía cubre **dos cosas distintas** (no las confundas):
> 1. **Selectores (XPath)** — "direcciones" para que Selenium encuentre un
>    elemento en la página. Se necesitan para la **tabla de la bandeja**.
> 2. **Etiquetas (texto)** — el nombre exacto de un campo tal como aparece en
>    pantalla (ej. "Tipo de Activo"). Se necesitan para el **detalle del
>    caso**, y ahí **NO hace falta capturar XPath** (te explico por qué en la
>    Parte 2).

---

## Antes de empezar: cómo capturar un XPath con F12

(Resumen rápido; el detalle completo con capturas está en
[CONFIGURACION_MANUAL.md](CONFIGURACION_MANUAL.md#2-cómo-capturar-un-selector-xpath-con-f12).)

1. Abre Appian en **Edge**, en la pantalla que quieras inspeccionar (bandeja o
   detalle de un caso).
2. Presiona **F12** para abrir las DevTools.
3. Presiona **Ctrl+Shift+C** (o clic en la flechita ↖) para entrar en "modo
   inspección".
4. Haz clic sobre el elemento que te interesa (una fila, una celda, un link).
   Se resalta la línea de HTML en el panel.
5. Clic derecho sobre esa línea resaltada → **Copy → Copy XPath**.
6. Para probar que funciona: en la pestaña **Console** de las DevTools, escribe
   `$x("TU_XPATH_AQUI")` y presiona Enter. Si devuelve un array con 1 o más
   elementos (`Array(1)`, `Array(20)`...), el XPath sirve. Si devuelve
   `Array(0)`, no encontró nada.

> 💡 Prefiere el XPath "normal" (`Copy XPath`) sobre el "completo" (`Copy full
> XPath`): es más corto y más resistente a cambios pequeños en la página.

---

## Parte 1 — Bandeja de Actividades (selectores XPath)

Ya confirmamos que en la bandeja necesitamos leer **4 cosas por cada fila**.
Para las 3 primeras necesito el XPath; para la fecha, además del XPath
necesito saber en qué formato se ve.

### 1.1 Las filas de la tabla

Haz clic sobre **una fila cualquiera** (en una zona sin link, por ejemplo un
espacio vacío de la fila, o sobre el `<tr>` en el HTML directamente) y copia
su XPath. Debe ser un XPath que, generalizado, tome **todas** las filas (por
ejemplo algo como `//table//tbody/tr`, pero puede variar).

- Pruébalo con `$x(...)` y confirma que el número de elementos que devuelve
  coincide con el número de solicitudes que ves en pantalla.

### 1.2 Columna "Numero De La Solicitud" (el ID, ej. PDA-7133)

Haz clic **directamente sobre el texto/link del ID** dentro de una fila.
Copia su XPath. Este debe quedar en dos versiones:
- El **XPath completo** tal como te lo da el navegador (para que yo entienda
  la estructura).
- Si puedes, identifica también la versión **relativa a la fila** (empieza
  con `.//`, por ejemplo `.//td[1]//a`) — si no sabes armarla, no te
  preocupes, con el XPath completo yo la deduzco.

### 1.3 Columna "Nombre Del Flujo"

Igual que el punto anterior: clic sobre el texto de esa celda (en una fila
que diga "Parametrización de Activos"), copiar XPath.

- Además, copia el **texto exacto** que aparece ahí (mayúsculas y tildes tal
  cual), por si hay variantes de nombre.

### 1.4 Columna "Fecha de Vencimiento"

Clic sobre el texto de esa celda, copiar XPath.

- Anota también un par de **ejemplos del formato** en que se ve la fecha,
  copiando el texto tal cual aparece en pantalla. Por ejemplo:
  `03/08/2026`, o `2026-08-03`, o `3 ago 2026`, etc. Esto es importante
  porque el bot necesita saber cómo interpretarla para poder ordenar por
  prioridad.

> 💡 Si varias columnas de la bandeja tienen una estructura de celda parecida
> (por ejemplo todas son `<td>` con un `<span>` adentro), probablemente el
> XPath de una te sirve de referencia para armar el de las otras. Aun así,
> captúralas todas por separado para no adivinar.

---

## Parte 2 — Detalle del caso/actividad (etiquetas de texto)

Cuando el bot abre un caso, la librería de Appian **ya lee automáticamente**
toda la tabla de campos del detalle (algo como una tabla de dos columnas:
nombre del campo y su valor) y nos la entrega lista. **Por eso aquí NO
necesitas capturar XPath** — solo necesito el **texto exacto** de dos campos.

### Pasos

1. Entra a un caso real de Parametrización de Activos (clic en su ID desde la
   bandeja).
2. Busca en el detalle el campo que indica el **tipo de activo** (ej.
   "Tipo de Activo", "Máscaras", "BRP", "PRJ", "Diferidos", "Mejoras"...).
   Copia el **nombre del campo tal cual está escrito** (con mayúsculas y
   tildes exactas). Anota también **qué valor tenía** en ese caso puntual.
3. Haz lo mismo con el campo que indica la **acción** (ej. "Acción" →
   "Creación", "Modificación", "Eliminación"...). Nombre del campo + valor.
4. **Repite esto en varios casos distintos** (idealmente uno por cada tipo de
   activo: máscaras, BRP, PRJ, diferidos, mejoras, y si puedes uno de cada
   acción: creación/modificación/eliminación). Esto es clave porque:
   - Confirma que el **nombre del campo** es siempre el mismo (o si cambia
     entre formularios, cuáles son las variantes).
   - Me da **todos los valores posibles** que puede traer cada campo, para
     completar `ALIAS_TIPO_ACTIVO` y `ALIAS_ACCION` en `config.py` (la tabla
     que traduce el texto de Appian a un nombre interno del bot).

> ⚠️ Si un valor no está en la tabla de alias, el bot **no se cae**, pero
> avisa en el log y no sabe qué handler usar para ese caso. Por eso conviene
> cubrir todas las variantes que existan desde el principio.

---

## Cómo me lo entregas

Lo más fácil: **copia esta plantilla, complétala y pégamela en el chat**
(no hace falta que sea código, texto plano está perfecto). También puedes
adjuntar capturas de pantalla del detalle del caso si prefieres que yo lea
los campos directamente de la imagen.

```
=== BANDEJA DE ACTIVIDADES ===

Filas de la tabla (XPath):
  <pegar aquí>

Numero De La Solicitud dentro de la fila (XPath):
  <pegar aquí>

Nombre Del Flujo dentro de la fila (XPath):
  <pegar aquí>
Texto exacto visto para activos fijos:
  <ej. "Parametrización de Activos">

Fecha de Vencimiento dentro de la fila (XPath):
  <pegar aquí>
Formato de fecha visto en pantalla (2-3 ejemplos):
  <ej. "03/08/2026", "04/08/2026">

=== DETALLE DEL CASO ===

Caso de ejemplo #1: <ID, ej. PDA-7133>
  Label "tipo de activo" (texto exacto): <...>
  Valor visto:                          <...>
  Label "acción" (texto exacto):        <...>
  Valor visto:                          <...>

Caso de ejemplo #2: <ID>
  Label "tipo de activo" (texto exacto): <...>
  Valor visto:                          <...>
  Label "acción" (texto exacto):        <...>
  Valor visto:                          <...>

(repite por cada tipo de activo / acción que puedas revisar)
```

Con esa información completo en `config.py`:
`BANDEJA_XPATH_FILAS`, `BANDEJA_XPATH_ID_EN_FILA`, los selectores nuevos de
"Nombre Del Flujo" y "Fecha de Vencimiento" (y la lógica de filtro/orden en
`bandeja_reader.py`), y `LABELS_TIPO_ACTIVO` / `LABELS_ACCION` /
`ALIAS_TIPO_ACTIVO` / `ALIAS_ACCION`.

> 📌 Esto **no incluye** todavía el mapeo de columnas Appian → macro SAP (los
> Excel adjuntos); eso quedó pendiente para otro momento, según lo hablado.

---

## Checklist

- [ ] XPath de las filas de la bandeja
- [ ] XPath del ID (Numero De La Solicitud) dentro de la fila
- [ ] XPath de Nombre Del Flujo dentro de la fila + texto exacto esperado
- [ ] XPath de Fecha de Vencimiento dentro de la fila + formato de fecha
- [ ] Label exacto de "tipo de activo" + valores vistos (varios casos)
- [ ] Label exacto de "acción" + valores vistos (varios casos)
