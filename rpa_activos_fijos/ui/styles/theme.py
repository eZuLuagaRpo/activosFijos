"""
ui/styles/theme.py — Tema claro y paleta Bancolombia.

Basado en el theme.py de la UI de ejemplo. Look limpio tipo app de Bancolombia:
fondo claro, tarjetas con esquinas redondeadas, acento amarillo #fdda24 y textos
oscuros #2c2a29.
"""

import customtkinter as ctk


def apply_theme():
    """Activa el modo claro y devuelve el diccionario de colores de la marca."""
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    return {
        # Paleta primaria Bancolombia
        "white": "#FFFFFF",
        "dark": "#2c2a29",

        # Paleta secundaria Bancolombia
        "yellow": "#fdda24",
        "green": "#00c389",
        "purple": "#9063cd",
        "orange": "#ff7f41",
        "pink": "#f5b6cd",
        "blue": "#59cbe8",

        # Alias de uso general
        "primary": "#fdda24",
        "secondary": "#2c2a29",
        "card": "#FFFFFF",

        # Apoyos UI
        "background": "#F7F7F5",
        "border": "#E4E1DD",
        "muted": "#706C68",
        "input": "#FFFFFF",
        "input_border": "#D8D4CF",
        "hover_yellow": "#E6C800",
        "hover_dark": "#1F1D1C",
        "disabled": "#B8B4AF",
        "danger": "#D93025",
        "success": "#00875A",

        # Sombra de tarjeta (rectángulo sólido, offset, detrás de la tarjeta
        # blanca; tkinter no soporta alpha real, así que se simula con un
        # tono cálido apenas más oscuro que el fondo).
        "card_shadow": "#E3DFD8",

        # Colores para la consola de logs (fondo oscuro para leer cómodo)
        "console_bg": "#1F1D1C",
        "console_text": "#F2F2F2",
        "console_info": "#59cbe8",
        "console_warn": "#fdda24",
        "console_error": "#ff6b6b",
    }
