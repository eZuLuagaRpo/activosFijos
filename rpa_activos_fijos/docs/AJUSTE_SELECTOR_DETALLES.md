# Ajuste futuro (opcional) — Selector de la sección "Detalles"

> **Contexto:** hoy (2026-08-11) el bot identifica la sección "Detalles"
> (donde está el tipo de activo + acción) buscándola por su **texto visible**
> ("Detalles"), no por un ID de Appian. Es un ajuste **deliberado**, no un
> error a medio resolver — abajo explico por qué. Este documento es solo
> para el día que quieras intentar algo más específico.
>
> **Por ahora el código se queda tal como está.** No hay nada urgente que
> hacer con esto.

---

## Por qué se cambió de ID a texto

El primer selector que capturaste fue un ID largo de Appian:
`f868ae114fc7b69e3840a9e5db2ddaee_sectionContents`. Funcionó en el caso
donde lo capturaste, pero falló en el **100% de los casos** de la corrida
siguiente (5 de 5, todos casos distintos). La explicación más probable:
Appian genera esos IDs **dinámicamente en cada render** de la página — no
son un identificador fijo de "la sección Detalles", son casi un número
aleatorio de esa instancia puntual. Por eso no sirve para otros casos ni
otras sesiones.

## ¿Vale la pena buscar otro selector mañana?

Puedes intentarlo, pero con esta expectativa clara: **es poco probable que
otro ID sirva mejor**, porque el problema no fue "capturaste mal el ID",
fue que Appian genera uno distinto cada vez que carga la página. Lo que sí
vale la pena buscar es un atributo **semántico y estable**, en vez de un ID
al azar. De mejor a peor:

1. **`data-testid`** — si el contenedor de "Detalles" (o algo cerca) tiene
   `data-testid="algo-descriptivo"`, eso SÍ suele ser estable (lo pone el
   desarrollador de Appian a propósito, no se genera solo). Es el mismo
   patrón con el que la librería encuentra menús como "Seguimiento de
   Solicitudes" o "Bandeja de Actividades" internamente.
2. **`data-text`** — parecido al anterior; algunos elementos de Appian lo
   usan (los menús del sitio, por ejemplo).
3. **Un `id` que NO parezca un hash largo y sin sentido** — si ves algo
   corto y legible (ej. `id="detalles-activos"`), podría ser estable. Si es
   una cadena larga de letras/números al azar
   (`f868ae114fc7b69e3840a9e5db2ddaee...`), casi seguro es generado y no
   sirve, igual que el anterior.

## Cómo capturarlo (y CONFIRMARLO antes de mandármelo)

1. Abre un caso real en Appian, F12, inspecciona el **contenedor completo**
   de la sección "Detalles" — la caja que incluye el título "Detalles" **y**
   los 6 renglones de tipos de activo debajo. No un renglón suelto, no solo
   el título.
2. Revisa sus atributos en el HTML: busca `data-testid`, `data-text`, o un
   `id` con pinta de fijo (ver lista de arriba).
3. **El paso que faltó la vez pasada, y es el más importante**: antes de
   mandármelo, prueba el mismo XPath en la Console de DevTools
   (`$x("TU_XPATH_AQUI")`) en **al menos 2 o 3 casos distintos** (no solo
   uno). Si el mismo XPath encuentra el elemento en los 3, es una señal
   fuerte de que sí es estable. Si en alguno no aparece, ese selector tiene
   el mismo problema que el anterior — mejor no lo mandes y seguimos con el
   de texto.
4. Si no encuentras nada mejor que el `id` hasheado: **no pasa nada**. El
   selector por texto que quedó puesto ya funciona razonablemente bien (es
   el mismo patrón con el que la propia librería encuentra sus secciones) y
   se puede quedar así indefinidamente.

## Dónde se hace el ajuste en el código (cuando tengas algo mejor)

Es un cambio de **una sola línea**, en `config.py`:

```python
# Buscar esta variable (sección "DETALLE DEL CASO — SECCIÓN Detalles"):
DETALLE_XPATH_SECCION_ACTIVOS = (
    "//div[@role='region' and .//h2[normalize-space(.)='Detalles']]"
)

# Reemplazar por tu selector nuevo, por ejemplo:
DETALLE_XPATH_SECCION_ACTIVOS = "//*[@data-testid='TU-VALOR-AQUI']"
```

No hay que tocar nada más. `flujos/flujo1_appian.py`
(`_leer_lineas_seccion_activos`) usa esa variable directamente, sin
importarle qué tipo de selector sea — XPath por ID, por texto o por
`data-testid` funcionan igual de bien para el código, la única diferencia es
qué tan estable es cada uno.

Mándame el XPath cuando lo tengas (y confírmame que probaste que funciona
en varios casos) y lo dejo listo.
