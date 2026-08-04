"""
appian/appian_client.py — Wrapper delgado sobre AppianFlow.

¿Por qué existe este archivo? La librería `an0016001_appian_flow` NO lanza
excepciones cuando algo falla: SIEMPRE devuelve un diccionario con la forma
    {"success": bool, "message": str, "data": ...}
Si nadie revisa `success`, el bot seguiría trabajando con datos malos SIN
enterarse. Este wrapper centraliza esa validación:

  - Llama al método real de la librería.
  - Revisa `success`.
  - Si es False, clasifica el `message` y lanza una excepción propia
    (ver core/exceptions.py) para que el flujo pueda decidir qué hacer.
  - Si es True, devuelve directamente el `data`.

Así, el resto del código usa try/except normal y no tiene que acordarse de
revisar `success` en cada llamada.
"""

# La clase orquestadora vive en el submódulo appian_flow. El __init__ del paquete
# NO la re-exporta, por eso se importa desde su módulo directamente.
from an0016001_appian_flow.appian_flow import AppianFlow

from config import (
    APPIAN_URL,
    BROWSER,
    DOWNLOAD_DIR,
    TIMEOUT,
    TIMEOUT_FILES,
)
from core.exceptions import (
    ActividadTomadaError,
    AppianError,
    CasoNoEncontradoError,
    SinAdjuntosError,
    TimeoutAppianError,
)


def _clasificar_error(mensaje):
    """
    Traduce el `message` de la librería a la excepción propia más adecuada.
    La clasificación es por palabras clave; si aparecen mensajes nuevos, se
    amplían aquí las reglas.
    """
    texto = (mensaje or "").lower()

    if "timeout" in texto or "tiempo" in texto:
        return TimeoutAppianError(mensaje)
    if "no encontrado" in texto or "no existe" in texto or "buscando el caso" in texto:
        return CasoNoEncontradoError(mensaje)
    if "tomad" in texto or "otro usuario" in texto:
        return ActividadTomadaError(mensaje)
    if "adjunto" in texto or "archivo" in texto:
        return SinAdjuntosError(mensaje)
    return AppianError(mensaje)


class AppianClient:
    """
    Envoltorio de AppianFlow. Cada método:
      1. Llama al método real de la librería.
      2. Valida `success`.
      3. Devuelve `data` o lanza una excepción propia.
    """

    def __init__(self, logger=None):
        self.logger = logger
        # Instanciamos la librería con la configuración central (nada hardcodeado).
        self._flow = AppianFlow(
            url=APPIAN_URL,
            download_dir=DOWNLOAD_DIR,
            browser=BROWSER,
            timeout=TIMEOUT,
            timeout_files=TIMEOUT_FILES,
        )

    # -- Utilidad interna: valida cualquier respuesta de la librería -----------
    def _validar(self, respuesta, paso):
        """
        Revisa una respuesta {success, message, data}.
        Si success es False, registra y lanza la excepción clasificada.
        Si es True, devuelve `data`.
        """
        # Defensa por si la librería devolviera algo inesperado.
        if not isinstance(respuesta, dict):
            raise AppianError(f"Respuesta inesperada en '{paso}': {respuesta!r}")

        if not respuesta.get("success"):
            mensaje = respuesta.get("message", "sin detalle")
            if self.logger:
                self.logger.error("Appian falló en '%s': %s", paso, mensaje)
            raise _clasificar_error(mensaje)

        return respuesta.get("data")

    # -- Métodos de negocio ----------------------------------------------------
    def start(self, user, password):
        """Abre Appian y hace login. Devuelve data (o lanza excepción)."""
        if self.logger:
            # OJO: nunca registramos la contraseña.
            self.logger.info("Iniciando sesión en Appian con usuario '%s'.", user)
        respuesta = self._flow.start(user, password)
        return self._validar(respuesta, "login en Appian")

    def search_case(self, case_id):
        """Busca y abre el detalle de un caso por su ID."""
        if self.logger:
            self.logger.info("Abriendo caso %s...", case_id)
        respuesta = self._flow.search_case(case_id)
        return self._validar(respuesta, f"búsqueda del caso {case_id}")

    def get_case_data(self, case_id, download_attachments=True):
        """
        Obtiene el detalle del caso. REQUIERE haber llamado antes a search_case.
        Devuelve data = {"info": DataFrame label|value, "files": [ {file,path,full_path} ]}.
        """
        if self.logger:
            self.logger.info("Leyendo datos del caso %s...", case_id)
        respuesta = self._flow.get_case_data(case_id, download_attachments)
        return self._validar(respuesta, f"lectura de datos del caso {case_id}")

    def cerrar(self):
        """Cierra el navegador. Debe llamarse SIEMPRE en un finally."""
        try:
            self._flow.cerrar()
            if self.logger:
                self.logger.info("Navegador cerrado.")
        except Exception as e:  # el cierre nunca debe tumbar el programa
            if self.logger:
                self.logger.warning("No se pudo cerrar el navegador limpiamente: %s", e)

    # -- Acceso controlado al driver (lo necesita el bandeja_reader) -----------
    @property
    def driver(self):
        """WebDriver de Selenium subyacente (para leer la bandeja)."""
        return self._flow.driver

    @property
    def wait(self):
        """WebDriverWait subyacente (esperas explícitas)."""
        return self._flow.wait

    @property
    def url(self):
        """URL base de Appian ya normalizada por la librería."""
        return self._flow.url
