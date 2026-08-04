"""
app.py — Punto de entrada del RPA "Parametrización de Activos Fijos".

Lanza la interfaz gráfica. Es el archivo que PyInstaller empaqueta como .exe.
"""

from ui.app_window import AppWindow


def main():
    app = AppWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
