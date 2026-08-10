"""
Módulo encargado de la gestión de descargas de archivos.

Contiene la clase DownloadManager, la cual permite:
- Detectar nuevas descargas en un directorio
- Validar que los archivos se descarguen completamente
- Controlar tiempos de espera y fallos en el proceso

Este componente es utilizado para asegurar que los archivos
descargados desde la aplicación estén completos y disponibles
antes de continuar con el flujo.
"""

import os
import time

TEMP_EXTENSIONS = (".crdownload", ".drcdown", ".tmp")


class DownloadManager:
    """
    Gestiona el proceso de descarga de archivos desde el navegador.

    Permite:
    - Detectar archivos nuevos en el directorio de descargas
    - Validar que el archivo haya terminado de descargarse
    - Manejar timeouts y errores durante la descarga
    """

    def __init__(self, driver, timeout):
        """
        Inicializa el gestor de descargas.

        Args:
            driver: Instancia del WebDriver de Selenium.
            timeout (int): Tiempo máximo de espera para la descarga (en segundos).
        """
        self.driver = driver
        self.timeout = timeout

    def wait_for_download(self, path):
        """
        Espera hasta que un archivo se descargue completamente en el directorio indicado.

        El método:
        - Detecta archivos nuevos en la carpeta
        - Ignora archivos temporales (descargas incompletas)
        - Verifica estabilidad del tamaño del archivo para confirmar finalización
        - Controla timeout del proceso

        Args:
            path (str): Ruta del directorio de descargas.

        Returns:
            str: Nombre del archivo descargado.

        Raises:
            Exception:
                - Si el navegador se cierra antes de finalizar la descarga
                - Si ocurre un timeout
                - Si ocurre cualquier error durante el proceso
        """
        try:
            start_time = time.time()
            initial_files = set(os.listdir(path))
            last_size = {}

            while True:

                # Si el navegador ya se cerró, abortar
                if not self.driver.service.is_connectable():
                    raise Exception(
                        "El navegador se cerró antes de finalizar la descarga"
                    )

                current_files = set(os.listdir(path))
                new_files = current_files - initial_files

                # Filtrar archivos temporales
                valid_files = [
                    f for f in new_files if not f.lower().endswith(TEMP_EXTENSIONS)
                ]

                # Verificar estabilidad del archivo
                for file in valid_files:
                    file_path = os.path.join(path, file)
                    size = os.path.getsize(file_path)

                    if file not in last_size:
                        last_size[file] = size
                        continue

                    # Si el tamaño no cambia, la descarga está completa
                    if last_size[file] == size:
                        return file

                    last_size[file] = size

                if time.time() - start_time > self.timeout:
                    raise Exception("Timeout esperando la descarga del archivo")

                time.sleep(2)

        except Exception as e:
            raise Exception(
                f"No fue posible completar la descarga del informe: {str(e)}"
            ) from e
