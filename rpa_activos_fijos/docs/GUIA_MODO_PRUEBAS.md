# Guía — Modo pruebas (reemplazo del Excel)

> **Para qué sirve esta guía:** explica, paso a paso, cómo probar el bot con
> **solicitudes reales de Appian** usando un Excel preparado por ti, mientras
> los usuarios sigan adjuntando el formato viejo.
>
> **Alcance actual:** solo **Activos BRP – Creación** (carga masiva).
> Última actualización: 2026-09-28.

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
- Valida tu Excel con las reglas de BRP – Creación.
- Deja listo el archivo `carga_sap/CREAR (BRP).xlsm` para SAP.

**Todavía NO hace (está en construcción):**
- **No entra a SAP** ni carga nada: solo deja el archivo listo.
- **No responde ni cierra** solicitudes en Appian.

Es decir: **hoy puedes correr el modo pruebas sin riesgo** de crear activos
ni de notificar a usuarios. Cuando se construya SAP y la respuesta en Appian,
cada una quedará detrás de su propio interruptor apagado, y esta guía se
actualizará.

---

## 3. Paso a paso

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

1. Copia la plantilla oficial:
   `plantillas/BRP/Plantilla Creación Activos BRP.xlsm`
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
4. Guarda el archivo.

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
INFO    | Caso PDA-7889: archivo para SAP preparado -> ...\carga_sap\CREAR (BRP).xlsm (copia de PDA-7889_brp_creacion_PRUEBA.xlsm)
WARNING | PENDIENTE: carga a SAP no implementada. Archivo listo para cargar: ...\carga_sap\CREAR (BRP).xlsm
INFO    | Caso PDA-7889 procesado correctamente.
```

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

- **Procesados OK:** tu Excel pasó la validación y quedó listo para SAP.
- **Fallidos:** algo salió mal (ver "Detalle de casos fallidos" y la
  sección 5 de esta guía).
- **Omitidos:** solicitudes de la bandeja sin archivo tuyo. Es normal.

El mismo contenido queda guardado en `rpa_activos_fijos/logs/ejecucion_AAAAMMDD_HHMMSS.log`.

### Paso 8 — Revisa los archivos que quedaron

| Carpeta | Archivo | Qué es |
|---|---|---|
| `downloads_test/` | `PDA-7889.xlsm` | **Tu archivo. Nunca se modifica.** |
| `downloads/` | `PDA-7889_brp_creacion.xls` (o la extensión que tenga) | El adjunto **real** del usuario, descargado de Appian. Se conserva, no se usa. |
| `downloads/` | `PDA-7889_brp_creacion_PRUEBA.xlsm` | **Copia de trabajo** de tu archivo: es la que se valida. |
| `carga_sap/` | `CREAR (BRP).xlsm` | Copia con el **nombre exacto que exige SAP**. Queda la de la **última** solicitud válida (cada una reemplaza a la anterior). |

> Puedes abrir `carga_sap/CREAR (BRP).xlsm` para confirmar que es tu archivo.
> **Ciérralo antes de volver a ejecutar el bot**: si está abierto, el bot no
> puede reemplazarlo y marca el caso como fallido.

### Paso 9 — Cuando termines: APAGA el modo

1. En `config.py` vuelve a dejar:
   ```python
   MODO_PRUEBAS_REEMPLAZO = False
   ```
2. (Opcional) Borra tus archivos de `downloads_test/` para que no se usen
   por error en una prueba futura. **No borres el archivo `.gitkeep`.**
3. **Nunca** generes el `.exe` para la usuaria con el modo en `True`.

---

## 4. Checklist rápido

- [ ] La solicitud está en la bandeja y en "Detalles" dice **Activos BRP → Crear**.
- [ ] Excel hecho desde la **plantilla oficial**, llenado desde la fila 2.
- [ ] Guardado como **`.xlsm`**.
- [ ] Nombre = **solo el número**: `PDA-7889.xlsm`.
- [ ] Archivo en **`rpa_activos_fijos/downloads_test/`** (uno por solicitud).
- [ ] `MODO_PRUEBAS_REEMPLAZO = True` en `config.py`, guardado.
- [ ] Bot reiniciado (`python app.py`).
- [ ] `carga_sap/CREAR (BRP).xlsm` **cerrado** en Excel.
- [ ] Al terminar: `MODO_PRUEBAS_REEMPLAZO = False`.

---

## 5. Problemas comunes

| Mensaje en la consola | Qué significa | Qué hacer |
|---|---|---|
| `Archivos de prueba encontrados (0): NINGUNO` | La carpeta está vacía o el archivo quedó en otro lado | Revisa que esté en `rpa_activos_fijos/downloads_test/` |
| `Caso PDA-XXXX OMITIDO: ... no hay archivo` (y tú sí pusiste uno) | El nombre no coincide exacto | Revisa el nombre (Paso 3): sin texto extra, con guion, sin doble extensión |
| `hay 2 archivos de prueba para PDA-XXXX ... Deja solo uno` | Hay `.xlsx` y `.xlsm` (u otro) con el mismo número | Deja solo el `.xlsm` |
| `Formato de archivo no soportado ('.xlsx'); la plantilla BRP - Creación debe ser .xlsm` | Guardaste como `.xlsx` | Guardar como "Libro habilitado para macros" (`.xlsm`) |
| `Faltan encabezados en la fila 1: ...` | Se modificó/borró algún encabezado | Partir de nuevo de la plantilla oficial |
| `fila N: Faltan campos obligatorios: ...` | Esa fila tiene obligatorios vacíos (o con 0) | Llenar las columnas indicadas |
| `fila N: C (Cantidad de Activos) debe ser 1 ...` | La cantidad no es 1 | Poner 1 (una fila = un activo) |
| `fila N: Es un vehículo ... y falta U (Modelo)` | Hay matrícula pero no modelo | Llenar U, o vaciar M si no es vehículo |
| `La plantilla no tiene filas de datos` | Solo tiene encabezados | Llenar al menos una fila desde la 2 |
| `Aún no hay validación implementada para (tipo='prj', ...)` | La solicitud real no es BRP – Creación | Usar una solicitud de BRP – Creación |
| `no se pudo borrar la copia anterior 'CREAR (BRP).xlsm' (¿está abierta...?)` | Tienes abierto ese archivo | Cerrarlo en Excel/SAP y ejecutar de nuevo |
| `El caso ... no trae adjuntos` / `trae 2 Excel adjuntos` | Problema con el adjunto **real** de Appian | En modo pruebas el adjunto real se descarga igual (a propósito, para no ocultar fallas reales). Usa otra solicitud |
| Advertencia `T (Fabricante) tiene N caracteres (máximo 30)` | Solo aviso, **no** rechaza | Opcional: acortarlo |

---

## 6. Detalles técnicos (para quien mantenga el código)

- Switch: `MODO_PRUEBAS_REEMPLAZO` en `config.py` (por defecto `False`).
  Carpetas: `DOWNLOAD_TEST_DIR` (`downloads_test/`) y `CARGA_SAP_DIR`
  (`carga_sap/`). Nombre SAP: `NOMBRE_ARCHIVO_SAP`.
- Código: `flujos/flujo1_appian.py` → `_buscar_archivo_prueba()` (antes de
  abrir la solicitud) y `_usar_archivo_prueba()` (después de descargar y
  renombrar el adjunto real). `orquestador.py` → `_avisar_modo_pruebas()` y
  conteo de omitidos (`CasoOmitidoError`). `flujos/flujo3_sap.py` →
  `preparar_archivo_sap()`.
- Con el switch en `False` el comportamiento es exactamente el del flujo
  real (hay una prueba automática que lo verifica aunque existan archivos en
  `downloads_test/`).
- Pruebas: `python -m pytest tests -q` desde `rpa_activos_fijos/`.
- Todo lo del modo está marcado con el texto **"MODO PRUEBAS"** en el código,
  para encontrarlo y retirarlo fácil cuando ya no se necesite.
