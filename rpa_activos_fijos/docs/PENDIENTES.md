# PENDIENTES — RPA Activos Fijos

> **Para qué sirve:** lista viva y detallada de TODO lo que falta por
> construir o definir, con el contexto necesario para retomarlo sin
> explicaciones. Complementa a [ESTADO_PROYECTO.md](ESTADO_PROYECTO.md)
> (qué está hecho y por qué) y a [GUIA_MODO_PRUEBAS.md](GUIA_MODO_PRUEBAS.md).
>
> **Cómo se usa:** cuando algo se resuelve, se marca ✅ con la fecha y se
> deja una línea en el Changelog de ESTADO_PROYECTO.md. Si aparece algo
> nuevo, se agrega aquí.
>
> Alcance actual: **Activos BRP – Creación** (carga masiva). Los demás
> activos/acciones se trabajan después, uno por uno.
> Última actualización: 2026-09-29.

---

## 0. Resumen del flujo completo (cómo debe quedar BRP – Creación)

```
APPIAN (preparación, todas las solicitudes)
  1. Leer bandeja → descargar TODOS los Excel → validar TODOS (con AC) ✅ P1 (hoy caso por caso, ver P8)
     (inválidos → responder en Appian de una vez)                         🔲 P10

POR CADA SOLICITUD VÁLIDA (uno por uno, por vencimiento)
  2. Copia para SAP SIN la columna extra → carga_sap/CREAR (BRP).xlsm   ✅ P2
  3. SAP Z_AM_MASIVA: crear masivo → ruta → "Ejecución de test"         ✅ etapa 1
  4. Clic en Ejecutar                                                    🔲 P3 (DE ÚLTIMO)
  5. Leer/exportar resultado → código SAP por activo (o error)           🔲 P3, P4
  6. Excel del usuario + columna "Código SAP"                            🔲 P5
  7. AS02 activo por activo: escribir la columna extra y guardar         🔲 P6
  8. Responder en Appian (Exitoso / No Exitoso + comentario + Excel)     🔲 P9
  Registro de estado por solicitud y por activo durante todo el proceso  🔲 P7
```

Interruptores en `config.py` (todos en `False` hasta que se decida
explícitamente; explicados en GUIA_MODO_PRUEBAS.md, sección 3):
`MODO_PRUEBAS_REEMPLAZO`, `SAP_EJECUTAR_REAL`, `SAP_MODIFICAR_REAL` (P6) y
`APPIAN_RESPONDER_REAL`.

**Prioridad acordada:** la bitácora / registro de estado (P7) es
importante para el usuario → construirla antes de activar Ejecutar o AS02.

---

## P1 — Plantilla nueva de BRP – Creación (columna extra AC) ✅ 2026-09-29

> **Resuelto:** AC validada como informativa, > 50 caracteres = ERROR;
> plantilla sin AC se rechaza (encabezado faltante). Fila 3 sobrante de la
> plantilla nueva borrada (confirmado por el usuario). Pruebas en
> `tests/test_validacion_brp_creacion.py`. Lo de abajo queda como contexto.

**Contexto (2026-09-29):** la plantilla que carga SAP (A..AB) no trae el
campo "TXT.NUM.PRAL.AF (Nombre y NIT del acreedor)" y SAP no acepta
columnas adicionales. Por eso el usuario enviará la plantilla de siempre +
**una columna extra al final**, que el bot usa después en AS02 (P6).

**Definido:**
- Plantilla oficial nueva: `plantillas/BRP/Plantilla Creación Activos BRP usuario.xlsm`
  (hoja "FORMATO", 29 columnas A..AC, con macros).
- Columna **AC**, encabezado exacto: `TXT.NUM.PRAL.AF (Nombre y NIT del acreedor)`.
- Clasificación: **informativa** (puede venir vacía), **máximo 50
  caracteres**. Si se excede → definir si advertencia o error (ver abajo).
- La columna **S "ACREEDOR" es OTRO campo**: se deja igual (informativa).
  No confundir aunque el Word la describa parecido.
- Obligatorios y demás reglas V1–V5: sin cambios (fuente de verdad = Word
  por nombre de campo).

**Decisiones tomadas (2026-09-29):**
- Fila 3 con valores sueltos en la plantilla nueva → eran restos: se
  borraron del archivo (edición puntual de esa fila; macros y comentarios
  intactos).
- Largo > 50 en AC → **ERROR** (invalida la fila).
- El usuario SIEMPRE envía la plantilla con AC → una plantilla sin la
  columna AC se rechaza por encabezado faltante (V3).
- Si AC está vacía en una fila: se asume que ese activo **no** pasa por
  AS02 (confirmar al construir P6).

---

## P2 — Copia para SAP sin la columna extra ✅ 2026-09-29

**Hecho:** `flujo3_sap.preparar_archivo_sap()` copia el Excel como
`carga_sap/CREAR (BRP).xlsm` y le quita las columnas de
`COLUMNAS_QUITAR_ANTES_DE_SAP` (config.py), ubicadas por **encabezado**.
Conserva macros. Si falla, borra la copia a medias. El Excel del usuario NO
se toca (conserva AC para P6 y la respuesta). Prueba automática: la copia
queda con los MISMOS encabezados que `plantillas/BRP/Plantilla Creación
Activos BRP.xlsm` (la de SAP).

**Por vigilar / decidir:**
- 1ª prueba real: openpyxl re-escribe el archivo; confirmar que SAP lo lee
  igual que el original (valores, macros, formato).
- ✅ Decidido (2026-09-29, opción b): todo lo que esté **a la derecha de
  AC** (ej. notas en AD, AE) se QUITA de la copia para SAP
  (`ULTIMA_COLUMNA_PLANTILLA` en config.py) y se deja un aviso en el log.
  El Excel del usuario lo conserva; la validación ya lo ignoraba.

---

## P3 — SAP etapa 2: Ejecutar + cuadro de resultados 🔲 (DE ÚLTIMO)

**Hecho (etapa 1):** entra a SAP, `/nZ_AM_MASIVA`, crear masivo, pega la
ruta, clic en "Ejecución de test", se detiene (`SAP_EJECUTAR_REAL = False`)
y pausa `SAP_PAUSA_REVISION_SEG`.

**Falta (insumos del usuario tras la prueba supervisada):**
- XPath del botón **Ejecutar** (`SAP_XPATH_BOTON_EJECUTAR`, hoy vacío).
- Cómo se ve el **cuadro de resultados**: XPath de la tabla/filas y del
  mensaje por activo; si se lee en pantalla o hay que **exportarlo** a
  Excel (el Word dice "exportar"; en SAP web la exportación descarga un
  archivo → definir botón y formato).
- Ejemplos reales de mensajes de **éxito** y de **error** por fila.
- Confirmar en la prueba: IDs del **login** de SAP (hoy estándar, por
  confirmar) y cómo queda **"Ejecución de test"** tras el clic.
- Al terminar: borrar la copia de `carga_sap/`.

---

## P4 — Extraer código SAP y asociarlo a cada fila 🔲

**Definido (Word 1.5):** mensaje "Se ha creado el activo fijo
**00000512313** Subnumero 0000" → código **512313** (sin ceros a la
izquierda, sin subnúmero).

**Por definir:**
- **Cómo se asocia cada mensaje a su fila** del Excel: ¿mismo orden que
  la plantilla? ¿el mensaje trae número de fila / inventario /
  denominación? (clave para no poner un código en la fila equivocada).
- Qué pasa si una fila da **error** en SAP: qué se escribe en su celda
  "Código SAP" (¿el texto del error?) y cómo afecta la respuesta (P9).
  SAP da el error **por fila**.

---

## P5 — Columna "Código SAP" en el Excel del usuario 🔲

**Definido:** se agrega una columna **"Código SAP"** al Excel que envió el
usuario (con su columna AC) y ese es el archivo que se le devuelve.

**Por definir:** posición (se asume **al final**, después de AC) y cómo se
escribe una fila con error (P4). Se guarda como archivo aparte (ej.
`salidas/PDA-7889_brp_creacion_RESPUESTA.xlsm`); el original no se modifica.

---

## P6 — Modificación en AS02, activo por activo 🔲

**Definido (2026-09-29):** por cada activo creado:
1. Barra de transacción → `/nAS02`.
2. **Activo fijo** `//*[@id="M0:46:::2:21-r"]` = Código SAP de esa fila.
3. **Sociedad** `//*[@id="M0:46:::4:21"]` = columna **B** de esa fila.
4. **Enter** → entra al activo (el campo está en la pantalla que abre, no
   hay que cambiar de pestaña).
5. Campo `//*[@id="M0:46:3:1:2B256:1::3:22"]`: **borrar lo que tenga** y
   escribir el valor de la columna **AC** de esa fila.
6. **Guardar**: botón `//*[@id="M0:36::btn[11]"]` (btn[11] = Guardar
   estándar de SAP); `Ctrl+S` como respaldo.

**Seguridad:** AS02 + Guardar **modifica activos reales** → interruptor
propio `SAP_MODIFICAR_REAL = False` (llena todo y no guarda). Ventaja: se
puede probar por separado sobre un activo YA existente, sin crear nada.

**Ya en `config.py` (2026-09-29):** `SAP_AS02_XPATH_ACTIVO_FIJO`,
`SAP_AS02_XPATH_SOCIEDAD`, `SAP_AS02_XPATH_TXT_ACREEDOR`,
`SAP_XPATH_BOTON_GUARDAR` y `SAP_MODIFICAR_REAL = False`. Falta el
recorrido (código) y lo de abajo.

**Por definir (el usuario lo trae):**
- Cómo confirma SAP que guardó: texto y XPath del mensaje de la barra de
  estado (ej. "Se ha modificado el activo fijo …").
- Qué hacer si falla la modificación de un activo (el activo ya existe):
  ¿reintento?, ¿se reporta en la columna?, ¿respuesta No Exitoso?
- Si AC viene vacía: se asume que se salta AS02 para ese activo (P1).

---

## P7 — Registro de estado por solicitud y por activo 🔲

**Por qué es indispensable:** crear (Ejecutar) y modificar (AS02) cambian
datos REALES. Si el bot se cae a mitad de camino, al volver a correr NO
puede repetir lo ya hecho (crearía activos duplicados) y debe retomar
exactamente donde quedó.

**Diseño acordado:** un archivo en disco (JSON) con una ficha por
solicitud (llave = número de solicitud) y, dentro, el avance de cada
activo:

```
PDA-7889: url, excel, estado = descargado → validado/invalido →
          creado_en_sap → modificado → respondido
  activos: fila 2 → código 512313, AS02 = hecho
           fila 3 → código 512314, AS02 = pendiente
```

Cada paso se anota **apenas ocurre** (antes de pasar al siguiente). Al
iniciar, el bot lee el registro: si una solicitud ya fue creada en SAP, NO
vuelve a ejecutar la masiva; solo termina las AS02 pendientes y responde.

---

## P8 — Orden de ejecución acordado (preparar todo → uno por uno) 🔲

**Acordado (2026-09-27):** (1) leer bandeja, descargar y validar TODAS;
(2) solo las válidas, una por una: SAP → respuesta. Hoy el orquestador
procesa cada solicitud de punta a punta antes de pasar a la siguiente.
Se reorganiza junto con P7.

---

## P9 — Respuesta en Appian 🔲

**Hecho:** selectores capturados en `config.py` (`RESPUESTA_*`) e
interruptor `APPIAN_RESPONDER_REAL = False`. Decisión: usar la librería
corporativa por **etiquetas/texto visible** (`FormHandler.fill_form`,
`button_by_text`; los adjuntos suben por `input[type=file]`, sin ventana de
Windows) y los XPath capturados como respaldo. `advance_case()` de la
librería NO sirve tal cual (siempre finaliza, ignora el interruptor).

**Por definir (el usuario lo trae):**
- **Textos visibles exactos** de: botón inicial en la solicitud, botón del
  modal ("Atender solicitud"), etiqueta de "¿Cómo deseas finalizar esta
  solicitud?", etiqueta del comentario, etiqueta/botón de adjuntos, botón
  Finalizar; y si aparece "Tomar tarea".
- **Lógica Exitoso / No Exitoso** (Word 1.6 da la base; falta el caso
  parcial: unos activos creados y otros con error, o AS02 fallida).
- **Texto parametrizado del comentario** (éxito y no éxito).
- Qué se adjunta en cada caso (en éxito: Excel con "Código SAP").

---

## P10 — Respuesta cuando la plantilla es inválida 🔲

**Pendiente del usuario funcional:** si al usuario se le devuelven las
observaciones por fila (ej. columna "Observaciones" o en el comentario).
Hoy el caso queda FALLIDO con el detalle por fila en el log.

---

## P12 — Paginación de la Bandeja de Actividades 🔲 (IMPORTANTE)

**Hallazgo (2026-09-29):** la bandeja de Appian es paginada (ej. 10 por
página). `bandeja_reader.listar_pendientes()` solo lee las filas de la
página VISIBLE (`BANDEJA_XPATH_FILAS` = `…/table/tbody/tr`): Appian solo
dibuja las filas de la página actual. Con 12 solicitudes, el bot leería 10
y **no avisaría**.

**Riesgos:** (1) falla en silencio ("Total de casos: 10"); (2) la prioridad
por vencimiento solo se aplica a lo visible (la más urgente puede estar en
la página 2); (3) como la bandeja trae OTROS procesos mezclados, las de
activos pueden quedar en páginas posteriores y no leerse nunca.

**Dato del usuario (2026-09-29):** la tabla tiene un selector de filas por
página (ej. 100).

**Solución propuesta:**
1. Antes de leer, poner la tabla en **100 filas por página** (o el máximo)
   → normalmente todo cabe en una página.
2. **Control de total:** leer el contador ("1 – 100 de 130"). Si el total
   cabe → normal. Si NO cabe (la bandeja trae otros procesos mezclados):
   - (a) [recomendado para empezar] aviso fuerte en el log ("se leyeron
     100 de 130, revisar a mano");
   - (b) [si hace falta] recorrer también las páginas siguientes con el
     botón "siguiente" (se guarda el `href` de cada solicitud, así que
     luego se entra directo sin importar la página).
   Ordenar por vencimiento DESPUÉS de juntar todo lo leído.

**Insumos del usuario:** XPath del selector de filas por página + XPath y
texto de la opción 100; qué pasa tras elegirla (¿recarga?, ¿cómo saber que
terminó?); si el valor se conserva entre sesiones; XPath y texto exacto del
contador ("1 – 10 de 12"). Solo para (b): botón "página siguiente" y cómo se
ve cuando no hay más páginas.

---

## P11 — Varios / mantenimiento 🔲

- Actualizar `GUIA_MODO_PRUEBAS.md` con cada etapa nueva (AS02, respuesta).
- Selector de la bandeja `//*[@id="sitesBody"]/div/div/div[6]/…` es casi
  un XPath completo (frágil): primer sospechoso si la bandeja falla.
- `DETALLE_XPATH_BOTON_ADJUNTO_RESPALDO` usa un ID de Appian inestable
  (no se ha necesitado).
- Caso "2 adjuntos": existe para OTRO activo (se verá después); en BRP
  Creación siempre es 1.
- Commit completo pendiente (el commit `7baf3e8` quedó parcial; lo hace el
  usuario).

---

## Carpeta `plantillas/` (raíz del repo)

**No la usa el bot en producción** (no va en el `.exe`: `build.bat` no la
incluye). Sirve para: (1) referencia de negocio (plantillas oficiales y
Word de proceso de cada activo) y (2) las **pruebas automáticas**
(`tests/`), que parten de la plantilla oficial. Debe quedarse en el repo.
