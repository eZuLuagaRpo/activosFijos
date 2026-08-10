"""
Módulo encargado de la creación y configuración del WebDriver.

Proporciona la función create_driver, la cual:
- Inicializa el navegador (Edge o Chrome)
- Configura preferencias de descarga
- Establece opciones de ejecución del navegador
- Retorna el driver y el objeto de espera explícita

Este módulo es la base de la infraestructura de automatización.
"""

import os
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions


def create_driver(browser="edge", timeout=60, download_dir=None):
    """
    Crea y configura una instancia de WebDriver.

    Configura el navegador con:
    - Opciones de ejecución (maximizado, logs)
    - Preferencias de descarga controladas
    - Tiempo de espera explícito (WebDriverWait)

    Args:
        browser (str, opcional): Navegador a utilizar ("edge" o "chrome").
        timeout (int, opcional): Tiempo de espera para elementos.
        download_dir (str, opcional): Ruta de descargas.

    Returns:
        tuple:
            - driver: Instancia del WebDriver configurado
            - wait: WebDriverWait asociado al driver

    Raises:
        ValueError: Si el navegador especificado no es soportado.
    """

    browser = browser.lower()

    # Carpeta de descargas controlada
    if not download_dir:
        download_dir = os.path.join(os.getcwd(), "downloads")

    os.makedirs(download_dir, exist_ok=True)

    # Preferencias de descarga (Chrome / Edge)
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }

    if browser == "chrome":
        options = ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option("prefs", prefs)

        service = ChromeService()
        driver = webdriver.Chrome(service=service, options=options)

    elif browser == "edge":
        options = EdgeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-logging")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option("prefs", prefs)

        service = EdgeService()
        driver = webdriver.Edge(service=service, options=options)

    else:
        raise ValueError(f"Navegador no soportado: {browser}. Use 'chrome' o 'edge'.")

    wait = WebDriverWait(driver, timeout)

    # Exponer la ruta al resto del flujo
    driver.download_dir = download_dir

    return driver, wait
