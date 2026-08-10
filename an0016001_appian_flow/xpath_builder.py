"""
Módulo utilitario para la construcción dinámica de selectores XPath.

Contiene la clase XPathBuilder, que proporciona métodos estáticos
para generar localizadores reutilizables en Selenium.

Permite abstraer la lógica de construcción de selectores,
haciendo el código más legible, mantenible y desacoplado
de la estructura HTML específica.
"""

from selenium.webdriver.common.by import By


class XPathBuilder:
    """
    Clase utilitaria para la generación de selectores XPath.

    Proporciona métodos reutilizables para localizar elementos comunes
    como botones, inputs, labels y opciones de dropdown, evitando
    duplicar lógica en distintas partes del código.
    """

    @staticmethod
    def button_by_text(text, equal=False):
        """
        Construye un selector XPath para botones basados en texto visible.

        Args:
            text (str): Texto del botón.
            equal (bool, opcional):
                - True: coincidencia exacta
                - False: contiene el texto

        Returns:
            tuple: Localizador (By.XPATH, xpath)
        """
        if equal:
            return (By.XPATH, f"//button[.//span[normalize-space(.)='{text}']]")

        return (
            By.XPATH,
            f"//button[.//span[contains(normalize-space(.), '{text}')]]",
        )

    @staticmethod
    def input_by_id(text):
        """
        Construye un selector para input basado en ID.

        Args:
            text (str): ID del input.

        Returns:
            tuple: Localizador (By.ID, id)
        """
        return (By.ID, text)

    @staticmethod
    def input_by_placeholder(text):
        """
        Construye un selector XPath para inputs por placeholder.

        Args:
            text (str): Texto del placeholder.

        Returns:
            tuple: Localizador XPath.
        """
        return (By.XPATH, f"//input[contains(@placeholder, '{text}') and @type='text']")

    @staticmethod
    def input_picker(text):
        """
        Construye un selector para campos de fecha tipo range picker.

        Args:
            text (str): Texto del label asociado (Ej: 'Desde', 'Hasta').

        Returns:
            tuple: Localizador XPath.
        """
        return (
            By.XPATH,
            (
                f"//span[normalize-space()='{text}']"
                "/following::input[@data-testid='DateRangeInputPicker-textInput'][1]"
            ),
        )

    @staticmethod
    def by_data_testid(testid):
        """
        Construye un selector usando el atributo data-testid.

        Args:
            testid (str): Valor del atributo data-testid.

        Returns:
            tuple: Localizador XPath.
        """
        return (By.XPATH, f"//*[@data-testid='{testid}']")

    @staticmethod
    def by_data_text(text):
        """
        Construye un selector usando el atributo data-text.

        Args:
            text (str): Valor del atributo data-text.

        Returns:
            tuple: Localizador XPath.
        """
        return (By.XPATH, f"//*[@data-text='{text}']")

    @staticmethod
    def dropdown_option(text):
        """
        Construye un selector para una opción de dropdown.

        Args:
            text (str): Texto visible de la opción.

        Returns:
            tuple: Localizador XPath.
        """
        return (By.XPATH, f"//li[@role='option' and normalize-space(.)='{text}']")

    @staticmethod
    def label_following_input(label):
        """
        Construye un selector para un input asociado a un label.

        Args:
            label (str): Texto del label.

        Returns:
            tuple: Localizador XPath.
        """
        return (By.XPATH, f"//label[normalize-space(.)='{label}']/ancestor::div//input")

    @staticmethod
    def contains_text(tag, text, equal=False):
        """
        Construye un selector XPath para elementos que contienen texto.

        Args:
            tag (str): Etiqueta HTML (ej: 'div', 'span', 'a').
            text (str): Texto a buscar.
            equal (bool, opcional):
                - True: coincidencia exacta
                - False: contiene texto

        Returns:
            tuple: Localizador XPath.
        """
        if equal:
            return (By.XPATH, f"//{tag}[normalize-space(.)='{text}']")

        return (By.XPATH, f"//{tag}[contains(normalize-space(.), '{text}')]")

    @staticmethod
    def contains_class(tag, text):
        """
        Construye un selector XPath para elementos que contienen una clase específica.

        Args:
            tag (str): Etiqueta HTML.
            text (str): Texto de la clase.

        Returns:
            tuple: Localizador XPath.
        """
        return (By.XPATH, f".//{tag}[contains(@class, '{text}')]")
