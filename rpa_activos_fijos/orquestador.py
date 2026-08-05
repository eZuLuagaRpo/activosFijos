"""
orquestador.py — Coordina los 3 flujos por cada caso y arma el resumen final.

Secuencia por cada solicitud detectada en la bandeja:
    Flujo 1 (obtener datos)  ->  Flujo 2 (transformar)  ->  Flujo 3 (STUB SAP)

Principios de resiliencia aplicados aquí:
  - AISLAMIENTO POR CASO: cada caso va dentro de su propio try/except. Si uno
    falla, se registra el motivo y se CONTINÚA con el siguiente. Un caso malo
    nunca tumba todo el lote.
  - CIERRE LIMPIO: el navegador se cierra SIEMPRE en un finally.
  - RESUMEN FINAL: al terminar se informa total, exitosos y fallidos (con motivo).

La función principal `ejecutar` recibe las credenciales y una `cola` opcional
para enviar los logs a la consola de la UI.
"""

from appian.appian_client import AppianClient
from core.exceptions import RPAError
from core.logger import crear_logger
from core.models import ResultadoCaso, ResumenLote
from flujos import flujo1_appian, flujo2_procesar, flujo3_sap


def _procesar_un_caso(client, caso, logger):
    """
    Ejecuta los flujos 1->2->3 para UN caso (un `CasoBandeja`) y devuelve su
    ResultadoCaso. No lanza excepción: cualquier fallo se captura y se
    refleja en el resultado.
    """
    case_id = caso.case_id
    resultado = ResultadoCaso(case_id=case_id)

    try:
        # --- Flujo 1: obtener la solicitud (detalle + Excel) ---
        resultado.paso = "Flujo 1 (Appian)"
        solicitud = flujo1_appian.obtener_solicitud(
            client, case_id, fecha_vencimiento=caso.fecha_vencimiento, logger=logger
        )

        # --- Flujo 2: transformar al formato macro ---
        resultado.paso = "Flujo 2 (Transformación)"
        archivos = flujo2_procesar.procesar_solicitud(solicitud, logger=logger)
        resultado.archivos_generados = archivos

        # --- Flujo 3: carga a SAP (STUB, pendiente) ---
        resultado.paso = "Flujo 3 (SAP - pendiente)"
        for archivo in archivos:
            flujo3_sap.cargar_a_sap(archivo, logger=logger)

        resultado.exito = True
        resultado.paso = "Completado"
        logger.info("Caso %s procesado correctamente.", case_id)

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

        # 1) Abrir Appian + login (si falla, abortamos con elegancia).
        client = AppianClient(logger=logger)
        client.start(user, password)
        logger.info("Sesión de Appian iniciada correctamente.")

        # 2) Leer la bandeja para saber qué casos hay pendientes (ya en orden
        #    de prioridad por fecha de vencimiento).
        casos = flujo1_appian.listar_casos_pendientes(client, logger=logger)
        resumen.total = len(casos)

        # 3) Procesar caso por caso, aislando fallos.
        for caso in casos:
            resultado = _procesar_un_caso(client, caso, logger)
            resumen.resultados.append(resultado)
            if resultado.exito:
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


def _emitir_resumen(resumen, logger):
    """Escribe en el log el resumen final del lote."""
    logger.info("=== Resumen de la ejecución ===")
    logger.info("Total de casos:   %s", resumen.total)
    logger.info("Procesados OK:    %s", resumen.exitosos)
    logger.info("Fallidos:         %s", resumen.fallidos)

    if resumen.fallidos:
        logger.info("Detalle de casos fallidos:")
        for r in resumen.resultados:
            if not r.exito:
                logger.info("  - %s | %s | %s", r.case_id, r.paso, r.motivo)

    logger.info("=== Fin de la ejecución ===")
