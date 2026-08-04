"""
ui/app_window.py — Ventana principal y navegación entre vistas.

Guarda las credenciales en MEMORIA (nunca en disco) y alterna entre la vista de
login y la de consola. Usa el fondo y el ícono de la carpeta assets.
"""

import os

import customtkinter as ctk
from PIL import Image

from config import APP_NOMBRE, ASSETS_DIR
from ui.styles.theme import apply_theme
from ui.views.console_view import ConsoleView
from ui.views.login_view import LoginView


class AppWindow(ctk.CTk):
    """Ventana raíz de la aplicación."""

    def __init__(self):
        super().__init__()

        self.title(APP_NOMBRE)
        self.geometry("900x680")
        self.resizable(False, False)

        self.colors = apply_theme()
        self.configure(fg_color=self.colors["background"])

        # Credenciales SOLO en memoria.
        self._user = None
        self._password = None

        self._configurar_icono()
        self._configurar_fondo()

        # Instanciamos las vistas una sola vez.
        self.login_view = LoginView(self, self.colors, self)
        self.console_view = ConsoleView(self, self.colors, self)

        self.mostrar_login()

    # -- Assets ---------------------------------------------------------------
    def _configurar_icono(self):
        icono = os.path.join(ASSETS_DIR, "icon.ico")
        if os.path.exists(icono):
            try:
                self.iconbitmap(icono)
            except Exception:
                pass  # el ícono no es crítico

    def _configurar_fondo(self):
        fondo = os.path.join(ASSETS_DIR, "fondo.png")
        if os.path.exists(fondo):
            try:
                imagen = Image.open(fondo)
                self.bg_image = ctk.CTkImage(
                    light_image=imagen, dark_image=imagen, size=(900, 680)
                )
                self.bg_label = ctk.CTkLabel(self, image=self.bg_image, text="")
                self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception:
                pass  # el fondo tampoco es crítico

    # -- Credenciales (en memoria) -------------------------------------------
    def set_credenciales(self, user, password):
        self._user = user
        self._password = password

    def get_credenciales(self):
        return self._user, self._password

    # -- Navegación -----------------------------------------------------------
    def _ocultar_todo(self):
        self.login_view.place_forget()
        self.console_view.place_forget()

    def mostrar_login(self):
        self._ocultar_todo()
        self.login_view.place(relx=0.5, rely=0.5, anchor="center")

    def mostrar_consola(self):
        self._ocultar_todo()
        self.console_view.place(relx=0.5, rely=0.5, anchor="center")
