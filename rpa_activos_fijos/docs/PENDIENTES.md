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
> Alcance actual: **Activos BRP – Creación** (AS01, activo por activo). Los
> demás activos/acciones se trabajan después, uno por uno.
> Última actualización: 2026-10-05 (formulario AS01 configurado + supervisión con "Continuar").

> **Renumeración 2026-10-04** (por el cambio de masiva → AS01/AS02/AS06):
> P1 se mantiene · P2 (copia sin AC) y P3/P4 (Ejecutar y cuadro de la
> masiva) quedaron **obsoletos** · nuevos P3–P5 (formulario AS01, supervisión,
> resultado por fila) · P6 (AS02 en creación) **obsoleto** · bitácora P7 → P6 ·
> orden P8 → P7 · respuesta P9 → P8 · plantilla inválida P10 → P9 ·
> paginación P12 → P10 · nuevo P11 (otras acciones BRP) · varios → P12.

---

## 0. Resumen del flujo completo (cómo debe quedar BRP – Creación)

```
APPIAN (preparación, todas las solicitudes)
  1. Leer bandeja → descargar TODOS los Excel → validar TODOS            ✅ (hoy caso por caso, ver P7)
     (bandeja paginada: hoy solo la página visible)                        🔲 P10
     (inválidos → responder en Appian de una vez)                          🔲 P9

POR CADA SOLICITUD VÁLIDA (una por una, por vencimiento)
  POR CADA FILA DEL EXCEL (= un activo):
    2. SAP AS01: llenar el formulario con los valores de la fila         ✅ P3 (faltan 3 dudas)
    3. Guardar (solo si guardar_permitido()); si no → "Continuar"          ✅ P4
    4. Leer el mensaje de SAP → código o error en "Código SAP"           ✅ código · 🔲 XPath del mensaje (P5)
       (si falla, se anota y se CONTINÚA con la siguiente fila)
  5. Responder en Appian (Exitoso / No Exitoso + comentario + Excel)     🔲 P8
  Bitácora por solicitud y POR FILA durante todo el proceso               🔲 P6
```

Interruptores en `config.py` (explicados en GUIA_MODO_PRUEBAS.md, sección 3):
`MODO_PRUEBAS_REEMPLAZO`, `MODO_PRUEBAS_SOLO_SAP` (sin Appian, 2026-10-05),
`SAP_GUARDAR_REAL` y `APPIAN_RESPONDER_REAL`, todos en `False`. En cualquier
modo de prueba, guardar en SAP está prohibido siempre.

**Prioridad acordada:** la bitácora (P6) es importante para el usuario →
construirla antes de encender `SAP_GUARDAR_REAL`.

---

## P1 — Plantilla de BRP – Creación con columna AC ✅ 2026-09-29

- Plantilla del usuario: `plantillas/BRP/Plantilla Creación Activos BRP usuario.xlsm`
  (hoja "FORMATO", A..AC). Se sigue usando IGUAL tras el cambio de negocio.
- AC "TXT.NUM.PRAL.AF (Nombre y NIT del acreedor)": informativa, > 50
  caracteres = ERROR; una plantilla sin AC se rechaza. Desde 2026-10-04 su
  valor se escribe en el campo del mismo nombre de **AS01** (AS01 lo tiene).
- La columna S "ACREEDOR" es OTRO campo.
- Formatos aceptados: **.xlsx y .xlsm** (2026-10-04).
- `plantillas/BRP/Plantilla Creación Activos BRP.xlsm` (A..AB) era el
  formato de la masiva: ya no lo usa el bot ni las pruebas.

---

## P2 — (OBSOLETO) Copia para SAP sin la columna AC

Retirado el 2026-10-04: SAP ya no recibe el archivo (no hay masiva).

---

## P3 — Formulario de AS01 por configuración ✅ 2026-10-05 (quedan formatos y casilla por confirmar)

**Hecho:** `SAP_FORMULARIO_AS01_BRP` en `config.py` (XPath entregados por el
usuario, 2026-10-05) y `SAP_FORMULARIOS_POR_CASO`. Pasos: pantalla inicial
(A clase, B sociedad, C cantidad) → Enter → formulario completo (D, AC, F,
G) → 4 pestañas más con doble clic lento (H, I, J, K, L, M, casilla N · O,
P, Q, R · S, T, U, V · W, X). Celdas vacías no se tocan; la casilla N solo
se marca si trae valor. `SAP_ESPERA_ENTRE_CLICS_SEG = 2` (SAP es lento).
Las filas se leen con `BaseValidador.leer_filas()` (misma lógica que la
validación). Pruebas: `tests/test_sap_as01.py`.

**Resuelto (usuario, 2026-10-05):** solo se llenan los campos de los XPath
entregados. Columnas del Excel sin XPath (**E** Marca, **Y** Número de
contrato, **Z** Área de valoración, **AA** Duración, **AB** Periodo) se
IGNORAN. Campos de AS01 sin columna ("Cantidad", "Total depreciados") NO se
llenan. Celda vacía → ese campo no se toca y se sigue con el siguiente.

**Dudas abiertas (el usuario):**
3. Formatos: fecha G se escribe `05.10.2026` (`SAP_FORMATO_FECHA`) y
   decimales con coma (`SAP_SEPARADOR_DECIMAL`) — **por confirmar** en la
   1ª prueba. Ojo con códigos con ceros a la izquierda guardados como número
   en Excel (ej. centro de coste `0012345` → Excel lo guarda `12345`).
4. Casilla N "Activo fijo paralizado": se asume que viene desmarcada por
   defecto y que "cualquier valor" en la celda = marcarla. Confirmar.

---

## P4 — Supervisión: detenerse antes de Guardar + botón "Continuar" ✅ 2026-10-05

- `flujo3_sap.guardar_permitido()`: solo True con `SAP_GUARDAR_REAL = True`
  **y** fuera de MODO PRUEBAS. Además, nunca se guarda si
  `SAP_XPATH_MENSAJE_ESTADO` está vacío (no se podría confirmar el resultado).
- Si no se puede guardar: por cada activo el bot llena el formulario, se
  detiene, la ventana del bot habilita **"Continuar (sin guardar)"** (aviso
  por la cola; el hilo del bot espera un `threading.Event`) y al presionarlo
  sale SIN guardar: Atrás ×2 (lento) + confirmar
  (`SAP_XPATH_BOTON_ATRAS`, `SAP_XPATH_CONFIRMAR_SALIR_SIN_GUARDAR`).
- Tras un ERROR en una fila NO se presiona Atrás (fuera del formulario podría
  llevar al menú o a cerrar sesión): solo se confirma la ventana de "salir
  sin guardar" si quedó abierta; la siguiente fila arranca con `/nAS01`.

---

## P5 — Resultado por fila → columna "Código SAP" 🔲 (código listo, falta el XPath)

**Hecho:**
- Guardar → leer la barra → `SAP_REGEX_ACTIVO_CREADO`: "El act.fj.
  **7129560** 0 se ha creado" → **7129560**. Si no coincide → `ERROR: <mensaje
  de SAP>`. Errores al llenar → `ERROR: ...` (con el mensaje de la barra si se
  puede leer). Siempre se CONTINÚA con la siguiente fila.
- `escribir_columna_codigo_sap()`: agrega "Código SAP" en la primera columna
  libre a la derecha (con la plantilla = **AD**) del Excel del usuario y lo
  guarda APARTE en `salidas/<archivo>_RESPUESTA.<ext>`; el original no se
  modifica. Solo se genera cuando se guarda de verdad.

**Falta (el usuario):**
- **XPath de la barra de mensajes** de SAP → `SAP_XPATH_MENSAJE_ESTADO`.
  Mientras esté vacío, el bot NO guarda.
- **Texto exacto de un mensaje de error** de AS01 (para confirmar que no se
  confunda con éxito).

---

## P6 — Bitácora de estado por solicitud y POR FILA 🔲 (PRIORITARIA)

**Por qué es indispensable:** cada "Guardar" en AS01 crea un activo REAL.
Si el bot se cae a mitad, al volver NO puede repetir filas ya creadas
(duplicados) y debe seguir exactamente donde quedó.

**Diseño:** archivo en disco (JSON), una ficha por solicitud (llave =
número de solicitud) y, dentro, cada fila:

```
PDA-7889: url, excel, estado = descargado → validado/invalido →
          en_sap → respondido
  fila 2 → creado, código 512313
  fila 3 → error SAP: "Centro de coste no existe"
  fila 4 → guardando…   ← se cayó aquí
```

- Cada paso se anota **apenas ocurre**. Antes de presionar Guardar se marca
  la fila como "guardando".
- Al reanudar: filas "creado"/"error" no se repiten; si una fila quedó en
  **"guardando"** (se cayó entre el clic y la respuesta) NO se reintenta
  sola → se marca para **revisión manual** (reintentar podría duplicar).

---

## P7 — Orden de ejecución acordado (preparar todo → uno por uno) 🔲

**Acordado (2026-09-27):** (1) leer bandeja, descargar y validar TODAS;
(2) solo las válidas, una por una: SAP → respuesta. Hoy el orquestador
procesa cada solicitud de punta a punta antes de pasar a la siguiente.
Se reorganiza junto con P6.

---

## P8 — Respuesta en Appian 🔲

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
- **Lógica Exitoso / No Exitoso**: según el Word (1.6), si SAP rechaza una o
  más filas → "Finalizado No Exitoso". Confirmar.
- **Texto parametrizado del comentario** (éxito y no éxito).
- Adjunto: Excel del usuario con la columna "Código SAP".

---

## P9 — Respuesta cuando la plantilla es inválida 🔲

**Pendiente del usuario funcional:** si al usuario se le devuelven las
observaciones por fila (ej. columna "Observaciones" o en el comentario).
Hoy el caso queda FALLIDO con el detalle por fila en el log.

---

## P10 — Paginación de la Bandeja de Actividades 🔲 (IMPORTANTE)

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

## P11 — Otras acciones de BRP: Modificar (AS02) y Borrar (AS06) 🔲

- Cada una tendrá **su propia plantilla** (distinta a la de creación) y su
  Word de proceso → nuevo validador en `validacion/plantillas/` + su
  formulario por configuración (mismo mecanismo de P3).
- AS02: en `config.py` quedan como **referencia** los selectores capturados
  el 2026-09-29 (`SAP_AS02_XPATH_ACTIVO_FIJO`, `SAP_AS02_XPATH_SOCIEDAD`,
  `SAP_AS02_XPATH_TXT_ACREEDOR`). Revisarlos con la plantilla de modificar.

---

## P12 — Varios / mantenimiento 🔲

- Actualizar `GUIA_MODO_PRUEBAS.md` con cada etapa nueva (AS01, "Continuar",
  respuesta).
- Selector de la bandeja `//*[@id="sitesBody"]/div/div/div[6]/…` es casi
  un XPath completo (frágil): primer sospechoso si la bandeja falla.
- `DETALLE_XPATH_BOTON_ADJUNTO_RESPALDO` usa un ID de Appian inestable
  (no se ha necesitado).
- Caso "2 adjuntos": existe para OTRO activo (se verá después); en BRP
  Creación siempre es 1.
- Login de SAP con IDs estándar: confirmar en la 1ª prueba real.
- `console_view._correr_bot` (código previo) llama `self.after()` desde el
  hilo del bot al terminar. Funciona con la ventana en `mainloop`, pero lo
  robusto es avisar por la cola (como se hizo con "Continuar"). Revisar si
  algún día la ventana no se actualiza al terminar.

---

## Carpeta `plantillas/` (raíz del repo)

**No la usa el bot en producción** (no va en el `.exe`: `build.bat` no la
incluye). Sirve para: (1) referencia de negocio (plantillas oficiales y
Word de proceso de cada activo) y (2) las **pruebas automáticas**
(`tests/`), que parten de la plantilla del usuario. Debe quedarse en el repo.
