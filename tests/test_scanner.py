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


def test_scan_varios_idiomas_comparten_path(tmp_path):
    from wikijs_sync.scanner import scan
    (tmp_path / "guia.md").write_text("# Guía\n", encoding="utf-8")
    (tmp_path / "guia.va.md").write_text("# Guia\n", encoding="utf-8")
    paginas = scan(str(tmp_path), "pruebas", allowed_locales={"es", "va"})
    assert {(p["path"], p["locale"]) for p in paginas} == {
        ("pruebas/guia", "es"), ("pruebas/guia", "va"),
    }


def test_scan_aviso_con_enlace_al_origen(tmp_path):
    from wikijs_sync.scanner import scan
    (tmp_path / "guia.md").write_text("# Guía\n", encoding="utf-8")
    pagina = scan(str(tmp_path), "pruebas",
                  source_url="https://gitlab.umh.es/g/r/-/blob/master")[0]
    assert pagina["content"].startswith("> Esta página se genera automáticamente")
    assert "/guia.md)" in pagina["content"]


def test_imagen_mismo_contenido_en_dry_run_y_real(tmp_path):
    from wikijs_sync.scanner import scan

    class ClienteFalso:
        def __init__(self):
            self.subidas = []
        def list_asset_names(self):
            return set()
        def upload_asset(self, ruta, nombre):
            self.subidas.append(nombre)

    (tmp_path / "logo.png").write_bytes(b"png")
    (tmp_path / "a.md").write_text("# A\n![logo](logo.png)\n", encoding="utf-8")
    cliente = ClienteFalso()
    real = scan(str(tmp_path), "pruebas/redes", client=cliente)[0]["content"]
    dry = scan(str(tmp_path), "pruebas/redes", client=None)[0]["content"]
    assert real == dry
    assert len(cliente.subidas) == 1
    assert cliente.subidas[0].startswith("pruebas-redes--logo-")

def test_imagen_ya_subida_no_se_vuelve_a_subir(tmp_path):
    from wikijs_sync.scanner import scan, asset_name

    (tmp_path / "logo.png").write_bytes(b"png")
    (tmp_path / "a.md").write_text("![logo](logo.png)\n", encoding="utf-8")
    ya_esta = asset_name("pruebas/redes", tmp_path / "logo.png")

    class ClienteFalso:
        subidas = []
        def list_asset_names(self):
            return {ya_esta}
        def upload_asset(self, ruta, nombre):
            self.subidas.append(nombre)

    cliente = ClienteFalso()
    scan(str(tmp_path), "pruebas/redes", client=cliente)
    assert cliente.subidas == []


# --- Tests para protección de docs_dir vacío (Problema 1) ---
def test_scan_falla_si_docs_dir_no_existe(tmp_path):
    """scan() debe fallar si docs_dir no existe (protección contra --prune destructivo)."""
    from wikijs_sync.scanner import scan, ScanError
    import pytest
    
    with pytest.raises(ScanError) as exc:
        scan(str(tmp_path / "no-existe"), "pruebas")
    assert "no existe" in str(exc.value)

def test_scan_falla_si_docs_dir_vacio(tmp_path):
    """scan() debe fallar si docs_dir existe pero no tiene .md."""
    from wikijs_sync.scanner import scan, ScanError
    import pytest
    
    # Carpeta existe pero vacía
    (tmp_path / "docs").mkdir()
    with pytest.raises(ScanError) as exc:
        scan(str(tmp_path / "docs"), "pruebas")
    assert "ningún fichero .md" in str(exc.value)

# --- Test para BOM (Problema 8) ---
def test_scan_ignora_bom_de_windows(tmp_path):
    """Los ficheros con BOM de Windows deben parsearse correctamente."""
    from wikijs_sync.scanner import scan
    
    # Escribir fichero con BOM (común en Windows)
    contenido_con_bom = b'\xef\xbb\xbf---\ntitle: Con BOM\n---\n# Titulo\n'
    (tmp_path / "doc.md").write_bytes(contenido_con_bom)
    
    paginas = scan(str(tmp_path), "pruebas")
    assert len(paginas) == 1
    # El front matter debe haberse parseado bien (título del YAML, no del #)
    assert paginas[0]["title"] == "Con BOM"


# --- Test para Error 5: título no sale de comentario en código ---
def test_titulo_ignora_comentario_en_bloque_codigo():
    """El título no debe salir de un comentario dentro de un bloque de código."""
    from wikijs_sync.scanner import extract_title
    
    contenido = """```bash
# instalar paquetes
apt-get install python3
```

# Título Real

Contenido aquí.
"""
    titulo = extract_title(contenido, "fallback")
    # Debe ser "Título Real", no "instalar paquetes"
    assert titulo == "Título Real"


def test_titulo_fallback_si_solo_hay_codigo():
    """Si solo hay comentarios en código, usa el fallback."""
    from wikijs_sync.scanner import extract_title
    
    contenido = """```python
# Este es un comentario de Python
print("hola")
```

Sin encabezado real aquí.
"""
    titulo = extract_title(contenido, "mi-fallback")
    assert titulo == "mi-fallback"
