"""
orquestador.py — Coordina los 3 flujos por cada caso y arma el resumen final.

Secuencia por cada solicitud detectada en la bandeja:
    Flujo 1 (obtener datos)  ->  Flujo 2 (validar plantilla)  ->  Flujo 3 (SAP)

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
from config import DOWNLOAD_TEST_DIR, MODO_PRUEBAS_REEMPLAZO
from core.exceptions import CasoOmitidoError, PlantillaInvalidaError, RPAError
from core.logger import crear_logger
from core.models import ResultadoCaso, ResumenLote
from flujos import flujo1_appian, flujo2_validar, flujo3_sap
from sap.sap_webgui import SapWebGui


def _procesar_un_caso(client, sap, caso, logger):
    """
    Ejecuta los flujos 1->2->3 para UN caso (un `CasoBandeja`) y devuelve su
    ResultadoCaso. No lanza excepción: cualquier fallo se captura y se
    refleja en el resultado. Al terminar (bien o mal) el navegador queda en
    la pestaña de Appian, que es donde arranca el Flujo 1 del siguiente caso.
    """
    case_id = caso.case_id
    resultado = ResultadoCaso(case_id=case_id)

    try:
        # --- Flujo 1: obtener la solicitud (detalle + Excel) ---
        resultado.paso = "Flujo 1 (Appian)"
        solicitud = flujo1_appian.obtener_solicitud(client, caso, logger=logger)

        # --- Flujo 2: validar la plantilla (el mismo Excel va a SAP) ---
        resultado.paso = "Flujo 2 (Validación)"
        resultado.validacion = flujo2_validar.validar_solicitud(
            solicitud, logger=logger
        )

        # --- Flujo 3: carga a SAP (hasta antes de Ejecutar, por ahora) ---
        resultado.paso = "Flujo 3 (SAP)"
        paso_final = flujo3_sap.cargar_a_sap(sap, solicitud, logger=logger)

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


def ejecutar(user, password, cola=None, logger=None):
    """
    Punto de entrada del bot. Corre todo el lote y devuelve un ResumenLote.

    Args:
        user (str): usuario de Appian (xxxx@bancolombia.com.co).
        password (str): contraseña de Appian (NUNCA se registra en logs).
        cola (queue.Queue, opcional): cola hacia la consola de la UI.
        logger: logger ya creado (si no, se crea uno con la cola dada).

    Returns:
        ResumenLote con el detalle de cada caso.
    """
    if logger is None:
        logger = crear_logger(cola=cola)

    resumen = ResumenLote()
    client = None

    try:
        logger.info("=== Inicio de ejecución del RPA de Activos Fijos ===")
        if MODO_PRUEBAS_REEMPLAZO:
            _avisar_modo_pruebas(logger)

        # 1) Abrir Appian + login (si falla, abortamos con elegancia).
        client = AppianClient(logger=logger)
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
            resultado = _procesar_un_caso(client, sap, caso, logger)
            resumen.resultados.append(resultado)
            if resultado.omitido:
                resumen.omitidos += 1
            elif resultado.exito:
                resumen.exitosos += 1
            else:
                resumen.fallidos += 1

    except RPAError as e:
        # Fallo global (ej. login o bandeja): no se puede continuar.
        logger.error("Ejecución abortada: %s", e)
    except Exception as e:
        logger.error("Ejecución abortada por error inesperado: %s", e)
    finally:
        # CIERRE LIMPIO: el navegador se cierra siempre.
        if client is not None:
            client.cerrar()

    _emitir_resumen(resumen, logger)
    return resumen


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


def _emitir_resumen(resumen, logger):
    """Escribe en el log el resumen final del lote."""
    logger.info("=== Resumen de la ejecución ===")
    if MODO_PRUEBAS_REEMPLAZO:
        logger.warning("(Ejecución en MODO PRUEBAS: Excel reemplazados por los de downloads_test)")
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
