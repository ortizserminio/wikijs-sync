from wikijs_sync.scanner import slugify, compute_path, extract_title

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
