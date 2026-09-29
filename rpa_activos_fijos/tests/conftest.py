"""Configuración de pytest: permite importar los módulos del bot (config, core, ...)."""

import os
import sys
import types

RAIZ_BOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ_BOT not in sys.path:
    sys.path.insert(0, RAIZ_BOT)

# La librería corporativa de Appian solo existe en el venv corporativo. Fuera
# de él se reemplaza por un módulo vacío para poder importar el orquestador
# (las pruebas usan un cliente de Appian falso, nunca la librería real).
try:
    import an0016001_appian_flow.appian_flow  # noqa: F401
except ImportError:
    _lib = types.ModuleType("an0016001_appian_flow")
    _sub = types.ModuleType("an0016001_appian_flow.appian_flow")
    _sub.AppianFlow = object
    sys.modules["an0016001_appian_flow"] = _lib
    sys.modules["an0016001_appian_flow.appian_flow"] = _sub
