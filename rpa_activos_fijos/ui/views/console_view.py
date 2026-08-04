"""
ui/views/console_view.py — Vista de consola de logs en vivo.

Muestra en tiempo real lo que hace el bot. Puntos clave de concurrencia:
  - Al presionar "Ejecutar", el bot corre en un HILO APARTE (threading.Thread)
    para que la ventana NUNCA se congele.
  - El bot y la UI se comunican con una COLA thread-safe (queue.Queue): el bot
    "deposita" mensajes de log en la cola; la UI los recoge periódicamente con
    `after()` (bucle no bloqueante).
  - El área de texto es de SOLO LECTURA.
"""

import queue
import threading

import customtkinter as ctk

import orquestador


class ConsoleView(ctk.CTkFrame):
    """Consola de ejecución + estado + botones Ejecutar/Volver."""

    def __init__(self, master, colors, app):
        super().__init__(master, fg_color="transparent", width=760, height=560)
        self.colors = colors
        self.app = app

        # Cola de logs (bot -> UI) y bandera de ejecución en curso.
        self.cola = queue.Queue()
        self.ejecutando = False
        self.hilo = None

        self.pack_propagate(False)
        self.grid_propagate(False)

        card = ctk.CTkFrame(
            self,
            width=760,
            height=560,
            fg_color=colors["card"],
            corner_radius=24,
            border_width=1,
            border_color=colors["border"],
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        # --- Encabezado ---
        cabecera = ctk.CTkFrame(card, fg_color="transparent")
        cabecera.pack(fill="x", padx=24, pady=(20, 8))

        ctk.CTkLabel(
            cabecera,
            text="Consola de ejecución",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=colors["secondary"],
        ).pack(side="left")

        self.estado_label = ctk.CTkLabel(
            cabecera,
            text="● Inactivo",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=colors["muted"],
        )
        self.estado_label.pack(side="right")

        # --- Área de logs (solo lectura) ---
        self.textbox = ctk.CTkTextbox(
            card,
            width=712,
            height=380,
            corner_radius=14,
            fg_color=colors["console_bg"],
            text_color=colors["console_text"],
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
        )
        self.textbox.pack(padx=24, pady=8)
        self.textbox.configure(state="disabled")

        # --- Botones ---
        botones = ctk.CTkFrame(card, fg_color="transparent")
        botones.pack(fill="x", padx=24, pady=(6, 18))

        self.volver_btn = ctk.CTkButton(
            botones,
            text="Volver",
            width=140,
            height=40,
            corner_radius=14,
            fg_color=colors["white"],
            text_color=colors["dark"],
            border_width=1,
            border_color=colors["dark"],
            hover_color=colors["border"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_volver,
        )
        self.volver_btn.pack(side="left")

        self.ejecutar_btn = ctk.CTkButton(
            botones,
            text="Ejecutar",
            width=180,
            height=40,
            corner_radius=14,
            fg_color=colors["primary"],
            text_color=colors["dark"],
            hover_color=colors["hover_yellow"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_ejecutar,
        )
        self.ejecutar_btn.pack(side="right")

        # Empezamos a vaciar la cola periódicamente.
        self._consumir_cola()

    # -- Estado visual ---------------------------------------------------------
    def _set_estado(self, texto, color):
        self.estado_label.configure(text="● " + texto, text_color=color)

    def _escribir(self, nivel, mensaje):
        """Inserta una línea en el textbox (coloreada según el nivel)."""
        self.textbox.configure(state="normal")
        self.textbox.insert("end", mensaje + "\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    # -- Bucle de consumo de la cola (no bloqueante) --------------------------
    def _consumir_cola(self):
        """Vacía la cola de logs hacia el textbox. Se re-agenda con after()."""
        try:
            while True:
                nivel, mensaje = self.cola.get_nowait()
                self._escribir(nivel, mensaje)
        except queue.Empty:
            pass
        # Volver a revisar en 100 ms (esto mantiene la UI fluida).
        self.after(100, self._consumir_cola)

    # -- Acciones de botones ---------------------------------------------------
    def _on_ejecutar(self):
        if self.ejecutando:
            return

        user, password = self.app.get_credenciales()
        if not user or not password:
            self._set_estado("Error", self.colors["danger"])
            self._escribir("ERROR", "No hay credenciales. Vuelve al login.")
            return

        self.ejecutando = True
        self.ejecutar_btn.configure(state="disabled")
        self.volver_btn.configure(state="disabled")
        self._set_estado("Ejecutando", self.colors["blue"])

        # Lanzamos el bot en un hilo aparte. daemon=True para que no bloquee el
        # cierre de la ventana.
        self.hilo = threading.Thread(
            target=self._correr_bot, args=(user, password), daemon=True
        )
        self.hilo.start()

    def _correr_bot(self, user, password):
        """Se ejecuta EN EL HILO SECUNDARIO. No debe tocar widgets directamente."""
        try:
            orquestador.ejecutar(user, password, cola=self.cola)
            estado, color = "Terminado", self.colors["success"]
        except Exception as e:
            # Cualquier fallo no controlado se informa por la cola.
            self.cola.put(("ERROR", f"Error no controlado: {e}"))
            estado, color = "Error", self.colors["danger"]
        finally:
            # Volvemos al hilo principal para tocar la UI de forma segura.
            self.after(0, lambda: self._finalizar(estado, color))

    def _finalizar(self, estado, color):
        self.ejecutando = False
        self.ejecutar_btn.configure(state="normal")
        self.volver_btn.configure(state="normal")
        self._set_estado(estado, color)

    def _on_volver(self):
        if self.ejecutando:
            return
        self.app.mostrar_login()
