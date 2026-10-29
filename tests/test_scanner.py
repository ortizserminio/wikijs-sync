from wikijs_sync.scanner import slugify, compute_path, extract_title, split_locale
IDIOMAS = {"es", "va", "en"}


def test_slugify_acentos_y_espacios():
    assert slugify("Guía de Uso") == "guia-de-uso"

def test_slugify_mayusculas():
    assert slugify("REQUISITOS") == "requisitos"

def test_path_simple():
    assert compute_path("instalacion/requisitos.md", "pruebas") == "pruebas/instalacion/requisitos"

def test_path_quita_extension_y_minusculas():
    assert compute_path("Guia.md", "pruebas") == "pruebas/guia"

def test_path_readme_es_la_carpeta():
    assert compute_path("instalacion/README.md", "pruebas") == "pruebas/instalacion"

def test_path_index_es_la_carpeta():
    assert compute_path("index.md", "pruebas") == "pruebas"

def test_title_desde_encabezado():
    assert extract_title("# Mi Título\n\ntexto", "fallback") == "Mi Título"

def test_title_fallback_si_no_hay_encabezado():
    assert extract_title("sin encabezado", "nombre-fichero") == "nombre-fichero"


def test_locale_con_sufijo_va():
    assert split_locale("requisitos.va.md", "es", IDIOMAS) == ("va", "requisitos.md")

def test_locale_con_sufijo_en():
    assert split_locale("guia.en.md", "es", IDIOMAS) == ("en", "guia.md")

def test_locale_sin_sufijo_usa_por_defecto():
    assert split_locale("requisitos.md", "es", IDIOMAS) == ("es", "requisitos.md")

def test_locale_no_confunde_nombre_con_punto():
    assert split_locale("config.app.md", "es", IDIOMAS) == ("es", "config.app.md")

def test_path_ignora_sufijo_idioma():
    _loc, base = split_locale("requisitos.va.md", "es", IDIOMAS)
    assert compute_path(base, "pruebas") == "pruebas/requisitos"



def test_locale_no_confunde_extension_de_dos_letras():
    # 'js' no está en IDIOMAS, así que no se trata como locale
    assert split_locale("setup.js.md", "es", IDIOMAS) == ("es", "setup.js.md")
