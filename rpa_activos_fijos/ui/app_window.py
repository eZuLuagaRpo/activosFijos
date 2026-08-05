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
        """
        Fondo claro (no el splash negro original, que no combinaba con las
        tarjetas blancas del centro) con acentos decorativos de marca —los
        trazos de onda de colores Bancolombia— apenas insinuados en las
        esquinas, MUY sutiles para no competir con el contenido.
        """
        # Base clara detrás de todo.
        self.bg_label = ctk.CTkLabel(self, text="", fg_color=self.colors["background"])
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self._onda_images = []  # referencias vivas (si no, el GC las borra)
        self._agregar_onda(
            "trazo-onda-11.png", ancho=620, x=-90, y=-70, opacidad=0.16
        )
        self._agregar_onda(
            "trazo-onda-12.png",
            ancho=620,
            x=900 - 620 + 90,
            y=680 - 260,
            opacidad=0.16,
            rotar_180=True,
        )

    def _agregar_onda(self, archivo, ancho, x, y, opacidad=0.16, rotar_180=False):
        """Coloca una imagen decorativa (trazo de onda) semi-transparente."""
        ruta = os.path.join(ASSETS_DIR, archivo)
        if not os.path.exists(ruta):
            return
        try:
            imagen = Image.open(ruta).convert("RGBA")
            if rotar_180:
                imagen = imagen.transpose(Image.ROTATE_180)
            alto = int(ancho * imagen.height / imagen.width)
            imagen = imagen.resize((ancho, alto), Image.LANCZOS)
            # Bajamos la opacidad multiplicando el canal alfa (aquí no hay
            # transparencia real de widget, solo de la imagen en sí).
            alpha = imagen.getchannel("A").point(lambda a, o=opacidad: int(a * o))
            imagen.putalpha(alpha)

            ctk_img = ctk.CTkImage(light_image=imagen, dark_image=imagen, size=(ancho, alto))
            self._onda_images.append(ctk_img)  # evita que el GC la recoja

            label = ctk.CTkLabel(self, image=ctk_img, text="")
            label.place(x=x, y=y)
        except Exception:
            pass  # es decorativo, nunca debe tumbar el arranque

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
