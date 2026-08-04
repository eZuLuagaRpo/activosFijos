"""
core/texto.py — Utilidades para normalizar texto.

Appian puede devolver los valores con mayúsculas, tildes o espacios de más
("Diferido ", "DIFERIDOS Y RENOVACIONES", "Creación"). Para poder compararlos
contra nuestros alias de config.py, primero los "normalizamos": todo a
minúsculas, sin tildes y sin espacios sobrantes.
"""

import unicodedata


def normalizar(texto):
    """
    Devuelve el texto en minúsculas, sin tildes y sin espacios extra.
    Ejemplo: "  Creación " -> "creacion".
    """
    if texto is None:
        return ""
    texto = str(texto).strip().lower()
    # Descompone las tildes y elimina los caracteres de acento.
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    # Colapsa espacios múltiples en uno solo.
    texto = " ".join(texto.split())
    return texto


def mapear_alias(valor_crudo, tabla_alias):
    """
    Normaliza `valor_crudo` y lo busca en `tabla_alias` (dict alias->canónico).
    Devuelve el valor canónico o None si no hay coincidencia.
    """
    clave = normalizar(valor_crudo)
    return tabla_alias.get(clave)
