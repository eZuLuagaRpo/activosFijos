"""
orquestador.py — Coordina los 3 flujos por cada caso y arma el resumen final.

Secuencia por cada solicitud detectada en la bandeja:
    Flujo 1 (obtener datos)  ->  Flujo 2 (validar plantilla)  ->  Flujo 3 (SAP)

MODO PRUEBAS SOLO SAP (config.MODO_PRUEBAS_SOLO_SAP): NO se entra a Appian; el
Flujo 1 se reemplaza por los Excel de downloads_test (flujos/modo_solo_sap.py)
y cada archivo pasa por Flujo 2 -> Flujo 3 igual que una solicitud.

Principios de resiliencia aplicados aquí:
  - AISLAMIENTO POR CASO: cada caso va dentro de su propio try/except. Si uno
    falla, se registra el motivo y se CONTINÚA con el siguiente. Un caso malo
    nunca tumba todo el lote.
  - CIERRE LIMPIO: el navegador se cierra SIEMPRE en un finally.
  - RESUMEN FINAL: al terminar se informa total, exitosos y fallidos (con motivo).

La función principal `ejecutar` recibe las credenciales y una `cola` opcional
para enviar los logs a la consola de la UI.
"""

import os

from appian.appian_client import AppianClient
from config import DOWNLOAD_TEST_DIR, MODO_PRUEBAS_REEMPLAZO, MODO_PRUEBAS_SOLO_SAP
from core.exceptions import CasoOmitidoError, PlantillaInvalidaError, RPAError
from core.logger import crear_logger
from core.models import ResultadoCaso, ResumenLote
from flujos import flujo1_appian, flujo2_validar, flujo3_sap, modo_solo_sap
from sap.sap_webgui import SapWebGui


def _procesar(case_id, obtener_solicitud, paso_inicial, sap, logger, esperar_continuar):
    """
    Corre UN caso: obtener la solicitud -> Flujo 2 -> Flujo 3, y devuelve su
    ResultadoCaso. No lanza excepción: cualquier fallo se captura y se
    refleja en el resultado. Al terminar (bien o mal) el navegador vuelve a
    la pestaña de Appian, que es donde arranca el siguiente caso.

    Args:
        obtener_solicitud: función SIN argumentos que devuelve la `Solicitud`
            (Flujo 1 con Appian, o el archivo local en modo solo SAP).
        paso_inicial: texto del paso mientras se obtiene la solicitud.
    """
    resultado = ResultadoCaso(case_id=case_id)

    try:
        # --- Flujo 1 (o archivo local): obtener la solicitud ---
        resultado.paso = paso_inicial
        solicitud = obtener_solicitud()

        # --- Flujo 2: validar la plantilla ---
        resultado.paso = "Flujo 2 (Validación)"
        resultado.validacion = flujo2_validar.validar_solicitud(
            solicitud, logger=logger
        )

        # --- Flujo 3: SAP, activo por activo ---
        resultado.paso = "Flujo 3 (SAP)"
        paso_final = flujo3_sap.cargar_a_sap(
            sap, solicitud, logger=logger, esperar_continuar=esperar_continuar
        )

        resultado.exito = True
        resultado.paso = paso_final or "Completado"
        logger.info("Caso %s procesado correctamente (%s).", case_id, resultado.paso)

    except CasoOmitidoError as e:
        # Saltado a propósito (ej. MODO PRUEBAS sin archivo): no es un fallo.
        resultado.omitido = True
        resultado.motivo = str(e)
        logger.info("Caso %s OMITIDO: %s", case_id, e)
    except PlantillaInvalidaError as e:
        # Plantilla con errores de negocio: el detalle por fila ya quedó en el
        # log (Flujo 2). PENDIENTE (confirmar con el usuario funcional): si se
        # le devuelven al usuario las observaciones por fila en Appian.
        resultado.exito = False
        resultado.validacion = e.resultado
        resultado.motivo = str(e)
        logger.error("Caso %s FALLÓ en %s: %s", case_id, resultado.paso, e)
    except RPAError as e:
        # Errores esperados y clasificados del bot: mensaje claro, sin traza cruda.
        resultado.exito = False
        resultado.motivo = str(e)
        logger.error("Caso %s FALLÓ en %s: %s", case_id, resultado.paso, e)
    except Exception as e:
        # Errores inesperados: se registran igual y NO detienen el lote.
        resultado.exito = False
        resultado.motivo = f"Error inesperado: {e}"
        logger.error(
            "Caso %s FALLÓ (inesperado) en %s: %s", case_id, resultado.paso, e
        )
    finally:
        if sap is not None:
            sap.volver_a_appian()

    return resultado


def _procesar_un_caso(client, sap, caso, logger, esperar_continuar=None):
    """Un caso de la bandeja de Appian: Flujo 1 -> 2 -> 3."""
    return _procesar(
        caso.case_id,
        lambda: flujo1_appian.obtener_solicitud(client, caso, logger=logger),
        "Flujo 1 (Appian)",
        sap,
        logger,
        esperar_continuar,
    )


def _agregar(resumen, resultado):
    resumen.resultados.append(resultado)
    if resultado.omitido:
        resumen.omitidos += 1
    elif resultado.exito:
        resumen.exitosos += 1
    else:
        resumen.fallidos += 1


def ejecutar(user, password, cola=None, logger=None, esperar_continuar=None):
    """
    Punto de entrada del bot. Corre todo el lote y devuelve un ResumenLote.

    Args:
        user (str): usuario de Appian (xxxx@bancolombia.com.co).
        password (str): contraseña de Appian (NUNCA se registra en logs).
        cola (queue.Queue, opcional): cola hacia la consola de la UI.
        logger: logger ya creado (si no, se crea uno con la cola dada).
        esperar_continuar (callable, opcional): la UI la entrega; bloquea
            hasta que la persona presione "Continuar" (supervisión en SAP).

    Returns:
        ResumenLote con el detalle de cada caso.
    """
    if logger is None:
        logger = crear_logger(cola=cola)

    resumen = ResumenLote()
    # Aquí cada recorrido deja el navegador APENAS lo abre, para poder
    # cerrarlo siempre (también si falla el login de Appian).
    navegador = {"client": None}

    try:
        logger.info("=== Inicio de ejecución del RPA de Activos Fijos ===")
        if MODO_PRUEBAS_REEMPLAZO and MODO_PRUEBAS_SOLO_SAP:
            raise RPAError(
                "MODO_PRUEBAS_REEMPLAZO y MODO_PRUEBAS_SOLO_SAP están encendidos a "
                "la vez en config.py. Deja solo uno en True."
            )

        if MODO_PRUEBAS_SOLO_SAP:
            _ejecutar_solo_sap(user, password, resumen, navegador, logger, esperar_continuar)
        else:
            _ejecutar_con_appian(user, password, resumen, navegador, logger, esperar_continuar)

    except RPAError as e:
        # Fallo global (ej. login o bandeja): no se puede continuar.
        logger.error("Ejecución abortada: %s", e)
    except Exception as e:
        logger.error("Ejecución abortada por error inesperado: %s", e)
    finally:
        # CIERRE LIMPIO: el navegador se cierra siempre.
        if navegador["client"] is not None:
            navegador["client"].cerrar()

    _emitir_resumen(resumen, logger)
    return resumen


def _ejecutar_con_appian(user, password, resumen, navegador, logger, esperar_continuar):
    """Recorrido normal: Appian (bandeja) -> por cada solicitud, flujos 1-2-3."""
    if MODO_PRUEBAS_REEMPLAZO:
        _avisar_modo_pruebas(logger)

    # 1) Abrir Appian + login (si falla, abortamos con elegancia).
    client = AppianClient(logger=logger)
    navegador["client"] = client
    client.start(user, password)
    logger.info("Sesión de Appian iniciada correctamente.")

    # 2) Leer la bandeja para saber qué casos hay pendientes (ya en orden
    #    de prioridad por fecha de vencimiento).
    casos = flujo1_appian.listar_casos_pendientes(client, logger=logger)
    resumen.total = len(casos)

    # SAP va en una pestaña del mismo navegador y con las mismas
    # credenciales. Solo se abre si algún caso llega al Flujo 3.
    sap = SapWebGui(client.driver, user, password, logger=logger)

    # 3) Procesar caso por caso, aislando fallos.
    for caso in casos:
        _agregar(resumen, _procesar_un_caso(client, sap, caso, logger, esperar_continuar))


def _ejecutar_solo_sap(user, password, resumen, navegador, logger, esperar_continuar):
    """
    MODO PRUEBAS SOLO SAP: NO entra a Appian. Se abre el navegador (lo crea la
    librería de Appian, sin iniciar sesión en Appian) y cada Excel de
    downloads_test con nombre <id>_<tipo>_<accion>.xlsx pasa por validación
    y SAP. Guardar está prohibido (flujo3_sap.guardar_permitido()).
    """
    _avisar_modo_solo_sap(logger)
    solicitudes, ignorados = modo_solo_sap.listar_archivos(logger=logger)
    resumen.total = len(solicitudes) + len(ignorados)

    for nombre in ignorados:
        _agregar(resumen, ResultadoCaso(
            case_id=nombre, omitido=True,
            motivo="nombre sin el formato <id>_<tipo>_<accion>.xlsx",
        ))
    if not solicitudes:
        return

    client = AppianClient(logger=logger)   # solo abre el navegador
    navegador["client"] = client
    sap = SapWebGui(client.driver, user, password, logger=logger)

    for solicitud in solicitudes:
        _agregar(resumen, _procesar(
            solicitud.case_id,
            lambda s=solicitud: s,
            "Archivo local (modo solo SAP)",
            sap,
            logger,
            esperar_continuar,
        ))


def _avisar_modo_pruebas(logger):
    """Aviso bien visible: el Excel de Appian se reemplaza por el de pruebas."""
    archivos = sorted(
        f for f in os.listdir(DOWNLOAD_TEST_DIR) if not f.startswith((".", "~$"))
    )
    logger.warning("#" * 70)
    logger.warning("#  MODO PRUEBAS ACTIVO (MODO_PRUEBAS_REEMPLAZO = True en config.py)")
    logger.warning("#  Se usarán los Excel de downloads_test en vez de los adjuntos de")
    logger.warning("#  Appian. Solicitudes sin archivo allí se OMITEN.")
    logger.warning("#  Archivos de prueba encontrados (%s): %s",
                   len(archivos), ", ".join(archivos) or "NINGUNO")
    logger.warning("#" * 70)


def _avisar_modo_solo_sap(logger):
    """Aviso bien visible: no se entra a Appian; solo validación + SAP."""
    logger.warning("#" * 70)
    logger.warning("#  MODO PRUEBAS SOLO SAP (MODO_PRUEBAS_SOLO_SAP = True en config.py)")
    logger.warning("#  NO se entra a Appian. Se usan los Excel de downloads_test")
    logger.warning("#  nombrados <id>_<tipo>_<accion>.xlsx (ej. prueba1_brp_creacion.xlsx).")
    logger.warning("#  En SAP NO se guarda nada (se detiene antes de Guardar).")
    logger.warning("#" * 70)


def _emitir_resumen(resumen, logger):
    """Escribe en el log el resumen final del lote."""
    logger.info("=== Resumen de la ejecución ===")
    if MODO_PRUEBAS_REEMPLAZO:
        logger.warning("(Ejecución en MODO PRUEBAS: Excel reemplazados por los de downloads_test)")
    if MODO_PRUEBAS_SOLO_SAP:
        logger.warning("(Ejecución en MODO PRUEBAS SOLO SAP: sin Appian, sin guardar en SAP)")
    logger.info("Total de casos:   %s", resumen.total)
    logger.info("Procesados OK:    %s", resumen.exitosos)
    logger.info("Fallidos:         %s", resumen.fallidos)
    if resumen.omitidos:
        logger.info("Omitidos:         %s", resumen.omitidos)

    if resumen.fallidos:
        logger.info("Detalle de casos fallidos:")
        for r in resumen.resultados:
            if not r.exito and not r.omitido:
                logger.info("  - %s | %s | %s", r.case_id, r.paso, r.motivo)

    logger.info("=== Fin de la ejecución ===")
