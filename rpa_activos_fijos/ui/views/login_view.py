"""
ui/views/login_view.py — Vista de login (credenciales de Appian).

La usuaria escribe su usuario y contraseña de Appian y presiona "Iniciar".
Estas credenciales se guardan SOLO en memoria (nunca en disco) y se reutilizarán
para SAP en el futuro. Al presionar "Iniciar" se valida que no estén vacías, se
pasa a la vista de consola y el bot ARRANCA DE UNA (sin un clic aparte de
"Ejecutar"), para que la usuaria dé el menor número de clics posible.
"""

import os

import customtkinter as ctk
from PIL import Image

from config import ASSETS_DIR


class LoginView(ctk.CTkFrame):
    """Formulario de credenciales de Appian."""

    def __init__(self, master, colors, app):
        super().__init__(master, fg_color="transparent", width=440, height=600)
        self.colors = colors
        self.app = app

        self.pack_propagate(False)
        self.grid_propagate(False)

        # "Sombra" de la tarjeta: un rectángulo apenas más oscuro, desplazado
        # unos pocos píxeles, para dar sensación de profundidad sin depender
        # de transparencia real (tkinter no la soporta en frames).
        ctk.CTkFrame(
            self,
            width=400,
            height=540,
            fg_color=colors["card_shadow"],
            corner_radius=26,
        ).place(relx=0.5, rely=0.5, anchor="center", x=6, y=8)

        card = ctk.CTkFrame(
            self,
            width=400,
            height=540,
            fg_color=colors["card"],
            corner_radius=24,
            border_width=1,
            border_color=colors["border"],
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)
        card.grid_propagate(False)

        self._logo_img = self._cargar_logo()
        if self._logo_img is not None:
            ctk.CTkLabel(card, image=self._logo_img, text="").pack(pady=(30, 10))
        else:
            ctk.CTkLabel(card, text="").pack(pady=(14, 0))

        ctk.CTkLabel(
            card,
            text="BANCOLOMBIA",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=colors["muted"],
        ).pack(pady=(0, 2))

        ctk.CTkLabel(
            card,
            text="RPA Activos Fijos",
            font=ctk.CTkFont(size=25, weight="bold"),
            text_color=colors["secondary"],
        ).pack(pady=(0, 8))

        ctk.CTkFrame(
            card, height=4, width=64, fg_color=colors["yellow"], corner_radius=10
        ).pack(pady=(0, 22))

        ctk.CTkLabel(
            card,
            text="Credenciales de Appian",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=colors["secondary"],
        ).pack(pady=(0, 14))

        self._campo(card, "Usuario")
        self.user_entry = ctk.CTkEntry(
            card,
            placeholder_text="usuario@bancolombia.com.co",
            width=300,
            height=40,
            corner_radius=12,
            fg_color=colors["input"],
            border_color=colors["input_border"],
            text_color=colors["dark"],
            placeholder_text_color=colors["muted"],
        )
        self.user_entry.pack(pady=(0, 14))

        self._campo(card, "Contraseña")
        self.pass_entry = ctk.CTkEntry(
            card,
            placeholder_text="••••••••",
            show="*",
            width=300,
            height=40,
            corner_radius=12,
            fg_color=colors["input"],
            border_color=colors["input_border"],
            text_color=colors["dark"],
            placeholder_text_color=colors["muted"],
        )
        self.pass_entry.pack(pady=(0, 4))

        self.msg_label = ctk.CTkLabel(
            card,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=colors["danger"],
            wraplength=300,
        )
        self.msg_label.pack(pady=(6, 2))

        ctk.CTkButton(
            card,
            text="Iniciar",
            width=300,
            height=44,
            corner_radius=14,
            fg_color=colors["primary"],
            text_color=colors["dark"],
            hover_color=colors["hover_yellow"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_iniciar,
        ).pack(pady=(16, 10))

        ctk.CTkLabel(
            card,
            text="Tus credenciales se usan solo durante la ejecución.\nNo se guardan en disco.",
            font=ctk.CTkFont(size=11),
            text_color=colors["muted"],
            justify="center",
        ).pack(pady=(0, 0))

        # Permitir iniciar con Enter.
        self.pass_entry.bind("<Return>", lambda e: self._on_iniciar())

    def _campo(self, card, texto):
        """Label pequeño y discreto encima de un campo de entrada."""
        ctk.CTkLabel(
            card,
            text=texto,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["muted"],
            anchor="w",
        ).pack(fill="x", padx=50, pady=(0, 3))

    def _cargar_logo(self):
        """Carga el ícono circular de marca para el encabezado de la tarjeta."""
        ruta = os.path.join(ASSETS_DIR, "logo.png")
        if not os.path.exists(ruta):
            return None
        try:
            imagen = Image.open(ruta)
            return ctk.CTkImage(light_image=imagen, dark_image=imagen, size=(52, 52))
        except Exception:
            return None

    def _on_iniciar(self):
        """Valida campos y, si están completos, avanza a la consola."""
        user = self.user_entry.get().strip()
        password = self.pass_entry.get()

        if not user or not password:
            self.msg_label.configure(text="Ingresa usuario y contraseña.")
            return

        self.msg_label.configure(text="")
        # Guardamos credenciales en memoria en la app, navegamos a la consola
        # y arrancamos el bot de inmediato (sin un clic extra de "Ejecutar").
        self.app.set_credenciales(user, password)
        self.app.mostrar_consola()
        self.app.console_view.iniciar_ejecucion()
