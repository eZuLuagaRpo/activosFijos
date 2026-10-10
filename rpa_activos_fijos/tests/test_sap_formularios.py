"""
Pruebas de los FORMULARIOS de SAP en config.py (sin navegador).

1. AS01 (creación BRP, ya probada en SAP real) sigue EXACTAMENTE igual que
   antes de reorganizar config.py en un catálogo de campos compartido.
2. Coherencia de TODOS los formularios: cada columna que usan existe en la
   plantilla validada, no se repite, y cada paso está bien armado.
3. AS02 (modificación BRP): pantalla inicial, extras y pestañas.
"""

import pytest

import config
from validacion import router

# FOTO de los 29 pasos de AS01 tomada ANTES de reorganizar config.py en un
# catálogo (2026-10-09). La creación BRP ya se probó en SAP real: si esto
# cambia sin querer, esta prueba falla.
FOTO_AS01_BRP = [
    ('campo', 'A', 'Clase de activo fijo', ['//*[@id="M0:46:::2:29"]']),
    ('campo', 'B', 'Sociedad', ['//*[@id="M0:46:::3:29"]']),
    ('campo', 'C', 'Ctd. de activos fijos iguales', ['//*[@id="M0:46:::4:29"]']),
    ('enter', None, 'abrir el formulario completo', []),
    ('campo', 'D', 'Denominación', ['//*[@id="M0:46:3:1:2B256:1::1:22"]']),
    ('campo', 'AC', 'TXT.NUM.PRAL.AF', ['//*[@id="M0:46:3:1:2B256:1::3:22"]']),
    ('campo', 'F', 'Número de inventario', ['//*[@id="M0:46:3:1:2B256:1::6:22"]']),
    ('campo', 'G', 'Capitalizado el', ['//*[@id="M0:46:3:1:2B256:3::1:22"]']),
    ('pestana', None, 'pestaña 2 (centro de coste...)', ['//*[@id="M0:46:3:1::0:1-title"]']),
    ('campo', 'H', 'Centro de coste', ['//*[@id="M0:46:3:1:2B257:1::1:22"]']),
    ('campo', 'I', 'CeCo responsable', ['//*[@id="M0:46:3:1:2B257:1::2:22"]']),
    ('campo', 'J', 'Orden costes', ['//*[@id="M0:46:3:1:2B257:1::3:22"]']),
    ('campo', 'K', 'Centro', ['//*[@id="M0:46:3:1:2B257:1::5:22"]']),
    ('campo', 'L', 'Emplazamiento', ['//*[@id="M0:46:3:1:2B257:1::6:22"]']),
    ('campo', 'M', 'Matrícula vehículo', ['//*[@id="M0:46:3:1:2B257:1::8:22"]']),
    ('casilla', 'N', 'Activo fijo paralizado', ['//*[@id="M0:46:3:1:2B257:1::12:1-txt"]']),
    ('pestana', None, 'pestaña 3 (estado...)', ['//*[@id="M0:46:3:1::0:2-title"]']),
    ('campo', 'O', 'Estado', ['//*[@id="M0:46:3:1:2B258:1::1:22"]']),
    ('campo', 'P', 'Tipo', ['//*[@id="M0:46:3:1:2B258:1::2:22"]']),
    ('campo', 'Q', 'Procedencia', ['//*[@id="M0:46:3:1:2B258:1::3:22"]']),
    ('campo', 'R', 'Ubicación', ['//*[@id="M0:46:3:1:2B258:1::4:22"]']),
    ('pestana', None, 'pestaña 4 (acreedor...)', ['//*[@id="M0:46:3:1::0:3-title"]']),
    ('campo', 'S', 'Acreedor', ['//*[@id="M0:46:3:1:2B259:1::1:23"]']),
    ('campo', 'T', 'Fabricante', ['//*[@id="M0:46:3:1:2B259:1::2:23"]']),
    ('campo', 'U', 'Denominación de tipo', ['//*[@id="M0:46:3:1:2B259:1::7:23"]']),
    ('campo', 'V', 'Parte prod. propia', ['//*[@id="M0:46:3:1:2B259:1::12:23"]']),
    ('pestana', None, 'pestaña 5 (clave de agrupamiento...)', ['//*[@id="M0:46:3:1::0:4-title"]']),
    ('campo', 'W', 'Clave de agrupamiento', ['//*[@id="M0:46:3:1:2B260:1::1:22"]']),
    ('campo', 'X', 'Indicador propiedad', ['//*[@id="M0:46:3:1:2B260:1::2:22"]']),
]


def _foto(formulario):
    return [(p["tipo"], p.get("columna"), p.get("nombre"), list(p.get("xpath", ())))
            for p in formulario]


def test_as01_no_cambio_con_la_reorganizacion():
    assert _foto(config.SAP_FORMULARIO_AS01_BRP) == FOTO_AS01_BRP


@pytest.mark.parametrize("caso", list(config.SAP_FORMULARIOS_POR_CASO))
def test_formularios_coherentes_con_su_plantilla(caso):
    formulario = config.SAP_FORMULARIOS_POR_CASO[caso]
    columnas_plantilla = {c.letra for c in router.resolver(*caso).columnas}
    usadas = [p["columna"] for p in formulario if p["tipo"] in ("campo", "casilla")]

    assert set(usadas) <= columnas_plantilla            # toda columna existe en la plantilla
    assert len(usadas) == len(set(usadas))              # ninguna columna se usa dos veces
    assert caso in config.SAP_TRANSACCION_POR_CASO      # tiene transacción
    for paso in formulario:
        assert paso["tipo"] in ("campo", "casilla", "enter", "pestana")
        if paso["tipo"] != "enter":
            assert paso["xpath"] and all(x.startswith("//") for x in paso["xpath"])
    # Las pestañas van en orden (2, 3, 4...) y después del Enter.
    pestanas = [p["xpath"][0] for p in formulario if p["tipo"] == "pestana"]
    orden = [config.SAP_PESTANAS_ACTIVO[n][1][0] for n in sorted(config.SAP_PESTANAS_ACTIVO)]
    assert pestanas == orden[: len(pestanas)]
    tipos = [p["tipo"] for p in formulario]
    assert tipos.index("enter") < tipos.index("pestana")


# -- AS02 (modificación) -------------------------------------------------------------

AS02 = config.SAP_FORMULARIO_AS02_BRP


def _por_columna(formulario):
    return {p["columna"]: p for p in formulario if "columna" in p}


def test_as02_pantalla_inicial_y_transaccion():
    assert config.SAP_TRANSACCION_POR_CASO[("brp", "modificacion")] == "AS02"
    assert _foto(AS02[:4]) == [
        ("campo", "A", "Activo fijo", ['//*[@id="M0:46:::2:21"]']),
        ("campo", "B", "Subnúmero", ['//*[@id="M0:46:::3:21"]']),
        ("campo", "C", "Sociedad", ['//*[@id="M0:46:::4:21"]']),
        ("enter", None, "abrir el formulario completo", []),
    ]


def test_as02_usa_los_mismos_xpath_que_as01_en_los_campos_comunes():
    as01, as02 = _por_columna(config.SAP_FORMULARIO_AS01_BRP), _por_columna(AS02)
    comunes = {  # columna en AS01 -> columna en AS02 (mismo campo de SAP)
        "D": "D", "F": "G", "H": "N", "I": "O", "J": "P", "K": "Q", "L": "R",
        "M": "T", "N": "W", "O": "X", "P": "Y", "Q": "Z", "R": "AA", "T": "AC",
        "U": "AH", "V": "AN", "W": "AO", "X": "AP",
    }
    for c01, c02 in comunes.items():
        assert as01[c01]["xpath"] == as02[c02]["xpath"], (c01, c02)


@pytest.mark.parametrize("columna, id_esperado", [
    ("F", "M0:46:3:1:2B256:1::5:22"),     # Número de serie
    ("J", "M0:46:3:1:2B256:2::1:22"),     # Último inventario el
    ("K", "M0:46:3:1:2B256:2::2:22"),     # Nota de inventario
    ("L", "M0:46:3:1:2B256:3::1:67"),     # Descapitalización el
    ("M", "M0:46:3:1:2B256:3::3:67"),     # Pedido el
    ("Q", "M0:46:3:1:2B257:1::5:22"),     # Centro
    ("S", "M0:46:3:1:2B257:1::7:22"),     # Local
    ("U", "M0:46:3:1:2B257:1::9:22"),     # Número de personal
    ("V", "M0:46:3:1:2B257:1::10:22"),    # Elem. PEP
    ("AB", "M0:46:3:1:2B258:1::5:22"),    # Total depreciados
    ("AF", "M0:46:3:1:2B259:1::5:23"),    # Sociedad GL asociada
    ("AG", "M0:46:3:1:2B259:1::6:23"),    # País origen
    ("AI", "M0:46:3:1:2B259:1::9:23"),    # Activo fijo orig.
    ("AK", "M0:46:3:1:2B259:1::9:67"),    # Alta el
    ("AL", "M0:46:3:1:2B259:1::10:23"),   # Año adquis. orig.
    ("AM", "M0:46:3:1:2B259:1::11:23"),   # Valor original
    ("AQ", "M0:46:3:1:2B260:1::4:22"),    # Val. patrim. man.
    ("AR", "M0:46:3:1:2B260:2::1:22"),    # Delegación Hacienda
    ("AW", "M0:46:3:1:2B260:2::5:57"),    # Inscripción del
    ("AZ", "M0:46:3:1:2B260:2::6:34"),    # Nº actual
    ("BE", "M0:46:3:1:2B260:2::7:76"),    # Superficie campo 2
    ("BF", "M0:46:3:1:2B261:1::1:22"),    # Clase
    ("BG", "M0:46:3:1:2B261:1::2:22"),    # Nº de póliza
    ("BH", "M0:46:3:1:2B261:1::3:22"),    # Comentario
    ("BI", "M0:46:3:1:2B261:1::5:22"),    # Inicio
])
def test_as02_extras(columna, id_esperado):
    assert _por_columna(AS02)[columna]["xpath"] == [f'//*[@id="{id_esperado}"]']


def test_as02_casillas_y_pestanas():
    casillas = {p["columna"] for p in AS02 if p["tipo"] == "casilla"}
    assert casillas == {"W", "AD", "AE"}
    pestanas = [p["xpath"][0] for p in AS02 if p["tipo"] == "pestana"]
    assert pestanas == [f'//*[@id="M0:46:3:1::0:{n}-title"]' for n in range(1, 6)]


def test_as02_ignora_columnas_sin_campo():
    usadas = set(_por_columna(AS02))
    for columna in ("E", "I", "AJ", "BJ", "BK", "BL", "BM", "BN", "BO"):
        assert columna not in usadas


def test_as02_no_puede_guardar_hasta_conocer_su_mensaje_de_exito():
    assert "AS02" not in config.SAP_REGEX_EXITO_POR_TRANSACCION
    assert "AS01" in config.SAP_REGEX_EXITO_POR_TRANSACCION
