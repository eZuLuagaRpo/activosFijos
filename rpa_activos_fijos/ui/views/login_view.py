"""
ui/views/login_view.py — Vista de login (credenciales de Appian).

La usuaria escribe su usuario y contraseña de Appian y presiona "Iniciar".
Estas credenciales se guardan SOLO en memoria (nunca en disco) y se reutilizarán
para SAP en el futuro. Al presionar "Iniciar" se valida que no estén vacías y se
pasa a la vista de consola.
"""

import customtkinter as ctk


class LoginView(ctk.CTkFrame):
    """Formulario de credenciales de Appian."""

    def __init__(self, master, colors, app):
        super().__init__(master, fg_color="transparent", width=430, height=560)
        self.colors = colors
        self.app = app

        self.pack_propagate(False)
        self.grid_propagate(False)

        card = ctk.CTkFrame(
            self,
            width=430,
            height=520,
            fg_color=colors["card"],
            corner_radius=24,
            border_width=1,
            border_color=colors["border"],
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)
        card.grid_propagate(False)

        ctk.CTkLabel(
            card,
            text="Bancolombia",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=colors["dark"],
        ).pack(pady=(26, 2))

        ctk.CTkLabel(
            card,
            text="RPA Activos Fijos",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=colors["secondary"],
        ).pack(pady=(0, 6))

        ctk.CTkFrame(
            card, height=3, width=72, fg_color=colors["yellow"], corner_radius=10
        ).pack(pady=(0, 18))

        ctk.CTkLabel(
            card,
            text="Credenciales de Appian",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=colors["secondary"],
        ).pack(pady=(2, 8))

        self.user_entry = ctk.CTkEntry(
            card,
            placeholder_text="usuario@bancolombia.com.co",
            width=300,
            height=38,
            corner_radius=12,
            fg_color=colors["input"],
            border_color=colors["input_border"],
            text_color=colors["dark"],
            placeholder_text_color=colors["muted"],
        )
        self.user_entry.pack(pady=8)

        self.pass_entry = ctk.CTkEntry(
            card,
            placeholder_text="Contraseña",
            show="*",
            width=300,
            height=38,
            corner_radius=12,
            fg_color=colors["input"],
            border_color=colors["input_border"],
            text_color=colors["dark"],
            placeholder_text_color=colors["muted"],
        )
        self.pass_entry.pack(pady=8)

        self.msg_label = ctk.CTkLabel(
            card,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=colors["danger"],
            wraplength=300,
        )
        self.msg_label.pack(pady=(6, 4))

        ctk.CTkButton(
            card,
            text="Iniciar",
            width=220,
            height=42,
            corner_radius=14,
            fg_color=colors["primary"],
            text_color=colors["dark"],
            hover_color=colors["hover_yellow"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_iniciar,
        ).pack(pady=(14, 6))

        ctk.CTkLabel(
            card,
            text="Tus credenciales se usan solo durante la ejecución.\nNo se guardan en disco.",
            font=ctk.CTkFont(size=11),
            text_color=colors["muted"],
            justify="center",
        ).pack(pady=(4, 0))

        # Permitir iniciar con Enter.
        self.pass_entry.bind("<Return>", lambda e: self._on_iniciar())

    def _on_iniciar(self):
        """Valida campos y, si están completos, avanza a la consola."""
        user = self.user_entry.get().strip()
        password = self.pass_entry.get()

        if not user or not password:
            self.msg_label.configure(text="Ingresa usuario y contraseña.")
            return

        self.msg_label.configure(text="")
        # Guardamos credenciales en memoria en la app y navegamos a la consola.
        self.app.set_credenciales(user, password)
        self.app.mostrar_consola()
